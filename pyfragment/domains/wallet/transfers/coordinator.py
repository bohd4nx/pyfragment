from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from typing import Protocol


class TransferCoordinator(Protocol):
    """Serializes the messages a wallet sends and shares the seqno of the last one.

    ``lock(address)`` covers one message, from reading its seqno to sending it, never the wait for Fragment's
    confirmation. Processes signing from the same wallet share one coordinator (e.g. backed by Redis): the pending seqno
    tells the next message to wait until the previous one has landed. Every call names the wallet, so one coordinator
    can serve several wallets.
    """

    def lock(self, address: str) -> AbstractAsyncContextManager[object]: ...

    async def load_pending(self, address: str) -> tuple[int, float] | None:
        """``(seqno, valid_until)`` of the last message sent from ``address``, or ``None``."""
        ...

    async def save_pending(self, address: str, seqno: int, valid_until: float) -> None: ...


class LocalTransferCoordinator:
    """The default: one process."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._pending: dict[str, tuple[int, float]] = {}

    def lock(self, address: str) -> AbstractAsyncContextManager[object]:
        return self._locks.setdefault(address, asyncio.Lock())

    async def load_pending(self, address: str) -> tuple[int, float] | None:
        return self._pending.get(address)

    async def save_pending(self, address: str, seqno: int, valid_until: float) -> None:
        self._pending[address] = (seqno, valid_until)
