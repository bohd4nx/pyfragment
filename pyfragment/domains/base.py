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
    """Normalize a Fragment operation's errors.

    ``FragmentError`` subclasses are re-raised untouched; anything else is wrapped in ``UnexpectedError``. The error
    is the caller's to report: it is logged here at debug level only, for context. ``description`` is a %-style
    template completing "Failed to ...".
    """
    try:
        yield
    except FragmentError as exc:
        logger.debug("Failed to " + description + ": %s", *args, exc)
        raise
    except Exception as exc:
        logger.debug("Failed to " + description + " due to an unexpected error", *args, exc_info=True)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc


class BaseService:
    def __init__(self, client: FragmentClient) -> None:
        self._client = client
