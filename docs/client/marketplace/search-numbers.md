# Search Numbers

Use this endpoint to search anonymous Telegram number listings.

## Method

```python
await client.search_numbers(
    query: str = "",
    sort: str | None = None,
    filter: str | None = None,
    offset_id: str | None = None,
) -> NumbersResult
```

## Parameters

- `query`: digits or text to match number listings
- `sort`: optional sort key passed to Fragment
- `filter`: optional listing filter passed to Fragment
- `offset_id`: page cursor for next page

`query` can be partial digits (for example `"888"`) when you need pattern-based discovery.

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

`NumbersResult` contains:

- `items: list[dict[str, Any]]`
- `next_offset_id: str | None`

## Pagination

If `next_offset_id` is not `None`, pass it back as `offset_id` to load the next page.

Keep requesting pages until `next_offset_id` becomes `None`.
