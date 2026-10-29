# Contributing to pyfragment

## Development setup

```bash
git clone https://github.com/bohd4nx/pyfragment.git
cd pyfragment
pip install -e ".[dev]"
```

## Running checks

```bash
# Lint and format
ruff check . --fix && ruff format .

# Type check (the library, and the examples so they don't rot)
mypy pyfragment --explicit-package-bases
mypy $(git ls-files 'examples/*.py') --explicit-package-bases

# Tests
pytest
```

All of them must pass before opening a PR (CI runs the same commands).

`tests/018_test_contract.py` checks the live fragment.com and is skipped by default; run it with `FRAGMENT_LIVE=1 pytest tests/018_test_contract.py`.

## Project structure

```
pyfragment/
  client.py           — FragmentClient (public entry point)
  constants.py        — fixed values: URLs, limits, timeouts, addresses
  enums.py            — PaymentMethod, WalletVersion, MnemonicType, ApiProvider, ApiMethod, ApiError, marketplace enums
  exceptions.py       — exception hierarchy and canonical messages
  schemas.py          — typed views of Fragment's response bodies
  utils/              — input validation (validation.py), exact money arithmetic (money.py)
  transport/          — HTTP layer: page (API hash), api (requests, 429 retry), session (reusable transport)
  domains/            — one package per feature domain
    ads/              — recharge_ads, topup_gram
    anonymous_numbers/— get_login_code, toggle_login_codes, terminate_sessions
    giveaways/        — stars.py (giveaway_stars), premium.py (giveaway_premium)
    marketplace/      — search_usernames, search_numbers, search_gifts (+ HTML parsers)
    payments/         — the shared purchase flow: run_purchase, PurchaseFlow, PaymentResult, confirmation
    purchases/        — stars.py (purchase_stars, check_stars_recipient), premium.py (purchase_premium, check_premium_recipient)
    recipients/       — recipient lookup shared by the purchase flows (Recipient model)
    wallet/           — the GRAM (ex TON) wallet: TonWallet (wallet.py), balances (balance.py), signing and sending
                        (transfer.py), on-chain lookup (lookup.py), payload comments (payload.py)
    base.py           — BaseService, operation() error guard
tests/                — unit tests (pytest); tests/fixtures holds real fragment.com markup and chain data;
                        tests/fake_ton.py is an in-memory blockchain API for signing with real wallets
examples/             — runnable usage examples (excluded from CI)
```

## Conventions

- All public async methods live on `FragmentClient` and delegate to a domain service.
- Where things go: public result dataclasses in each domain's `models.py`; typed views of Fragment's responses in
  `schemas.py`; enums (and sets of their members) in `enums.py`; fixed values in `constants.py`; helpers in `utils/`; message
  templates on the exception classes.
- Domain functions receive a `FragmentClient` instance, never raw HTTP clients.
- Patch targets in tests use the module where the name is **defined**, e.g. `pyfragment.domains.wallet.wallet.make_ton_client` or `pyfragment.domains.payments.flow.process_transaction`.
- Fragment method names and error texts are enums (`ApiMethod`, `ApiError`); response bodies are read through `pyfragment.schemas`. A new Fragment call means a new `ApiMethod` member; tests use the enums, not string literals.
- Errors: raise a `FragmentError` subclass with a message template defined on the exception class; wrap a whole operation with `domains.base.operation()`. Don't log what you raise: the caller decides.
- The library is a thin wrapper: no retries besides Fragment's 429. Report failures with a `retryable` flag and let the caller decide.
- Money: compare amounts in integer nanograms / USDT units (`utils/money.py`), never floats. A transfer is signed and sent once; whether it paid is read from the chain, and every failure after signing surfaces as a `BroadcastError`.
- tonutils swallows provider failures in some calls (`wallet.refresh()` turns a bad API key into an empty wallet): use the strict helpers on `domains/wallet/wallet.py`'s `TonWallet`.
- Parser changes are checked against real markup: add or refresh a trimmed response under `tests/fixtures/` (see its README).
- Versioning follows [CalVer](https://calver.org/): `YYYY.MINOR.MICRO`. Bump in `pyproject.toml`; tag as `vYYYY.MINOR.MICRO`.

## Pull requests

- Keep PRs focused — one feature or fix per PR.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Add or update tests for any changed behaviour.
