# Top Up GRAM

Use this method to send GRAM (ex TON) to a user's Telegram balance.

## Method

```python
await client.topup_gram(
    username: str,
    amount: int,
    show_sender: bool = True,
) -> AdsTopupResult
```

## Parameters

- `username`: recipient Telegram username — `@username`, `username`, or `https://t.me/username`
- `amount`: integer from `1` to `1_000_000_000`
- `show_sender`: controls sender visibility

**`amount` must be an integer in the allowed range.**

## Return

- `AdsTopupResult(transaction_id, username, amount, confirmed, comment, boc)`

`confirmed` reflects Fragment's own post-broadcast acknowledgement, not whether the transfer happened — see [Result Models](../../reference/models.md#confirmed).

## Typical errors

- `ConfigurationError`: invalid amount
- `UserNotFoundError`: recipient not found on Fragment
- `InsufficientBalanceError`: insufficient GRAM (ex TON) balance

## Example

```python
result: AdsTopupResult = await client.topup_gram("@username", amount=10, show_sender=True)
print(result.transaction_id)
```
