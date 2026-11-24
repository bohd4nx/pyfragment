from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from pyfragment.constants.chain import DEVICE_INFO
from pyfragment.enums import ApiError
from pyfragment.exceptions import AlreadySubscribedError, InvoiceExpiredError, SessionExpiredError, VerificationError
from pyfragment.schemas import InvoiceRequest, TransactionLink
from pyfragment.utils.errors import has_error, raise_for_error

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient
    from pyfragment.domains.payments.flow import PurchaseFlow

logger = logging.getLogger(__name__)


def wallet_fields(account: dict[str, Any]) -> dict[str, str]:
    """The ``account``/``device`` pair Fragment's frontend sends so it can tell which wallet is paying."""
    return {"account": json.dumps(account), "device": json.dumps(DEVICE_INFO)}


async def create_invoice(client: BaseClient, flow: PurchaseFlow, init_data: dict[str, Any]) -> str:
    result = await client.call(flow.init_method, init_data, page_url=flow.page_url)
    if has_error(result, ApiError.ALREADY_SUBSCRIBED):
        raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
    if result.get("need_ton"):
        raise SessionExpiredError(SessionExpiredError.NEED_TON.format(context=flow.label))
    req_id = InvoiceRequest.from_response(result).req_id
    if not req_id:
        raise_for_error(result)
        raise SessionExpiredError(SessionExpiredError.NO_REQUEST_ID.format(context=flow.label))
    return req_id


async def request_transaction(
    client: BaseClient, flow: PurchaseFlow, req_id: str, link_data: dict[str, Any] | None
) -> dict[str, Any]:
    transaction = await client.call(
        flow.link_method,
        {"transaction": 1, "id": req_id, **(link_data or {})},
        page_url=flow.page_url,
    )
    link = TransactionLink.from_response(transaction)
    if link.need_verify:
        logger.debug(
            "Fragment requires verification (flow=%s, error=%s, confirm_method=%s)",
            flow.label,
            transaction.get("error"),
            link.confirm_method,
        )
        raise VerificationError(VerificationError.KYC_REQUIRED)
    if has_error(transaction, ApiError.INVOICE_EXPIRED):
        raise InvoiceExpiredError(InvoiceExpiredError.EXPIRED.format(context=flow.label))
    raise_for_error(transaction)
    return transaction
