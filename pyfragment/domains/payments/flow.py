from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import DEVICE_INFO
from pyfragment.domains.payments.confirmation import confirm_purchase, is_confirmed
from pyfragment.enums import ApiError, ApiMethod, PaymentMethod
from pyfragment.exceptions import AlreadySubscribedError, FragmentAPIError, TransactionError, VerificationError
from pyfragment.schemas import InvoiceRequest, TransactionLink, error_text, has_error
from pyfragment.services.tonapi.account import get_account_info
from pyfragment.services.tonapi.transaction import process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

logger = logging.getLogger(__name__)


async def cancel_invoice(client: FragmentClient, req_id: str, page_url: str) -> None:
    try:
        await client.call(ApiMethod.CANCEL_INVOICE, {"req_id": req_id}, page_url=page_url)
    except Exception:
        logger.exception("Failed to cancel Fragment invoice '%s'", req_id)


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
