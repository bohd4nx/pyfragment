# Changelog

All notable changes to pyfragment are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Calendar Versioning](https://calver.org/) (`YYYY.MINOR.MICRO`).

---

## [2026.3.0] — 2026-05-21

### Changed

- Internal architecture reorganized around explicit domain packages:
  - TON account and balance helpers are now unified under `pyfragment.domains.tonapi.account`
  - service wrappers and operation modules are aligned by domain (`ads`, `purchases`, `giveaways`, `anonymous_numbers`, `marketplace`, `tonapi`)
- Package exports were cleaned up for domain and model packages (`__init__.py`) to provide clearer public symbols.
- Examples and system tests were updated to follow current public import paths and project structure.

### Fixed

- `get_cookies_from_browser()` is now patch-friendly in tests (`pyfragment.core.cookies.rookiepy` can be mocked reliably).
- Anonymous number `NOT_OWNED` error message wording was adjusted for test and backward-compatibility with existing matchers.

## [2026.2.3] — 2026-05-12

### Fixed

- Fixed USDT payment flow: the USDT balance check now correctly targets the wallet linked to the Fragment account (`transaction["from"]`), not the signing seed wallet. These are two distinct addresses — the seed wallet only signs the transaction and covers TON gas fees, while USDT is withdrawn from the Fragment-linked wallet.
- Fixed `clean_decode()` incorrectly treating binary TON cell payloads (e.g. jetton transfer messages with non-zero op codes) as text comments. Only cells with op code `0x00000000` are now decoded as snake-encoded UTF-8 strings; all other op codes return the raw `Cell` as-is.
- Restored and correctly wired USDT balance validation so `WalletError` is raised before broadcasting when the Fragment-linked wallet has insufficient USDT.

### Note

- USDT (`usdt_ton`) payments require USDT to be held in the TON wallet that is linked to your Fragment account profile. The seed wallet configured in `FragmentClient` is only used to sign transactions and pay TON network fees.

---

## [2026.2.2] — 2026-05-11

### Added

- `payment_method` option (`"ton"` / `"usdt_ton"`) for:
  - `purchase_stars()`
  - `purchase_premium()`
  - `giveaway_stars()`
  - `giveaway_premium()`

### Changed

- Added runtime validation for `payment_method` via `SUPPORTED_PAYMENT_METHODS` and `ConfigurationError.INVALID_PAYMENT_METHOD`
- Updated method docstrings to explicitly document recipient/channel formats:
  - `@username` / `username` / `https://t.me/username`
- `get_wallet()` now returns balances as separate fields: `ton_balance` and `usdt_balance`
- Wallet/system test output now prints TON and USDT balances on separate lines
- Balance checks are now method-aware with explicit thresholds:
  - `ton`: minimum TON balance threshold via `MIN_TON_BALANCE` (based on current 50 Stars purchase amount)
  - `usdt_ton`: minimum USDT balance threshold via `MIN_USDT_BALANCE` (based on current 50 Stars purchase amount)

### Tests

- Extended stars and premium test suites to cover:
  - invalid payment method
  - payment method propagation to `init*Request` payloads
  - accepted query formats (`@`, plain username, `t.me` link)
- Extended wallet tests to verify separate TON/USDT balance values in `WalletInfo`

### Documentation

- Simplified `README` usage example

## [2026.2.1] — 2026-05-03

### Fixed

- Fragment API 429 responses are now retried automatically (up to 3 attempts) with exponential backoff and jitter in `fragment_request`
- Retry delays in TON transaction broadcasting now include jitter to reduce contention under concurrent calls
- Improved handling of non-200 HTTP responses in `get_fragment_hash`
- Removed unnecessary `method` key leaking into certain API request payloads

### Changed

- Type hints refined across the codebase for better clarity and `mypy` strict compliance

---

## [2026.2.0] — 2026-04-14

### Added

- `get_cookies_from_browser(browser)` — extract Fragment session cookies directly from an installed browser (Chrome, Firefox, Edge, Brave, Arc, Opera, Safari, and more); no browser extension or manual copy-paste required
  ```python
  from pyfragment import get_cookies_from_browser
  result = get_cookies_from_browser("chrome")  # or "firefox", "edge", "brave", ...
  client = FragmentClient(seed="...", api_key="...", cookies=result.cookies)
  print(result.expires)  # ISO 8601 expiry of stel_ssid, or None for session cookies
  ```
- `CookieResult` — return type of `get_cookies_from_browser()`; exposes `.cookies` (`dict[str, str]`) and `.expires` (ISO 8601 string or `None`)

### Changed

- `DEVICE` Tonkeeper fingerprint updated: `appVersion` → `26.04.0`
- `tonutils` upgraded to **2.1.0**
- Minimum Python version lowered to **3.10** (previously 3.12)

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

[2026.3.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.3.0
[2026.2.3]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.3
[2026.2.2]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.2
[2026.2.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.1
[2026.2.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.0
[2026.1.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.1.0
[2026.0.2]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.2
[2026.0.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.1
