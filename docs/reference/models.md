# Result Models

Every high-level method returns a typed model, so you can rely on predictable fields instead of raw payload parsing.

Exported result models:

- `CookieResult(cookies, expires)`
- `StarsResult(transaction_id, username, amount)`
- `PremiumResult(transaction_id, username, amount)`
- `AdsTopupResult(transaction_id, username, amount)`
- `AdsRechargeResult(transaction_id, amount)`
- `StarsGiveawayResult(transaction_id, channel, winners, amount)`
- `PremiumGiveawayResult(transaction_id, channel, winners, amount)`
- `WalletInfo(address, state, ton_balance, usdt_balance)`
- `LoginCodeResult(number, code, active_sessions)`
- `TerminateSessionsResult(number, message)`
- `UsernamesResult(items, next_offset_id)`
- `NumbersResult(items, next_offset_id)`
- `GiftsResult(items, next_offset)`

Most high-level methods return one of these dataclasses.

## Where they are used

- Stars/Premium purchase: `StarsResult`, `PremiumResult`
- Stars/Premium giveaway: `StarsGiveawayResult`, `PremiumGiveawayResult`
- Ads: `AdsTopupResult`, `AdsRechargeResult`
- Wallet and utility: `WalletInfo`, `LoginCodeResult`, `TerminateSessionsResult`
- Marketplace search: `UsernamesResult`, `NumbersResult`, `GiftsResult`

**Use these models directly in your app layer and avoid passing raw dictionaries around.**
