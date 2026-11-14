"""Check every listing in this registry, or the ones a pull request touches.

    python tools/check.py                         # everything
    python tools/check.py --base origin/main --author rae   # a pull request

Exit 1 on any error. `--json` prints the report the review card is built from.

A listing this registry would merge must also be one yaaf would accept, so when
the `yaaf` package is importable its own validators run too: a role goes through
the model POST /admin/roles uses, a project through the Founder's `validate`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTINGS = ROOT / "listings"
SCHEMA = ROOT / "schema"

ID = re.compile(r"^@([a-z0-9][a-z0-9-]{0,38})/([a-z0-9-]{2,64})$")
BLANK = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
ENV_REF = re.compile(r"\$\{?([A-Z][A-Z0-9_]{2,})\}?")
MCP_REF = re.compile(r"mcp__([a-z0-9-]{2,32})__")

#: Variables an agent's shell has whatever the role was granted. Mentioning
#: them in a prompt is not asking for a credential.
SHELL_VARS = {"HOME", "PATH", "PWD", "USER", "SHELL", "TMPDIR", "TMP", "LANG", "TERM",
              "WORKSPACE", "OLDPWD", "HOSTNAME", "PYTHONPATH", "VIRTUAL_ENV"}

#: Shapes of real credentials. A listing never carries a value, so any match is
#: refused, whatever field it hides in.
SECRET_SHAPES = [
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"), "an Anthropic key"),
    (re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}"), "an OpenAI-style key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS access key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "a GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"), "a GitHub token"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "a Google API key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"), "a JWT"),
]
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
URL = re.compile(r"https?://([A-Za-z0-9.-]+)")
#: Hosts a listing may name without the review card asking whose they are.
NEUTRAL_HOSTS = re.compile(r"(^|\.)(example\.(com|org|net)|example|localhost|github\.com|"
                           r"wikipedia\.org|sec\.gov|wordpress\.org|python\.org|"
                           r"googleapis\.com|google\.com|developers\.google\.com)$")


@dataclass
class Listing:
    id: str
    folder: Path
    meta: dict | None = None
    versions: dict[int, dict] = field(default_factory=dict)
    raw: dict[int, bytes] = field(default_factory=dict)


@dataclass
class Report:
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)

    def error(self, where: str, text: str) -> None:
        self.errors.append({"where": where, "text": text})

    def warn(self, where: str, text: str) -> None:
        item = {"where": where, "text": text}
        if item not in self.warnings:
            self.warnings.append(item)


def _schema_validator(name: str):
    try:
        import jsonschema
    except ImportError:  # the checks below still run; CI installs it
        return None
    schema = json.loads((SCHEMA / name).read_text())
    return jsonschema.Draft202012Validator(schema)


def load(folder: Path, report: Report) -> Listing:
    rel = folder.relative_to(ROOT)
    listing = Listing(id=f"@{folder.parent.name}/{folder.name}", folder=folder)
    meta_path = folder / "listing.json"
    try:
        listing.meta = json.loads(meta_path.read_text())
    except FileNotFoundError:
        report.error(str(rel), "listing.json is missing")
    except ValueError as exc:
        report.error(f"{rel}/listing.json", f"not valid JSON: {exc}")
    for path in sorted((folder / "versions").glob("*.json")):
        where = str(path.relative_to(ROOT))
        if not re.fullmatch(r"[1-9][0-9]*\.json", path.name):
            report.error(where, "version files are named 1.json, 2.json, …")
            continue
        raw = path.read_bytes()
        try:
            listing.versions[int(path.stem)] = json.loads(raw)
            listing.raw[int(path.stem)] = raw
        except ValueError as exc:
            report.error(where, f"not valid JSON: {exc}")
    return listing


def strings(value, path=""):
    """Every string in a JSON value, with where it sits."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, f"{path}.{k}" if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings(v, f"{path}[{i}]")


def env_var_name(secret_name: str) -> str:
    # yaaf.core.naming.env_var_name, kept identical so this runs without yaaf.
    return re.sub(r"[^A-Za-z0-9]+", "_", secret_name).strip("_").upper()


