# Literal Types

These literals describe accepted string values for key method parameters.

## PaymentMethod

```python
PaymentMethod = Literal["ton", "usdt_ton"]
```

## WalletVersion

```python
WalletVersion = Literal["V4R2", "V5R1"]
```

These literals are exported from `pyfragment` (top-level), `pyfragment.models`, and `pyfragment.models.enums`.

## Usage notes

- Use `PaymentMethod` for purchase and giveaway operations.
- Use `WalletVersion` when configuring `FragmentClient`.

**Passing unsupported values raises `ConfigurationError`.**
