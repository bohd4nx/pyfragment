# Search Gifts

This endpoint is the most flexible marketplace search and supports collection, traits, and pagination.

## Method

```python
await client.search_gifts(
    query: str = "",
    collection: str | None = None,
    sort: AuctionSort | str | None = None,
    filter: AuctionFilter | str | None = None,
    view: str | None = None,
    attr: dict[str, list[str]] | None = None,
    offset: int | None = None,
) -> GiftsResult
```

## Parameters

- `query`: search text (empty string for broad listing)
- `collection`: collection slug, the last part of its Fragment URL (`bowtie` for `fragment.com/gifts/bowtie`). Unknown slugs are silently ignored by Fragment and return every collection
- `sort`: optional `AuctionSort` (or its string value); unknown values raise `ConfigurationError`
- `filter`: optional `AuctionFilter` (or its string value); unknown values raise `ConfigurationError`
- `view`: optional view name passed to Fragment as-is
- `attr`: optional trait filters: key is a `GiftAttribute` (`Model`, `Backdrop` or `Symbol`, any casing), value is a list of allowed values. Unknown trait names raise `ConfigurationError`
- `offset`: page offset for next page

**`attr` is ideal for narrowing results by visual or rarity traits.**

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

## Attribute filter format

Each trait is sent as `attr[trait]`, JSON-encoded (`'["value1", "value2"]'`) — this is the exact format Fragment's
own frontend uses.

Example:

```python
attr={
    "Model": ["Bordeaux", "Red Rose"],
    "Backdrop": ["Onyx Black"],
}
```

## Return type

`GiftsResult` contains:

- `items: list[AuctionItem]` — a `TypedDict` with `slug`, `name` (including the `#number`), `status`, `price`, `date`
- `next_offset: int | None`

## Result size and pagination

Gifts are paged 60 at a time. If `next_offset` is not `None`, pass it back as `offset` to load the next page. Fragment stops after **1 200 items** per query (20 pages), so narrow the query (`collection`, `attr`, `filter`) for more.

## Item format

Each item is an `AuctionItem` dict: `slug` (Fragment path, e.g. `username/durov`), `name`, `status`, `price` (in GRAM, two decimals, or `None`) and `date` (ISO 8601, UTC, or `None`).

`status` is the label Fragment shows: `For sale`, `Sold`, `Available`, `Taken`, `On auction`, ... Plain auction rows in the *auction* listing carry no label, so `status` is `None` there. Gift statuses also include `Not for sale` and `On auction`.

## Example

```python
result: GiftsResult = await client.search_gifts(
    query="",
    collection="bowtie",
    sort="price_desc",
    filter="auction",
)
print(len(result.items), result.next_offset)
```
