# Fixtures

Real `searchAuctions` responses from fragment.com (captured 2026-09-28, unauthenticated), cut down to a few
representative items. Only listing rows were removed; the surrounding markup is untouched.

| File | What it is |
| --- | --- |
| `usernames_one_per_status.html` | Usernames listing: one row per status (available, for sale, on auction, sold, taken, plain auction) |
| `usernames_search_result.html` | A whole username text-search response, including the "Show more" footer |
| `numbers_one_per_status.html` | Numbers listing: one row per status (for sale, sold, plain auction) |
| `numbers_search_result.html` | A whole number text-search response, including the "Show more" footer |
| `gifts_one_per_status.html` | Gifts grid: one card per status (available, for sale, not for sale, on auction, sold) |
| `gifts_next_page_response.json` | A paginated gifts response, `{"part": true, "body": ..., "foot": ...}` |

Refresh them from live responses when Fragment changes its markup, then update the expected values in
`tests/020_test_parsers.py`.

## Purchase flow (captured 2026-09-28 from a logged-in session with a connected wallet, nothing was paid)

| File | What it is |
| --- | --- |
| `stars_invoice_response.json` | `initBuyStarsRequest` for 50 Stars paid in GRAM, reduced to the fields the library reads |
| `stars_transaction_link_response.json` | `getBuyStarsLink` for that invoice: the transaction to sign and the `confirmReq` details |

The invoice id and the sender wallet address are replaced with placeholders; the payload, amount and destination are as
Fragment sent them.
