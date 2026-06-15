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
PaymentMethod.USDT_ETH    # USDT on Ethereum
PaymentMethod.USDT_POL    # USDT on Polygon
PaymentMethod.USDC_ETH    # USDC on Ethereum
PaymentMethod.USDC_BASE   # USDC on Base
PaymentMethod.USDC_POL    # USDC on Polygon
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
