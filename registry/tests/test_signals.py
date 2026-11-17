"""Install counts and outcome reports, attacked: the two numbers people
choose by are the two worth inflating."""

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import count_installs  # noqa: E402
import outcomes  # noqa: E402


def issue(listing, author, *, n=1, at="2026-11-10T00:00:00Z", **report):
    body = {"listing": listing, "version": n, "finished": True, "days": 3, "usd": 40.0, "runs": 12,
            "requirements_met": 9, "requirements": 9, "claims_verified": 4, "claims": 4, **report}
    return {"title": f"Outcome: {listing} v{n}", "user": {"login": author}, "created_at": at,
            "body": "Numbers only.\n\n```json\n" + json.dumps(body) + "\n```\n"}


def test_a_publisher_cannot_grade_their_own_listing():
    assert outcomes.aggregate([issue("@rae/desk", "rae")]) == {}


def test_one_account_counts_once_per_listing():
    out = outcomes.aggregate([issue("@rae/desk", "sam", usd=10.0, at="2026-11-01T00:00:00Z"),
                              issue("@rae/desk", "sam", usd=30.0, at="2026-11-09T00:00:00Z"),
                              issue("@rae/desk", "kim", usd=50.0)])
    assert out["@rae/desk"]["reports"] == 2 and out["@rae/desk"]["median_usd"] == 40.0


def test_a_report_that_does_not_add_up_is_skipped():
    bad = [issue("@rae/desk", "sam", requirements_met=12, requirements=9),
           issue("@rae/desk", "kim", days=-1),
           {**issue("@rae/desk", "lee"), "title": "Outcome: @sam/other v1"},
           {**issue("@rae/desk", "max"), "body": "no numbers here"}]
    assert outcomes.aggregate(bad) == {}


def test_pull_requests_are_not_reports():
    pr = {**issue("@rae/desk", "sam"), "pull_request": {"url": "x"}}
    assert outcomes.aggregate([pr]) == {}


def _log(path, rows):
    fields = "date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status"
    lines = ["#Version: 1.0", f"#Fields: {fields}"]
    lines += ["\t".join([d, "00:00:00", "YUL", "100", ip, m, "h", uri, st]) for d, ip, m, uri, st in rows]
    with gzip.open(path, "wt") as fh:
        fh.write("\n".join(lines) + "\n")


def test_installs_count_one_address_once_a_day(tmp_path, monkeypatch):
    logs = tmp_path / "logs"
    logs.mkdir()
    uri = "/marketplace/listings/rae/desk/versions/1.json"
    _log(logs / "a.gz", [("2026-11-10", "1.1.1.1", "GET", uri, "200")] * 50
         + [("2026-11-10", "2.2.2.2", "GET", uri, "200"),
            ("2026-11-11", "1.1.1.1", "GET", uri, "200"),
            ("2026-11-11", "3.3.3.3", "GET", uri, "404"),
            ("2026-11-11", "4.4.4.4", "GET", "/marketplace/index.json", "200")])
    counts = tmp_path / "counts.json"
    monkeypatch.setattr(sys, "argv", ["count_installs", str(logs), "--counts", str(counts)])
    count_installs.main()
    assert json.loads(counts.read_text())["counts"] == {"@rae/desk": 3}
    count_installs.main()  # the same file again is not counted twice
    assert json.loads(counts.read_text())["counts"] == {"@rae/desk": 3}
