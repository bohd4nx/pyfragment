from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyfragment.constants import DEVICE_INFO
from pyfragment.domains.payments.confirmation import confirm_purchase, is_confirmed
from pyfragment.domains.payments.models import PaymentResult
from pyfragment.domains.payments.state import state_nonce
from pyfragment.domains.wallet.transfer import process_transaction
from pyfragment.enums import ApiError, ApiMethod, PaymentMethod, StateMode
from pyfragment.exceptions import AlreadySubscribedError, FragmentAPIError, SessionExpiredError, VerificationError
from pyfragment.schemas import InvoiceRequest, TransactionLink, error_text, has_error

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
    # Whether the page's update*State calls carry the lv/dh pair: the Stars and Premium pages send it,
    # the Ads pages only send the mode (as fragment.com's own frontend does).
    versioned_state: bool = True

    def state_params(self, mode: str = StateMode.NEW, dh: str | None = None, **extra: Any) -> dict[str, Any]:
        """Parameters of an ``update*State`` call of this page, as fragment.com's frontend sends them."""
        if not self.versioned_state:
            return {"mode": mode, **extra}
        return {"mode": mode, "lv": "false", "dh": dh or state_nonce(), **extra}

    async def open(self, client: FragmentClient, **extra: Any) -> None:
        """The ``update*State`` call Fragment's frontend makes when the purchase page opens."""
        await client.call(self.state_method, self.state_params(**extra), page_url=self.page_url)


async def run_purchase(
    client: FragmentClient,
    flow: PurchaseFlow,
    init_data: dict[str, Any],
    link_data: dict[str, Any] | None = None,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PaymentResult:
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
        raise SessionExpiredError(SessionExpiredError.NO_REQUEST_ID.format(context=flow.label))
    logger.debug("Invoice %s obtained for %s (%s)", invoice.req_id, flow.label, payment_method)

    account = client.ton_wallet.account_info()
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
    link = TransactionLink.from_response(transaction)
    if link.need_verify:
        logger.debug(
            "Fragment returned need_verify for %s (error=%r, confirm_method=%r)",
            flow.label,
            transaction.get("error"),
            link.confirm_method,
        )
        raise VerificationError(VerificationError.KYC_REQUIRED)

    sent = await process_transaction(
        client,
        transaction,
        payment_method=payment_method,
        required_payment_amount=invoice.amount,
        req_id=invoice.req_id,
    )
    # The money is out: from here on nothing raises (confirmation failures only leave confirmed=False).
    state_response = await confirm_purchase(client, flow, account, sent.boc, transaction)
    confirmed = is_confirmed(state_response)
    logger.debug("Invoice %s: purchase %s (confirmed=%s)", invoice.req_id, flow.label, confirmed)
    return PaymentResult(transaction_id=sent.msg_hash, confirmed=confirmed, comment=sent.comment, boc=sent.boc)
