# Premium Purchase

Use this method to gift Telegram Premium to a specific user.

## Method

```python
await client.purchase_premium(
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = "ton",
) -> PremiumResult
```

## Parameters

- `username`: accepts `@username`, `username`, or `https://t.me/username`
- `months`: one of `3`, `6`, `12`
- `show_sender`: controls sender visibility on recipient side
- `payment_method`: `"ton"` or `"usdt_ton"`

**`months` only supports `3`, `6`, or `12`.**

## Return

- `PremiumResult(transaction_id, username, amount)`

## Typical errors

- `ConfigurationError`
- `UserNotFoundError`
- `WalletError`
- `VerificationError`