def check_listing(listing: Listing, report: Report, listing_v, version_v) -> None:
    rel = str(listing.folder.relative_to(ROOT))
    meta = listing.meta
    if meta is None:
        return
    if listing_v is not None:
        for err in listing_v.iter_errors(meta):
            report.error(f"{rel}/listing.json", f"{'.'.join(map(str, err.path)) or '(top)'}: {err.message}")
    if meta.get("id") != listing.id:
        report.error(f"{rel}/listing.json", f"id must be {listing.id}, matching its folder")
    if not listing.versions:
        report.error(rel, "a listing needs at least versions/1.json")
        return
    numbers = sorted(listing.versions)
    if numbers != list(range(1, len(numbers) + 1)):
        report.error(rel, f"versions must run 1..n with no gaps, found {numbers}")
    slug = listing.id.split("/", 1)[1]
    for n, version in listing.versions.items():
        where = f"{rel}/versions/{n}.json"
        if version_v is not None:
            for err in version_v.iter_errors(version):
                report.error(where, f"{'.'.join(map(str, err.path)) or '(top)'}: {err.message}")
        if version.get("id") != listing.id or version.get("version") != n:
            report.error(where, f"must say id {listing.id} and version {n}")
        if version.get("kind") != meta.get("kind"):
            report.error(where, f"kind {version.get('kind')!r} does not match the listing's {meta.get('kind')!r}")
        check_secrets(version, where, report)
        if version.get("kind") == "role" and isinstance(version.get("role"), dict):
            if version["role"].get("slug") != slug:
                report.error(where, f"role.slug must be {slug!r}, the listing's own slug")
            check_role(version["role"], version.get("needs") or {}, where, report)
        elif version.get("kind") == "project" and isinstance(version.get("bundle"), dict):
            check_project(version, where, report)
        check_privacy(version, where, report)


def check_secrets(version: dict, where: str, report: Report) -> None:
    for path, text in strings(version):
        for shape, what in SECRET_SHAPES:
            if shape.search(text):
                report.error(where, f"{path} contains what looks like {what}. A listing never "
                                    "carries a credential; declare it under needs.keys instead")


def check_privacy(version: dict, where: str, report: Report) -> None:
    """Things that are usually somebody's own, for a human to look at. Warnings,
    because a listing about the SEC may name sec.gov on purpose."""
    for path, text in strings(version):
        for match in EMAIL.finditer(text):
            if not NEUTRAL_HOSTS.search(match.group(1).lower()):
                report.warn(where, f"{path} names an email address ({match.group(0)}). Is it the publisher's?")
        for match in URL.finditer(text):
            host = match.group(1).lower()
            if not NEUTRAL_HOSTS.search(host):
                report.warn(where, f"{path} names {host}. Is it the publisher's own?")


def _declared_keys(needs: dict) -> dict[str, dict]:
    return {k.get("name"): k for k in needs.get("keys") or [] if isinstance(k, dict)}


def _declared_sources(needs: dict) -> dict[str, dict]:
    return {s.get("name"): s for s in needs.get("data_sources") or [] if isinstance(s, dict)}


def check_role(role: dict, needs: dict, where: str, report: Report,
               *, project_keys: set[str] | None = None) -> None:
    for path, text in strings(role):
        if BLANK.search(text):
            report.error(where, f"role {role.get('slug')}: {path} has a blank. Roles serve many "
                                "projects, so they never have blanks; move the specific part to "
                                "the project's standing orders")
    keys = _declared_keys(needs)
    scopes = set(role.get("secret_scopes") or [])
    declared_vars = {env_var_name(name): name for name in keys}
    for scope in scopes:
        if scope not in keys:
            report.error(where, f"role {role.get('slug')} receives the credential {scope!r}, "
                                "which needs.keys does not declare")
    prompt = role.get("system_prompt") or ""
    for var in sorted(set(ENV_REF.findall(prompt))):
        if var in SHELL_VARS or var.startswith("YAAF_"):
            continue
        name = declared_vars.get(var)
        if name is None:
            report.error(where, f"role {role.get('slug')}: the prompt reads ${var}, but no key in "
                                "needs.keys is named for it")
        elif name not in scopes:
            report.error(where, f"role {role.get('slug')}: the prompt reads ${var}, but the role's "
                                f"secret_scopes do not include {name!r}, so it would never have it")
    sources = _declared_sources(needs)
    for name in sorted(set(MCP_REF.findall(prompt))):
        if name not in sources:
            report.error(where, f"role {role.get('slug')}: the prompt calls mcp__{name}__ tools, "
                                "but needs.data_sources does not declare that source")
    perms = role.get("tool_permissions") or {}
    if "mcp_servers" in perms:
        report.error(where, f"role {role.get('slug')}: roles do not own data sources; declare it "
                            "under needs.data_sources")
    if project_keys is None:
        for name, key in keys.items():
            if name not in scopes:
                report.error(where, f"needs.keys declares {name!r}, which the role never receives")
            elif role.get("slug") not in key.get("roles", []):
                report.error(where, f"needs.keys {name!r} must list {role.get('slug')!r} in roles")


