# Changelog

All notable changes to pyfragment are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Calendar Versioning](https://calver.org/) (`YYYY.MINOR.MICRO`).

---

## [Unreleased]

### Added

- **`get_stars_price(amount)`** — returns the current GRAM price for a given number of Stars as a `Decimal`.
- **`get_stars_packages()`** — returns all predefined Stars purchase options (`StarsPackage(stars, gram, usd)`)
  with live GRAM and USD prices from Fragment.
- **`get_premium_packages()`** — returns all Telegram Premium subscription options
  (`PremiumPackage(months, gram, usd)`) with live GRAM and USD prices, fetched from the `/premium/gift` page.
- **`get_my_usernames()` / `get_my_numbers()` / `get_my_gifts()`** — return assets owned by the authenticated
  account (`MyUsernamesResult`, `MyNumbersResult`, `MyGiftsResult`, each wrapping a `list[AuctionItem]`).
- **`disconnect_wallet()`** — disconnects the linked TON wallet from Fragment (`tonLogOut`).
- `StarsPackage`, `PremiumPackage`, `MyUsernamesResult`, `MyNumbersResult`, `MyGiftsResult` exported from
  `pyfragment`.

### Changed

- **`DEVICE_INFO`** updated to match current Tonkeeper TON Connect capabilities:
  removed the legacy `"SendTransaction"` string entry, added `"extraCurrencySupported": true` to
  `SendTransaction`, bumped `appVersion` to `26.10.1`.

- **Telegram Wallet:** `WalletVersion.TG` for Telegram's self-custodial contract. Always paired with
  `mnemonic_type="multichain"` — the 12-word phrase (or the 24 words shown after a key rotation; words 1–12
  keep the address, words 13–24 are the active key).
- **Multichain (BIP-39) phrases:** `FragmentClient(mnemonic_type="multichain")` for BIP-39 wallets
  (`m/44'/607'/0'`). The default is `"ton"`; the scheme is never guessed automatically.
  `MnemonicType` is exported from `pyfragment` and `pyfragment.enums`.
- **`on_transfer_prepared` callback** — `FragmentClient(on_transfer_prepared=async_fn)`. Called with a
  `TransferIntent` after signing and before sending. If it raises, nothing is sent; a crash after it returns
  leaves enough information to verify whether the transfer landed.
- **`comment` and `boc` in all purchase results.** Every result (`StarsResult`, `PremiumResult`, etc.)
  now carries `comment` (Fragment's `Ref#…` payment reference) and `boc` (the raw signed message). All six
  results share the new `PaymentResult` base (`transaction_id`, `confirmed`, `comment`, `boc`).
  `PaymentResult`, `TransferIntent` and `Recipient` are exported from the package root.
- **`check_stars_recipient()` / `check_premium_recipient()`** — validate a recipient without starting a
  purchase. Return a `Recipient` (`recipient`, `username`, `name`, `photo`, `myself`).
- `FragmentClient(gas_reserve=...)` — GRAM the wallet must keep on top of any payment for network fees.
  Defaults to `0.33`; replaces `MIN_GRAM_BALANCE`.
- `FragmentClient(confirm_timeout=...)` — seconds to wait for Fragment's own confirmation after paying.
  Defaults to `60`; pass `0` to skip.

### Changed

- **A transfer is signed and sent exactly once.** Fragment's confirmation API is the outcome signal.
  Send errors are logged but do not raise — the provider's response to `sendBoc` is not authoritative
  (toncenter answers 500 to some sends that went through). A 429 is retried once while the message is
  still valid; any other error is logged.
- **Transfers expire with Fragment's invoice.** The signed message carries a `valid_until` capped at 60 s,
  never past Fragment's `validUntil`. An expired transaction is refused before signing (`TransactionError`),
  as is a transaction with multiple messages — signing only the first would pay a partial invoice.
- **Seqno is read explicitly.** A provider failure raises `ProviderError` instead of silently signing
  seqno 0, which would deploy an uninitialised wallet and waste the transfer.
- **Fragment's payload is signed byte-for-byte.** Previously the payload was decoded and re-encoded,
  silently stripping surrounding whitespace.
- **Balances and amounts are exact `Decimal` values** (previously rounded to 4 decimal places). A USDT
  payment requires the attached GRAM plus the gas reserve, the same as a GRAM payment.
- **Exception hierarchy restructured** — every error carries `retryable` (`True` = nothing was paid,
  repeating is safe):
  - `NetworkError` — Fragment unreachable (timeout, dropped connection); always `retryable=True`
  - `HTTPStatusError` (`status`, `url`) — unexpected HTTP status; `retryable=True` for 429 and 5xx
  - `SessionExpiredError` — HTTP 401/403, "Access denied", missing request ID, or a freshly fetched API
    hash also rejected (previously this last case was returned silently as a valid result)
  - `RecipientError` → `UserNotFoundError`, `ChannelNotFoundError`, `AlreadySubscribedError`
  - `ChainError` → `InsufficientBalanceError` (`balance`, `required`, `currency`),
    `ProviderError` (`status`), `TransactionError`
  - `UnexpectedError` is now a direct subclass of `FragmentError`, not `OperationError`
  - Blockchain errors (`ChainError` and below) are no longer subclasses of `FragmentAPIError`
  - `ChannelNotFoundError` is now a subclass of `RecipientError`, not `UserNotFoundError`
- `toggle_login_codes()` raises `AnonymousNumberError` on failure, like `terminate_sessions()`.
- The wallet key is derived once at first use and reused; `TonWallet.aclose()` clears the cached account
  payload so a reconnect never reuses stale on-chain state.
- The library no longer logs the errors it raises.
- `Recipient.username` stores the query exactly as the caller passed it (previously normalised:
  `@durov` → `durov`, `https://t.me/durov` → `durov`).
- Dependencies: tonutils ≥ 2.5.1, ton-core ≥ 0.7.1 (now declared), curl-cffi ≥ 0.16.3.

### Fixed

- Cookies given as non-object JSON raise `CookieError` instead of `AttributeError`.
- `get_wallet()` error messages no longer reference Tonapi when toncenter is the configured provider.

### Removed

- `FragmentPageError`, `OperationError`, `WalletError` — replaced by the restructured hierarchy:
  `HTTPStatusError` / `SessionExpiredError`, `ChainError` / `UnexpectedError`,
  `InsufficientBalanceError` / `ProviderError`.
- `get_cookies_from_browser()`, `CookieResult`, `SupportedBrowser`, the `browser` install extra —
  pass cookies as a dict or JSON string.
- `MIN_GRAM_BALANCE` → `FragmentClient(gas_reserve=...)` / `DEFAULT_GAS_RESERVE`.
  `NANO_PER_GRAM`, `USDT_UNITS` → `GRAM_DECIMALS`, `USDT_DECIMALS`.
- `MAX_BROADCAST_ATTEMPTS` — a transfer is sent once (with one 429 retry).
- `PaymentMethod.USDT_ETH`, `USDT_POL`, `USDC_ETH`, `USDC_BASE`, `USDC_POL` and `SUPPORTED_PAYMENT_METHODS` —
  `PaymentMethod` now contains only `GRAM` and `USDT_GRAM`.
- `client.tonapi` → `client.wallet` (`WalletService`).
- `clean_decode()` — the payment comment is in the result's `comment` field.
- `BroadcastError` — send errors are logged; Fragment's confirmation API is the outcome signal.
- `find_transfer()` / `TransferInfo` — on-chain scan removed; Fragment's confirmation API is the source of truth.
- `normalize_username()` — see `Recipient.username` change above.

### Migration

- **Exceptions:** catch `RecipientError` (or specifically `ChannelNotFoundError`) for giveaways; `ChainError`
  for wallet and blockchain failures. Check `error.retryable` before deciding to retry — `True` means nothing
  was paid and repeating is safe.
- **Balances** are `Decimal`; use `float(balance)` where a float is needed.
- **`process_transaction()`** returns `TransferIntent` (`msg_hash`, `boc`, `destination`, `amount_nano`,
  `comment`, `payment_method`, `req_id`, `valid_until`) instead of `(hash, boc)`.

---

## [2026.4.0] — 2026-09-28

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
- Parser and purchase-flow tests run against real, trimmed fragment.com responses (`tests/fixtures/`).
- CI type-checks the examples too, so they can't drift from the API. The GitHub Actions in the workflows are
  up to date (`setup-uv` v10, `action-gh-release` v3.0.3).
- `tests/021_test_signing.py` signs real Fragment payloads (GRAM and USDT) with a throwaway wallet and verifies the
  broadcast message: valid signature for the wallet's key, right destination, amount and comment, jetton body untouched.

### Changed

- **The seed phrase is validated when the client is created.** tonutils only rejects words outside the wordlist: a
  phrase with a wrong checksum, a BIP39-style phrase or a password-protected one silently derives a *different*
  wallet, which showed up much later as an empty balance. `FragmentClient` now raises `ConfigurationError` for anything
  that isn't a valid TON phrase. The phrase is also normalized (lower-cased, whitespace collapsed): `Word` used to
  derive another wallet than `word`.
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
- Examples use the enums, handle errors the same way (specific errors first, `FragmentError` last) and show `confirmed`;
  the gifts example pages through results.

### Removed

- **Invoice cancellation.** After a failed purchase the client called Fragment's `cancelInvoice`, but Fragment
  answers "Bad request" to it for every GRAM/USDT invoice (checked on a live invoice with a connected wallet), so it
  never did anything. Abandoned invoices expire on their own; the extra request and the `ApiMethod.CANCEL_INVOICE`
  member are gone.
- `pyfragment.core.transport`: use `pyfragment.transport`.
- `parse_required_payment_amount()`: use `pyfragment.schemas.InvoiceRequest.amount`.

### Fixed

- **`get_wallet()` and the pre-broadcast balance check reported an empty wallet when the blockchain provider failed.**
  tonutils' `wallet.refresh()` answers *any* provider error (invalid API key, outage, timeout) with "nonexistent
  account, zero balance", so a bad key looked like an empty wallet ("0.0000 GRAM available"). The wallet state is now
  read with `client.get_info()`, and provider failures surface as `WalletError` with the provider's message.
- **A zero USDT balance was not recognised on toncenter.** For an owner without a USDT jetton wallet tonapi answers
  404 but toncenter a TVM exit code -13; only the former counted as `0.0`, so toncenter users got
  `usdt_balance=None` from `get_wallet()` and a "failed to fetch USDT balance" error instead of "insufficient
  USDT balance".
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

[Unreleased]: https://github.com/bohd4nx/pyfragment/compare/v2026.4.0...HEAD
[2026.4.0]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.4.0
[2026.3.4]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.3.4
[2026.3.3]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.3.3
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
