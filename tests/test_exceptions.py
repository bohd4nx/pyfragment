"""The exception hierarchy, retryable flags, message templates and constructors."""

import pickle

import pytest
from tonutils.exceptions import ProviderResponseError

from pyfragment import exceptions
from pyfragment.exceptions import (
    AboveMaximumError,
    AlreadySubscribedError,
    AmountError,
    AnonymousNumberError,
    BelowMinimumError,
    ChainError,
    ChannelNotFoundError,
    ClientError,
    ConfigurationError,
    CookieError,
    FragmentAPIError,
    FragmentError,
    HTTPStatusError,
    InvalidPackageError,
    InvoiceExpiredError,
    NetworkError,
    ParseError,
    ProviderError,
    RecipientError,
    ServerError,
    SessionExpiredError,
    TransactionError,
    UnexpectedError,
    UserNotFoundError,
    VerificationError,
    WalletAlreadyLinkedError,
)
from tests.support.fake_ton import provider_error

PARENTS = [
    (ClientError, FragmentError),
    (ConfigurationError, ClientError),
    (CookieError, ClientError),
    (FragmentAPIError, FragmentError),
    (NetworkError, FragmentAPIError),
    (ServerError, FragmentAPIError),
    (HTTPStatusError, FragmentAPIError),
    (SessionExpiredError, FragmentAPIError),
    (RecipientError, FragmentAPIError),
    (UserNotFoundError, RecipientError),
    (ChannelNotFoundError, RecipientError),
    (AlreadySubscribedError, RecipientError),
    (AmountError, FragmentAPIError),
    (BelowMinimumError, AmountError),
    (AboveMaximumError, AmountError),
    (InvalidPackageError, FragmentAPIError),
    (InvoiceExpiredError, FragmentAPIError),
    (WalletAlreadyLinkedError, FragmentAPIError),
    (AnonymousNumberError, FragmentAPIError),
    (ParseError, FragmentAPIError),
    (VerificationError, FragmentAPIError),
    (ChainError, FragmentError),
    (ProviderError, ChainError),
    (TransactionError, ChainError),
    (UnexpectedError, FragmentError),
]


class TestHierarchy:
    @pytest.mark.parametrize(("child", "parent"), PARENTS, ids=lambda c: c.__name__)
    def test_parent(self, child: type[Exception], parent: type[Exception]) -> None:
        assert child.__bases__ == (parent,)

    def test_every_error_is_a_fragment_error(self) -> None:
        assert all(issubclass(getattr(exceptions, name), FragmentError) for name in exceptions.__all__)

    def test_every_public_error_is_listed_in_all(self) -> None:
        defined = {
            name for name, value in vars(exceptions).items() if isinstance(value, type) and issubclass(value, FragmentError)
        }
        assert defined == set(exceptions.__all__)

    @pytest.mark.parametrize("error", [ProviderError, TransactionError])
    def test_chain_errors_are_not_fragment_api_errors(self, error: type[Exception]) -> None:
        assert not issubclass(error, FragmentAPIError)

    def test_a_blanket_except_catches_everything_the_library_raises(self) -> None:
        with pytest.raises(FragmentError):
            raise TransactionError("x")


class TestRetryable:
    @pytest.mark.parametrize(
        "error", [NetworkError("x"), ServerError("x"), InvoiceExpiredError("x"), TransactionError.expired(1)]
    )
    def test_transient_errors(self, error: FragmentError) -> None:
        assert error.retryable

    @pytest.mark.parametrize(
        "error",
        [
            FragmentError("x"),
            ConfigurationError("x"),
            CookieError("x"),
            SessionExpiredError("x"),
            UserNotFoundError("x"),
            AmountError("x"),
            InvalidPackageError("x"),
            ParseError("x"),
            VerificationError("x"),
            TransactionError("x"),
            UnexpectedError("x"),
        ],
    )
    def test_everything_else_is_final(self, error: FragmentError) -> None:
        assert not error.retryable

    @pytest.mark.parametrize("flag", [True, False])
    def test_the_flag_can_be_overridden_per_instance(self, flag: bool) -> None:
        assert FragmentError("x", retryable=flag).retryable is flag
        assert not NetworkError("x", retryable=False).retryable

    def test_an_override_does_not_leak_to_the_class(self) -> None:
        FragmentError("x", retryable=True)

        assert FragmentError.retryable is False

    def test_the_message_is_the_exception_text(self) -> None:
        assert str(FragmentError("boom")) == "boom"
        assert str(FragmentError()) == ""


