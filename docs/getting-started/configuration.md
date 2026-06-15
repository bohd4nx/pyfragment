# Library and Configuration

Main entry point of the library is `FragmentClient`.

```python
FragmentClient(
    seed: str,
    api_key: str,
    cookies: dict[str, Any] | str,
    wallet_version: str = "V5R1",
    api_provider: str = "tonapi",
    timeout: float = 30.0,
)
```

## Parameters

- `seed`: wallet mnemonic (**12 or 24 words**)
- `api_key`: API key — from [tonconsole.com](https://tonconsole.com) (tonapi) or [@toncenter](https://t.me/toncenter)
- `cookies`: Fragment cookies as a dictionary or JSON string
- `wallet_version`: `"V4R2"`, `"V5R1"`, `"HighloadV2"`, or `"HighloadV3R1"`
- `api_provider`: blockchain API provider — `"tonapi"` (default) or `"toncenter"`
- `timeout`: request timeout in seconds

**If `api_key` or cookies are missing, initialization fails immediately.**

## Required cookies

- `stel_ssid`
- `stel_dt`
- `stel_token`
- `stel_ton_token`

## Minimal initialization pattern

```python
from pyfragment import FragmentClient

async with FragmentClient(
    seed="word1 word2 ... word24",
    api_key="YOUR_API_KEY",
    cookies={
        "stel_ssid": "...",
        "stel_dt": "...",
        "stel_token": "...",
        "stel_ton_token": "...",
    },
) as client:
    wallet = await client.get_wallet()
```

## Switching API provider

By default, the library uses [tonconsole.com](https://tonconsole.com) (tonapi). To use [toncenter](https://t.me/toncenter) instead, pass `api_provider="toncenter"`:

```python
async with FragmentClient(
    seed="...",
    api_key="YOUR_TONCENTER_API_KEY",
    cookies={...},
    api_provider="toncenter",
) as client:
    ...
```

Both providers work identically — the correct `tonutils` client is selected automatically based on `api_provider`.

## Validation behavior

At initialization, library validates:

- seed format,
- cookie shape and required keys,
- supported wallet version,
- supported API provider,
- parseability of cookie JSON strings.

Constructor-level issues are raised as `ConfigurationError` or `CookieError`.
