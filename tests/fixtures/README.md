# Fixtures

Real responses from fragment.com, trimmed to a few representative items; markup is untouched. Captured 2026-11-24
with a logged-in session that has a connected wallet; nothing was paid (the invoice was created and never signed).
Personal values (invoice id, recipient token and photo, the account's name and wallet) are replaced by placeholders.

Refresh them when Fragment changes its markup, then update the expected values in the tests that load them
(`tests/support/fixtures.py` has the loaders).

## `html/`

| File | What it is |
| --- | --- |
| `usernames_listing.html` | `searchAuctions` for usernames: one row per status (plain auction, for sale, sold) |
| `usernames_search.html` | A username text search: statuses available and on auction, and the "Show more" footer |
| `numbers_listing.html` | Numbers listing: one row per status (plain auction, for sale, sold) |
| `gifts_listing.html` | Gifts grid: one card per status (not for sale, on auction, available, for sale, sold) and the next offset |
| `gifts_list.html` | Gifts with `view=list`: table rows and the next offset |
| `premium_page_months.html` | The duration radios of fragment.com/premium/gift: months, GRAM price, USD price |
| `stars_history.html` | The table of fragment.com/stars/history with one purchase |
| `premium_history_empty.html` | fragment.com/premium/history of an account without gifts |

## `json/`

| File | What it is |
| --- | --- |
| `stars_prices.json` | `updateStarsPrices` for 50 Stars: the price and the package options |
| `stars_recipient_found.json` | `searchStarsRecipient` for an existing user |
| `stars_recipient_not_found.json`, `stars_recipient_not_a_user.json` | `searchStarsRecipient` for a free name and for a bot |
| `premium_recipient_already_subscribed.json` | `searchPremiumGiftRecipient` for a user who already has Premium |
| `giveaway_channel_not_found.json`, `giveaway_not_a_channel.json` | `searchStarsGiveawayRecipient` for a free name and for a bot |
| `stars_below_minimum.json`, `stars_above_maximum.json`, `stars_amount_range.json` | `updateStarsPrices` outside the limits (`options_html` cleared) |
| `giveaway_too_many_winners.json`, `giveaway_bad_package.json` | `updateStarsGiveawayPrices` with too many winners and with a package that doesn't exist (`options_html` cleared) |
| `stars_invoice.json` | `initBuyStarsRequest` for 50 Stars paid in GRAM, reduced to the fields the library reads |
| `stars_transaction_link.json` | `getBuyStarsLink` for that invoice: the transaction to sign and the `confirmReq` details |
| `gifts_next_page.json` | A paginated gifts response, `{"part": true, "body": ..., "foot": ...}` |
| `assets_list_empty.json` | `getAssetsList` of an account that owns nothing (no owned item has been captured) |
| `invalid_method.json` | The answer to a method Fragment doesn't know |

## `chain/`

| File | What it is |
| --- | --- |
| `wallet_payment_transaction.json` | A wallet's transaction paying Fragment for 1700 Stars (public mainnet data from tonapi, captured 2026-10-23): the raw transaction BOC, its hash, lt and time, the normalized hash of the external message that started it, and the payment comment |
