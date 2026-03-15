import json
from pathlib import Path

import pytest


@pytest.fixture
def cookies():
    """Load Fragment cookies from cookies.json; skip the test if unavailable."""
    cookies_path = Path(__file__).resolve().parents[1] / "cookies.json"
    if not cookies_path.exists():
        pytest.skip("cookies.json not found")
    try:
        with cookies_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        pytest.skip(f"Cookies unavailable — {exc}")
