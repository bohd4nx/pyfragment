from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import (
    DEVICE_INFO,
    PREMIUM_MONTHS_VALID,
    PREMIUM_PAGE,
    STARS_PAGE,
    STARS_PURCHASE_MAX,
    STARS_PURCHASE_MIN,
)
from pyfragment.domains.payments import (
    cancel_invoice,
    confirm_purchase,
    is_confirmed,
    parse_required_payment_amount,
    state_nonce,
)
from pyfragment.domains.purchases.models import PremiumResult, StarsResult
from pyfragment.enums import SUPPORTED_PAYMENT_METHODS, PaymentMethod
from pyfragment.exceptions import (
    AlreadySubscribedError,
    ConfigurationError,
    FragmentAPIError,
    FragmentError,
    TransactionError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
)
from pyfragment.services.tonapi.account import get_account_info
from pyfragment.services.tonapi.transaction import process_transaction

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


async def purchase_stars(
    client: FragmentClient,
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsResult:
    if not isinstance(amount, int) or not (STARS_PURCHASE_MIN <= amount <= STARS_PURCHASE_MAX):
        raise ConfigurationError(ConfigurationError.INVALID_STARS_AMOUNT)
    if payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(m.value for m in SUPPORTED_PAYMENT_METHODS)),
            )
        )

    try:
        result = await client.call("searchStarsRecipient", {"query": username, "quantity": ""}, page_url=STARS_PAGE)
        if "assigned to a user" in str(result.get("error", "")).lower():
            raise UserNotFoundError(UserNotFoundError.NOT_A_USER.format(username=username))
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        await client.call(
            "updateStarsBuyState",
            {"mode": "new", "lv": "false", "dh": state_nonce()},
            page_url=STARS_PAGE,
        )
        result = await client.call(
            "initBuyStarsRequest",
            {"recipient": recipient, "quantity": amount, "payment_method": payment_method},
            page_url=STARS_PAGE,
        )
        required_payment_amount = parse_required_payment_amount(result)
        req_id = result.get("req_id")
        if not req_id:
            if result.get("error"):
                raise FragmentAPIError(str(result["error"]))
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Stars purchase"))

        try:
            account = await get_account_info(client)
            transaction = await client.call(
                "getBuyStarsLink",
                {
                    "account": json.dumps(account),
                    "device": json.dumps(DEVICE_INFO),
                    "transaction": 1,
                    "id": req_id,
                    "show_sender": int(show_sender),
                },
                page_url=STARS_PAGE,
            )
            if transaction.get("need_verify"):
                raise VerificationError(VerificationError.KYC_REQUIRED)

            tx_hash, tx_boc = await process_transaction(
                client,
                transaction,
                payment_method=payment_method,
                required_payment_amount=required_payment_amount,
            )
        except TransactionError:
            # The broadcast itself may or may not have reached the chain; leave the invoice alone.
            raise
        except Exception:
            await cancel_invoice(client, req_id, STARS_PAGE)
            raise
        state_response = await confirm_purchase(client, account, tx_boc, transaction, "updateStarsBuyState", STARS_PAGE)
        return StarsResult(transaction_id=tx_hash, username=username, amount=amount, confirmed=is_confirmed(state_response))

    except FragmentError as exc:
        logger.error(
            "Failed to purchase %s Stars for user '%s' using '%s': %s",
            amount,
            username,
            payment_method,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception(
            "Failed to purchase %s Stars for user '%s' using '%s' due to an unexpected error",
            amount,
            username,
            payment_method,
        )
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def purchase_premium(
    client: FragmentClient,
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PremiumResult:
    if months not in PREMIUM_MONTHS_VALID:
        raise ConfigurationError(ConfigurationError.INVALID_MONTHS)
    if payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise ConfigurationError(
            ConfigurationError.INVALID_PAYMENT_METHOD.format(
                method=payment_method,
                supported=", ".join(sorted(m.value for m in SUPPORTED_PAYMENT_METHODS)),
            )
        )

    try:
        result = await client.call("searchPremiumGiftRecipient", {"query": username, "months": months}, page_url=PREMIUM_PAGE)
        if "assigned to a user" in str(result.get("error", "")).lower():
            raise UserNotFoundError(UserNotFoundError.NOT_A_USER.format(username=username))
        recipient = result.get("found", {}).get("recipient")
        if not recipient:
            raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))

        await client.call(
            "updatePremiumState",
            {"mode": "new", "lv": "false", "dh": state_nonce()},
            page_url=PREMIUM_PAGE,
        )
        result = await client.call(
            "initGiftPremiumRequest",
            {"recipient": recipient, "months": months, "payment_method": payment_method},
            page_url=PREMIUM_PAGE,
        )
        error_text = str(result.get("error", "")).strip().lower()
        if "already subscribed to telegram premium" in error_text:
            raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
        required_payment_amount = parse_required_payment_amount(result)
        req_id = result.get("req_id")
        if not req_id:
            if error_text:
                raise FragmentAPIError(str(result["error"]))
            raise FragmentAPIError(FragmentAPIError.NO_REQUEST_ID.format(context="Premium purchase"))

        try:
            account = await get_account_info(client)
            transaction = await client.call(
                "getGiftPremiumLink",
                {
                    "account": json.dumps(account),
                    "device": json.dumps(DEVICE_INFO),
                    "transaction": 1,
                    "id": req_id,
                    "show_sender": int(show_sender),
                },
                page_url=PREMIUM_PAGE,
            )
            if transaction.get("need_verify"):
                raise VerificationError(VerificationError.KYC_REQUIRED)

            tx_hash, tx_boc = await process_transaction(
                client,
                transaction,
                payment_method=payment_method,
                required_payment_amount=required_payment_amount,
            )
        except TransactionError:
            # The broadcast itself may or may not have reached the chain; leave the invoice alone.
            raise
        except Exception:
            await cancel_invoice(client, req_id, PREMIUM_PAGE)
            raise
        state_response = await confirm_purchase(client, account, tx_boc, transaction, "updatePremiumState", PREMIUM_PAGE)
        return PremiumResult(transaction_id=tx_hash, username=username, amount=months, confirmed=is_confirmed(state_response))

    except FragmentError as exc:
        logger.error(
            "Failed to purchase %s months of Premium for user '%s' using '%s': %s",
            months,
            username,
            payment_method,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception(
            "Failed to purchase %s months of Premium for user '%s' using '%s' due to an unexpected error",
            months,
            username,
            payment_method,
        )
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
