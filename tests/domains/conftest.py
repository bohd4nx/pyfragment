from unittest.mock import AsyncMock

import pytest

from tests.support.data import SENT


@pytest.fixture
def paid(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Stands in for the wallet transfer (reports ``SENT``) and makes the confirmation polling instant."""
    process = AsyncMock(return_value=SENT)
    monkeypatch.setattr("pyfragment.domains.payments.flow.process_transaction", process)
    monkeypatch.setattr("pyfragment.domains.payments.confirmation.CONFIRM_STATE_POLL_INTERVAL", 0)
    return process
