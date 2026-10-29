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

- `PremiumResult(transaction_id, username, amount, confirmed, comment, boc)`

`confirmed` reflects Fragment's own post-broadcast acknowledgement, not whether the transfer happened — see [Result Models](../../reference/models.md#confirmed).

## Checking the recipient first

`await client.check_premium_recipient(username, months=3)` looks the recipient up without buying anything and returns a `Recipient(recipient, username, name, photo, myself)`, or raises `UserNotFoundError`. It also raises `AlreadySubscribedError` if the user already has Premium.

The recipient is sent to Fragment as typed (Fragment parses `@username` and `t.me` links itself); `username` in results is the query as you passed it.

## Typical errors

- `ConfigurationError`
- `UserNotFoundError`: the username doesn't exist, or belongs to a channel or bot
- `AlreadySubscribedError`: the recipient already has Telegram Premium
- `InsufficientBalanceError`
- `VerificationError`

## Example

```python
result: PremiumResult = await client.purchase_premium("@username", months=6, payment_method=PaymentMethod.GRAM)
print(result.transaction_id)
```
