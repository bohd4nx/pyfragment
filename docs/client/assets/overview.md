# My Assets

Fetch items owned by the authenticated Fragment account.

## Methods

```python
await client.get_my_usernames() -> MyUsernamesResult
await client.get_my_numbers()   -> MyNumbersResult
await client.get_my_gifts()     -> MyGiftsResult
```

All three fetch the corresponding `/my/*` Fragment page and parse the auction rows using the same parser as the marketplace search.

## Return types

Each result wraps a `list[AuctionItem]`:

- `MyUsernamesResult(items)`
- `MyNumbersResult(items)`
- `MyGiftsResult(items)`

Each `AuctionItem` is a `TypedDict` with `slug`, `name`, `status`, `price`, `date` — same as marketplace search results.

## Example

```python
usernames = await client.get_my_usernames()
numbers   = await client.get_my_numbers()
gifts     = await client.get_my_gifts()

for item in usernames.items:
    print(item["name"], item["status"])
```

## Errors

- `SessionExpiredError`: session cookies are invalid or expired (these pages require authentication)
