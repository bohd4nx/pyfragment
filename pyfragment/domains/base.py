from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from pyfragment.core.constants import BASE_HEADERS
from pyfragment.exceptions import FragmentError, UnexpectedError
from pyfragment.transport import FragmentTransport

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def raw_api_call(
    cookies: dict[str, Any],
    timeout: float,
    method: str,
    data: dict[str, Any] | None,
    page_url: str,
    headers: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """One-shot Fragment API call on a throwaway session, for use without a ``FragmentClient``."""
    transport = FragmentTransport(cookies, timeout, headers if headers is not None else dict(BASE_HEADERS))
    try:
        return await transport.call(method, data, page_url)
    finally:
        await transport.aclose()


@contextmanager
def operation(logger: logging.Logger, description: str, *args: object) -> Iterator[None]:
    """Log a failed Fragment operation once and normalize its errors.

    ``FragmentError`` subclasses are logged and re-raised untouched; anything else is wrapped in
    ``UnexpectedError``. ``description`` is a %-style template completing "Failed to ...".
    """
    try:
        yield
    except FragmentError as exc:
        logger.error("Failed to " + description + ": %s", *args, exc, exc_info=True)
        raise
    except Exception as exc:
        logger.exception("Failed to " + description + " due to an unexpected error", *args)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


class BaseService:
    def __init__(self, client: FragmentClient) -> None:
        self._client = client
