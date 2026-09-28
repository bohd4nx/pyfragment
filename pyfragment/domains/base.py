from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from pyfragment.exceptions import FragmentError, UnexpectedError

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


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
