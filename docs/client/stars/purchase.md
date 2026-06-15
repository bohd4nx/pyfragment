# Stars Purchase

Use this method to send Telegram Stars directly to a user.

## Method

```python
await client.purchase_stars(
    username: str,
    amount: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsResult
```

## Parameters

- `username`: accepts `@username`, `username`, or `https://t.me/username`
- `amount`: integer from `50` to `10_000_000`
- `show_sender`: controls sender visibility on recipient side
- `payment_method`: `PaymentMethod.GRAM` (default), `PaymentMethod.USDT_GRAM`, or any other `PaymentMethod` value

**Amount must be between `50` and `10_000_000`.**

## Return

- `StarsResult(transaction_id, username, amount)`

## Typical errors

- `ConfigurationError`: invalid amount or payment method
- `UserNotFoundError`: target user not found
- `WalletError`: insufficient balance or wallet-side issue
- `VerificationError`: verification/KYC required for operation

## Example

```python
result: StarsResult = await client.purchase_stars("@username", amount=500, payment_method=PaymentMethod.GRAM)
print(result.amount)
```