class TestHTTPStatusError:
    @pytest.mark.parametrize("status", [429, 500, 502, 503, 599])
    def test_transient_statuses_are_retryable_and_say_so(self, status: int) -> None:
        error = HTTPStatusError(status, "https://fragment.com/api")

        assert error.retryable
        assert str(error) == HTTPStatusError.UNAVAILABLE.format(status=status, url="https://fragment.com/api")

    @pytest.mark.parametrize("status", [400, 404, 418, 499])
    def test_other_statuses_are_final(self, status: int) -> None:
        error = HTTPStatusError(status, "https://fragment.com/api")

        assert not error.retryable
        assert str(error) == HTTPStatusError.BAD_STATUS.format(status=status, url="https://fragment.com/api")

    def test_keeps_status_and_url(self) -> None:
        error = HTTPStatusError(502, "u")

        assert (error.status, error.url) == (502, "u")

    @pytest.mark.parametrize("status", [429, 502, 404])
    def test_survives_pickling(self, status: int) -> None:
        restored = pickle.loads(pickle.dumps(HTTPStatusError(status, "https://fragment.com/api")))

        assert isinstance(restored, HTTPStatusError)
        assert (restored.status, restored.url, restored.retryable) == (status, "https://fragment.com/api", status != 404)
        assert str(restored) == str(HTTPStatusError(status, "https://fragment.com/api"))


class TestProviderError:
    @pytest.mark.parametrize(
        ("status", "retryable"), [(None, True), (429, True), (500, True), (503, True), (400, False), (404, False)]
    )
    def test_retryable_depends_on_the_status(self, status: int | None, retryable: bool) -> None:
        error = ProviderError("x", status)

        assert error.status == status and error.retryable is retryable

    def test_from_exception_takes_the_status_of_a_provider_answer(self) -> None:
        exc = provider_error(503, "overloaded")

        error = ProviderError.from_exception(ProviderError.BALANCE_CHECK_FAILED, exc, currency="USDT")

        assert error.status == 503 and error.retryable
        assert str(error) == ProviderError.BALANCE_CHECK_FAILED.format(currency="USDT", exc=exc)

    def test_from_exception_with_a_client_error_status_is_final(self) -> None:
        error = ProviderError.from_exception(
            ProviderError.WALLET_STATE_FAILED, ProviderResponseError(code=401, message="bad key", endpoint="tonapi.io")
        )

        assert error.status == 401 and not error.retryable

    def test_from_exception_without_a_status_is_transient(self) -> None:
        error = ProviderError.from_exception(ProviderError.WALLET_INFO_FAILED, TimeoutError("slow"))

        assert error.status is None and error.retryable
        assert "slow" in str(error)


class TestTransactionError:
    def test_expired_is_retryable_and_names_the_deadline(self) -> None:
        error = TransactionError.expired(1_900_000_000)

        assert error.retryable
        assert str(error) == TransactionError.EXPIRED.format(valid_until=1_900_000_000)


class TestAmountErrors:
    @pytest.mark.parametrize(
        ("text", "minimum", "maximum"),
        [
            ("Enter amount from 50 to 10000000", 50, 10_000_000),
            ("Enter amount from 1,000 to 2,500,000", 1_000, 2_500_000),
            ("Enter amount from 50", None, None),
            ("no numbers here", None, None),
        ],
    )
    def test_amount_error_reads_both_bounds_or_none(self, text: str, minimum: int | None, maximum: int | None) -> None:
        error = AmountError.from_text(text)

        assert (error.minimum, error.maximum, str(error)) == (minimum, maximum, text)

    def test_below_minimum_reads_the_first_number(self) -> None:
        error = BelowMinimumError.from_text("You can buy a minimum of 35,000 stars")

        assert (error.minimum, error.maximum) == (35_000, None)

    def test_above_maximum_reads_the_first_number(self) -> None:
        error = AboveMaximumError.from_text("You can choose up to 5 winners for the selected package")

        assert (error.minimum, error.maximum) == (None, 5)

    @pytest.mark.parametrize("error", [BelowMinimumError, AboveMaximumError])
    def test_a_message_without_numbers_leaves_the_bounds_empty(self, error: type[AmountError]) -> None:
        built = error.from_text("no numbers")

        assert (built.minimum, built.maximum) == (None, None)

    def test_the_constructor_takes_bounds_directly(self) -> None:
        error = AmountError("x", 1, 2)

        assert (error.minimum, error.maximum) == (1, 2)

    def test_a_bare_error_has_no_bounds(self) -> None:
        assert (AmountError("x").minimum, AmountError("x").maximum) == (None, None)


