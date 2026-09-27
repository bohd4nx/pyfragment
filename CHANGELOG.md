# Changelog

All notable changes to pyfragment are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Calendar Versioning](https://calver.org/) (`YYYY.MINOR.MICRO`).

---

## [Unreleased]

### Added

- **Enums instead of string literals**, exported from `pyfragment` and `pyfragment.enums`:
  - `AuctionSort`, `AuctionFilter` and `GiftAttribute` for marketplace searches (plain strings are still accepted);
  - `ApiMethod` (every Fragment `/api` method the library calls), `ApiError` (known Fragment error texts),
    `StateMode` and `MarketplaceType`. `client.call()` accepts an `ApiMethod` or any method name.
- **`AuctionItem`**, a `TypedDict` for marketplace items (`slug`, `name`, `status`, `price`, `date`). Items are
  still plain dicts at runtime.
- **`ChannelNotFoundError`** (a `UserNotFoundError` subclass), raised by giveaways when the channel doesn't exist.
- **`FragmentClient.aclose()`** closes the HTTP session; leaving `async with FragmentClient(...)` calls it.
- **`pyfragment.schemas`**: typed views of Fragment's response bodies (`RecipientSearch`, `InvoiceRequest`,
  `TransactionLink`, `PageState`) plus `error_text()` and `has_error()`.
- `SUPPORTED_PAYMENT_METHODS` is exported from the package root.
- **Live contract checks**: `tests/018_test_contract.py` (opt-in with `FRAGMENT_LIVE=1`) and a weekly `Contract`
  workflow verify against fragment.com that the API hash is still discoverable and that limits, payment methods,
  sort/filter values, gift traits and error texts still match what the library assumes.
- Parser tests run against real, trimmed fragment.com responses (`tests/fixtures/`).

### Changed

- **Much faster and lighter on Fragment.** The client keeps one HTTP session and caches the API hash per page, so a
  call is a single POST instead of a page load plus a POST on a fresh connection (about 8x faster after the first
  call, far fewer requests per purchase, less risk of rate limiting). A rejected hash (Fragment answers
  `200 {"error": "Bad request"}`) is refreshed and the call retried once.
- **Marketplace searches are validated.** Fragment silently ignores unknown `sort`, `filter` and gift trait names
  and returns the default listing, so a typo used to give quietly wrong results. They now raise
  `ConfigurationError`. `"price"`, Fragment's default order, is a valid `sort`.
- **`search_gifts(attr=...)`** takes any `Mapping[str, Sequence[str]]`; trait names (`Model`, `Backdrop`,
  `Symbol`) are matched case-insensitively and sent the way Fragment expects. `{"model": [...]}` used to filter nothing.
- **One purchase engine.** Stars, Premium, both giveaways, GRAM topup and Ads recharge share a single
  search/init/sign/broadcast/confirm implementation instead of six copies. Two visible consequences: `recharge_ads()`
  now also checks the wallet against Fragment's invoice amount like every other flow, and `topup_gram()` reports a
  channel or bot recipient as `UserNotFoundError` like Stars and Premium.
- **Better recipient errors.** "Already subscribed to Premium" now raises `AlreadySubscribedError` at recipient
  lookup, where it used to look like a missing user. Unrelated errors (expired session, rate limit, ...) surface as
  `FragmentAPIError` instead of posing as "not found". `UserNotFoundError.NOT_A_USER` says the username may simply
  not exist, because Fragment answers unknown usernames and channels/bots identically.
- `WalletInfo.usdt_balance` is `float | None`: `None` means the USDT lookup failed (it used to be reported as `0.0`).
  The GRAM balance is still returned.
- `FragmentClient.headers` is always a copy, so mutating one client's headers no longer leaks into `BASE_HEADERS`
  and other clients.
- **Internal layout** (import paths of internals changed, see *Removed*):
  - the HTTP layer is the `pyfragment.transport` package (`page`, `api`, `session`);
  - `pyfragment.domains.payments` is a package (`validation`, `state`, `confirmation`, `flow`);
  - `ads/tonup.py` is now `ads/topup.py`;
  - magic numbers and codes live in `core.constants` (`NANO_PER_GRAM`, `USDT_UNITS`, `MAINNET_CHAIN_ID`,
    `FRAGMENT_API_URL`, retry limits) and `http.HTTPStatus`.
- The marketplace parsers were re-checked against about 17 600 real listings and simplified.

### Removed

- **Invoice cancellation.** After a failed purchase the client called Fragment's `cancelInvoice`, but Fragment
  answers "Bad request" to it for every GRAM/USDT invoice (checked on a live invoice with a connected wallet), so it
  never did anything. Abandoned invoices expire on their own; the extra request and the `ApiMethod.CANCEL_INVOICE`
  member are gone.
