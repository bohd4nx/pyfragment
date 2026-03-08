import pytest

from app.core.config import config
from app.core.cookies import load_cookies
from app.core.exceptions import CookiesError


@pytest.fixture
def cookies():
    """Load Fragment cookies; skip the test if they are unavailable."""
    try:
        return load_cookies()
    except CookiesError as exc:
        pytest.skip(f"Cookies unavailable — {exc}")


@pytest.fixture
def tests_config():
    """Require a fully configured environment (SEED + API_KEY); skip otherwise."""
    if config is None:
        pytest.skip("Config unavailable — set SEED and API_KEY in .env or environment")
    return config
