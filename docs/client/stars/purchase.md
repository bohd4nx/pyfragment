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
- `payment_method`: `PaymentMethod.GRAM` (default) or `PaymentMethod.USDT_GRAM` — other `PaymentMethod` values aren't broadcastable yet and raise `ConfigurationError`

**Amount must be between `50` and `10_000_000`.**

## Return

- `StarsResult(transaction_id, username, amount, confirmed, comment, boc)`

`confirmed` reflects Fragment's own post-broadcast acknowledgement, not whether the transfer happened — see [Result Models](../../reference/models.md#confirmed).

## Checking the recipient first

`await client.check_stars_recipient(username)` looks the recipient up without buying anything and returns a `Recipient(recipient, username, name, photo, myself)`, or raises `UserNotFoundError`.

The recipient is sent to Fragment as typed (Fragment parses `@username` and `t.me` links itself); `username` in results is the query as you passed it.

## Typical errors

- `ConfigurationError`: invalid amount or payment method
- `UserNotFoundError`: the username doesn't exist, or belongs to a channel or bot
- `InsufficientBalanceError`: the wallet can't cover the payment plus the gas reserve (`balance`, `required`, `currency`)
- `VerificationError`: verification/KYC required for operation

## Example

```python
result: StarsResult = await client.purchase_stars("@username", amount=500, payment_method=PaymentMethod.GRAM)
print(result.amount)
```
