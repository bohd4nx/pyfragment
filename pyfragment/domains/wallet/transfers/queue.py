from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary

from tonutils.exceptions import ProviderResponseError

from pyfragment.domains.wallet.models import TransferIntent
from pyfragment.domains.wallet.transfers.coordinator import LocalTransferCoordinator
from pyfragment.domains.wallet.transfers.request import TransferRequest
from pyfragment.exceptions import ProviderError, TransactionError
from pyfragment.utils.transaction import signing_expiry

if TYPE_CHECKING:
    from pyfragment.domains.wallet.wallet import TonWallet

logger = logging.getLogger(__name__)


@dataclass
class Entry:
    request: TransferRequest
    wallet: TonWallet
    done: asyncio.Future[TransferIntent]


class TransferQueue:
    """Sends the payments of one wallet in groups, one external message per group.

    A message has to wait for the previous one to land before it can take the next seqno, so while one group waits for
    its block the next one fills up: whatever has queued by then goes out together, up to what the wallet carries in
    one message. A lone payment is never held back to wait for company.
    """

    def __init__(self) -> None:
        self.coordinator = LocalTransferCoordinator()  # the default one is per wallet, not per client
        self._waiting: list[Entry] = []
        self._runner: asyncio.Task[None] | None = None

    async def submit(self, wallet: TonWallet, request: TransferRequest) -> TransferIntent:
        loop = asyncio.get_running_loop()
        entry = Entry(request, wallet, loop.create_future())
        self._waiting.append(entry)
        if self._runner is None or self._runner.done():
            self._runner = loop.create_task(self._run())
        return await entry.done

    async def _run(self) -> None:
        while self._waiting:
            limit = self._waiting[0].wallet.batch_limit
            group = [entry for entry in self._waiting[:limit] if not entry.done.cancelled()]
            del self._waiting[:limit]
            if not group:
                continue
            try:
                await self._send(group)
            except Exception as exc:
                for entry in group:
                    if not entry.done.done():
                        entry.done.set_exception(exc)

    async def _send(self, group: list[Entry]) -> None:
        wallet = group[0].wallet
        async with wallet.coordinator.lock():
            group = drop_expired(group)
            if not group:
                return
            valid_until = signing_expiry((entry.request.deadline for entry in group), time.time())
            params = await wallet.transfer_params(valid_until)
            external = await wallet.sign([entry.request.builder for entry in group], params)
            intents = [entry.request.intent(external, valid_until) for entry in group]
            logger.debug("Signed %d transfer(s) as %s (valid_until=%d)", len(intents), intents[0].msg_hash, valid_until)
            for entry, intent in zip(group, intents, strict=True):
                if entry.request.on_prepared is not None:
                    await entry.request.on_prepared(intent)
            await broadcast(await wallet.ton(), external.as_hex)
            await wallet.commit_seqno(params, valid_until)
        for entry, intent in zip(group, intents, strict=True):
            if not entry.done.done():
                entry.done.set_result(intent)


def drop_expired(group: list[Entry]) -> list[Entry]:
    """The entries whose invoice is still open; the others fail as retryable."""
    kept = []
    for entry in group:
        deadline = entry.request.deadline
        if deadline is not None and deadline <= time.time():
            entry.done.set_exception(TransactionError.expired(deadline))
        else:
            kept.append(entry)
    return kept


async def broadcast(ton: Any, boc_hex: str) -> None:
    """Send the signed message. Only a definite rejection raises: the chain decides whether it landed.

    Other send errors are logged: Fragment's confirmation API reports the outcome, and toncenter answers 500 to some
    sends that went through. Rate limits and transient errors were already retried by the tonutils client.
    """
    try:
        await ton.send_message(boc_hex)
    except ProviderResponseError as exc:
        code = exc.code
        if code is not None and 400 <= code < 500 and code != HTTPStatus.TOO_MANY_REQUESTS:
            raise ProviderError(f"Transfer rejected by provider (HTTP {code}): {exc}", status=code) from exc
        logger.warning("Failed to send transfer: %s", exc)
    except Exception as exc:
        logger.warning("Failed to send transfer: %s", exc)


# One queue per wallet and event loop: purchases of different clients on the same wallet end up in the same groups.
_queues: WeakKeyDictionary[asyncio.AbstractEventLoop, dict[str, TransferQueue]] = WeakKeyDictionary()


def queue_for(address: str) -> TransferQueue:
    return _queues.setdefault(asyncio.get_running_loop(), {}).setdefault(address, TransferQueue())