def check_project(version: dict, where: str, report: Report) -> None:
    bundle = version["bundle"]
    project = bundle.get("project") or {}
    needs = version.get("needs") or {}
    if bundle.get("values_included") not in (False, None):
        report.error(where, "bundle.values_included must be false: a listing never carries values")
    for secret in bundle.get("secrets") or []:
        if isinstance(secret, dict) and ({"value", "ciphertext"} & secret.keys()):
            report.error(where, f"bundle.secrets[{secret.get('name')}] carries a value")
    for leaked in ("chairman_email", "github_repo", "billing_secret_name", "billing_secret_id",
                   "credential_names", "fallback_credential_name"):
        if project.get(leaked):
            report.error(where, f"bundle.project.{leaked} is set. It names the publisher's own "
                                "account; leave it out")
    for entry in (project.get("integrations") or {}).get("mcp_servers") or []:
        if isinstance(entry, dict) and (entry.get("url_host") or entry.get("url")):
            declared = _declared_sources(needs).get(entry.get("name"), {})
            if declared.get("address", "bring-your-own") == "bring-your-own":
                report.error(where, f"data source {entry.get('name')!r} carries an address but is "
                                    "declared bring-your-own; drop url_host and url_port")
    for key in ("mail", "slack", "webhook_secret", "github_webhook_secret"):
        if key in (project.get("integrations") or {}):
            report.error(where, f"bundle.project.integrations.{key} is this install's wiring, not the design")

    # Blanks: declared ⇔ used, and never inside a role.
    inputs = {i.get("id"): i for i in version.get("inputs") or [] if isinstance(i, dict)}
    used: set[str] = set()
    for path, text in strings(project):
        used.update(BLANK.findall(text))
    for name in sorted(used - inputs.keys()):
        report.error(where, f"the blank {{{{{name}}}}} is used but not declared in inputs")
    for name in sorted(inputs.keys() - used):
        report.error(where, f"inputs declares {name!r}, which no blank uses")
    for name, spec in inputs.items():
        if spec.get("type") == "choice" and not spec.get("choices"):
            report.error(where, f"input {name!r} is a choice with no choices")

    # Every hired role is present: carried whole, and each carried role valid.
    carried = {r.get("slug"): r for r in bundle.get("roles") or [] if isinstance(r, dict)}
    hired = {t.get("role_slug") for t in project.get("teams") or [] if isinstance(t, dict)}
    hired.add(project.get("ceo_role_slug") or "ceo")
    for slug in sorted(s for s in hired - carried.keys() if s):
        report.error(where, f"the project hires {slug!r} but bundle.roles does not carry it")
    for use in version.get("uses") or []:
        if use.get("slug") not in carried:
            report.error(where, f"uses names {use.get('id')} as {use.get('slug')!r}, which bundle.roles does not carry")
    all_scopes: set[str] = set()
    for role in carried.values():
        check_role(role, needs, where, report, project_keys=set())
        all_scopes.update(role.get("secret_scopes") or [])
    for name, key in _declared_keys(needs).items():
        if name not in all_scopes:
            report.error(where, f"needs.keys declares {name!r}, which no role receives")
        for slug in key.get("roles") or []:
            if slug not in carried:
                report.error(where, f"needs.keys {name!r} grants {slug!r}, which the project does not hire")
            elif name not in (carried[slug].get("secret_scopes") or []):
                report.error(where, f"needs.keys {name!r} grants {slug!r}, whose secret_scopes lack it")
    for name, source in _declared_sources(needs).items():
        for slug in source.get("roles") or []:
            if slug not in carried:
                report.error(where, f"data source {name!r} is granted to {slug!r}, which the project does not hire")
    if needs.get("mailbox") != bool(project.get("needs_mail")):
        report.error(where, "needs.mailbox must match bundle.project.needs_mail")


def fill(value, inputs: dict[str, dict]):
    """The bundle as an installer would have it, with every blank given its example."""
    if isinstance(value, str):
        return BLANK.sub(lambda m: str((inputs.get(m.group(1)) or {}).get("example", m.group(1))), value)
    if isinstance(value, dict):
        return {k: fill(v, inputs) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, inputs) for v in value]
    return value


