import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import build_index  # noqa: E402


def test_every_hash_is_of_the_bytes_served(tmp_path):
    index = build_index.build(tmp_path / "out", repo="owner/repo")
    assert index["listings"], "the shipped library builds"
    for listing in index["listings"]:
        for version in listing["versions"]:
            served = (tmp_path / "out" / version["path"]).read_bytes()
            assert hashlib.sha256(served).hexdigest() == version["sha256"]


def test_tiers_follow_the_namespace(tmp_path):
    index = build_index.build(tmp_path / "out")
    assert {l["tier"] for l in index["listings"] if l["publisher"] == "yaaf"} == {"official"}


def test_the_index_says_what_each_version_can_do(tmp_path):
    index = build_index.build(tmp_path / "out")
    engine = next(l for l in index["listings"] if l["id"] == "@yaaf/a-content-engine")
    latest = engine["versions"][-1]
    assert "wordpress" in latest["keys"] and "web" in latest["can_do"]
    assert latest["inputs"] == ["subject", "site", "publication"]
    json.dumps(index)


def test_outcomes_ride_on_the_listing(tmp_path):
    index = build_index.build(tmp_path / "out", outcomes={"@yaaf/writer": {"reports": 2, "finished": 1}})
    writer = next(l for l in index["listings"] if l["id"] == "@yaaf/writer")
    assert writer["outcomes"] == {"reports": 2, "finished": 1}
