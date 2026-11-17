from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from pyfragment.exceptions import FragmentError, UnexpectedError


@contextmanager
def operation(logger: logging.Logger, description: str, *args: object) -> Iterator[None]:
    """Re-raise ``FragmentError`` as is and wrap anything else in ``UnexpectedError``; log only at debug level.

    ``description`` is a %-style template completing "Failed to ...".
    """
    try:
        yield
    except FragmentError as exc:
        logger.debug("Failed to " + description + ": %s", *args, exc)
        raise
    except Exception as exc:
        logger.debug("Failed to " + description + " due to an unexpected error", *args, exc_info=True)
        raise UnexpectedError(UnexpectedError.UNEXPECTED.format(exc=exc)) from exc
