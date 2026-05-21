# Top Up TON

Use this method to send TON to a user's Telegram balance.

## Method

```python
await client.topup_ton(
    username: str,
    amount: int,
    show_sender: bool = True,
) -> AdsTopupResult
```

## Parameters

- `username`: recipient Telegram username
- `amount`: integer from `1` to `1_000_000_000`
- `show_sender`: controls sender visibility

**Important:** `amount` must be an integer in the allowed range.

## Return

- `AdsTopupResult(transaction_id, username, amount)`
