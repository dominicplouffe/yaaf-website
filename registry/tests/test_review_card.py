import copy
import json

import check
import review_card
from conftest import errors  # noqa: F401  (fixture module)


def _card(registry, monkeypatch, listing_id, previous=None, author="rae", first=False):
    handle, slug = listing_id.lstrip("@").split("/")
    monkeypatch.setattr(review_card, "ROOT", registry)
    base = {}
    if previous is not None:
        base[f"listings/{handle}/{slug}/versions/1.json"] = previous
    monkeypatch.setattr(review_card, "at_base",
                        lambda ref, rel: base.get(rel.as_posix()) if not first else None)
    monkeypatch.setattr(review_card, "risk_read", lambda prompt: [])
    listing = check.load(registry / "listings" / handle / slug, check.Report())
    return review_card.card_for(listing, "origin/main", author, check.Report(), {})


def _move(registry, src, handle):
    """Republish an official listing under a community handle, as version 2."""
    src_dir = registry / "listings" / "yaaf" / src
    dest = registry / "listings" / handle / src
    dest.mkdir(parents=True)
    (dest / "versions").mkdir()
    meta = json.loads((src_dir / "listing.json").read_text())
    meta["id"] = f"@{handle}/{src}"
    (dest / "listing.json").write_text(json.dumps(meta))
    v1 = json.loads((src_dir / "versions" / "1.json").read_text())
    v1["id"] = meta["id"]
    (dest / "versions" / "1.json").write_text(json.dumps(v1))
    return dest, v1


def test_a_role_that_runs_commands_with_a_key_needs_two(registry, monkeypatch):
    _move(registry, "blog-writer", "rae")
    _, high, reasons = _card(registry, monkeypatch, "@rae/blog-writer")
    assert high and "has a shell while holding a key" in reasons


def test_an_update_that_adds_a_power_needs_two_and_shows_the_diff(registry, monkeypatch):
    dest, v1 = _move(registry, "writer", "rae")
    v2 = copy.deepcopy(v1)
    v2["version"] = 2
    v2["role"]["tool_permissions"]["bash"] = True
    v2["role"]["system_prompt"] += "\nAlso tidy the workspace with shell commands."
    (dest / "versions" / "2.json").write_text(json.dumps(v2))
    card, high, reasons = _card(registry, monkeypatch, "@rae/writer", previous=v1)
    assert high and any("adds bash" in r for r in reasons)
    assert "+Also tidy the workspace" in card and "(update)" in card


def test_a_plain_update_from_a_known_publisher_needs_one(registry, monkeypatch):
    dest, v1 = _move(registry, "writer", "rae")
    v2 = copy.deepcopy(v1)
    v2["version"] = 2
    v2["role"]["system_prompt"] += "\nKeep headings short."
    (dest / "versions" / "2.json").write_text(json.dumps(v2))
    _, high, reasons = _card(registry, monkeypatch, "@rae/writer", previous=v1)
    assert not high, reasons
