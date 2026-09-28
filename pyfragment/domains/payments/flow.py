from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import DEVICE_INFO
from pyfragment.domains.payments.confirmation import confirm_purchase, is_confirmed
from pyfragment.enums import ApiError, ApiMethod, PaymentMethod
from pyfragment.exceptions import AlreadySubscribedError, FragmentAPIError, VerificationError
from pyfragment.schemas import InvoiceRequest, TransactionLink, error_text, has_error
from pyfragment.services.tonapi.account import get_account_info
from pyfragment.services.tonapi.transaction import process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient

logger = logging.getLogger(__name__)


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
    Fragment cannot cancel a GRAM/USDT invoice (``cancelInvoice`` answers "Bad request" for it), so an invoice
    abandoned by a failure simply expires on its own.
    """
    result = await client.call(flow.init_method, init_data, page_url=flow.page_url)
    if has_error(result, ApiError.ALREADY_SUBSCRIBED):
        raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
    invoice = InvoiceRequest.from_response(result)
    if not invoice.req_id:
        if error := error_text(result):
            raise FragmentAPIError(error)
        raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context=flow.label))

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
    state_response = await confirm_purchase(client, account, tx_boc, transaction, flow.state_method, flow.page_url)
    return PurchaseReceipt(transaction_id=tx_hash, confirmed=is_confirmed(state_response))
