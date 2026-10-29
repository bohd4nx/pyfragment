"""An in-memory stand-in for a tonutils client, so the real wallet code signs real messages without any network.

It models what matters for money: a sent message lands at most once, and only a message that lands moves the seqno on.
A send can fail without landing, or fail after landing (toncenter answers 500 to sendBoc calls that went through).
A landed message shows up in the wallet's history, the way the library confirms it.
"""

import hashlib
import time
from collections.abc import Iterator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from ton_core import ContractState, MessageAny, NetworkGlobalID, Slice
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
        lands: bool = True,
        skips: bool = False,
    ) -> None:
        self.balance = balance
        self.state = state
        self.seqno = seqno
        self.data_raw = data_raw
        self.lands = lands  # False: the provider accepts messages that then never make it on-chain
        self.skips = skips  # True: messages land, but the wallet skips the transfer (as when it can't afford it)
        self.connected = False
        self.sent: list[bytes] = []  # every send attempt, in order
        self.landed: list[bytes] = []  # messages that made it on-chain, each once
        self.info_errors: list[Exception] = []  # raised by get_info, one per call, before it answers again
        self.seqno_errors: list[Exception] = []  # raised by the seqno get-method, one per call
        self.send_errors: list[tuple[Exception, bool]] = []  # (error, landed anyway) for the next send attempts
        self.transactions: list[Any] = []  # newest first, for get_transactions
        self.transaction_errors: list[Exception] = []
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
        last_lt = self.transactions[0].lt if self.transactions else None
        return ContractInfo(balance=self.balance, state=self.state, data_raw=self.data_raw, last_transaction_lt=last_lt)

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
        if self.lands and message not in self.landed:
            self.landed.append(message)
            self.seqno += 1
            self.state = ContractState.ACTIVE  # the first message deploys the wallet
            self.transactions.insert(0, self._transaction(message))

    def _transaction(self, message: bytes) -> SimpleNamespace:
        """The wallet transaction a landed external message makes, with just what the library reads of it."""
        lt = (self.transactions[0].lt + 1) if self.transactions else 1_000  # well above 0 so last_lt=0 never stops search
        action = SimpleNamespace(success=True, skipped_actions=1 if self.skips else 0)
        return SimpleNamespace(
            lt=lt,
            now=int(time.time()),
            in_msg=MessageAny.deserialize(Slice.one_from_boc(message)),
            out_msgs=[],
            outmsg_cnt=0 if self.skips else 1,
            description=SimpleNamespace(aborted=False, compute_ph=SimpleNamespace(success=True), action=action),
            cell=SimpleNamespace(hash=hashlib.sha256(message).digest()),
        )

    async def get_transactions(
        self, address: Any, limit: int = 100, from_lt: int | None = None, to_lt: int | None = None
    ) -> list[Any]:
        if self.transaction_errors:
            raise self.transaction_errors.pop(0)
        older = [tx for tx in self.transactions if from_lt is None or tx.lt <= from_lt]
        return older[:limit]


@contextmanager
def use_fake_ton(ton: FakeTon) -> Iterator[FakeTon]:
    """Make every FragmentClient created inside talk to ``ton`` instead of tonapi/toncenter."""
    with patch("pyfragment.domains.wallet.wallet.make_ton_client", return_value=ton):
        yield ton
