"""Read Fragment's error text, match known messages and turn them into exceptions."""

import pytest

from pyfragment import (
    AboveMaximumError,
    AmountError,
    BelowMinimumError,
    FragmentAPIError,
    InvalidPackageError,
    ServerError,
)
from pyfragment.enums import ApiError
from pyfragment.utils.errors import TYPED_ERRORS, api_error, error_text, has_error, raise_for_error

# error_text / has_error


def test_error_text_none_on_success() -> None:
    assert error_text({"ok": True}) is None
    assert error_text({"error": ""}) is None


def test_error_text_returns_message() -> None:
    assert error_text({"error": "Bad request"}) == "Bad request"


@pytest.mark.parametrize(
    ("message", "error"),
    [
        ("Please enter a username assigned to a user.", ApiError.NOT_A_USER),
        ("This account is already subscribed to Telegram Premium.", ApiError.ALREADY_SUBSCRIBED),
        ("Bad request", ApiError.BAD_REQUEST),
        ("bad REQUEST", ApiError.BAD_REQUEST),
        ("Invalid method", ApiError.INVALID_METHOD),
        ("Access denied", ApiError.ACCESS_DENIED),
    ],
)
def test_has_error_matches_known_messages_case_insensitively(message: str, error: ApiError) -> None:
    assert has_error({"error": message}, error)


def test_has_error_false_for_other_or_missing_errors() -> None:
    assert not has_error({"error": "Something else"}, ApiError.BAD_REQUEST)
    assert not has_error({}, ApiError.BAD_REQUEST)


# api_error / raise_for_error


def test_api_error_none_without_an_error() -> None:
    assert api_error({"ok": True}) is None
    raise_for_error({"ok": True})


def test_api_error_is_a_plain_fragment_error_for_unknown_messages() -> None:
    error = api_error({"error": "Amount is invalid"})
    assert type(error) is FragmentAPIError
    assert str(error) == "Amount is invalid"


@pytest.mark.parametrize(
    ("message", "minimum"),
    [
        ("You can buy a minimum of 35,000 stars", 35_000),
        ("You can buy a minimum of 50 stars", 50),
        ("you can buy a minimum of stars", None),
    ],
)
def test_api_error_below_minimum_reads_the_amount(message: str, minimum: int | None) -> None:
    error = api_error({"error": message})
    assert type(error) is BelowMinimumError
    assert (error.minimum, error.maximum) == (minimum, None)
    assert str(error) == message


@pytest.mark.parametrize(
    ("message", "maximum"),
    [
        ("You can buy up to 10,000,000 stars", 10_000_000),
        ("You can choose up to 5 winners for the selected package", 5),
        ("You can choose up to 24000 subscriptions", 24_000),
    ],
)
def test_api_error_above_maximum_reads_the_amount(message: str, maximum: int) -> None:
    error = api_error({"error": message})
    assert type(error) is AboveMaximumError
    assert (error.minimum, error.maximum) == (None, maximum)


def test_api_error_amount_range_reads_both_bounds() -> None:
    error = api_error({"error": "Enter amount from 50 to 10000000"})
    assert type(error) is AmountError
    assert (error.minimum, error.maximum) == (50, 10_000_000)


def test_api_error_amount_errors_share_a_base() -> None:
    assert issubclass(BelowMinimumError, AmountError)
    assert issubclass(AboveMaximumError, AmountError)


def test_api_error_invalid_package() -> None:
    error = api_error({"error": "Please select one of the star packages."})
    assert type(error) is InvalidPackageError


def test_error_text_unescapes_what_fragment_escapes() -> None:
    assert error_text({"error": "You&#39;re not an owner of this number"}) == "You're not an owner of this number"


def test_server_error_is_retryable() -> None:
    error = api_error({"error": "Server error"})
    assert type(error) is ServerError
    assert error.retryable


def test_typed_errors_are_not_retryable() -> None:
    for message in ("You can buy a minimum of 35,000 stars", "You can buy up to 5 stars", "Enter amount from 1 to 2"):
        error = api_error({"error": message})
        assert error is not None
        assert not error.retryable


def test_raise_for_error_raises_the_typed_error() -> None:
    with pytest.raises(BelowMinimumError):
        raise_for_error({"error": "You can buy a minimum of 35,000 stars"})


# Every exception is public and every Fragment message has a place


def test_every_exception_is_exported_from_the_package() -> None:
    import inspect

    import pyfragment
    from pyfragment import exceptions

    defined = {
        name
        for name, cls in inspect.getmembers(exceptions, inspect.isclass)
        if issubclass(cls, exceptions.FragmentError) and cls.__module__ == exceptions.__name__
    }
    assert defined == set(exceptions.__all__)
    assert set(exceptions.__all__) <= set(pyfragment.__all__)


@pytest.mark.parametrize("error", [e for e in ApiError if e in TYPED_ERRORS])
def test_every_typed_message_builds_its_exception(error: ApiError) -> None:
    built = api_error({"error": f"prefix {error.value} 12,345 suffix"})
    assert built is not None
    assert isinstance(built, FragmentAPIError)
    assert type(built) is not FragmentAPIError