- `pyfragment.core.transport`: use `pyfragment.transport`. `raw_api_call()` stays in `pyfragment.domains.base`
  as a one-shot call on a throwaway session.
- `parse_required_payment_amount()`: use `pyfragment.schemas.InvoiceRequest.amount`.

### Fixed

- **`giveaway_stars()` accepted 1-15 winners; Fragment allows 1-5.** Values above 5 passed local validation and
  failed remotely after the invoice flow had started.
- **`wallet_version="HighloadV2"` / `"HighloadV3R1"` were always rejected**, although documented: the value was
  upper-cased before matching. Wallet versions are now matched case-insensitively.
- **`True`/`False` passed the integer checks** for amounts and counts (`topup_gram("@user", True)` topped up
  1 GRAM). Booleans are now rejected.
- **`check_gram_payment_balance()` required `max(payment, reserve)` instead of `payment + reserve`**, so a wallet
  holding exactly the payment amount passed the check and had nothing left for the network fee.
- **Payment methods that can't be broadcast yet** (`usdt_eth`, `usdt_pol`, `usdc_eth`, `usdc_base`, `usdc_pol`)
  are rejected before any network call. Their balance check always looked at the TON-chain USDT balance, i.e. the
  wrong currency on the wrong chain.
- Gifts on auction reported `status=None`; Fragment splits that status into two `<span>`s. It is `"On auction"` now.
- Giveaways reported an unknown channel as "Telegram user ... not found"; they raise `ChannelNotFoundError`.
- `get_fragment_hash()` built the wrong referer for the root URL (`https://fragment.com` became `https:/`, which
  affected `search_usernames()`) and for URLs with a trailing slash or a `/` in the query string.
- `confirm_purchase()` polled with `lv=1`; Fragment's own frontend always sends `lv=false`.
- The release workflow no longer appends the `---` separator to the GitHub Release body.

---

## [2026.3.4] — 2026-08-14

### Added

- `StarsResult`, `PremiumResult`, `AdsTopupResult`, `AdsRechargeResult`, `StarsGiveawayResult`, and `PremiumGiveawayResult` now carry a `confirmed: bool` field, reflecting whether Fragment's own backend acknowledged the broadcast transaction. `transaction_id` is still set as soon as the transfer is broadcast — `confirmed` is a separate, best-effort signal.

### Changed

- Purchase, giveaway, and Ads topup/recharge flows now report the broadcast transaction to Fragment (`confirmReq`) and wait for Fragment's own confirmation, instead of treating a successful broadcast as the end of the flow.
- A failed purchase/giveaway/topup now cancels the Fragment invoice it opened (`cancelInvoice`), except when the broadcast itself is what failed — in that case the invoice is left alone, since it's unclear whether the transaction reached the chain.
- `BASE_HEADERS` no longer hardcodes `User-Agent`, `Sec-Ch-Ua*`, or `Accept-Language` — `curl_cffi`'s `impersonate="chrome"` already supplies these consistently with its real TLS/HTTP2 fingerprint, and hardcoding them risked drifting out of sync with it.
- `get_fragment_hash()` no longer reuses XHR-style headers for the plain page load used to extract Fragment's request hash; it now lets `curl_cffi`'s page-navigation defaults apply on their own.
- Refreshed the spoofed Tonkeeper `appVersion` to `26.07.1`.

### Fixed

- Fixed the request hash extraction regex in `get_fragment_hash()` to correctly match Fragment's HTML.
- Removed the dead `x-aj-referer` header, not present in Fragment's actual traffic.
- Excluded `*.md` from `ruff format` so CI doesn't fail whenever a `ruff` release changes how it formats Python code fences in `CHANGELOG.md`/`README.md` (`ruff` isn't pinned in dev deps).
- `search_gifts()` pagination was broken: Fragment expects the next page's cursor as `offset_id`, not `offset`, and answers with `{"part": true, "body": ..., "foot": ...}` instead of a single `"html"` field — the parser now handles both request and response shapes correctly.
- `parse_required_payment_amount()` failed to parse Fragment-formatted amounts with thousand separators (e.g. `"1,000,000,000"`), silently disabling the pre-broadcast balance check for large Ads top-ups.
- Stars/Premium/giveaway/Ads init requests that fail without a `req_id` now raise Fragment's actual error message (e.g. `"Amount is invalid"`) instead of a generic "no request ID" error.
- `search_gifts()`'s `attr` filter was sent as Python's `str(list)` (e.g. `"['Sweet Glaze']"`) instead of a JSON array, which Fragment doesn't understand — now serialized with `json.dumps()`.
- `search_usernames()`/`search_numbers()` pagination never worked: Fragment doesn't return a `next_offset_id` JSON field, the cursor lives in the HTML as `data-next-offset`, and paginated responses use the same `{"part": true, "body": ..., "foot": ...}` shape as gift search — both are now parsed correctly.
- `parse_auction_rows()` returned `date: None` for sold/plain listings, since their `<time>` tag has no `data-relative` attribute (only active-auction countdowns do) — now falls back to a plain `<time datetime="...">` match.

