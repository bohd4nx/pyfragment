# Error Handling

Tell failures apart by exception class and attributes, never by message text.

## Exception hierarchy

- `FragmentError` — every error has `retryable`: nothing was sent and repeating the call may succeed
  - `ClientError`
    - `ConfigurationError` — invalid argument or client option
    - `CookieError` — unreadable cookies or missing `stel_*` keys
  - `FragmentAPIError` — Fragment's API answered with an error (the message is Fragment's own text)
    - `NetworkError` — Fragment could not be reached (retryable)
    - `HTTPStatusError` — unexpected HTTP status: `status`, `url` (retryable for 429 and 5xx)
    - `SessionExpiredError` — the session behind the cookies is logged out: refresh the cookies
    - `RecipientError`
      - `UserNotFoundError`
      - `ChannelNotFoundError`
      - `AlreadySubscribedError`
    - `VerificationError` — KYC required
    - `ParseError`
    - `AnonymousNumberError`
  - `ChainError` — the GRAM (ex TON) side
    - `InsufficientBalanceError` — `balance`, `required` (exact `Decimal`s), `currency`
    - `ProviderError` — tonapi/toncenter failed: `status` (retryable)
    - `TransactionError` — Fragment's transaction can't be signed (invalid, or its invoice expired: retryable)
  - `UnexpectedError`

## Did money leave the wallet?

`retryable=True` on any error means nothing was paid and the purchase is safe to retry. The library signs and sends a transfer only once; if the send fails, Fragment's confirmation API is the authoritative signal. See [Payment Safety](../client/transfers.md).

## Recommended handling pattern

```python
from pyfragment import (
    ConfigurationError,
    FragmentError,
    InsufficientBalanceError,
    SessionExpiredError,
    UserNotFoundError,
)

try:
    result = await client.purchase_stars("@username", amount=500)
except UserNotFoundError:
    ...  # recipient does not exist on Fragment
except InsufficientBalanceError as error:
    ...  # top up error.required - error.balance error.currency
except SessionExpiredError:
    ...  # refresh the Fragment cookies
except ConfigurationError:
    ...  # invalid local input
except FragmentError as error:
    ...  # anything else; error.retryable says whether to try again
```

## Method-to-error mapping

- Stars purchase: `ConfigurationError`, `UserNotFoundError`, `InsufficientBalanceError`, `VerificationError`
- Premium purchase: the same plus `AlreadySubscribedError` (raised as soon as Fragment reports it at recipient lookup)
- Stars/Premium giveaway: `ConfigurationError`, `ChannelNotFoundError`, `InsufficientBalanceError`, `VerificationError`
- Ads operations: `ConfigurationError`, `UserNotFoundError`, `InsufficientBalanceError`, `VerificationError`
- Any call to Fragment: `SessionExpiredError`, `HTTPStatusError`, `NetworkError`
- Wallet and transfer lookups: `ProviderError`

## Canonical messages

See `pyfragment/exceptions.py` for the message templates.
