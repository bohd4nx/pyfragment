import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest

from pyfragment import FragmentClient
from tests.support.data import API_KEY, COOKIES, SEED
from tests.support.fake_ton import FakeTon


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pyfragment.domains.wallet.wallet.SEQNO_POLL_INTERVAL", 0.002)


@pytest.fixture
async def make_client(fake_ton: FakeTon) -> AsyncIterator[Callable[..., FragmentClient]]:
    """Builds clients on the ``fake_ton`` chain and closes them after the test."""
    clients: list[FragmentClient] = []

    def make(**options: Any) -> FragmentClient:
        options.setdefault("seed", SEED)
        client = FragmentClient(api_key=API_KEY, cookies=COOKIES, **options)
        clients.append(client)
        return client

    yield make
    await asyncio.gather(*(client.aclose() for client in clients))
