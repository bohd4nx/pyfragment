from __future__ import annotations

import logging
from dataclasses import asdict
from decimal import Decimal
from typing import TYPE_CHECKING

from pyfragment.constants.fragment import STARS_PAGE
from pyfragment.constants.limits import STARS_PURCHASE
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase
from pyfragment.domains.purchases.models import StarsPackage, StarsResult
from pyfragment.domains.purchases.parser import parse_gram_price, parse_stars_packages
from pyfragment.domains.recipients import Recipient, find_user
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import FragmentAPIError
from pyfragment.schemas import raise_for_error
from pyfragment.utils.validation import check_limit, validate_payment_method

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


logger = logging.getLogger(__name__)

STARS_FLOW = PurchaseFlow(
    page_url=STARS_PAGE,
    state_method=ApiMethod.UPDATE_STARS_BUY_STATE,
    init_method=ApiMethod.INIT_BUY_STARS_REQUEST,
    link_method=ApiMethod.GET_BUY_STARS_LINK,
    label="Stars purchase",
    wallet_in_link=False,
)


async def find_recipient(client: BaseClient, username: str) -> Recipient:
    return await find_user(
        client, ApiMethod.SEARCH_STARS_RECIPIENT, STARS_FLOW.page_url, {"query": username, "quantity": ""}, username
    )


async def get_stars_price(client: BaseClient, amount: int) -> Decimal:
    check_limit(STARS_PURCHASE, amount)
    with operation(logger, "get Stars price for %s", amount):
        result = await client.call(ApiMethod.UPDATE_STARS_PRICES, {"quantity": amount}, page_url=STARS_PAGE)
        raise_for_error(result)
        price = parse_gram_price(str(result.get("cur_price", "")))
        if price is None or price <= 0:
            raise FragmentAPIError(f"Fragment returned no price for {amount} Stars")
        return price


async def get_stars_packages(client: BaseClient) -> list[StarsPackage]:
    with operation(logger, "get Stars packages"):
        result = await client.call(ApiMethod.UPDATE_STARS_PRICES, {"quantity": STARS_PURCHASE.min}, page_url=STARS_PAGE)
        raise_for_error(result)
        packages = parse_stars_packages(str(result.get("options_html", "")))
        if not packages:
            raise FragmentAPIError("Fragment returned no Stars packages")
        return packages


async def check_stars_recipient(client: BaseClient, username: str) -> Recipient:
    with operation(logger, "check Stars recipient '%s'", username):
        return await find_recipient(client, username)


async def purchase_stars(
    client: BaseClient,
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsResult:
    check_limit(STARS_PURCHASE, amount)
    validate_payment_method(payment_method)

    with operation(logger, "purchase %s Stars for user '%s' using '%s'", amount, username, payment_method):
        recipient = await find_recipient(client, username)
        await STARS_FLOW.open(client)
        payment = await run_purchase(
            client,
            STARS_FLOW,
            {"recipient": recipient.recipient, "quantity": amount, "payment_method": payment_method},
            {"show_sender": int(show_sender)},
            payment_method,
        )
        return StarsResult(**asdict(payment), username=recipient.username, amount=amount)
