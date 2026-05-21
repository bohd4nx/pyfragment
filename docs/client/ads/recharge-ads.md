# Recharge Ads

Use this method to add funds to your Telegram Ads account.

## Method

```python
await client.recharge_ads(
    account: str,
    amount: int,
) -> AdsRechargeResult
```

## Parameters

- `account`: channel or bot username linked to your ads account
- `amount`: integer from `1` to `1_000_000_000`

**Important:** `amount` must be an integer in the allowed range.

## Return

- `AdsRechargeResult(transaction_id, amount)`
