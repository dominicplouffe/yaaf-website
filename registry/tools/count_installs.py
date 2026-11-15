"""Count installs from CloudFront access logs into counts.json.

    python tools/count_installs.py LOG_DIR [--counts counts.json]

An install is yaaf downloading a listing version file
(/marketplace/listings/<handle>/<slug>/versions/<n>.json) with a 200. One
address counts once per listing per day, so refreshing a page or a retry loop
does not inflate a number people choose by. yaaf sends no telemetry: these
logs are the only source, and they hold nothing yaaf did not already send to
fetch the file.

Counts accumulate: each run adds the days it reads to the existing file, and
remembers which log files it has read so a file is never counted twice.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

PATH = re.compile(r"^/marketplace/listings/([a-z0-9][a-z0-9-]{0,38})/([a-z0-9-]{2,64})/versions/\d+\.json$")


def count_file(path: Path) -> dict[str, set[tuple[str, str]]]:
    seen: dict[str, set[tuple[str, str]]] = {}
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
        fields: list[str] = []
        for line in fh:
            if line.startswith("#Fields:"):
                fields = line.split()[1:]
                continue
            if line.startswith("#") or not fields:
                continue
            row = dict(zip(fields, line.rstrip("\n").split("\t"), strict=False))
            if row.get("cs-method") != "GET" or row.get("sc-status") != "200":
                continue
            match = PATH.match(row.get("cs-uri-stem", ""))
            if not match:
                continue
            listing = f"@{match.group(1)}/{match.group(2)}"
            seen.setdefault(listing, set()).add((row.get("date", ""), row.get("c-ip", "")))
    return seen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("logs", type=Path)
    parser.add_argument("--counts", type=Path, default=Path(__file__).resolve().parents[1] / "counts.json")
    args = parser.parse_args()
    state = json.loads(args.counts.read_text()) if args.counts.exists() else {}
    counts: dict[str, int] = state.get("counts", {})
    read: set[str] = set(state.get("read", []))
    for path in sorted(p for p in args.logs.iterdir() if p.is_file()):
        if path.name in read:
            continue
        for listing, visits in count_file(path).items():
            counts[listing] = counts.get(listing, 0) + len(visits)
        read.add(path.name)
    args.counts.write_text(json.dumps({"counts": dict(sorted(counts.items())),
                                       "read": sorted(read)[-5000:]}, indent=1) + "\n")
    print(f"{sum(counts.values())} installs across {len(counts)} listings")


if __name__ == "__main__":
    main()
