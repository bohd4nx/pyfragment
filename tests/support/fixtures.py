"""Loaders for the real fragment.com responses under tests/fixtures (see its README)."""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent / "fixtures"


def html(name: str) -> str:
    return (ROOT / "html" / name).read_text()


def response(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((ROOT / "json" / name).read_text())
    return result


def chain(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((ROOT / "chain" / name).read_text())
    return result
