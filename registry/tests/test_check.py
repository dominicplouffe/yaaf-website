"""Every rule check.py enforces, attacked the way a submission would."""

import json

import check
from conftest import edit, errors


def test_the_shipped_library_passes(registry):
    assert errors() == []


def test_a_key_pasted_into_a_prompt_is_refused(registry):
    edit(registry, "yaaf/writer", 1, lambda b: b["role"].__setitem__(
        "system_prompt", b["role"]["system_prompt"] + " Use sk-ant-api03-" + "x" * 40))
    assert any("Anthropic key" in e for e in errors())


def test_a_key_hidden_deep_in_a_project_is_refused(registry):
    edit(registry, "yaaf/a-content-engine", 1,
         lambda b: b["bundle"]["project"]["integrations"].__setitem__("note", "ghp_" + "a" * 36))
    assert any("GitHub token" in e for e in errors())


def test_a_secret_value_in_the_bundle_is_refused(registry):
    edit(registry, "yaaf/a-content-engine", 1,
         lambda b: b["bundle"]["secrets"][0].__setitem__("value", "admin:abcd efgh"))
    assert any("carries a value" in e for e in errors())


def test_a_prompt_reading_an_undeclared_key_is_refused(registry):
    edit(registry, "yaaf/writer", 1, lambda b: b["role"].__setitem__(
        "system_prompt", b["role"]["system_prompt"] + " Post with $SHOPIFY_TOKEN."))
    assert any("$SHOPIFY_TOKEN" in e for e in errors())


def test_a_shell_variable_is_not_a_credential(registry):
    edit(registry, "yaaf/writer", 1, lambda b: b["role"].__setitem__(
        "system_prompt", b["role"]["system_prompt"] + " Work under $HOME and $WORKSPACE."))
    assert errors() == []


def test_a_declared_key_no_role_receives_is_refused(registry):
    edit(registry, "yaaf/writer", 1, lambda b: b["needs"]["keys"].append(
        {"name": "stripe", "label": "Stripe key", "roles": ["writer"], "required": True}))
    assert any("'stripe'" in e for e in errors())


def test_a_data_source_the_prompt_calls_must_be_declared(registry):
    edit(registry, "yaaf/researcher", 1, lambda b: b["role"].__setitem__(
        "system_prompt", b["role"]["system_prompt"] + " Call mcp__crm__search first."))
    assert any("mcp__crm__" in e for e in errors())


def test_a_role_never_has_blanks(registry):
    edit(registry, "yaaf/writer", 1, lambda b: b["role"].__setitem__(
        "system_prompt", b["role"]["system_prompt"] + " Write for {{business}}."))
    assert any("never have blanks" in e for e in errors())


def test_a_blank_must_be_declared_and_every_input_used(registry):
    def change(b):
        b["bundle"]["project"]["goal"] += " Mention {{brand}}."
        b["inputs"].append({"id": "unused", "question": "Never asked?", "type": "text",
                            "example": "x", "required": False})
    edit(registry, "yaaf/a-content-engine", 1, change)
    found = errors()
    assert any("{{brand}}" in e for e in found)
    assert any("'unused'" in e for e in found)


def test_the_publishers_own_account_never_travels(registry):
    edit(registry, "yaaf/settle-an-argument", 1,
         lambda b: b["bundle"]["project"].__setitem__("chairman_email", "me@acme.com"))
    assert any("chairman_email" in e for e in errors())


def test_a_bring_your_own_source_carries_no_address(registry):
    def change(b):
        b["bundle"]["project"]["integrations"]["mcp_servers"] = [
            {"name": "ads", "url_secret": "ads-url", "url_host": "10.0.0.4", "url_port": 8080,
             "roles": ["writer"]}]
        b["needs"]["data_sources"] = [{"name": "ads", "serves": "Ad reports", "address": "bring-your-own",
                                       "auth": "none", "access": "bulk", "tools": [], "roles": ["writer"],
                                       "required": True}]
    edit(registry, "yaaf/your-first-hour", 1, change)
    assert any("carries an address" in e for e in errors())


def test_a_hired_role_must_travel_with_the_project(registry):
    edit(registry, "yaaf/settle-an-argument", 1,
         lambda b: b["bundle"].__setitem__("roles", [r for r in b["bundle"]["roles"] if r["slug"] != "writer"]))
    assert any("does not carry it" in e for e in errors())


def test_a_role_listing_must_be_named_for_its_role(registry):
    edit(registry, "yaaf/writer", 1, lambda b: b["role"].__setitem__("slug", "engineer"))
    assert any("listing's own slug" in e for e in errors())


def test_yaaf_itself_refuses_what_yaaf_would_refuse(registry):
    import pytest

    pytest.importorskip("yaaf", reason="yaaf's own validators run where yaaf is installed")
    edit(registry, "yaaf/writer", 1, lambda b: b["role"].__setitem__("effort", "ludicrous"))
    assert any("yaaf would refuse role writer" in e for e in errors())


def test_versions_have_no_gaps(registry):
    folder = registry / "listings" / "yaaf" / "writer" / "versions"
    (folder / "3.json").write_text((folder / "1.json").read_text().replace('"version": 1', '"version": 3'))
    assert any("no gaps" in e for e in errors())


# ── what a pull request may touch ──────────────────────────────────────────────

def change_errors(rows, author):
    report = check.Report()
    check.check_change(rows, author, report)
    return [e["text"] for e in report.errors]


def test_a_merged_version_never_changes():
    assert any("never changes" in e for e in change_errors(
        [("M", "listings/rae/ads-audit/versions/1.json")], "rae"))
    assert any("never changes" in e for e in change_errors(
        [("D", "listings/rae/ads-audit/versions/1.json")], "rae"))


def test_a_new_version_is_fine():
    assert change_errors([("A", "listings/rae/ads-audit/versions/2.json")], "rae") == []


def test_you_publish_only_under_your_own_name():
    assert any("@rae may only publish under @rae" in e for e in change_errors(
        [("A", "listings/sam/thing/versions/1.json")], "rae"))
    assert change_errors([("A", "listings/RAE/thing/versions/1.json")], "rae") == []


def test_the_official_namespace_is_reserved():
    assert any("reserved" in e for e in change_errors(
        [("A", "listings/yaaf/new-role/versions/1.json")], "yaaf"))


def test_moderators_may_mark_anyone_removed(registry, monkeypatch):
    (registry / "MODERATORS").write_text("@mod\n")
    assert change_errors([("M", "listings/rae/ads-audit/listing.json")], "mod") == []


def test_only_moderators_touch_the_registrys_own_files(registry):
    (registry / "MODERATORS").write_text("mod\n")
    assert any("only moderators" in e for e in change_errors([("M", "tools/check.py")], "rae"))
    assert change_errors([("M", "tools/check.py")], "mod") == []


def test_the_schema_files_are_valid_json(registry):
    for path in (registry / "schema").glob("*.json"):
        json.loads(path.read_text())
