"""An in-memory stand-in for a tonutils client, so the real wallet code signs real messages without any network.

It models what matters for money: a sent message lands at most once, and only a message that lands moves the seqno on.
A send can fail without landing, or fail after landing (toncenter answers 500 to sendBoc calls that went through).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from ton_core import ContractState, NetworkGlobalID
from tonutils.exceptions import ProviderResponseError, RunGetMethodError
from tonutils.types import ContractInfo


def provider_error(code: int, message: str = "error") -> ProviderResponseError:
    return ProviderResponseError(code=code, message=message, endpoint="tonapi.io")


class FakeTon:
    network = NetworkGlobalID.MAINNET

    def __init__(
        self,
        balance: int = 10_000_000_000,
        state: ContractState = ContractState.ACTIVE,
        seqno: int = 5,
        data_raw: str | None = None,
    ) -> None:
        self.balance = balance
        self.state = state
        self.seqno = seqno
        self.data_raw = data_raw
        self.connected = False
        self.sent: list[bytes] = []  # every send attempt, in order
        self.landed: list[bytes] = []  # messages the provider accepted (not rejected), each once
        self.info_errors: list[Exception] = []  # raised by get_info, one per call, before it answers again
        self.seqno_errors: list[Exception] = []  # raised by the seqno get-method, one per call
        self.send_errors: list[tuple[Exception, bool]] = []  # (error, landed anyway) for the next send attempts
        self.seqno_reads = 0
        self.closed = False

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.connected = False
        self.closed = True

    async def get_info(self, address: Any) -> ContractInfo:
        if self.info_errors:
            raise self.info_errors.pop(0)
        return ContractInfo(balance=self.balance, state=self.state, data_raw=self.data_raw, last_transaction_lt=None)

    async def run_get_method(self, address: Any, method_name: str, stack: list[Any] | None = None) -> list[Any]:
        if method_name != "seqno":
            raise RunGetMethodError(address=str(address), exit_code=11, method_name=method_name)
        self.seqno_reads += 1
        if self.seqno_errors:
            raise self.seqno_errors.pop(0)
        return [self.seqno]

    async def send_message(self, boc: str) -> None:
        message = bytes.fromhex(boc)
        self.sent.append(message)
        if self.send_errors:
            error, landed = self.send_errors.pop(0)
            if landed:
                self._land(message)
            raise error
        self._land(message)

    def _land(self, message: bytes) -> None:
        if message not in self.landed:
            self.landed.append(message)
            self.seqno += 1
            self.state = ContractState.ACTIVE  # the first message deploys the wallet


@contextmanager
def use_fake_ton(ton: FakeTon) -> Iterator[FakeTon]:
    """Make every FragmentClient created inside talk to ``ton`` instead of tonapi/toncenter."""
    with patch("pyfragment.domains.wallet.wallet.make_ton_client", return_value=ton):
        yield ton
