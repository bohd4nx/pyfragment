from __future__ import annotations

import html
import logging
from typing import TYPE_CHECKING

from pyfragment.core.constants import NUMBERS_PAGE
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult
from pyfragment.domains.anonymous_numbers.parser import parse_login_code
from pyfragment.domains.base import operation
from pyfragment.enums import ApiMethod
from pyfragment.exceptions import AnonymousNumberError, FragmentAPIError
from pyfragment.schemas import error_text

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


logger = logging.getLogger(__name__)


def _strip_plus(number: str) -> str:
    return number.lstrip("+")


async def get_login_code(client: FragmentClient, number: str) -> LoginCodeResult:
    with operation(logger, "get login code for number '%s'", number):
        result = await client.call(
            ApiMethod.UPDATE_LOGIN_CODES,
            {"number": _strip_plus(number), "lt": "0", "from_app": "1"},
            page_url=NUMBERS_PAGE,
        )

        if result.get("html"):
            code, active_sessions = parse_login_code(result["html"])
        else:
            code, active_sessions = None, 0

        return LoginCodeResult(number=number, code=code, active_sessions=active_sessions)


async def toggle_login_codes(client: FragmentClient, number: str, can_receive: bool) -> None:
    with operation(logger, "toggle login code delivery for number '%s' (can_receive=%s)", number, can_receive):
        result = await client.call(
            ApiMethod.TOGGLE_LOGIN_CODES,
            {"number": _strip_plus(number), "can_receive": int(can_receive)},
            page_url=NUMBERS_PAGE,
        )

        if error := error_text(result):
            raise FragmentAPIError(html.unescape(error))


async def terminate_sessions(client: FragmentClient, number: str) -> TerminateSessionsResult:
    with operation(logger, "terminate sessions for number '%s'", number):
        clean = _strip_plus(number)

        confirmation = await client.call(ApiMethod.TERMINATE_PHONE_SESSIONS, {"number": clean}, page_url=NUMBERS_PAGE)

        if error := error_text(confirmation):
            raise AnonymousNumberError(AnonymousNumberError.TERMINATE_FAILED.format(number=number, error=html.unescape(error)))

        terminate_hash = confirmation.get("terminate_hash")
        if not terminate_hash:
            raise AnonymousNumberError(AnonymousNumberError.NOT_OWNED.format(number=number))

        result = await client.call(
            ApiMethod.TERMINATE_PHONE_SESSIONS,
            {"number": clean, "terminate_hash": terminate_hash},
            page_url=NUMBERS_PAGE,
        )

        if error := error_text(result):
            raise AnonymousNumberError(AnonymousNumberError.TERMINATE_FAILED.format(number=number, error=html.unescape(error)))

        return TerminateSessionsResult(number=number, message=result.get("msg"))
