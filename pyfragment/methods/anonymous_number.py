import html
from typing import TYPE_CHECKING

from pyfragment.types import AnonymousNumberError, FragmentAPIError, FragmentError, UnexpectedError
from pyfragment.types.constants import NUMBERS_PAGE
from pyfragment.types.results import LoginCodeResult, TerminateSessionsResult
from pyfragment.utils import parse_login_code

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


def _strip_plus(number: str) -> str:
    return number.lstrip("+") if isinstance(number, str) else number


async def get_login_code(client: "FragmentClient", number: str) -> LoginCodeResult:
    """Fetch the current pending login code for an anonymous number.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        number: Phone number with or without leading ``+`` (e.g. ``"+1234567890"``).

    Returns:
        :class:`LoginCodeResult` with ``number``, ``code`` (``None`` if no pending code),
        and ``active_sessions`` count.

    Raises:
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
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

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def toggle_login_codes(client: "FragmentClient", number: str, can_receive: bool) -> None:
    """Enable or disable login code delivery for an anonymous number.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        number: Phone number with or without leading ``+``.
        can_receive: ``True`` to allow receiving codes, ``False`` to block them.

    Raises:
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
    try:
        clean = _strip_plus(number)
        result = await client.call(
            "toggleLoginCodes",
            {"number": clean, "can_receive": 1 if can_receive else 0},
            page_url=NUMBERS_PAGE,
        )

        if result.get("error"):
            raise FragmentAPIError(html.unescape(result["error"]))

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


async def terminate_sessions(client: "FragmentClient", number: str) -> TerminateSessionsResult:
    """Terminate all active Telegram sessions for an anonymous number.

    This is a two-step operation: Fragment first returns a confirmation hash,
    which is then submitted to confirm the termination.

    Args:
        client: Authenticated :class:`FragmentClient` instance.
        number: Phone number with or without leading ``+``.

    Returns:
        :class:`TerminateSessionsResult` with ``number`` and ``message``.

    Raises:
        AnonymousNumberError: If the number is not owned by this account or has no active sessions,
            or if Fragment returns an error during termination.
        FragmentAPIError: If the Fragment API returns an error.
        UnexpectedError: For any other unexpected failure.
    """
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

    except FragmentError:
        raise
    except Exception as exc:
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
