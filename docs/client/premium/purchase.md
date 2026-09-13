# Premium Purchase

Use this method to gift Telegram Premium to a specific user.

## Method

```python
await client.purchase_premium(
    username: str,
    months: int,
    show_sender: bool = True,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> PremiumResult
```

## Parameters

- `username`: accepts `@username`, `username`, or `https://t.me/username`
- `months`: one of `3`, `6`, `12`
- `show_sender`: controls sender visibility on recipient side
- `payment_method`: `PaymentMethod.GRAM` (default) or `PaymentMethod.USDT_GRAM` — other `PaymentMethod` values aren't broadcastable yet and raise `ConfigurationError`

**`months` only supports `3`, `6`, or `12`.**

## Return

- `PremiumResult(transaction_id, username, amount, confirmed)`

`confirmed` reflects Fragment's own post-broadcast acknowledgement, not whether the transfer happened — see [Result Models](../../reference/models.md#confirmed).

## Typical errors

- `ConfigurationError`
- `UserNotFoundError`
- `WalletError`
- `VerificationError`

## Example

```python
result: PremiumResult = await client.purchase_premium("@username", months=6, payment_method=PaymentMethod.GRAM)
print(result.transaction_id)
```
