# Terminate Sessions

Use this method to terminate active sessions for an anonymous number.

## Method

```python
await client.terminate_sessions(number: str) -> TerminateSessionsResult
```

## Parameters

- `number`: anonymous number (with or without leading `+`)

## Return

- `number`
- `message`
