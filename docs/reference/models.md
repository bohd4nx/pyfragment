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
- `WalletInfo(address, state, gram_balance, usdt_balance)`
- `LoginCodeResult(number, code, active_sessions)`
- `TerminateSessionsResult(number, message)`
- `UsernamesResult(items, next_offset_id)`
- `NumbersResult(items, next_offset_id)`
- `GiftsResult(items, next_offset)`

Most high-level methods return one of these dataclasses.

## Where they are used

- `purchase_stars()`: `StarsResult`
- `purchase_premium()`: `PremiumResult`
- `giveaway_stars()`: `StarsGiveawayResult`
- `giveaway_premium()`: `PremiumGiveawayResult`
- `topup_gram()`: `AdsTopupResult`
- `recharge_ads()`: `AdsRechargeResult`
- `get_wallet()`: `WalletInfo`
- `get_login_code()`: `LoginCodeResult`
- `terminate_sessions()`: `TerminateSessionsResult`
- `search_usernames()`: `UsernamesResult`
- `search_numbers()`: `NumbersResult`
- `search_gifts()`: `GiftsResult`

## Methods without dataclass return

- `toggle_login_codes()`: returns `None`
- `call()`: returns `dict[str, Any]` (raw Fragment API response)

## Cookie helper

`CookieResult` is returned by `get_cookies_from_browser()`, not by `FragmentClient` methods.

**Use these models directly in your app layer and avoid passing raw dictionaries around.**
