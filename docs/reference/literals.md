# Literal Types

These literals describe accepted string values for key method parameters.

## ApiProvider

```python
from pyfragment.enums import ApiProvider

ApiProvider.TONAPI    # tonconsole.com — default
ApiProvider.TONCENTER # t.me/toncenter
```

Pass as string to `FragmentClient(api_provider=...)`:

```python
FragmentClient(..., api_provider="tonapi")    # default
FragmentClient(..., api_provider="toncenter")
```

## PaymentMethod

```python
from pyfragment.enums import PaymentMethod

PaymentMethod.GRAM        # GRAM (ex TON) — default
PaymentMethod.USDT_GRAM   # USDT on GRAM (ex TON)
PaymentMethod.USDT_ETH    # USDT on Ethereum (not supported yet)
PaymentMethod.USDT_POL    # USDT on Polygon (not supported yet)
PaymentMethod.USDC_ETH    # USDC on Ethereum (not supported yet)
PaymentMethod.USDC_BASE   # USDC on Base (not supported yet)
PaymentMethod.USDC_POL    # USDC on Polygon (not supported yet)
```

Only `GRAM` and `USDT_GRAM` can be broadcast today. To check programmatically, use `SUPPORTED_PAYMENT_METHODS`:

```python
from pyfragment import SUPPORTED_PAYMENT_METHODS

PaymentMethod.USDT_ETH in SUPPORTED_PAYMENT_METHODS  # False
```

## WalletVersion

```python
from pyfragment.enums import WalletVersion

WalletVersion.V5R1       # default
WalletVersion.V4R2
WalletVersion.HighloadV2
WalletVersion.HighloadV3R1
```

## ApiMethod

Every Fragment `/api` method the library calls (`ApiMethod.SEARCH_STARS_RECIPIENT`, `ApiMethod.INIT_BUY_STARS_REQUEST`, …). `client.call()` accepts an `ApiMethod` or any plain method name.

## ApiError

Error texts Fragment returns in the `error` field of an HTTP 200 response (`BAD_REQUEST`, `INVALID_METHOD`, `ACCESS_DENIED`, `NOT_A_USER`, `ALREADY_SUBSCRIBED`). Fragment reports failures in the body, not in the HTTP status.

## AuctionSort / AuctionFilter / MarketplaceType

```python
from pyfragment import AuctionFilter, AuctionSort

await client.search_usernames("ton", sort=AuctionSort.PRICE_ASC, filter=AuctionFilter.SALE)
```

- `AuctionSort`: `PRICE` (default), `PRICE_DESC`, `PRICE_ASC`, `LISTED`, `ENDING`
- `AuctionFilter`: `AVAILABLE` (`""`, default), `AUCTION`, `SALE`, `SOLD`
- `MarketplaceType`: `USERNAMES`, `NUMBERS`, `GIFTS`

## StateMode

`NEW`, `PROCESSING`, `DONE` — the `mode` of a purchase page while Fragment processes a transaction.

All enums are exported from both `pyfragment` (top-level) and `pyfragment.enums`.

## Usage notes

- Use `ApiProvider` when configuring the blockchain API provider in `FragmentClient`.
- Use `PaymentMethod` for purchase and giveaway operations.
- Use `WalletVersion` when configuring `FragmentClient`.

**Passing unsupported values raises `ConfigurationError`.**
