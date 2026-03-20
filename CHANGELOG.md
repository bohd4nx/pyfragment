# Changelog

All notable changes to pyfragment are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Calendar Versioning](https://calver.org/) (`YYYY.MINOR.MICRO`).

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
