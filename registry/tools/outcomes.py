"""Turn the registry's "Outcome:" issues into outcomes.json.

    gh api --paginate "repos/OWNER/REPO/issues?state=all&per_page=100" > issues.json
    python tools/outcomes.py issues.json > outcomes.json

yaaf opens one issue per project that chose to report how a listing went:
numbers from its receipt and nothing else. This counts them per listing.

So a listing cannot grade itself: a report from the listing's own publisher is
not counted, and each GitHub account counts once per listing (its latest
report). Reports that do not parse are skipped, never guessed at.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

TITLE = re.compile(r"^Outcome: (@[a-z0-9][a-z0-9-]{0,38}/[a-z0-9-]{2,64}) v(\d+)$")
BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)
NUMBERS = ("days", "runs", "requirements_met", "requirements", "claims_verified", "claims")


def parse(issue: dict) -> dict | None:
    title = TITLE.match(str(issue.get("title") or "").strip())
    found = BLOCK.search(str(issue.get("body") or ""))
    if not title or not found:
        return None
    try:
        report = json.loads(found.group(1))
    except ValueError:
        return None
    if report.get("listing") != title.group(1):
        return None
    for key in NUMBERS:
        if not isinstance(report.get(key), int) or report[key] < 0:
            return None
    if report["requirements_met"] > report["requirements"]:
        return None
    usd = report.get("usd")
    if usd is not None and (not isinstance(usd, (int, float)) or usd < 0):
        return None
    return {"listing": title.group(1), "version": int(title.group(2)),
            "author": str((issue.get("user") or {}).get("login") or "").lower(),
            "at": issue.get("created_at") or "", "finished": bool(report.get("finished")),
            "days": report["days"], "usd": usd,
            "requirements_met": report["requirements_met"], "requirements": report["requirements"]}


def aggregate(issues: list[dict]) -> dict:
    latest: dict[tuple[str, str], dict] = {}
    for issue in issues:
        if "pull_request" in issue:
            continue
        report = parse(issue)
        if report is None or not report["author"]:
            continue
        publisher = report["listing"][1:].split("/")[0]
        if report["author"] == publisher:
            continue
        key = (report["listing"], report["author"])
        if key not in latest or report["at"] > latest[key]["at"]:
            latest[key] = report
    by_listing: dict[str, list[dict]] = {}
    for (listing, _), report in latest.items():
        by_listing.setdefault(listing, []).append(report)
    out = {}
    for listing, reports in sorted(by_listing.items()):
        costs = [r["usd"] for r in reports if r["usd"] is not None]
        required = sum(r["requirements"] for r in reports)
        out[listing] = {
            "reports": len(reports),
            "finished": sum(r["finished"] for r in reports),
            "median_days": statistics.median(r["days"] for r in reports),
            "median_usd": round(statistics.median(costs), 2) if costs else None,
            "requirements_met_share": round(sum(r["requirements_met"] for r in reports) / required, 2)
            if required else None,
        }
    return out


def main() -> int:
    issues = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else json.load(sys.stdin)
    if isinstance(issues, dict):
        issues = [issues]
    print(json.dumps(aggregate(issues), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
