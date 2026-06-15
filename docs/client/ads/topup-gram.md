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

- `AdsTopupResult(transaction_id, username, amount)`

## Typical errors

- `ConfigurationError`: invalid amount
- `UserNotFoundError`: recipient not found on Fragment
- `WalletError`: insufficient GRAM (ex TON) balance

## Example

```python
result: AdsTopupResult = await client.topup_gram("@username", amount=10, show_sender=True)
print(result.transaction_id)
```
