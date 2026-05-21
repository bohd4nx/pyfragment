# Library and Configuration

Main entry point of the library is `FragmentClient`.

```python
FragmentClient(
    seed: str,
    api_key: str,
    cookies: dict[str, Any] | str,
    wallet_version: str = "V5R1",
    timeout: float = 30.0,
)
```

## Parameters

- `seed`: wallet mnemonic (**12, 18, or 24 words**)
- `api_key`: Tonapi key from https://tonconsole.com
- `cookies`: Fragment cookies as a dictionary or JSON string
- `wallet_version`: `"V4R2"` or `"V5R1"`
- `timeout`: request timeout in seconds

**If `api_key` is too short or cookies are incomplete, initialization fails immediately.**

## Required cookies

- `stel_ssid`
- `stel_dt`
- `stel_token`
- `stel_ton_token`

## Minimal initialization pattern

```python
from pyfragment import FragmentClient

client = FragmentClient(
    seed="word1 word2 ... word24",
    api_key="YOUR_TONAPI_KEY",
    cookies={
        "stel_ssid": "...",
        "stel_dt": "...",
        "stel_token": "...",
        "stel_ton_token": "...",
    },
)
```

Use it inside async context manager:

```python
async with client:
    wallet = await client.get_wallet()
```

You can also create the client directly inside `async with` if you prefer one-block setup.

## Validation behavior

At initialization, library validates:

- seed format,
- cookie shape and required keys,
- supported wallet version,
- parseability of cookie JSON strings.

Constructor-level issues are raised as `ConfigurationError` or `CookieError`.

**Tip:** keep validation failures visible in logs during initial integration. They save a lot of debugging time.
