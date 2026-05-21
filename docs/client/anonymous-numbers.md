# Anonymous Numbers

These methods help you manage login behavior and active sessions for anonymous numbers owned by your current account.

## get_login_code

```python
await client.get_login_code(number: str) -> LoginCodeResult
```

Returns:

- `number`
- `code` (`None` if no pending code)
- `active_sessions`

## toggle_login_codes

```python
await client.toggle_login_codes(number: str, can_receive: bool) -> None
```

Use `can_receive=True` to allow incoming login codes, or `False` to block them.

## terminate_sessions

```python
await client.terminate_sessions(number: str) -> TerminateSessionsResult
```

Returns:

- `number`
- `message`

## Common errors

- `AnonymousNumberError.NOT_OWNED`
- `AnonymousNumberError.TERMINATE_FAILED`

## Practical note

These methods operate only on numbers owned by the currently authorized Fragment account.

**If a number is not yours, requests will fail with `AnonymousNumberError`.**
