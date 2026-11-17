"""Build index.json, and the folder that serves it, from listings/.

    python tools/build_index.py --out dist/

Writes <out>/index.json and copies every listing under <out>/listings/, so the
paths in the index resolve relative to the index's own URL. The sha256 of each
version is of the exact bytes copied, which are the bytes yaaf will download.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTINGS = ROOT / "listings"
OFFICIAL = {"yaaf"}


def summarise(version: dict) -> dict:
    """What a version can do and needs, in the words the install screen uses."""
    if version.get("kind") == "role":
        roles = [version.get("role") or {}]
    else:
        roles = list((version.get("bundle") or {}).get("roles") or [])
    can_do = sorted({tool for role in roles
                     for tool, on in (role.get("tool_permissions") or {}).items() if on is True})
    needs = version.get("needs") or {}
    return {
        "can_do": can_do,
        "keys": [k["name"] for k in needs.get("keys") or []],
        "required_keys": [k["name"] for k in needs.get("keys") or [] if k.get("required")],
        "data_sources": [s["name"] for s in needs.get("data_sources") or []],
        "mailbox": bool(needs.get("mailbox")),
        "github_repo": bool(needs.get("github_repo")),
        "inputs": [i["id"] for i in version.get("inputs") or []],
        "roles": [r.get("slug") for r in roles],
        "has_receipt": bool(version.get("receipt")),
    }


def build(out: Path, *, repo: str | None = None, client_id: str | None = None,
          counts: dict[str, int] | None = None, outcomes: dict[str, dict] | None = None) -> dict:
    counts = counts or {}
    outcomes = outcomes or {}
    listings = []
    if out.exists():
        shutil.rmtree(out)
    (out / "listings").mkdir(parents=True)
    for folder in sorted(p for p in LISTINGS.glob("*/*") if p.is_dir()):
        meta = json.loads((folder / "listing.json").read_text())
        handle = folder.parent.name
        dest = out / "listings" / handle / folder.name
        (dest / "versions").mkdir(parents=True)
        shutil.copyfile(folder / "listing.json", dest / "listing.json")
        versions = []
        for path in sorted((folder / "versions").glob("*.json"), key=lambda p: int(p.stem)):
            raw = path.read_bytes()
            (dest / "versions" / path.name).write_bytes(raw)
            version = json.loads(raw)
            versions.append({
                "version": version["version"],
                "path": f"listings/{handle}/{folder.name}/versions/{path.name}",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "published_at": version["published_at"],
                "changes": version["changes"],
                **summarise(version),
            })
        listings.append({
            **meta,
            "publisher": handle,
            "tier": "official" if handle in OFFICIAL else "community",
            "latest": versions[-1]["version"] if versions else None,
            "versions": versions,
            "installs": int(counts.get(meta["id"], 0)),
            # How it went for people who ran it and chose to say, from
            # tools/outcomes.py. Never the publisher's own report.
            **({"outcomes": outcomes[meta["id"]]} if meta["id"] in outcomes else {}),
        })
    index = {
        "registry": {
            "spec": 1,
            "name": "yaaf marketplace",
            "publish": {"method": "github-pr", "repo": repo, "client_id": client_id},
        },
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "listings": listings,
    }
    (out / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n")
    return index


def _read(path: Path) -> dict:
    return json.loads(path.read_text()) if path and path.exists() else {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--repo", help="owner/repo pull requests go to")
    parser.add_argument("--client-id", help="the GitHub OAuth app publishers sign in with")
    parser.add_argument("--counts", type=Path, default=ROOT / "counts.json",
                        help="installs per listing, from tools/count_installs.py")
    parser.add_argument("--outcomes", type=Path, default=ROOT / "outcomes.json",
                        help="reports per listing, from tools/outcomes.py")
    args = parser.parse_args()
    counts = _read(args.counts)
    counts = counts.get("counts", counts)
    settings = _read(ROOT / "registry.json")
    index = build(args.out, repo=args.repo or settings.get("repo"),
                  client_id=args.client_id or settings.get("client_id"), counts=counts,
                  outcomes=_read(args.outcomes))
    print(f"{len(index['listings'])} listing(s) → {args.out / 'index.json'}")


if __name__ == "__main__":
    main()
