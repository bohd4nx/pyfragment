"""Fixtures shared by the whole suite."""

from collections.abc import AsyncIterator, Iterator

import pytest

from pyfragment import FragmentClient
from tests.support.data import API_KEY, COOKIES, SEED
from tests.support.fake_fragment import FakeFragment
from tests.support.fake_ton import FakeTon, use_fake_ton


@pytest.fixture
def fake_ton() -> Iterator[FakeTon]:
    """A funded, deployed wallet on an in-memory chain: every client created while it is active talks to it."""
    with use_fake_ton(FakeTon()) as ton:
        yield ton


@pytest.fixture
async def client() -> AsyncIterator[FragmentClient]:
    async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=COOKIES) as fragment_client:
        yield fragment_client


@pytest.fixture
def fragment(client: FragmentClient, monkeypatch: pytest.MonkeyPatch) -> FakeFragment:
    """``client`` with its Fragment transport replaced by a script the test fills in."""
    fake = FakeFragment()
    monkeypatch.setattr(client._transport, "call", fake.call)
    monkeypatch.setattr(client._transport, "fetch_page", fake.fetch_page)
    return fake
