import pytest

from app.core.cookies import load_cookies
from app.core.exceptions import CookiesError


@pytest.fixture
def cookies():
    """Load Fragment cookies, skip the test if they are unavailable."""
    try:
        return load_cookies()
    except CookiesError as exc:
        pytest.skip(f"Cookies unavailable — {exc}")
