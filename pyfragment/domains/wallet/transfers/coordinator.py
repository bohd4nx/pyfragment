from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from typing import Protocol


class TransferCoordinator(Protocol):
    """Serializes the messages a wallet sends and shares the seqno of the last one.

    ``lock()`` covers one message, from reading its seqno to sending it, never the wait for Fragment's confirmation.
    Processes signing from the same wallet share one coordinator (e.g. backed by Redis): the pending seqno tells the
    next message to wait until the previous one has landed. One instance serves one wallet: the pending seqno and the
    lock carry no wallet identity, so key them by the wallet when the backing store is shared.
    """

    def lock(self) -> AbstractAsyncContextManager[object]: ...

    async def load_pending(self) -> tuple[int, float] | None:
        """``(seqno, valid_until)`` of the last sent message, or ``None``."""
        ...

    async def save_pending(self, seqno: int, valid_until: float) -> None: ...


class LocalTransferCoordinator:
    """The default: one process."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._pending: tuple[int, float] | None = None

    def lock(self) -> AbstractAsyncContextManager[object]:
        return self._lock

    async def load_pending(self) -> tuple[int, float] | None:
        return self._pending

    async def save_pending(self, seqno: int, valid_until: float) -> None:
        self._pending = (seqno, valid_until)
