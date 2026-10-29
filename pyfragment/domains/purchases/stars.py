from __future__ import annotations

import logging
from dataclasses import asdict
from decimal import Decimal
from typing import TYPE_CHECKING

from pyfragment.constants import STARS_PAGE, STARS_PURCHASE_MAX, STARS_PURCHASE_MIN
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase, validate_payment_method
from pyfragment.domains.purchases.models import StarsPackage, StarsResult
from pyfragment.domains.purchases.parser import parse_gram_price, parse_stars_packages
from pyfragment.domains.recipients import Recipient, find_user
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import ConfigurationError, FragmentAPIError
from pyfragment.schemas import error_text
from pyfragment.utils.validation import is_int_in_range

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

STARS_FLOW = PurchaseFlow(
    page_url=STARS_PAGE,
    state_method=ApiMethod.UPDATE_STARS_BUY_STATE,
    init_method=ApiMethod.INIT_BUY_STARS_REQUEST,
    link_method=ApiMethod.GET_BUY_STARS_LINK,
    label="Stars purchase",
)


async def _find_recipient(client: FragmentClient, username: str) -> Recipient:
    return await find_user(
        client, ApiMethod.SEARCH_STARS_RECIPIENT, STARS_FLOW.page_url, {"query": username, "quantity": ""}, username
    )


async def get_stars_price(client: FragmentClient, amount: int) -> Decimal:
    """Return the current GRAM price for ``amount`` Stars."""
    if not is_int_in_range(amount, STARS_PURCHASE_MIN, STARS_PURCHASE_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    with operation(logger, "get Stars price for %s", amount):
        result = await client.call(ApiMethod.UPDATE_STARS_PRICES, {"quantity": amount}, page_url=STARS_PAGE)
        if err := error_text(result):
            raise FragmentAPIError(err)
        price = parse_gram_price(str(result.get("cur_price", "")))
        if price is None or price <= 0:
            raise FragmentAPIError(f"Fragment returned no price for {amount} Stars")
        return price


async def get_stars_packages(client: FragmentClient) -> list[StarsPackage]:
    """Return all predefined Stars purchase packages with current GRAM and USD prices."""
    with operation(logger, "get Stars packages"):
        result = await client.call(
            ApiMethod.UPDATE_STARS_PRICES, {"quantity": STARS_PURCHASE_MIN}, page_url=STARS_PAGE
        )
        if err := error_text(result):
            raise FragmentAPIError(err)
        packages = parse_stars_packages(str(result.get("options_html", "")))
        if not packages:
            raise FragmentAPIError("Fragment returned no Stars packages")
        return packages


async def check_stars_recipient(client: FragmentClient, username: str) -> Recipient:
    with operation(logger, "check Stars recipient '%s'", username):
        return await _find_recipient(client, username)


async def purchase_stars(
    client: FragmentClient,
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsResult:
    if not is_int_in_range(amount, STARS_PURCHASE_MIN, STARS_PURCHASE_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    validate_payment_method(payment_method)

    with operation(logger, "purchase %s Stars for user '%s' using '%s'", amount, username, payment_method):
        recipient = await _find_recipient(client, username)
        await STARS_FLOW.open(client)
        payment = await run_purchase(
            client,
            STARS_FLOW,
            {"recipient": recipient.recipient, "quantity": amount, "payment_method": payment_method},
            {"show_sender": int(show_sender)},
            payment_method,
        )
        return StarsResult(**asdict(payment), username=recipient.username, amount=amount)
