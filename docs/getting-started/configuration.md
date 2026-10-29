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
    headers: dict[str, str | None] | None = None,
    mnemonic_type: str | None = None,
    gas_reserve: Decimal | float | str = Decimal("0.33"),
    confirm_timeout: float = 60.0,
    on_transfer_prepared: Callable[[TransferIntent], Awaitable[None]] | None = None,
)
```

## Parameters

- `seed`: wallet mnemonic (see [Wallets](#wallets))
- `api_key`: API key — from [tonconsole.com](https://tonconsole.com) (tonapi) or [@toncenter](https://t.me/toncenter)
- `cookies`: Fragment cookies as a dictionary or JSON string
- `wallet_version`: `"V5R1"` (default), `"V4R2"`, `"HighloadV2"`, `"HighloadV3R1"`, or `"TG"` (Telegram Wallet)
- `mnemonic_type`: `"ton"` (default) or `"multichain"`; a Telegram Wallet is always `"multichain"`
- `api_provider`: blockchain API provider — `"tonapi"` (default) or `"toncenter"`
- `timeout`: request timeout in seconds
- `headers`: custom HTTP headers for Fragment API calls — defaults to `BASE_HEADERS` when omitted; a `None` value for a key omits that header instead of sending it empty
- `gas_reserve`: GRAM (ex TON) the wallet must keep on top of a payment for fees (exact; a float is read through `str`)
- `confirm_timeout`: seconds to wait for Fragment's confirmation after paying; `0` reports the purchase right away
- `on_transfer_prepared`: async callback receiving each signed transfer before it is sent — see [Payment Safety](../client/transfers.md)

## Wallets

| Wallet | `wallet_version` | `mnemonic_type` | Words |
| --- | --- | --- | --- |
| Tonkeeper, MyTonWallet and other TON wallets | `"V5R1"` (W5) or `"V4R2"` | `"ton"` (default) | 12 or 24 |
| Multichain wallets (BIP-39 phrase) | `"V5R1"` or `"V4R2"` | `"multichain"` | 12, 15, 18, 21 or 24 |
| Telegram Wallet (self-custodial) | `"TG"` | `"multichain"` (implied) | 12, or 24 after a key rotation |
| Highload wallets | `"HighloadV2"` or `"HighloadV3R1"` | either | |

Keep the system clock synced (NTP): the library tells whether a transfer can still land by its expiry time.

A multichain phrase derives its key from the BIP-39 seed at `m/44'/607'/0'`. The scheme is never guessed: a phrase that
only fits the other scheme is rejected with a hint. After a Telegram Wallet key rotation the app shows 24 words: words
1-12 keep the address, words 13-24 are the current key — pass all 24.

**Before paying from a new configuration, check that `(await client.get_wallet()).address` is the address your wallet
app shows.** A wrong version or scheme derives a different (empty) wallet.

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

## Lifecycle

The client keeps one HTTP session and one blockchain API connection and reuses them across calls. Use `async with FragmentClient(...) as client:` (or call `await client.aclose()`) to release them.

## Validation behavior

At initialization, library validates:

- seed: a valid phrase for the chosen wallet and `mnemonic_type` (case and whitespace are normalized; password-protected TON phrases are rejected),
- cookie shape and required keys,
- supported wallet version,
- supported API provider and mnemonic type,
- `gas_reserve` and `confirm_timeout`,
- parseability of cookie JSON strings.

Constructor-level issues are raised as `ConfigurationError` or `CookieError`.