class TestMessageTemplates:
    @pytest.mark.parametrize(
        ("template", "fields"),
        [
            (ConfigurationError.MISSING_VARS, {"keys": "seed"}),
            (ConfigurationError.UNSUPPORTED_VERSION, {"value": "v", "supported": "s"}),
            (ConfigurationError.UNSUPPORTED_MNEMONIC_TYPE, {"value": "v", "supported": "s"}),
            (ConfigurationError.INVALID_SEED, {"exc": "e"}),
            (ConfigurationError.INVALID_CONFIRM_TIMEOUT, {"value": "v"}),
            (ConfigurationError.INVALID_MAX_BATCH, {"value": "v"}),
            (ConfigurationError.UNSUPPORTED_PROVIDER, {"value": "v", "supported": "s"}),
            (ConfigurationError.TOO_MANY_WINNERS, {"amount": 1000, "max": 5, "per_winner": 100}),
            (ConfigurationError.OUT_OF_RANGE, {"label": "l", "min": 1, "max": 2}),
            (ConfigurationError.INVALID_SORT, {"value": "v", "supported": "s"}),
            (ConfigurationError.INVALID_FILTER, {"value": "v", "supported": "s"}),
            (ConfigurationError.INVALID_GIFT_VIEW, {"value": "v", "supported": "s"}),
            (ConfigurationError.INVALID_GIFT_ATTRIBUTE, {"value": "v", "supported": "s"}),
            (ConfigurationError.INVALID_PAYMENT_METHOD, {"method": "m", "supported": "s"}),
            (CookieError.READ_FAILED, {"exc": "e"}),
            (CookieError.MISSING_KEYS, {"keys": "k"}),
            (NetworkError.UNREACHABLE, {"url": "u", "exc": "e"}),
            (SessionExpiredError.REJECTED, {"status": 403, "url": "u"}),
            (SessionExpiredError.ACCESS_DENIED, {"context": "c"}),
            (SessionExpiredError.NEED_TON, {"context": "c"}),
            (SessionExpiredError.NO_REQUEST_ID, {"context": "c"}),
            (SessionExpiredError.NO_HASH, {"url": "u"}),
            (SessionExpiredError.NOT_LOGGED_IN, {"url": "u"}),
            (SessionExpiredError.STALE_HASH, {"url": "u"}),
            (UserNotFoundError.NOT_FOUND, {"username": "u"}),
            (UserNotFoundError.NOT_A_USER, {"username": "u"}),
            (ChannelNotFoundError.NOT_FOUND, {"channel": "c"}),
            (ChannelNotFoundError.NOT_A_CHANNEL, {"channel": "c"}),
            (InvoiceExpiredError.EXPIRED, {"context": "c"}),
            (AnonymousNumberError.NOT_OWNED, {"number": "n"}),
            (AnonymousNumberError.TERMINATE_FAILED, {"number": "n", "error": "e"}),
            (AnonymousNumberError.TOGGLE_FAILED, {"number": "n", "error": "e"}),
            (ParseError.UNPARSEABLE, {"context": "c", "exc": "e"}),
            (ParseError.NOTHING_FOUND, {"what": "w"}),
            (ProviderError.BALANCE_CHECK_FAILED, {"currency": "c", "exc": "e"}),
            (ProviderError.WALLET_STATE_FAILED, {"exc": "e"}),
            (ProviderError.WALLET_INFO_FAILED, {"exc": "e"}),
            (TransactionError.MULTIPLE_MESSAGES, {"count": 2}),
            (TransactionError.EXPIRED, {"valid_until": 1}),
            (UnexpectedError.UNEXPECTED, {"exc": "e"}),
        ],
    )
    def test_formats_with_exactly_its_fields(self, template: str, fields: dict[str, object]) -> None:
        text = template.format(**fields)

        assert "{" not in text

    def test_the_session_errors_tell_the_user_which_cookie_to_refresh(self) -> None:
        assert "stel_token" in SessionExpiredError.ACCESS_DENIED and "stel_ton_token" in SessionExpiredError.ACCESS_DENIED
        assert "stel_ton_token" in SessionExpiredError.NEED_TON

    def test_the_verification_error_points_at_the_profile_page(self) -> None:
        from pyfragment.constants.fragment import PROFILE_PAGE

        assert PROFILE_PAGE in VerificationError.KYC_REQUIRED
