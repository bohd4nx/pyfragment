from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyfragment.constants import PREMIUM_MONTHS_VALID, PREMIUM_PAGE
from pyfragment.domains.base import operation
from pyfragment.domains.payments import PurchaseFlow, run_purchase, validate_payment_method
from pyfragment.domains.purchases.models import PremiumPackage, PremiumResult
from pyfragment.domains.purchases.parser import parse_premium_packages
from pyfragment.domains.recipients import Recipient, find_user
from pyfragment.enums import ApiMethod, PaymentMethod
from pyfragment.exceptions import ConfigurationError, FragmentAPIError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)

PREMIUM_FLOW = PurchaseFlow(
    page_url=PREMIUM_PAGE,
    state_method=ApiMethod.UPDATE_PREMIUM_STATE,
    init_method=ApiMethod.INIT_GIFT_PREMIUM_REQUEST,
    link_method=ApiMethod.GET_GIFT_PREMIUM_LINK,
    label="Premium purchase",
)


async def _find_recipient(client: FragmentClient, username: str, months: int) -> Recipient:
    return await find_user(
        client,
        ApiMethod.SEARCH_PREMIUM_GIFT_RECIPIENT,
        PREMIUM_FLOW.page_url,
        {"query": username, "months": months},
        username,
    )


async def get_premium_packages(client: FragmentClient) -> list[PremiumPackage]:
    """Return all Premium subscription packages with current GRAM and USD prices."""
    with operation(logger, "get Premium packages"):
        html = await client._transport.fetch_page(PREMIUM_PAGE)
        packages = parse_premium_packages(html)
        if not packages:
            raise FragmentAPIError("Fragment returned no Premium packages")
        return packages


async def check_premium_recipient(client: FragmentClient, username: str, months: int = 3) -> Recipient:
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    with operation(logger, "check Premium recipient '%s' for %s months", username, months):
        return await _find_recipient(client, username, months)


async def purchase_premium(
    client: FragmentClient,
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PremiumResult:
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    validate_payment_method(payment_method)

    with operation(logger, "purchase %s months of Premium for user '%s' using '%s'", months, username, payment_method):
        recipient = await _find_recipient(client, username, months)
        await PREMIUM_FLOW.open(client)
        payment = await run_purchase(
            client,
            PREMIUM_FLOW,
            {"recipient": recipient.recipient, "months": months, "payment_method": payment_method},
            {"show_sender": int(show_sender)},
            payment_method,
        )
        return PremiumResult(**asdict(payment), username=recipient.username, amount=months)
