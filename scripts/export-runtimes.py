"""Read yaaf's runtime registries and print them as JSON for the site.

Called by sync-content.mjs as `python3 -I scripts/export-runtimes.py <yaaf>`.

The harness, provider and model registries in `yaaf/runtimes/` are the one
place yaaf itself reads to decide what a seat can run on — the credential form,
the fire drill and the lease all read them. So the site reads them too, rather
than restating them in prose that drifts the first time a provider lands.

They are importable without yaaf's dependencies: `harnesses.py` imports nothing
from `yaaf` (a test in the repo holds that, because the sandbox reads the same
copy), and `providers.py` and `catalog.py` import only each other. Only the
pinned CLI versions come from somewhere else — the sandbox Dockerfile, which is
what actually decides them.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main(repo: Path) -> None:
    sys.path.insert(0, str(repo))
    from yaaf.runtimes.catalog import MODELS
    from yaaf.runtimes.harnesses import HARNESSES
    from yaaf.runtimes.providers import PROVIDERS

    dockerfile = (repo / "deploy/sandbox/Dockerfile").read_text()
    pins = dict(re.findall(r"npm install -g (@?[\w./-]+)@([\d.]+)", dockerfile))
    # The npm package each CLI harness installs. The Claude CLI is installed
    # unpinned, and the site says so rather than inventing a version.
    package = {
        "claude_cli": "@anthropic-ai/claude-code",
        "claude_agent_sdk": "@anthropic-ai/claude-code",
        "codex_cli": "@openai/codex",
        "gemini_cli": "@google/gemini-cli",
        "opencode": "opencode-ai",
    }

    harnesses = []
    for h in HARNESSES.values():
        if h.family == "mock":
            continue
        harnesses.append({
            "name": h.name,
            "label": h.label,
            "family": h.family,
            "providers": list(h.providers),
            "accepts": list(h.accepts),
            "withholds": list(h.withholds),
            "cost": h.cost,
            "search": h.search,
            "conversation": h.conversation,
            "package": package.get(h.name),
            "pinned": pins.get(package.get(h.name, ""), None),
        })

    providers = []
    for p in PROVIDERS.values():
        providers.append({
            "name": p.name,
            "label": p.label,
            # A method since yaaf#67: the default harness is a fact about the
            # credential kind, and this is the first kind's.
            "default_harness": p.default_harness(),
            "kinds": [{"mode": k.mode, "meter": k.meter, "bills": k.bills,
                       "default_harness": k.default_harness} for k in p.kinds],
            "served_by": [h["name"] for h in harnesses if p.name in h["providers"]],
            "credential_base_url": p.credential_base_url,
            "search": p.search,
            "reports_cost": p.reports_cost,
            "local": getattr(p, "local", False),
            "lineup": dict(p.lineup) if getattr(p, "lineup", None) else None,
            "models": [m.id for m in MODELS if m.provider == p.name],
            "priced": [m.id for m in MODELS if m.provider == p.name and m.price is not None],
        })

    models = [{
        "id": m.id,
        "provider": m.provider,
        "tier": m.tier,
        "price": None if m.price is None else {
            "input": m.price.input, "output": m.price.output, "as_of": m.price.as_of,
        },
    } for m in MODELS]

    json.dump({"harnesses": harnesses, "providers": providers, "models": models}, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
