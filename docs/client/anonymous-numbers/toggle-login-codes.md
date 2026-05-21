# Toggle Login Codes

Use this method to allow or block login code delivery.

## Method

```python
await client.toggle_login_codes(number: str, can_receive: bool) -> None
```

## Parameters

- `number`: anonymous number (with or without leading `+`)
- `can_receive`: `True` to allow codes, `False` to block codes

## Return

- `None`
