# Search Numbers

Use this endpoint to search anonymous Telegram number listings.

## Method

```python
await client.search_numbers(
    query: str = "",
    sort: AuctionSort | str | None = None,
    filter: AuctionFilter | str | None = None,
    offset_id: str | None = None,
) -> NumbersResult
```

## Parameters

- `query`: digits or text to match number listings
- `sort`: optional `AuctionSort` (or its string value); unknown values raise `ConfigurationError`
- `filter`: optional `AuctionFilter` (or its string value); unknown values raise `ConfigurationError`
- `offset_id`: page cursor returned as `next_offset_id`

`query` can be partial digits (for example `"888"`) when you need pattern-based discovery.

## Sorting values

Values of `AuctionSort` (Fragment silently ignores unknown values, so the library rejects them):

- `price` (default)
- `price_desc`
- `price_asc`
- `listed`
- `ending`

## Filter values

Values of `AuctionFilter`:

- empty string (`AuctionFilter.AVAILABLE`, default)
- `auction`
- `sale`
- `sold`

## Return type

`NumbersResult` contains:

- `items: list[AuctionItem]` — a `TypedDict` with `slug`, `name`, `status`, `price`, `date`
- `next_offset_id: str | None`

## Result size and pagination

Fragment returns at most **500 items** per query and does not page past that: `offset_id=500` always comes back empty. To see more, narrow the query (`query`, `filter`, `sort`).

`next_offset_id` is the "Show more" cursor of a text search and can be set even when the page is complete, so an empty follow-up page is normal.

## Item format

Each item is an `AuctionItem` dict: `slug` (Fragment path, e.g. `username/durov`), `name`, `status`, `price` (in GRAM, two decimals, or `None`) and `date` (ISO 8601, UTC, or `None`).

`status` is the label Fragment shows: `For sale`, `Sold`, `Available`, `Taken`, `On auction`, ... Plain auction rows in the *auction* listing carry no label, so `status` is `None` there.

## Example

```python
result: NumbersResult = await client.search_numbers("888", sort="price_asc", filter="sale")
print(len(result.items), result.next_offset_id)
```
