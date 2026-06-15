from __future__ import annotations

import html
import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import NUMBERS_PAGE
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult
from pyfragment.domains.anonymous_numbers.parser import parse_login_code
from pyfragment.exceptions import AnonymousNumberError, FragmentAPIError, FragmentError, UnexpectedError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


def _strip_plus(number: str) -> str:
    return number.lstrip("+") if isinstance(number, str) else number


async def get_login_code(client: FragmentClient, number: str) -> LoginCodeResult:
    try:
        clean = _strip_plus(number)
        result = await client.call(
            "updateLoginCodes",
            {"number": clean, "lt": "0", "from_app": "1"},
            page_url=NUMBERS_PAGE,
        )

        if result.get("html"):
            code, active_sessions = parse_login_code(result["html"])
        else:
            code, active_sessions = None, 0

        return LoginCodeResult(number=number, code=code, active_sessions=active_sessions)

    except FragmentError as exc:
        logger.error("Failed to get login code for number '%s': %s", number, exc, exc_info=True)
        raise
    except Exception as exc:
        logger.exception("Failed to get login code for number '%s' due to an unexpected error", number)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def toggle_login_codes(client: FragmentClient, number: str, can_receive: bool) -> None:
    try:
        clean = _strip_plus(number)
        result = await client.call(
            "toggleLoginCodes",
            {"number": clean, "can_receive": 1 if can_receive else 0},
            page_url=NUMBERS_PAGE,
        )

        if result.get("error"):
            raise FragmentAPIError(html.unescape(result["error"]))

    except FragmentError as exc:
        logger.error(
            "Failed to toggle login code delivery for number '%s' (can_receive=%s): %s",
            number,
            can_receive,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.exception(
            "Failed to toggle login code delivery for number '%s' (can_receive=%s) due to an unexpected error",
            number,
            can_receive,
        )
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def terminate_sessions(client: FragmentClient, number: str) -> TerminateSessionsResult:
    try:
        clean = _strip_plus(number)

        confirmation = await client.call(
            "terminatePhoneSessions",
            {"number": clean},
            page_url=NUMBERS_PAGE,
        )

        if confirmation.get("error"):
            raise AnonymousNumberError(
                AnonymousNumberError.TERMINATE_FAILED.format(number=number, error=html.unescape(confirmation["error"]))
            )

        terminate_hash = confirmation.get("terminate_hash")
        if not terminate_hash:
            raise AnonymousNumberError(AnonymousNumberError.NOT_OWNED.format(number=number))

        result = await client.call(
            "terminatePhoneSessions",
            {"number": clean, "terminate_hash": terminate_hash},
            page_url=NUMBERS_PAGE,
        )

        if result.get("error"):
            raise AnonymousNumberError(
                AnonymousNumberError.TERMINATE_FAILED.format(number=number, error=html.unescape(result["error"]))
            )

        return TerminateSessionsResult(number=number, message=result.get("msg"))

    except FragmentError as exc:
        logger.error("Failed to terminate sessions for number '%s': %s", number, exc, exc_info=True)
        raise
    except Exception as exc:
        logger.exception("Failed to terminate sessions for number '%s' due to an unexpected error", number)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