def check_with_yaaf(listing: Listing, report: Report) -> bool:
    try:
        from pydantic import ValidationError

        from yaaf.server.api.admin import RoleIn
    except Exception:
        return False
    rel = str(listing.folder.relative_to(ROOT))
    for n, version in listing.versions.items():
        where = f"{rel}/versions/{n}.json"
        roles = ([version["role"]] if isinstance(version.get("role"), dict)
                 else list((version.get("bundle") or {}).get("roles") or []))
        for role in roles:
            try:
                RoleIn.model_validate(role)
            except ValidationError as exc:
                for err in exc.errors()[:5]:
                    report.error(where, f"yaaf would refuse role {role.get('slug')}: "
                                        f"{'.'.join(map(str, err['loc']))}: {err['msg']}")
        if isinstance(version.get("bundle"), dict):
            from yaaf.founder.tools import validate

            inputs = {i["id"]: i for i in version.get("inputs") or [] if isinstance(i, dict) and "id" in i}
            filled = fill(version["bundle"], inputs)
            for problem in validate(filled):
                report.error(where, f"yaaf would refuse the project: {problem}")
    return True


def changed_files(base: str) -> list[tuple[str, str]]:
    out = subprocess.run(["git", "diff", "--name-status", "--no-renames", f"{base}...HEAD", "--", "."],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    prefix = subprocess.run(["git", "rev-parse", "--show-prefix"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    rows = []
    for line in out.splitlines():
        status, path = line.split("\t", 1)
        rows.append((status, path[len(prefix):] if prefix and path.startswith(prefix) else path))
    return rows


def moderators() -> set[str]:
    path = ROOT / "MODERATORS"
    if not path.exists():
        return set()
    return {line.strip().lstrip("@").lower() for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")}


def check_change(rows: list[tuple[str, str]], author: str | None, report: Report) -> set[Path]:
    """What a pull request may touch. Returns the listing folders it touched."""
    touched: set[Path] = set()
    mods = moderators()
    for status, path in rows:
        parts = Path(path).parts
        if not parts or parts[0] != "listings":
            if author and author.lower() not in mods:
                report.error(path, "only moderators change files outside listings/")
            continue
        if len(parts) < 3:
            report.error(path, "files live in listings/<handle>/<slug>/")
            continue
        handle = parts[1]
        touched.add(ROOT / "listings" / handle / parts[2])
        if author is not None:
            owner = handle.lower() == author.lower()
            moderating = author.lower() in mods
            if handle == "yaaf" and not moderating:
                report.error(path, "@yaaf is reserved for the library that ships with yaaf")
            elif not owner and not moderating:
                report.error(path, f"@{author} may only publish under @{author}, not @{handle}")
        if len(parts) == 5 and parts[3] == "versions" and status in ("M", "D"):
            report.error(path, "a published version never changes. Publish a new version instead")
    return touched


def run(base: str | None = None, author: str | None = None) -> tuple[Report, list[Listing], bool]:
    report = Report()
    listing_v = _schema_validator("listing.schema.json")
    version_v = _schema_validator("version.schema.json")
    if listing_v is None:
        report.warn("(checks)", "jsonschema is not installed, so the schema checks were skipped")
    folders = sorted(p for p in LISTINGS.glob("*/*") if p.is_dir())
    if base:
        touched = check_change(changed_files(base), author, report)
        folders = [f for f in folders if f in touched]
    listings = [load(folder, report) for folder in folders]
    used_yaaf = False
    for listing in listings:
        if not ID.match(listing.id):
            report.error(str(listing.folder.relative_to(ROOT)), f"{listing.id} is not a valid listing id")
            continue
        check_listing(listing, report, listing_v, version_v)
        used_yaaf = check_with_yaaf(listing, report) or used_yaaf
    if not used_yaaf and listings:
        report.warn("(checks)", "yaaf is not importable, so yaaf's own validators did not run")
    return report, listings, used_yaaf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", help="git ref the pull request is based on")
    parser.add_argument("--author", help="GitHub login of the pull request's author")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    report, listings, _ = run(args.base, args.author)
    if args.json:
        print(json.dumps({"listings": [l.id for l in listings], "errors": report.errors,
                          "warnings": report.warnings}, indent=2))
    else:
        for item in report.errors:
            print(f"error  {item['where']}: {item['text']}")
        for item in report.warnings:
            print(f"note   {item['where']}: {item['text']}")
        print(f"{len(listings)} listing(s) checked, {len(report.errors)} error(s), "
              f"{len(report.warnings)} note(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
