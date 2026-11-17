"""Publish the library that ships with yaaf as @yaaf listings.

    YAAF_REPO=../yaaf python tools/import_yaaf.py

Reads roles/*.json and examples/*.json from a yaaf checkout and writes
listings/yaaf/<slug>/. An existing listing gets a new version only when what it
installs changed; otherwise it is left exactly as it is, because a version once
merged never changes.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "listings" / "yaaf"
YAAF = Path(os.environ.get("YAAF_REPO", ROOT.parents[1] / "yaaf")).resolve()

#: The commit before the example write-ups were deleted; their "what you get"
#: paragraphs are the best description each example ever had.
WRITEUPS_AT = "ee91e2a^"

KEYS = {
    "wordpress": {"label": "WordPress application password", "format": "username:application-password",
                  "help": "https://wordpress.org/documentation/article/application-passwords/"},
    "github": {"label": "GitHub token for the project's repository",
               "format": "a fine-grained personal access token",
               "help": "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"},
    "market-data": {"label": "Market data API key", "format": "your data provider's API key"},
    "news-api": {"label": "News API key", "format": "your news provider's API key"},
}

#: Each example's blanks: the text that becomes `{{id}}` (or is dropped), and the
#: question the Founder asks. Every `find` must be in the goal, or the import stops.
EXAMPLES = {
    "01-your-first-hour": {
        "slug": "your-first-hour", "category": "content", "domains": ["general"],
        "summary": "One 800-word briefing note that explains a subject you name to a smart beginner.",
        "edits": [("RUNNING A MARATHON", "{{subject}}"),
                  ("Replace that subject with whatever I actually want to understand before you start planning. ", "")],
        "inputs": [{"id": "subject", "question": "What do you want explained?", "type": "text",
                    "example": "running a marathon", "required": True}],
    },
    "02-settle-an-argument": {
        "slug": "settle-an-argument", "category": "research", "domains": ["general"],
        "summary": "A memo that answers one question you are stuck on, with evidence you could defend.",
        "edits": [("SHOULD A SMALL TEAM START ON POSTGRES OR SQLITE?", "{{question}}"),
                  (" Replace that with my actual question first.", "")],
        "inputs": [{"id": "question", "question": "What question should it settle?", "type": "text",
                    "example": "Should a small team start on Postgres or SQLite?", "required": True}],
    },
    "03-a-desk-the-world-wakes": {
        "slug": "a-desk-the-world-wakes", "category": "build", "domains": ["general"],
        "summary": "A standing triage desk that answers what arrives at your project's webhook, day and night.",
        "edits": [("MY SIDE PROJECT — replace that with what you are actually watching before planning.", "{{product}}.")],
        "inputs": [{"id": "product", "question": "Which product does the desk watch?", "type": "text",
                    "example": "my side project", "required": True}],
    },
    "04-an-overnight-crew": {
        "slug": "an-overnight-crew", "category": "build", "domains": ["general"],
        "summary": "Keeps a repository you own healthy overnight: one valuable piece of maintenance a night.",
        "edits": [("MY REPO", "the repository set in this project's Settings")],
        "inputs": [],
    },
    "05-a-tutor-that-adapts": {
        "slug": "a-tutor-that-adapts", "category": "content", "domains": ["education"],
        "summary": "One lesson a week on a subject you choose, re-planned around what you actually get wrong.",
        "edits": [("Teach me SQL,", "Teach me {{subject}},"),
                  (" Replace the subject with what I want to learn before planning.", "")],
        "inputs": [{"id": "subject", "question": "What do you want to learn?", "type": "text",
                    "example": "SQL", "required": True}],
    },
    "06-a-red-team": {
        "slug": "a-red-team", "category": "challenge", "domains": ["general"],
        "summary": "Builds one small tool, then a second team tries to break it until it cannot.",
        "edits": [("A COMMAND-LINE TOOL THAT VALIDATES AND NORMALISES CSV FILES AGAINST A SCHEMA — replace that with "
                   "what I actually want, keeping it small enough that hardening it is the interesting part.",
                   "{{thing}}. Keep it small enough that hardening it is the interesting part.")],
        "inputs": [{"id": "thing", "question": "What small thing should it build and attack?", "type": "text",
                    "example": "a command-line tool that validates and normalises CSV files against a schema",
                    "required": True}],
    },
    "07-tell-me-what-changed": {
        "slug": "tell-me-what-changed", "category": "research", "domains": ["general"],
        "summary": "A weekly note on what changed in the things you depend on, and only what matters to you.",
        "edits": [("PYTHON'S RELEASE NOTES AND MAJOR WEB-FRAMEWORK RELEASES", "{{watch}}"),
                  (" Replace that with what I depend on before planning.", "")],
        "inputs": [{"id": "watch", "question": "What should it watch for you?", "type": "text",
                    "example": "Python's release notes and major web-framework releases", "required": True}],
    },
    "08-a-game-you-can-play": {
        "slug": "a-game-you-can-play", "category": "build", "domains": ["games"],
        "summary": "A small browser game you can actually play, built, tested and tuned by a game team.",
        "edits": [], "inputs": [],
    },
    "09-one-idea-thirty-days": {
        "slug": "one-idea-thirty-days", "category": "growth", "domains": ["general"],
        "summary": "One software idea worth building, with outside proof that someone wants it, in 30 days.",
        "edits": [], "inputs": [],
    },
    "10-read-the-filings": {
        "slug": "read-the-filings", "category": "research", "domains": ["markets"],
        "summary": "An initiation note on a US-listed company you name, built only from its SEC filings.",
        "edits": [("ONE US-LISTED COMPANY I NAME", "{{company}}")],
        "inputs": [{"id": "company", "question": "Which US-listed company?", "type": "text",
                    "example": "a US-listed company you know", "required": True}],
    },
    "11-numbers-you-can-defend": {
        "slug": "numbers-you-can-defend", "category": "research", "domains": ["data"],
        "summary": "Answers a question from a public dataset so a skeptic could re-derive every number.",
        "edits": [("WHICH COLLEGE MAJORS ACTUALLY PAY, AND HOW SURE CAN ANYONE HONESTLY BE — replace that with whatever "
                   "you actually want to know from this data, or point the whole project at a different public CSV entirely.",
                   "{{question}}")],
        "inputs": [{"id": "question", "question": "What should the data answer?", "type": "text",
                    "example": "Which college majors actually pay, and how sure can anyone honestly be?",
                    "required": True}],
    },
    "12-a-content-engine": {
        "slug": "a-content-engine", "category": "content", "domains": ["general"],
        "summary": "Blog posts on your subject, drafted to WordPress, graded by whether real readers respond.",
        "edits": [("ONE SUBJECT I ACTUALLY KNOW SOMETHING ABOUT — replace this with yours, and name the site they go to.",
                   "{{subject}}, for {{site}}."),
                  ("NAME THE ONE YOU WOULD BE COMPARED TO", "{{publication}}")],
        "controlled_domains": ["{{site}}"],
        "inputs": [
            {"id": "subject", "question": "What subject do you know well enough to judge a post on?",
             "type": "text", "example": "home espresso", "required": True},
            {"id": "site", "question": "Which site do the posts go to?", "type": "domain",
             "example": "your-site.example", "required": True},
            {"id": "publication", "question": "Which publication would your posts be compared to?",
             "type": "text", "example": "the publication your readers already trust on this subject",
             "required": True},
        ],
    },
}


def role_summary(description: str) -> str:
    first = re.split(r"(?<=[.!?])\s", description.strip(), maxsplit=1)[0]
    if len(first) <= 160:
        return first
    cut = first[:157].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def needs_for(roles: list[dict], *, required: set[str] = frozenset(), github_repo=False,
              mailbox=False) -> dict:
    keys: dict[str, dict] = {}
    for role in roles:
        for scope in role.get("secret_scopes") or []:
            entry = keys.setdefault(scope, {"name": scope, **{k: v for k, v in KEYS.get(scope, {
                "label": scope.replace("-", " ").capitalize() + " key"}).items()},
                "file": False, "roles": [], "required": scope in required})
            entry["roles"].append(role["slug"])
    return {"keys": list(keys.values()), "data_sources": [], "mailbox": mailbox, "github_repo": github_repo}


def writeup(stem: str) -> dict:
    try:
        text = subprocess.run(["git", "show", f"{WRITEUPS_AT}:examples/{stem}.md"], cwd=YAAF,
                              capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}

    def para(*labels: str) -> str | None:
        for label in labels:
            m = re.search(rf"\*\*{label}:\*\*\s*(.+?)(?:\n\n|\Z)", text, re.S)
            if m:
                clean = re.sub(r"\s+", " ", m.group(1)).strip()
                clean = re.sub(r"[*_`]", "", clean)
                return (clean[:1].upper() + clean[1:])[:800]
        return None

    details = {"what_you_get": para("What you get"), "what_it_costs": para("What it costs", "Cost"),
               "what_you_need": para("What you need")}
    return {k: v for k, v in details.items() if v}


def write_listing(slug: str, meta: dict, version_body: dict) -> str:
    folder = OUT / slug
    versions = folder / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    existing = sorted(versions.glob("*.json"), key=lambda p: int(p.stem))
    payload_keys = ("role", "bundle", "uses", "needs", "inputs")
    status = "unchanged"
    if existing:
        latest = json.loads(existing[-1].read_text())
        if all(latest.get(k) == version_body.get(k) for k in payload_keys):
            n = None
        else:
            n = int(existing[-1].stem) + 1
            status = f"v{n}"
    else:
        n = 1
        status = "new"
    if n is not None:
        body = {"id": f"@yaaf/{slug}", "version": n, "kind": meta["kind"],
                "published_at": date.today().isoformat(),
                "changes": "First version." if n == 1 else "Updated from the yaaf repository.",
                **version_body}
        (versions / f"{n}.json").write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n")
    (folder / "listing.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return status


def main() -> int:
    roles_dir, examples_dir = YAAF / "roles", YAAF / "examples"
    if not roles_dir.is_dir():
        print(f"no yaaf checkout at {YAAF}; set YAAF_REPO", file=sys.stderr)
        return 2
    library = {json.loads(p.read_text())["slug"]: json.loads(p.read_text())
               for p in sorted(roles_dir.glob("*.json"))}
    report: dict[str, int] = {}
    for slug, role in library.items():
        meta = {"id": f"@yaaf/{slug}", "kind": "role", "name": role["name"],
                "summary": role_summary(role["description"]), "category": role["category"],
                "domains": role.get("domains") or [], "license": "Apache-2.0", "status": "active"}
        status = write_listing(slug, meta, {"role": role, "needs": needs_for([role])})
        report[status] = report.get(status, 0) + 1

    for path in sorted(examples_dir.glob("*.json")):
        spec = EXAMPLES.get(path.stem)
        if spec is None:
            print(f"{path.name}: no entry in EXAMPLES, skipped", file=sys.stderr)
            continue
        bundle = json.loads(path.read_text())
        project = dict(bundle["project"])
        goal = project["goal"]
        for find, replace in spec["edits"]:
            if find not in goal:
                print(f"{path.name}: {find[:50]!r} is no longer in the goal; update EXAMPLES", file=sys.stderr)
                return 1
            goal = goal.replace(find, replace)
        project["goal"] = goal
        if "controlled_domains" in spec:
            project["controlled_domains"] = spec["controlled_domains"]
        for private in ("chairman_email", "github_repo", "billing_secret_name", "credential_names",
                        "fallback_credential_name", "deadline"):
            project.pop(private, None)
        hired = [project.get("ceo_role_slug") or "ceo"] + [t["role_slug"] for t in project.get("teams") or []]
        hired = list(dict.fromkeys(hired))
        carried = [library[s] for s in hired]
        secrets = [{k: v for k, v in s.items() if k in ("name", "role_scopes", "kind", "file")}
                   for s in bundle.get("secrets") or []]
        out_bundle = {"yaaf_bundle": 1, "kind": "project_setup", "source_slug": spec["slug"],
                      "values_included": False, "project": project, "roles": carried, "secrets": secrets}
        required = {s["name"] for s in secrets if s["name"] == "github" and path.stem.startswith("04")}
        needs = needs_for(carried, required=required, github_repo=path.stem.startswith("04"),
                          mailbox=bool(project.get("needs_mail")))
        meta = {"id": f"@yaaf/{spec['slug']}", "kind": "project", "name": project["name"],
                "summary": spec["summary"], "category": spec["category"], "domains": spec["domains"],
                "license": "Apache-2.0", "status": "active"}
        details = writeup(path.stem)
        if details:
            meta["details"] = details
        body = {"bundle": out_bundle,
                "uses": [{"id": f"@yaaf/{s}", "version": 1, "slug": s} for s in hired],
                "needs": needs}
        if spec["inputs"]:
            body["inputs"] = spec["inputs"]
        status = write_listing(spec["slug"], meta, body)
        report[status] = report.get(status, 0) + 1
    print(", ".join(f"{n} {k}" for k, n in sorted(report.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
