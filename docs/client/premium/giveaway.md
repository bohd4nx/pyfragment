# Premium Giveaway

Use this method to run a Telegram Premium giveaway for your channel.

## Method

```python
await client.giveaway_premium(
    channel: str,
    winners: int,
    months: int = 3,
    payment_method: PaymentMethod = "ton",
) -> PremiumGiveawayResult
```

## Parameters

- `channel`: accepts `@channel`, `channel`, or `https://t.me/channel`
- `winners`: integer from `1` to `24_000`
- `months`: one of `3`, `6`, `12`
- `payment_method`: `"ton"` or `"usdt_ton"`

**`winners` must be a positive integer, and large values can increase total cost significantly.**

## Return

- `PremiumGiveawayResult(transaction_id, channel, winners, amount)`

## Typical errors

- `ConfigurationError`
- `UserNotFoundError`
- `WalletError`
- `VerificationError`

## Example

```python
result: PremiumGiveawayResult = await client.giveaway_premium("@channel", winners=100, months=3)
print(result.amount)
```
