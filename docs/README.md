# Overview

`pyfragment` is an async Python client for [Fragment](https://fragment.com).

If you are integrating Fragment into a bot or backend, this docs set is meant to be practical, not theoretical.

**Recommended reading order:**

1. Install the package
2. Configure `FragmentClient`
3. Set up credentials and cookies
4. Run the quick start
5. Move to feature-specific flows

## Who this is for

- Python developers integrating Fragment into bots, services, and automation.
- Teams that need predictable typed results and explicit error behavior.

**Important:** this library is not affiliated with Fragment or Telegram.

## Where to begin

1. [Installation](getting-started/installation.md)
2. [Library and Configuration](getting-started/configuration.md)
3. [Credentials and Cookies](getting-started/credentials-and-cookies.md)
4. [Quick Start](getting-started/quickstart.md)

## Feature entry points

- Stars: [Purchase](client/stars/purchase.md), [Giveaway](client/stars/giveaway.md)
- Premium: [Purchase](client/premium/purchase.md), [Giveaway](client/premium/giveaway.md)
- Marketplace: [Overview](client/marketplace/overview.md), Ads: [Overview](client/ads/overview.md)
- Numbers: [Anonymous Numbers](client/anonymous-numbers/overview.md)
- Utility operations: [Raw API Calls](client/raw-call.md)

## Additional references

- [Error Handling](reference/errors.md)
- [Result Models](reference/models.md)
- [Literal Types](reference/literals.md)
- [Troubleshooting](advanced/troubleshooting.md)
