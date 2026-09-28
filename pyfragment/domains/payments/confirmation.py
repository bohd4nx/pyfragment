from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import CONFIRM_STATE_POLL_INTERVAL, CONFIRM_STATE_TIMEOUT, DEVICE_INFO
from pyfragment.domains.payments.state import state_nonce
from pyfragment.enums import ApiMethod, StateMode
from pyfragment.schemas import PageState, TransactionLink

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

logger = logging.getLogger(__name__)


async def confirm_purchase(
    client: FragmentClient,
    account: dict[str, Any],
    tx_boc: str,
    transaction_data: dict[str, Any],
    state_method: ApiMethod | str,
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
    link = TransactionLink.from_response(transaction_data)
    dh = state_nonce()
    try:
        if link.confirm_method:
            await client.call(
                link.confirm_method,
                {
                    "account": json.dumps(account),
                    "device": json.dumps(DEVICE_INFO),
                    "boc": tx_boc,
                    **link.confirm_params,
                },
                page_url=page_url,
            )

        deadline = time.monotonic() + CONFIRM_STATE_TIMEOUT
        mode: str = StateMode.NEW
        response: dict[str, Any] = {}
        while time.monotonic() < deadline:
            response = await client.call(state_method, {"mode": mode, "lv": "false", "dh": dh}, page_url=page_url)
            state = PageState.from_response(response, default_mode=mode)
            mode = state.mode
            if state.is_done:
                return response
            await asyncio.sleep(CONFIRM_STATE_POLL_INTERVAL)

        logger.warning("Timed out waiting for Fragment to confirm '%s' (dh=%s)", state_method, dh)
        return response
    except Exception:
        logger.exception("Failed to confirm Fragment purchase via '%s' (dh=%s)", state_method, dh)
        return None


def is_confirmed(state_response: dict[str, Any] | None) -> bool:
    """Whether `confirm_purchase()` got Fragment's definitive done signal, not just a timeout/error."""
    return state_response is not None and PageState.from_response(state_response).is_done
