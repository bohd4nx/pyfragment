# Stars Purchase

Use this method to send Telegram Stars directly to a user.

## Method

```python
await client.purchase_stars(
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = "ton",
) -> StarsResult
```

## Parameters

- `username`: accepts `@username`, `username`, or `https://t.me/username`
- `amount`: integer from `50` to `1_000_000`
- `show_sender`: controls sender visibility on recipient side
- `payment_method`: `"ton"` or `"usdt_ton"`

**Amount must be between `50` and `1_000_000`.**

## Return

- `StarsResult(transaction_id, username, amount)`

## Typical errors

- `ConfigurationError`: invalid amount or payment method
- `UserNotFoundError`: target user not found
- `WalletError`: insufficient balance or wallet-side issue
- `VerificationError`: verification/KYC required for operation
