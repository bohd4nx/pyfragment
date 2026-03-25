import json
import os

import pytest

from pyfragment import FragmentClient
from tests.shared import VALID_API_KEY, VALID_COOKIES, VALID_SEED


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


@pytest.fixture
def client() -> FragmentClient:
    """Pre-built FragmentClient with dummy credentials."""
    return FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
