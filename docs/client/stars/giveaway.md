# Stars Giveaway

Use this method to run a Stars giveaway for a channel audience.

## Method

```python
await client.giveaway_stars(
    channel: str,
    winners: int,
    amount: int,
    payment_method: PaymentMethod = "ton",
) -> StarsGiveawayResult
```

## Parameters

- `channel`: accepts `@channel`, `channel`, or `https://t.me/channel`
- `winners`: integer from `1` to `5`
- `amount`: integer from `500` to `1_000_000` (per winner)
- `payment_method`: `"ton"` or `"usdt_ton"`

**Each winner receives the full `amount` value.**

## Return

- `StarsGiveawayResult(transaction_id, channel, winners, amount)`

## Typical errors

- `ConfigurationError`
- `UserNotFoundError`
- `WalletError`
- `VerificationError`
