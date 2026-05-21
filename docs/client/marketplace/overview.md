# Marketplace Overview

Marketplace methods are exposed directly on `FragmentClient` and via `client.marketplace` service.

If you only need one thing: pick the method by asset type (username, number, gift), then paginate until `next_offset_id` or `next_offset` becomes `None`.

Available methods:

- [Search Usernames](search-usernames.md)
- [Search Numbers](search-numbers.md)
- [Search Gifts](search-gifts.md)

## Shared behavior

- All methods are async.
- All methods call Fragment `searchAuctions` under the hood.
- `sort` and `filter` are optional passthrough strings.

**These values are passed to Fragment as-is.** If Fragment changes accepted values, behavior can change too.

Common values used by Fragment pages:

- `sort`: `price_desc`, `price_asc`, `listed`, `ending`
- `filter`: empty string, `auction`, `sale`, `sold`

## Pagination model

- Usernames and Numbers return `next_offset_id` (string)
- Gifts return `next_offset` (integer)

Use these fields to request next pages.
