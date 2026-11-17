"""Run yaaf's $0 fire drill on every project listing a pull request touches.

    python tools/drill.py --base origin/main --out drill.json

Each project's latest version is filled with its blanks' examples and handed to
`yaaf rehearse`, which runs it on a mock runtime and calls no model. The result
is one line per listing for the review card; a drill that says the project
cannot start fails this step.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--yaaf", default="yaaf", help="the yaaf command")
    args = parser.parse_args()
    report, listings, _ = check.run(args.base)
    results: dict[str, str] = {}
    failed = False
    for listing in listings:
        if not listing.versions or (listing.meta or {}).get("kind") != "project":
            continue
        version = listing.versions[max(listing.versions)]
        inputs = {i["id"]: i for i in version.get("inputs") or []}
        bundle = check.fill(version["bundle"], inputs)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(bundle, fh)
        run = subprocess.run([args.yaaf, "rehearse", fh.name, "--json"], capture_output=True, text=True,
                             timeout=300)
        Path(fh.name).unlink(missing_ok=True)
        if run.returncode != 0:
            results[listing.id] = f"✗ could not run: {(run.stderr or run.stdout).strip()[:300]}"
            failed = True
            continue
        try:
            verdict = json.loads(run.stdout)
        except ValueError:
            results[listing.id] = "✗ the drill printed something that is not JSON"
            failed = True
            continue
        starts = verdict.get("verdict") or verdict.get("summary") or {}
        ok = bool(verdict.get("ok", verdict.get("passed", True)))
        results[listing.id] = ("✓ " if ok else "✗ ") + (
            starts if isinstance(starts, str) else json.dumps(starts)[:300])
        failed = failed or not ok
    args.out.write_text(json.dumps(results, indent=1))
    for k, v in results.items():
        print(f"{k}: {v}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
