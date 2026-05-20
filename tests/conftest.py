import json
import os
from typing import cast

import pytest

import pyfragment.domains.ads.recharge  # noqa: F401
import pyfragment.domains.giveaways.giveaway  # noqa: F401
import pyfragment.domains.purchases.purchase  # noqa: F401
import pyfragment.domains.wallet.topup  # noqa: F401
from pyfragment import FragmentClient
from tests.shared import VALID_API_KEY, VALID_COOKIES, VALID_SEED


@pytest.fixture
def cookies() -> dict[str, str]:
    """Load Fragment cookies from COOKIES_JSON env var; skip if unavailable."""
    raw = os.environ.get("COOKIES_JSON")
    if not raw:
        pytest.skip("COOKIES_JSON env var not set")
    try:
        return cast(dict[str, str], json.loads(raw))
    except Exception as exc:
        pytest.skip(f"Cookies unavailable — {exc}")


@pytest.fixture
def client() -> FragmentClient:
    """Pre-built FragmentClient with dummy credentials."""
    return FragmentClient(seed=VALID_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES)
