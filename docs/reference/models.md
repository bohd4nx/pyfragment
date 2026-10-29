# Result Models

Every high-level method returns a typed model, so you can rely on predictable fields instead of raw payload parsing.

Exported result models (the purchase results share the `PaymentResult` base: `transaction_id`, `confirmed`, `comment`, `boc`):

- `StarsResult(transaction_id, username, amount, confirmed, comment, boc)`
- `PremiumResult(transaction_id, username, amount, confirmed, comment, boc)`
- `AdsTopupResult(transaction_id, username, amount, confirmed, comment, boc)`
- `AdsRechargeResult(transaction_id, amount, confirmed, comment, boc)`
- `StarsGiveawayResult(transaction_id, channel, winners, amount, confirmed, comment, boc)`
- `PremiumGiveawayResult(transaction_id, channel, winners, amount, confirmed, comment, boc)`
- `WalletInfo(address, state, gram_balance, usdt_balance)` — exact `Decimal` balances; `usdt_balance` is `None` if the USDT lookup failed (the balance is unknown, not zero)
- `Recipient(recipient, username, name, photo, myself)` — from `check_stars_recipient()` / `check_premium_recipient()`
- `TransferIntent(msg_hash, boc, destination, amount_nano, comment, payment_method, req_id, valid_until)` — passed to `on_transfer_prepared`
- `LoginCodeResult(number, code, active_sessions)`
- `TerminateSessionsResult(number, message)`
- `UsernamesResult(items, next_offset_id)`, `NumbersResult(items, next_offset_id)`, `GiftsResult(items, next_offset)` — `items` is a list of `AuctionItem` (`slug`, `name`, `status`, `price`, `date`)
- `MyUsernamesResult(items)`, `MyNumbersResult(items)`, `MyGiftsResult(items)` — owned assets; same `AuctionItem` list format
- `StarsPackage(stars, gram, usd)` — one predefined Stars purchase option with live GRAM and USD prices
- `PremiumPackage(months, gram, usd)` — one Telegram Premium subscription option with live GRAM and USD prices

Most high-level methods return one of these dataclasses.

## Where they are used

- `purchase_stars()`: `StarsResult`
- `purchase_premium()`: `PremiumResult`
- `giveaway_stars()`: `StarsGiveawayResult`
- `giveaway_premium()`: `PremiumGiveawayResult`
- `topup_gram()`: `AdsTopupResult`
- `recharge_ads()`: `AdsRechargeResult`
- `get_wallet()`: `WalletInfo`
- `check_stars_recipient()`, `check_premium_recipient()`: `Recipient`
- `get_login_code()`: `LoginCodeResult`
- `terminate_sessions()`: `TerminateSessionsResult`
- `search_usernames()`: `UsernamesResult`
- `search_numbers()`: `NumbersResult`
- `search_gifts()`: `GiftsResult`
- `get_my_usernames()`: `MyUsernamesResult`
- `get_my_numbers()`: `MyNumbersResult`
- `get_my_gifts()`: `MyGiftsResult`
- `get_stars_price()`: `Decimal`
- `get_stars_packages()`: `list[StarsPackage]`
- `get_premium_packages()`: `list[PremiumPackage]`

## `transaction_id`, `comment` and `boc`

`transaction_id` is the normalized hash of the signed message.
`comment` is Fragment's payment reference sent with the transfer (`Ref#...`), `boc` the signed message itself.
`username` / `channel` is the query exactly as you passed it to the method.

## `confirmed`

`StarsResult`, `PremiumResult`, `AdsTopupResult`, `AdsRechargeResult`, `StarsGiveawayResult`, and `PremiumGiveawayResult` all carry a `confirmed: bool` field. A result is returned only once its GRAM (ex TON)/USDT transfer is on-chain: the payment happened. `confirmed` reflects a separate, best-effort step: after paying, the client reports the transaction to Fragment and waits (up to `confirm_timeout`, 60s by default) for Fragment's own backend to acknowledge it. If that wait times out or the report call fails, `confirmed` is `False` although the payment went through — the method does not raise in that case. Treat `confirmed` as a UI/observability signal, not as the source of truth for whether the purchase happened.

**Never retry a purchase just because `confirmed` is `False`** — that would pay twice. See [Payment Safety](../client/transfers.md).

## Methods without dataclass return

- `toggle_login_codes()`: returns `None`
- `logout()`, `disconnect_wallet()`: return `None`
- `call()`: returns `dict[str, Any]` (raw Fragment API response)

**Use these models directly in your app layer and avoid passing raw dictionaries around.**
