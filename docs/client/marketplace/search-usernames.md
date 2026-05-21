# Search Usernames

Use this endpoint to discover Telegram usernames listed on Fragment.

## Method

```python
await client.search_usernames(
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> UsernamesResult
```

## Parameters

- `query`: search text (empty string means broad listing)
- `sort`: optional sort key passed to Fragment
- `filter`: optional listing filter passed to Fragment
- `offset_id`: page cursor for next page

For broad browsing, use empty `query` and set sorting only.

## Sorting values

Common values accepted by Fragment:

- `price_desc`
- `price_asc`
- `listed`
- `ending`

## Filter values

Common values accepted by Fragment:

- empty string
- `auction`
- `sale`
- `sold`

## Return type

`UsernamesResult` contains:

- `items: list[dict[str, Any]]`
- `next_offset_id: str | None`

## Pagination

If `next_offset_id` is not `None`, pass it back as `offset_id` to load the next page.

This is cursor pagination, so do not try to calculate offsets manually.
