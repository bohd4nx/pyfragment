# Get Login Code

Use this method to fetch a pending login code for an anonymous number.

## Method

```python
await client.get_login_code(number: str) -> LoginCodeResult
```

## Parameters

- `number`: anonymous number (with or without leading `+`)

## Return

- `number`
- `code` (`None` if no pending code)
- `active_sessions`
