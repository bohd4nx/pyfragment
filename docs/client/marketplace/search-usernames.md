# Search Usernames

Use this endpoint to discover Telegram usernames listed on Fragment.

## Method

```python
await client.search_usernames(
    query: str = "",
    sort: AuctionSort | str | None = None,
    filter: AuctionFilter | str | None = None,
    offset_id: str | None = None,
) -> UsernamesResult
```

## Parameters

- `query`: search text (empty string means broad listing)
- `sort`: optional `AuctionSort` (or its string value); unknown values raise `ConfigurationError`
- `filter`: optional `AuctionFilter` (or its string value); unknown values raise `ConfigurationError`
- `offset_id`: page cursor for next page

For broad browsing, use empty `query` and set sorting only.

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

`UsernamesResult` contains:

- `items: list[AuctionItem]` — a `TypedDict` with `slug`, `name`, `status`, `price`, `date`
- `next_offset_id: str | None`

## Pagination

If `next_offset_id` is not `None`, pass it back as `offset_id` to load the next page.

This is cursor pagination, so do not try to calculate offsets manually.

## Example

```python
result: UsernamesResult = await client.search_usernames("durov", sort="price_desc", filter="auction")
print(len(result.items), result.next_offset_id)
```
