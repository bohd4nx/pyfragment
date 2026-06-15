# Stars Giveaway

Use this method to run a Stars giveaway for a channel audience.

## Method

```python
await client.giveaway_stars(
    channel: str,
    winners: int,
    amount: int,
    payment_method: PaymentMethod = PaymentMethod.GRAM,
) -> StarsGiveawayResult
```

## Parameters

- `channel`: accepts `@channel`, `channel`, or `https://t.me/channel`
- `winners`: integer from `1` to `15`
- `amount`: integer from `500` to `1_000_000` (per winner)
- `payment_method`: `PaymentMethod.GRAM` (default), `PaymentMethod.USDT_GRAM`, or any other `PaymentMethod` value

**Each winner receives the full `amount` value.**

## Return

- `StarsGiveawayResult(transaction_id, channel, winners, amount)`

## Typical errors

- `ConfigurationError`
- `UserNotFoundError`
- `WalletError`
- `VerificationError`

## Example

```python
result: StarsGiveawayResult = await client.giveaway_stars("@channel", winners=3, amount=1000)
print(result.transaction_id)
```
