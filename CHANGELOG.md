# Changelog

All notable changes to pyfragment are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Calendar Versioning](https://calver.org/) (`YYYY.MINOR.MICRO`).

---

## [2026.2.0] — 2026-04-14

### Added

- `get_cookies_from_browser(browser)` — extract Fragment session cookies directly from an installed browser (Chrome, Firefox, Edge, Brave, Arc, Opera, Safari, and more); no browser extension or manual copy-paste required
  ```python
  from pyfragment.utils import get_cookies_from_browser
  cookies = get_cookies_from_browser("chrome")  # or "firefox", "edge", "brave", ...
  client = FragmentClient(seed="...", api_key="...", cookies=cookies)
  ```

### Changed

- `tonutils` upgraded to **2.1.0**

---

## [2026.1.0] — 2026-03-25

### Added

**Giveaways**
- `giveaway_stars(channel, winners, amount)` — Stars giveaway; 1–5 winners, 500–1 000 000 stars each
- `giveaway_premium(channel, winners, months)` — Premium giveaway; 1–24 000 winners, 3/6/12 months each
- `StarsGiveawayResult`, `PremiumGiveawayResult` result types

**Telegram Ads**
- `recharge_ads(account, amount)` — top up a Telegram Ads account; 1–1 000 000 000 TON
- `AdsRechargeResult` result type

**Marketplace**
- `search_usernames(query?, sort?, filter?, offset_id?)` — search Fragment usernames; `sort`: `price_desc / price_asc / listed / ending`, `filter`: `auction / sale / sold`
- `search_numbers(query?, sort?, filter?, offset_id?)` — search Fragment anonymous numbers; same `sort` / `filter` / pagination semantics
- `search_gifts(query?, collection?, sort?, filter?, view?, attr?, offset?)` — search Fragment gifts; `attr` accepts `{"Model": ["Foosball"], "Backdrop": ["Celtic Blue"]}`
- `UsernamesResult`, `NumbersResult`, `GiftsResult` result types

**Anonymous numbers**
- `get_login_code(number)` — fetch the current pending login code
- `toggle_login_codes(number, can_receive)` — enable or disable login code delivery
- `terminate_sessions(number)` — terminate all active Telegram sessions (two-step flow handled internally)
- `LoginCodeResult`, `TerminateSessionsResult` result types; `AnonymousNumberError` exception

**Raw API**
- `FragmentClient.call(method, data, *, page_url)` — raw request to any Fragment API method
- `FRAGMENT_BASE_URL` constant — base URL shared across all page constants and headers

**Examples**
- `examples/client/` — `wallet_info.py` (wallet info), `raw_api_call.py` (raw API call)
- `examples/numbers/` — `manage_number.py` (login code fetch, session termination)
- `examples/auctions/` — `search_usernames.py`, `search_numbers.py`, `search_gifts.py` (marketplace search with pagination)
- `examples/purchase/` — `send_stars.py`, `send_premium.py`, `topup_ton_balance.py`, `run_stars_giveaway.py`, `run_premium_giveaway.py`, `recharge_ads_balance.py`

### Changed
- All result types now expose a unified `amount` field (`months` and `stars` removed)
- `__repr__` includes the unit — `3 months`, `500 stars`, etc.
- `timestamp` removed from all result dataclasses
- All page URL constants built from `FRAGMENT_BASE_URL`;
- `TransactionError` includes an SSL hint; `DUPLICATE_SEQNO` variant auto-retried up to 2 times (2 s apart)
- Error messages rewritten: "what happened → why → what to do"

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

[2026.2.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.0
[2026.1.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.1.0
[2026.0.2]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.2
[2026.0.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.1
