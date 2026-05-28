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

# Type check
mypy . --explicit-package-bases

# Tests
pytest
```

All three must pass before opening a PR.

## Project structure

```
pyfragment/
  client.py           — FragmentClient (public entry point)
  core/               — transport, cookies, constants
  domains/            — one package per feature domain
    ads/              — recharge_ads, topup_ton
    anonymous_numbers/— buy_number, manage_number
    giveaways/        — giveaway_stars, giveaway_premium
    marketplace/      — search_usernames, search_numbers, search_gifts
    purchases/        — purchase_stars, purchase_premium
    tonapi/           — wallet info, transaction signing
  models/             — result dataclasses and enums
  exceptions.py       — exception hierarchy
tests/                — unit tests (pytest)
examples/             — runnable usage examples (excluded from CI)
```

## Conventions

- All public async methods live on `FragmentClient` and delegate to a domain service.
- Domain functions receive a `FragmentClient` instance, never raw httpx clients.
- Patch targets in tests use the module where the name is **defined**, e.g. `pyfragment.domains.tonapi.transaction.process_transaction`.
- Versioning follows [CalVer](https://calver.org/): `YYYY.MINOR.MICRO`. Bump in `pyproject.toml`; tag as `vYYYY.MINOR.MICRO`.

## Pull requests

- Keep PRs focused — one feature or fix per PR.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Add or update tests for any changed behaviour.
