# Changelog

All notable changes to pyfragment are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Calendar Versioning](https://calver.org/) (`YYYY.MINOR.MICRO`).

---

## [2026.0.1] — 2026-03-16

### Added
- Initial stable release of `pyfragment`
- `FragmentClient` — async client for the Fragment.com API
- `purchase_premium(username, months)` — purchase Telegram Premium for any user (3, 6, or 12 months)
- `purchase_stars(username, amount)` — send Telegram Stars to any user (50–1,000,000)
- `topup_ton(username, amount)` — top up TON Ads balance (1–1,000,000,000 TON)
- `get_wallet()` — fetch wallet address and balance
- Support for TON wallet versions `V4R2` and `V5R1`
- Structured exception hierarchy (`FragmentError`, `ConfigurationError`, `CookieError`, etc.)
- `py.typed` marker — full PEP 561 typing support for type-checkers

[2026.0.1]: https://github.com/bohd4nx/pyfragment/releases/tag/v2026.0.1
