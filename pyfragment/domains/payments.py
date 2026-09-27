from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import CONFIRM_STATE_POLL_INTERVAL, CONFIRM_STATE_TIMEOUT, DEVICE_INFO
from pyfragment.enums import SUPPORTED_PAYMENT_METHODS, ApiError, ApiMethod, PaymentMethod, StateMode
from pyfragment.exceptions import (
    AlreadySubscribedError,
    ConfigurationError,
    FragmentAPIError,
    TransactionError,
    VerificationError,
)
from pyfragment.schemas import InvoiceRequest, PageState, TransactionLink, error_text, has_error
from pyfragment.services.tonapi.account import get_account_info
from pyfragment.services.tonapi.transaction import process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

logger = logging.getLogger(__name__)


def validate_payment_method(payment_method: PaymentMethod) -> None:
    if payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(m.value for m in SUPPORTED_PAYMENT_METHODS)),
            )
        )


def parse_required_payment_amount(init_response: dict[str, Any]) -> float | None:
    return InvoiceRequest.from_response(init_response).amount


def state_nonce() -> str:
    # Fragment accepts a pseudo-random request nonce in state update/poll methods.
    return str(random.randint(100_000_000, 2_147_483_647))


def new_state_params(**extra: Any) -> dict[str, Any]:
    """Parameters of the ``update*State`` call Fragment's frontend makes when a purchase page opens."""
    return {"mode": StateMode.NEW, "lv": "false", "dh": state_nonce(), **extra}


async def cancel_invoice(client: FragmentClient, req_id: str, page_url: str) -> None:
    try:
        await client.call(ApiMethod.CANCEL_INVOICE, {"req_id": req_id}, page_url=page_url)
    except Exception:
        logger.exception("Failed to cancel Fragment invoice '%s'", req_id)


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


@dataclass(frozen=True)
class PurchaseFlow:
    """The Fragment API methods and page that make up one invoice-based purchase flow."""

    page_url: str
    state_method: ApiMethod
    init_method: ApiMethod
    link_method: ApiMethod
    label: str  # human-readable flow name, used in error messages


@dataclass(frozen=True)
class PurchaseReceipt:
    transaction_id: str
    confirmed: bool


async def run_purchase(
    client: FragmentClient,
    flow: PurchaseFlow,
    init_data: dict[str, Any],
    link_data: dict[str, Any] | None = None,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PurchaseReceipt:
    """Create the invoice, sign and broadcast its transaction, then wait for Fragment's confirmation.

    The caller finds the recipient and runs any page-specific state/price updates first.
    Once the transaction has been broadcast, failures are never retried or cancelled here:
    the money may already be on its way, so the invoice is only cancelled for failures before that.
    """
    result = await client.call(flow.init_method, init_data, page_url=flow.page_url)
    if has_error(result, ApiError.ALREADY_SUBSCRIBED):
        raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
    invoice = InvoiceRequest.from_response(result)
    if not invoice.req_id:
        if error := error_text(result):
            raise FragmentAPIError(error)
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context=flow.label))

    try:
        account = await get_account_info(client)
        transaction = await client.call(
            flow.link_method,
            {
                "account": json.dumps(account),
                "device": json.dumps(DEVICE_INFO),
                "transaction": 1,
                "id": invoice.req_id,
                **(link_data or {}),
            },
            page_url=flow.page_url,
        )
        if TransactionLink.from_response(transaction).need_verify:
            raise VerificationError(VerificationError.KYC_REQUIRED)

        tx_hash, tx_boc = await process_transaction(
            client,
            transaction,
            payment_method=payment_method,
            required_payment_amount=invoice.amount,
        )
    except TransactionError:
        # The broadcast itself may or may not have reached the chain; leave the invoice alone.
        raise
    except Exception:
        await cancel_invoice(client, invoice.req_id, flow.page_url)
        raise

    state_response = await confirm_purchase(client, account, tx_boc, transaction, flow.state_method, flow.page_url)
    return PurchaseReceipt(transaction_id=tx_hash, confirmed=is_confirmed(state_response))
