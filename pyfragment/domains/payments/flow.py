from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyfragment.domains.payments.confirmation import confirm_purchase
from pyfragment.domains.payments.invoice import create_invoice, request_transaction
from pyfragment.domains.payments.models import PaymentResult
from pyfragment.domains.payments.state import state_nonce
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.enums import ApiMethod, PaymentMethod, StateMode

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient

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
    # Whether the get*Link call carries account/device: fragment.com's Stars, Premium and giveaway pages
    # send only id/transaction (the wallet comes from the session), the Ads pages still send both.
    wallet_in_link: bool = True

    def state_params(self, mode: str = StateMode.NEW, dh: str | None = None, **extra: Any) -> dict[str, Any]:
        """Parameters of an ``update*State`` call of this page, as fragment.com's frontend sends them."""
        if not self.versioned_state:
            return {"mode": mode, **extra}
        return {"mode": mode, "lv": "false", "dh": dh or state_nonce(), **extra}

    async def open(self, client: BaseClient, **extra: Any) -> None:
        """The ``update*State`` call Fragment's frontend makes when the purchase page opens."""
        await client.call(self.state_method, self.state_params(**extra), page_url=self.page_url)


async def run_purchase(
    client: BaseClient,
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
    req_id = await create_invoice(client, flow, init_data)
    logger.debug("Obtained invoice (req_id=%s, flow=%s, payment_method=%s)", req_id, flow.label, payment_method)
    transaction = await request_transaction(client, flow, req_id, link_data)
    sent = await process_transaction(client, transaction, payment_method=payment_method, req_id=req_id)
    # The money is out: from here on nothing raises (confirmation failures only leave confirmed=False).
    account = client.ton_wallet.account_info()
    confirmed = await confirm_purchase(client, flow, account, sent.boc, transaction)
    logger.debug("Completed purchase (req_id=%s, flow=%s, confirmed=%s)", req_id, flow.label, confirmed)
    return PaymentResult(transaction_id=sent.msg_hash, confirmed=confirmed, comment=sent.comment, boc=sent.boc)
