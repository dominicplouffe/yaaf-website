import json
import shutil
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import check  # noqa: E402

SHIPPED = Path(__file__).resolve().parents[1] / "listings"


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """A private copy of the registry, so a test can break a listing freely."""
    root = tmp_path / "registry"
    shutil.copytree(SHIPPED, root / "listings")
    shutil.copytree(SHIPPED.parent / "schema", root / "schema")
    monkeypatch.setattr(check, "ROOT", root)
    monkeypatch.setattr(check, "LISTINGS", root / "listings")
    monkeypatch.setattr(check, "SCHEMA", root / "schema")
    return root


def edit(root: Path, listing: str, n: int, change) -> None:
    path = root / "listings" / listing / "versions" / f"{n}.json"
    body = json.loads(path.read_text())
    change(body)
    path.write_text(json.dumps(body))


def errors() -> list[str]:
    report, _, _ = check.run()
    return [e["text"] for e in report.errors]
