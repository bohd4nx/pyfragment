from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import PREMIUM_PAGE
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.purchases.models import PremiumPackage, PremiumResult
from pyfragment.domains.purchases.parser import parse_premium_packages
from pyfragment.domains.recipients import Recipient, find_user
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import FragmentAPIError
from pyfragment.utils.validation import check_months, validate_payment_method

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


logger = logging.getLogger(__name__)

PREMIUM_FLOW = PurchaseFlow(
    page_url=PREMIUM_PAGE,
    state_method=ApiMethod.UPDATE_PREMIUM_STATE,
    init_method=ApiMethod.INIT_GIFT_PREMIUM_REQUEST,
    link_method=ApiMethod.GET_GIFT_PREMIUM_LINK,
    label="Premium purchase",
)


async def find_recipient(client: BaseClient, username: str, months: int) -> Recipient:
    return await find_user(
        client,
        ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT,
        PREMIUM_FLOW.page_url,
        {"query": username, "months": months},
        username,
    )


async def get_premium_packages(client: BaseClient) -> list[PremiumPackage]:
    with operation(logger, "get Premium packages"):
        html = await client._transport.fetch_page(PREMIUM_PAGE)
        packages = parse_premium_packages(html)
        if not packages:
            raise FragmentAPIError("Fragment returned no Premium packages")
        return packages


async def check_premium_recipient(client: BaseClient, username: str, months: int = 3) -> Recipient:
    check_months(months)
    with operation(logger, "check Premium recipient (username=%s, months=%s)", username, months):
        return await find_recipient(client, username, months)


async def purchase_premium(
    client: BaseClient,
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PremiumResult:
    check_months(months)
    validate_payment_method(payment_method)

    with operation(logger, "purchase Premium (username=%s, months=%s, payment_method=%s)", username, months, payment_method):
        recipient = await find_recipient(client, username, months)
        await PREMIUM_FLOW.open(client)
        payment = await run_purchase(
            client,
            PREMIUM_FLOW,
            {"recipient": recipient.recipient, "months": months, "payment_method": payment_method},
            {"show_sender": int(show_sender)},
            payment_method,
        )
        return PremiumResult(**asdict(payment), username=recipient.username, amount=months)
