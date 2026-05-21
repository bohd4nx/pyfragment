# Client Overview

`FragmentClient` is the main API surface.

You can call methods directly on the client or use grouped services.

Grouped service wrappers:

- `client.purchases`
- `client.giveaways`
- `client.ads`
- `client.anonymous_numbers`
- `client.marketplace`
- `client.tonapi`

Main async methods on `FragmentClient`:

- `purchase_stars(...)`
- `purchase_premium(...)`
- `giveaway_stars(...)`
- `giveaway_premium(...)`
- `topup_ton(...)`
- `recharge_ads(...)`
- `get_wallet()`
- `get_login_code(...)`
- `toggle_login_codes(...)`
- `terminate_sessions(...)`
- `search_usernames(...)`
- `search_numbers(...)`
- `search_gifts(...)`
- `call(...)`

All methods are async and should be used inside `async with FragmentClient(...) as client:`.

## Flow map

- Stars: [Purchase](stars/purchase.md), [Giveaway](stars/giveaway.md)
- Premium: [Purchase](premium/purchase.md), [Giveaway](premium/giveaway.md)
- Ads: [Ads operations](ads.md)
- Utility operations: [Anonymous Numbers](anonymous-numbers.md), [Marketplace](marketplace/overview.md), [Raw API Calls](raw-call.md)

**If you are new to the library, start with Stars Purchase or Wallet read (`get_wallet`) first.**
