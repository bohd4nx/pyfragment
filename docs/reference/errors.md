# Error Handling

Good error handling is the difference between a stable integration and random production failures.

## Exception hierarchy

- `FragmentError`
  - `ClientError`
    - `ConfigurationError`
    - `CookieError`
  - `FragmentAPIError`
    - `FragmentPageError`
    - `UserNotFoundError`
    - `AlreadySubscribedError`
    - `AnonymousNumberError`
    - `TransactionError`
    - `ParseError`
    - `VerificationError`
  - `OperationError`
    - `WalletError`
    - `UnexpectedError`

## Recommended handling pattern

```python
from pyfragment import ConfigurationError, FragmentError, UserNotFoundError, WalletError

try:
    result = await client.purchase_stars("@username", amount=500)
except UserNotFoundError:
    # recipient does not exist on Fragment
    ...
except WalletError:
    # insufficient balance or wallet-side issue
    ...
except ConfigurationError:
    # invalid local input
    ...
except FragmentError:
    # any other library-level failure
    ...
```

**Catch specific errors first, then fallback to `FragmentError`.**

## Method-to-error mapping

- Stars purchase: `ConfigurationError`, `UserNotFoundError`, `WalletError`, `VerificationError`
- Premium purchase: `ConfigurationError`, `UserNotFoundError`, `AlreadySubscribedError`, `WalletError`, `VerificationError`
- Stars/Premium giveaway: `ConfigurationError`, `UserNotFoundError`, `WalletError`, `VerificationError`
- Ads operations: `ConfigurationError`, `UserNotFoundError`, `WalletError`, `VerificationError`
- Cookies/auth setup: `CookieError`, `ConfigurationError`, `FragmentPageError`

## Canonical messages

See `pyfragment/exceptions.py` for source-of-truth message templates.
