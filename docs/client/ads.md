# Ads

Ads methods cover two different actions:

- sending TON to a user,
- recharging your own Telegram Ads account.

## topup_ton

```python
await client.topup_ton(
    username: str,
    amount: int,
    show_sender: bool = True,
) -> AdsTopupResult
```

Rules:

- `username`: recipient Telegram username
- `amount`: integer from `1` to `1_000_000_000`
- `show_sender`: sender visibility

**Important:** `amount` must be an integer in allowed range.

## recharge_ads

```python
await client.recharge_ads(
    account: str,
    amount: int,
) -> AdsRechargeResult
```

Rules:

- `account`: channel/bot username linked to your ads account
- `amount`: integer from `1` to `1_000_000_000`

## Returns

- `AdsTopupResult(transaction_id, username, amount)`
- `AdsRechargeResult(transaction_id, amount)`

## Common errors

- `ConfigurationError`
- `UserNotFoundError` (topup recipient)
- `WalletError`
- `VerificationError`

## Related flows

- [Stars Purchase](stars/purchase.md)
- [Premium Purchase](premium/purchase.md)
