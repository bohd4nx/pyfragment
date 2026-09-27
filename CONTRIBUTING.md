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
  enums.py            — PaymentMethod, WalletVersion, ApiProvider, ApiMethod, ApiError, marketplace enums
  exceptions.py       — exception hierarchy and canonical messages
  schemas.py          — typed views of Fragment's response bodies
  core/               — constants, input validation helpers
  transport/          — HTTP layer: page (API hash), api (requests, 429 retry), session (reusable transport)
  domains/            — one package per feature domain
    ads/              — recharge_ads, topup_gram
    anonymous_numbers/— get_login_code, toggle_login_codes, terminate_sessions
    giveaways/        — giveaway_stars, giveaway_premium
    marketplace/      — search_usernames, search_numbers, search_gifts (+ HTML parsers)
    payments/         — the shared purchase flow: run_purchase, confirmation, state helpers
    purchases/        — purchase_stars, purchase_premium
    base.py           — BaseService, raw_api_call, operation() error guard
    recipients.py     — recipient lookup shared by the purchase flows
  services/           — shared infrastructure services
    cookies/          — browser cookie extraction (models + service)
    tonapi/           — wallet info, transaction signing (tonapi/toncenter)
tests/                — unit tests (pytest); tests/fixtures holds real fragment.com markup
examples/             — runnable usage examples (excluded from CI)
```

## Conventions

- All public async methods live on `FragmentClient` and delegate to a domain service.
- Domain functions receive a `FragmentClient` instance, never raw HTTP clients.
- Patch targets in tests use the module where the name is **defined**, e.g. `pyfragment.services.tonapi.account.make_ton_client` or `pyfragment.domains.payments.flow.process_transaction`.
- Fragment method names and error texts are enums (`ApiMethod`, `ApiError`); response bodies are read through `pyfragment.schemas`. A new Fragment call means a new `ApiMethod` member; tests use the enums, not string literals.
- Errors: raise a `FragmentError` subclass with a message template defined on the exception class; wrap a whole operation with `domains.base.operation()` so it is logged once.
- tonutils swallows provider failures in some calls (`wallet.refresh()` turns a bad API key into an empty wallet): use the strict helpers in `services/tonapi/account.py`.
- Parser changes are checked against real markup: add or refresh a trimmed response under `tests/fixtures/` (see its README).
- Versioning follows [CalVer](https://calver.org/): `YYYY.MINOR.MICRO`. Bump in `pyproject.toml`; tag as `vYYYY.MINOR.MICRO`.

## Pull requests

- Keep PRs focused — one feature or fix per PR.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Add or update tests for any changed behaviour.
