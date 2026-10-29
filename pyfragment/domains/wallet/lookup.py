from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ton_core import normalize_hash

from pyfragment.constants import TRANSACTIONS_PAGE_SIZE
from pyfragment.domains.wallet.models import TransferInfo
from pyfragment.domains.wallet.payload import body_comment
from pyfragment.domains.wallet.wallet import provider_error
from pyfragment.exceptions import ConfigurationError, ProviderError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

logger = logging.getLogger(__name__)


def _succeeded(tx: Any) -> bool:
    # Wallets send with "ignore errors": a transfer the wallet can't afford is skipped silently while the tx
    # succeeds and seqno advances. Both outmsg_cnt > 0 and skipped_actions == 0 must hold.
    description = tx.description
    if getattr(description, "aborted", True):
        return False
    compute = getattr(description, "compute_ph", None)
    action = getattr(description, "action", None)
    return (
        compute is not None
        and bool(compute.success)
        and action is not None
        and action.success
        and action.skipped_actions == 0
        and tx.outmsg_cnt > 0
    )


def _msg_hash(tx: Any) -> str | None:
    in_msg = tx.in_msg
    return normalize_hash(in_msg) if in_msg is not None and in_msg.is_external else None


def _comments(tx: Any) -> list[str]:
    return [comment for out in tx.out_msgs if (comment := body_comment(out.body)) is not None]


def _transfer_info(tx: Any) -> TransferInfo:
    comments = _comments(tx)
    return TransferInfo(
        hash=tx.cell.hash.hex(),
        lt=tx.lt,
        utime=tx.now,
        msg_hash=_msg_hash(tx),
        comment=comments[0] if comments else None,
        success=_succeeded(tx),
    )


async def _scan_transactions(
    client: FragmentClient,
    *,
    stop: Callable[[Any], bool],
    match: Callable[[Any], bool],
) -> TransferInfo | None:
    ton_wallet = client.ton_wallet
    try:
        ton = await ton_wallet.ton()
        address = ton_wallet.wallet().address
        from_lt: int | None = None
        while True:
            page = await ton.get_transactions(address, limit=TRANSACTIONS_PAGE_SIZE, from_lt=from_lt)
            for tx in page:
                if stop(tx):
                    return None
                if match(tx):
                    return _transfer_info(tx)
            if len(page) < TRANSACTIONS_PAGE_SIZE:
                return None
            from_lt = page[-1].lt - 1
    except Exception as exc:
        raise provider_error(ProviderError.TRANSFER_LOOKUP_FAILED, exc) from exc


async def find_transfer(
    client: FragmentClient,
    *,
    msg_hash: str | None = None,
    comment: str | None = None,
    since: datetime,
) -> TransferInfo | None:
    """The newest wallet transaction since ``since`` started by ``msg_hash`` and/or sending ``comment``, or ``None``.

    Raises ``ProviderError`` when the history can't be read: "couldn't check" is never reported as "not found".
    """
    if msg_hash is None and comment is None:
        raise ConfigurationError(ConfigurationError.TRANSFER_QUERY)
    since_ts = since.timestamp()
    low_hash = msg_hash.lower() if msg_hash is not None else None
    return await _scan_transactions(
        client,
        stop=lambda tx: tx.now < since_ts,
        match=lambda tx: (low_hash is None or _msg_hash(tx) == low_hash) and (comment is None or comment in _comments(tx)),
    )


async def _find_transfer_by_lt(
    client: FragmentClient,
    *,
    msg_hash: str,
    last_lt: int,
) -> TransferInfo | None:
    """Find the wallet transaction that matches ``msg_hash``, stopping at ``last_lt``.

    Uses the wallet's logical time (not the local clock) as the lower bound, which eliminates clock-skew false
    negatives: any transaction with lt <= last_lt predates our send, so we stop there.
    """
    low_hash = msg_hash.lower()
    return await _scan_transactions(
        client,
        stop=lambda tx: tx.lt <= last_lt,
        match=lambda tx: _msg_hash(tx) == low_hash,
    )
