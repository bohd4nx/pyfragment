"""Reading Fragment's error text and turning it into typed exceptions."""

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
from tests.support import fixtures


class TestErrorText:
    def test_none_without_an_error(self) -> None:
        assert error_text({"ok": True}) is None
        assert error_text({"error": ""}) is None

    def test_unescapes_what_fragment_escapes(self) -> None:
        assert error_text({"error": "You&#39;re not an owner of this number"}) == "You're not an owner of this number"


class TestHasError:
    @pytest.mark.parametrize(
        ("message", "error"),
        [
            ("Please enter a username assigned to a user.", ApiError.NOT_A_USER),
            ("This account is already subscribed to Telegram Premium.", ApiError.ALREADY_SUBSCRIBED),
            ("bad REQUEST", ApiError.BAD_REQUEST),
            ("Invalid method", ApiError.INVALID_METHOD),
        ],
    )
    def test_matches_known_messages_case_insensitively(self, message: str, error: ApiError) -> None:
        assert has_error({"error": message}, error)

    def test_false_for_other_or_missing_errors(self) -> None:
        assert not has_error({"error": "Something else"}, ApiError.BAD_REQUEST)
        assert not has_error({}, ApiError.BAD_REQUEST)

    def test_real_fixture_messages(self) -> None:
        assert has_error(fixtures.response("invalid_method.json"), ApiError.INVALID_METHOD)
        assert has_error(fixtures.response("premium_recipient_already_subscribed.json"), ApiError.ALREADY_SUBSCRIBED)


class TestApiError:
    def test_none_without_an_error(self) -> None:
        assert api_error({"ok": True}) is None

    def test_unknown_message_is_a_plain_api_error(self) -> None:
        error = api_error({"error": "Amount is invalid"})
        assert type(error) is FragmentAPIError
        assert str(error) == "Amount is invalid"

    def test_server_error_is_retryable(self) -> None:
        error = api_error({"error": "Server error"})
        assert type(error) is ServerError and error.retryable

    def test_below_minimum_from_fragment(self) -> None:
        error = api_error(fixtures.response("stars_below_minimum.json"))
        assert type(error) is BelowMinimumError
        assert (error.minimum, error.maximum) == (50, None)
        assert not error.retryable

    def test_above_maximum_from_fragment(self) -> None:
        error = api_error(fixtures.response("stars_above_maximum.json"))
        assert type(error) is AboveMaximumError
        assert (error.minimum, error.maximum) == (None, 10_000_000)

    def test_too_many_winners_is_an_above_maximum(self) -> None:
        error = api_error(fixtures.response("giveaway_too_many_winners.json"))
        assert type(error) is AboveMaximumError
        assert error.maximum == 5

    def test_amount_range_names_both_bounds(self) -> None:
        error = api_error(fixtures.response("stars_amount_range.json"))
        assert type(error) is AmountError
        assert (error.minimum, error.maximum) == (50, 10_000_000)

    def test_bad_package(self) -> None:
        assert type(api_error(fixtures.response("giveaway_bad_package.json"))) is InvalidPackageError

    @pytest.mark.parametrize(
        ("message", "minimum"),
        [("You can buy a minimum of 35,000 stars", 35_000), ("you can buy a minimum of stars", None)],
    )
    def test_below_minimum_without_or_with_thousands_separators(self, message: str, minimum: int | None) -> None:
        assert api_error({"error": message}).minimum == minimum  # type: ignore[union-attr]

    @pytest.mark.parametrize("error", [e for e in ApiError if e in TYPED_ERRORS])
    def test_every_typed_message_builds_its_exception(self, error: ApiError) -> None:
        built = api_error({"error": f"prefix {error.value} 12,345 suffix"})
        assert isinstance(built, FragmentAPIError) and type(built) is not FragmentAPIError

    def test_amount_errors_share_a_base(self) -> None:
        assert issubclass(BelowMinimumError, AmountError) and issubclass(AboveMaximumError, AmountError)


class TestRaiseForError:
    def test_silent_without_an_error(self) -> None:
        raise_for_error({"ok": True})

    def test_raises_the_typed_error(self) -> None:
        with pytest.raises(BelowMinimumError):
            raise_for_error(fixtures.response("stars_below_minimum.json"))

    def test_raises_a_plain_error_for_unknown_text(self) -> None:
        with pytest.raises(FragmentAPIError, match="Something new"):
            raise_for_error({"error": "Something new"})
