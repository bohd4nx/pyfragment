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

All enums are exported from both `pyfragment` (top-level) and `pyfragment.enums`.

## Usage notes

- Use `ApiProvider` when configuring the blockchain API provider in `FragmentClient`.
- Use `PaymentMethod` for purchase and giveaway operations.
- Use `WalletVersion` when configuring `FragmentClient`.

**Passing unsupported values raises `ConfigurationError`.**
