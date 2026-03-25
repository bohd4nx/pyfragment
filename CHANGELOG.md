# Changelog

All notable changes to pyfragment are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Calendar Versioning](https://calver.org/) (`YYYY.MINOR.MICRO`).

---

## [Unreleased]

### Added

**Giveaways**
- `giveaway_stars(channel, winners, amount)` — run a Telegram Stars giveaway for a channel (1–5 winners, 500–1 000 000 stars each); raises `UserNotFoundError` if the channel is not found on Fragment, `ConfigurationError` if `winners` or `amount` are out of range
- `giveaway_premium(channel, winners, months)` — run a Telegram Premium giveaway for a channel (1–24 000 winners, 3/6/12 months each); raises `UserNotFoundError` if the channel is not found on Fragment, `ConfigurationError` if `winners` or `months` are invalid
- `StarsGiveawayResult` and `PremiumGiveawayResult` result types

**Telegram Ads**
- `recharge_ads(account, amount)` — add funds to your own Telegram Ads account; `account` is the channel or bot username linked to your Ads account; raises `ConfigurationError` if `amount` is out of range (1–1 000 000 000 TON)
- `AdsRechargeResult` result type

**Marketplace**
- `search_auctions(query, type?, sort?, filter?, offset_id?)` — search the Fragment marketplace for usernames, numbers, or collectibles; `type` is one of `"usernames"`, `"numbers"`, `"collectibles"` (optional); `sort` is one of `"price_desc"`, `"price_asc"`, `"listed"`, `"ending"`; `filter` is one of `""`, `"auction"`, `"sale"`, `"sold"`; supports pagination via `offset_id`; returns parsed item dicts with `slug`, `name`, `status`, `price`, `ends_at`
- `AuctionsResult` result type

**Raw API access**
- `FragmentClient.call(method, data, *, page_url)` — send a raw request to any Fragment API method without waiting for a library update
- `FRAGMENT_BASE_URL` constant — single source of truth for the Fragment base URL used across all page constants and headers

**Anonymous number management**
- `get_login_code(number)` — fetch the current pending login code for an anonymous number
- `toggle_login_codes(number, can_receive)` — enable or disable login code delivery for an anonymous number
- `terminate_sessions(number)` — terminate all active Telegram sessions for an anonymous number (two-step flow handled internally)
- `LoginCodeResult` and `TerminateSessionsResult` result types
- `AnonymousNumberError` exception — raised when a number is not owned or session termination fails

**Examples**
- `examples/giveaway_stars.py` — Stars giveaway with `UserNotFoundError` / `ConfigurationError` handling
- `examples/giveaway_premium.py` — Premium giveaway with `UserNotFoundError` / `ConfigurationError` handling
- `examples/call.py` — raw API call via `client.call()`
- `examples/anonymous_number.py` — login code fetch and session termination with `AnonymousNumberError` handling
- `examples/recharge_ads.py` — self-service Ads recharge with `ConfigurationError` / `WalletError` handling

### Changed
- All result types (`PremiumResult`, `StarsResult`, `StarsGiveawayResult`, `PremiumGiveawayResult`) now use a single unified `amount` field instead of `months`, `stars` — consistent API across every method
- `__repr__` on result types now includes the unit (`3 months`, `500 stars`) for clarity
- Method module files renamed to match their function: `premium.py` → `purchase_premium.py`, `stars.py` → `purchase_stars.py`, `ton.py` → `topup_ton.py`
- `timestamp` field removed from all result dataclasses
- All page URL constants (`STARS_PAGE`, `PREMIUM_PAGE`, etc.) now built from `FRAGMENT_BASE_URL` instead of hardcoded strings
- `STARS_REVENUE_PAGE` and `ADS_PAGE` constants replaced by a single `ADS_TOPUP_PAGE` shared by both `topup_ton` and `recharge_ads`
- `TransactionError` now includes an SSL hint when a broadcast fails due to certificate verification errors
- `TransactionError.DUPLICATE_SEQNO` — dedicated error raised after 3 failed attempts due to a `406 Duplicate msg_seqno` response from the TON network; broadcast is automatically retried (up to 2 retries, 2 s apart) before giving up
- All error message templates rewritten to follow a "what happened → why → what to do" pattern — every template is now actionable and includes a fix hint where applicable

---

## [2026.0.2] — 2026-03-20

### Added
- `timeout` parameter on `FragmentClient` (default `30.0` s) — passed through to every HTTP request

### Changed
- Cookie validation: narrowed type internally so no `# type: ignore` is needed in `FragmentClient.__init__`
- `WALLET_CLASSES` typed as `dict[str, Any]` so mypy resolves `from_mnemonic` correctly
- All four `examples/` files updated to `async with FragmentClient`, f-strings, and aligned error messages
- README usage section rewritten with a single comprehensive `async with` example

### Fixed
- mypy: missing return path in `process_transaction` after retry loop
- mypy: `cookies` union-attr error in `FragmentClient.__init__`

---

## [2026.0.1] — 2026-03-16

### Added
- Initial stable release of `pyfragment`
- `FragmentClient` — async client for the Fragment.com API with context manager support (`async with`)
- `purchase_premium(username, months)` — purchase Telegram Premium for any user (3, 6, or 12 months)
- `purchase_stars(username, amount)` — send Telegram Stars to any user (50–1,000,000)
- `topup_ton(username, amount)` — top up TON Ads balance (1–1,000,000,000 TON)
- `get_wallet()` — fetch wallet address and balance
- Support for TON wallet versions `V4R2` and `V5R1`
- Structured exception hierarchy (`FragmentError`, `ConfigurationError`, `CookieError`, etc.)
- `py.typed` marker — full PEP 561 typing support for type-checkers
- `__repr__` on all result types for readable debug output

[2026.0.2]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.2
[2026.0.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.1
