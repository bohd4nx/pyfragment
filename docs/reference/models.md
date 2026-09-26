# Result Models

Every high-level method returns a typed model, so you can rely on predictable fields instead of raw payload parsing.

Exported result models:

- `CookieResult(cookies, expires)`
- `StarsResult(transaction_id, username, amount, confirmed)`
- `PremiumResult(transaction_id, username, amount, confirmed)`
- `AdsTopupResult(transaction_id, username, amount, confirmed)`
- `AdsRechargeResult(transaction_id, amount, confirmed)`
- `StarsGiveawayResult(transaction_id, channel, winners, amount, confirmed)`
- `PremiumGiveawayResult(transaction_id, channel, winners, amount, confirmed)`
- `WalletInfo(address, state, gram_balance, usdt_balance)` — `usdt_balance` is `None` if the USDT lookup failed (the balance is unknown, not zero)
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

## `confirmed`

`StarsResult`, `PremiumResult`, `AdsTopupResult`, `AdsRechargeResult`, `StarsGiveawayResult`, and `PremiumGiveawayResult` all carry a `confirmed: bool` field. `transaction_id` is set as soon as the GRAM (ex TON)/USDT transfer is broadcast to the chain — the purchase itself already happened at that point. `confirmed` reflects a separate, best-effort step: after broadcasting, the client reports the transaction to Fragment and waits (up to ~60s) for Fragment's own backend to acknowledge it. If that wait times out or the report call fails, `confirmed` is `False` even though the payment went through — the method does not raise in that case. Treat `confirmed` as a UI/observability signal, not as the source of truth for whether the purchase happened.

## Methods without dataclass return

- `toggle_login_codes()`: returns `None`
- `call()`: returns `dict[str, Any]` (raw Fragment API response)

## Cookie helper

`CookieResult` is returned by `get_cookies_from_browser()`, not by `FragmentClient` methods.

**Use these models directly in your app layer and avoid passing raw dictionaries around.**
