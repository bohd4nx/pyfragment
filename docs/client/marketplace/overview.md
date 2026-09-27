# Marketplace Overview

Marketplace methods are exposed directly on `FragmentClient` and via `client.marketplace` service.

If you only need one thing: pick the method by asset type (username, number, gift), then read `items`. Only gifts paginate in earnest (see below).

Available methods:

- [Search Usernames](search-usernames.md)
- [Search Numbers](search-numbers.md)
- [Search Gifts](search-gifts.md)

## Shared behavior

- All methods are async.
- All methods call Fragment `searchAuctions` under the hood.
- `sort` and `filter` are optional `AuctionSort` / `AuctionFilter` values (plain strings work too); unknown values raise `ConfigurationError`.

Fragment silently ignores unknown `sort`/`filter` values and returns the default listing, which is why the library validates them up front.

Common values used by Fragment pages:

- `sort`: `price` (default), `price_desc`, `price_asc`, `listed`, `ending`
- `filter`: empty string (available, default), `auction`, `sale`, `sold`

## Pagination model

- Usernames and Numbers: Fragment returns at most 500 items per query and does not page past that (`next_offset_id` is only the "Show more" cursor of text searches and can be set on a complete page).
- Gifts return `next_offset` (integer), 60 items per page, up to 1 200 items per query.

Narrow the query (`query`, `filter`, `sort`, and for gifts `collection`/`attr`) instead of expecting to walk the whole marketplace.
