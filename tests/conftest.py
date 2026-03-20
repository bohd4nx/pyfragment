import json
import os

import pytest


@pytest.fixture
def cookies():
    """Load Fragment cookies from COOKIES_JSON env var; skip if unavailable."""
    raw = os.environ.get("COOKIES_JSON")
    if not raw:
        pytest.skip("COOKIES_JSON env var not set")
    try:
        return json.loads(raw)
    except Exception as exc:
        pytest.skip(f"Cookies unavailable — {exc}")
