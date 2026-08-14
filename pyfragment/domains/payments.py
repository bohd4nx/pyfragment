from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import CONFIRM_STATE_POLL_INTERVAL, CONFIRM_STATE_TIMEOUT, DEVICE_INFO

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

logger = logging.getLogger(__name__)


def parse_required_payment_amount(init_response: dict[str, Any]) -> float | None:
    raw_amount = init_response.get("amount")
    try:
        # Fragment formats larger amounts with thousand separators (e.g. "1,000,000,000").
        return float(str(raw_amount).replace(",", ""))
    except (TypeError, ValueError):
        return None


def state_nonce() -> str:
    # Fragment accepts a pseudo-random request nonce in state update/poll methods.
    return str(random.randint(100_000_000, 2_147_483_647))


async def cancel_invoice(client: FragmentClient, req_id: str, page_url: str) -> None:
    try:
        await client.call("cancelInvoice", {"req_id": req_id}, page_url=page_url)
    except Exception:
        logger.exception("Failed to cancel Fragment invoice '%s'", req_id)


async def confirm_purchase(
    client: FragmentClient,
    account: dict[str, Any],
    tx_boc: str,
    transaction_data: dict[str, Any],
    state_method: str,
    page_url: str,
) -> dict[str, Any] | None:
    """Report the broadcast transaction to Fragment and wait for its own confirmation.

    Mirrors what fragment.com's frontend actually does after a wallet sends a transaction:
    it posts the signed boc to the `confirm_method` named in the transaction payload (e.g.
    "confirmReq", with `confirm_params` such as `{"id": req_id}`) so Fragment's backend starts
    tracking it, then long-polls the page's state endpoint with a fresh nonce until it reports
    `need_update: false` (mode flips new -> processing -> done). The blockchain transfer has
    already succeeded by the time this runs, so failures here are logged, not raised.
    """
    confirm_method = transaction_data.get("confirm_method")
    confirm_params = transaction_data.get("confirm_params") or {}
    dh = state_nonce()
    try:
        if confirm_method:
            await client.call(
                confirm_method,
                {
                    "account": json.dumps(account),
                    "device": json.dumps(DEVICE_INFO),
                    "boc": tx_boc,
                    **confirm_params,
                },
                page_url=page_url,
            )

        deadline = time.monotonic() + CONFIRM_STATE_TIMEOUT
        mode = "new"
        response: dict[str, Any] = {}
        while time.monotonic() < deadline:
            response = await client.call(state_method, {"mode": mode, "lv": "false", "dh": dh}, page_url=page_url)
            mode = str(response.get("mode", mode))
            if not response.get("need_update", True):
                return response
            await asyncio.sleep(CONFIRM_STATE_POLL_INTERVAL)

        logger.warning("Timed out waiting for Fragment to confirm '%s' (dh=%s)", state_method, dh)
        return response
    except Exception:
        logger.exception("Failed to confirm Fragment purchase via '%s' (dh=%s)", state_method, dh)
        return None


def is_confirmed(state_response: dict[str, Any] | None) -> bool:
    """Whether `confirm_purchase()` got Fragment's definitive done signal, not just a timeout/error."""
    return state_response is not None and not state_response.get("need_update", True)
