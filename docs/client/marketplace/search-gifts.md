# Search Gifts

This endpoint is the most flexible marketplace search and supports collection, traits, and pagination.

## Method

```python
await client.search_gifts(
    query: str = "",
    collection: str | None = None,
    sort: str | None = None,
    filter: str | None = None,
    view: str | None = None,
    attr: dict[str, list[str]] | None = None,
    offset: int | None = None,
) -> GiftsResult
```

## Parameters

- `query`: search text (empty string for broad listing)
- `collection`: collection slug (for example `plushpepe`, `swisswatch`)
- `sort`: optional sort key passed to Fragment
- `filter`: optional listing filter passed to Fragment
- `view`: optional UI/view mode passed to Fragment
- `attr`: optional trait filters where key is trait name and value is list of allowed values
- `offset`: page offset for next page

**`attr` is ideal for narrowing results by visual or rarity traits.**

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

## Attribute filter format

`attr` is encoded into request fields in this form:

- `attr[trait_name] = ["value1", "value2"]`

Example:

```python
attr={
    "model": ["gold", "silver"],
    "rarity": ["rare"],
}
```

In requests, each trait is sent as `attr[trait]` with a list of values.

## Return type

`GiftsResult` contains:

- `items: list[dict[str, Any]]`
- `next_offset: int | None`

## Pagination

If `next_offset` is not `None`, pass it back as `offset` to load the next page.

## Example

```python
result: GiftsResult = await client.search_gifts(
    query="",
    collection="plushpepe",
    sort="price_desc",
    filter="auction",
)
print(len(result.items), result.next_offset)
```