---

## [2026.3.3] — 2026-07-05

### Changed

- Replaced `httpx` with `curl_cffi` (`impersonate="chrome"`) for all HTTP requests, for a TLS/HTTP2 fingerprint closer to a real browser.

---

## [2026.3.2] — 2026-06-16

### Added

- Added `ApiProvider` enum with `TONAPI` (tonconsole.com, default) and `TONCENTER` (t.me/toncenter) values.
- Added `api_provider` parameter to `FragmentClient` — select the blockchain API provider at init time (`"tonapi"` or `"toncenter"`).
- Both providers accept `api_key` with the same interface; the correct `tonutils` client is selected automatically.

- New `AlreadySubscribedError` exception for Premium purchase flows when Fragment returns: `This account is already subscribed to Telegram Premium.`
- New `UserNotFoundError.NOT_A_USER` message for when Fragment returns: `Please enter a username assigned to a user.` (e.g. when the username belongs to a channel or bot).
- Added `WalletVersion.HighloadV2` and `WalletVersion.HighloadV3R1` to `WalletVersion`

### Changed

- Updated purchase and giveaway flow state nonces (`dh`) to use nonce-like dynamic values with a wider integer range.
- Stars and Premium giveaway flows now include explicit price update steps before init requests:
  - `updateStarsGiveawayPrices`
  - `updatePremiumGiveawayPrices`
- Updated `DEVICE_INFO` fingerprint: Tonkeeper `appVersion` -> `26.05.0`.
- Updated client docstrings and purchase examples to document all supported payment methods.

### Renamed — TON -> GRAM (ex TON)

The TON blockchain has been rebranded to **GRAM (ex TON)**. All identifiers, messages, and documentation have been updated accordingly.

**Public API**

- `FragmentClient.topup_ton()` → `topup_gram()`
- `PaymentMethod.TON` → `PaymentMethod.GRAM`
- `PaymentMethod.USDT_TON` → `PaymentMethod.USDT_GRAM`
- `WalletInfo.ton_balance` → `WalletInfo.gram_balance`

**Constants**

- `TON_TOPUP_MIN` / `TON_TOPUP_MAX` → `GRAM_TOPUP_MIN` / `GRAM_TOPUP_MAX`
- `MIN_TON_BALANCE` → `MIN_GRAM_BALANCE`
- `USDT_TON_MASTER_ADDRESS` → `USDT_GRAM_MASTER_ADDRESS`

**Exceptions**

- `ConfigurationError.INVALID_TON_AMOUNT` → `INVALID_GRAM_AMOUNT`
- `WalletError.LOW_TON_BALANCE` → `LOW_GRAM_BALANCE`
- `WalletError.TON_BALANCE_CHECK_FAILED` → `GRAM_BALANCE_CHECK_FAILED`

**Internals**

- `pyfragment/core/constants/ton.py` → `gram.py`
- `check_ton_payment_balance()` → `check_gram_payment_balance()`

---

## [2026.3.1] — 2026-05-29

### Added

- Python 3.13 and 3.14 are now officially supported and included in the CI test matrix and PyPI classifiers.
- `WalletVersion` is now exported from the top-level `pyfragment` package.

### Changed

- `process_transaction` (internal) refactored into focused subfunctions: `_extract_message`, `_check_payment_balances`, `_broadcast_with_retry`.
- `raw_api_call()` moved from `FragmentClient` into `pyfragment.domains.base` and exposed as a standalone helper.
- `tonapi` domain internal helpers removed from public `__init__.py` exports; only `TonapiService` is exported.
- README rewritten with badges, structured sections, and complete usage examples.
- Added `CONTRIBUTING.md` and `SECURITY.md`.

### Fixed

- CI: `mypy` now runs with `--explicit-package-bases` to avoid false-positive import errors.
- CI: `pip` dependency cache enabled to speed up workflow runs.
- CI: `warn_unused_ignores` suppressed for `pyfragment.core.cookies` to handle the optional `rookiepy` dependency correctly across environments where the package may or may not be installed.
- Publish workflow now uses `generate_release_notes: true` instead of manual changelog extraction.

### Removed

- `tonapi/transfer.py` and associated `TonTransferResult` / `UsdtTransferResult` models (internal, unused).

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

[2026.3.2]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.3.2
[2026.3.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.3.1
[2026.3.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.3.0
[2026.2.3]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.3
[2026.2.2]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.2
[2026.2.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.1
[2026.2.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.2.0
[2026.1.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.1.0
[2026.0.2]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.2
[2026.0.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.1
