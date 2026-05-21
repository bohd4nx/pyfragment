# Raw API Calls

Use `client.call()` when you need a Fragment API method that does not yet have a dedicated wrapper.

```python
result = await client.call(
    "searchPremiumGiftRecipient",
    {"query": "@username", "months": 3},
    page_url="https://fragment.com/premium/gift",
)
```

Signature:

```python
await client.call(
    method: str,
    data: dict[str, Any] | None = None,
    *,
    page_url: str = "https://fragment.com",
) -> dict[str, Any]
```

## Parameters

- `method`: Fragment API method name
- `data`: optional request payload as dictionary
- `page_url`: page URL used for referer/hash context (defaults to `https://fragment.com`)

## Return

- `dict[str, Any]`: raw Fragment API response

Use this carefully:

- request/response shape is Fragment-defined,
- undocumented methods can change without notice,
- you are responsible for validating returned fields.

## Recommended approach

Use dedicated wrappers first, and fallback to `call()` only for missing API surface.
