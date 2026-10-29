# Credentials and Cookies

This page covers the three things you need before making real requests: Tonapi key, wallet seed, and Fragment cookies.

## Tonapi key

Generate an API key at https://tonconsole.com.

## Seed phrase

Use your GRAM (ex TON) wallet mnemonic: a TON wallet phrase (Tonkeeper, MyTonWallet, ...), the BIP-39 phrase of a
multichain wallet, or the phrase of your Telegram Wallet. See
[Library and Configuration](configuration.md#wallets) for the matching `wallet_version` and `mnemonic_type`.

- **Keep it private.**
- **Never log it or commit it to git.**

## Fragment cookies

You must be logged in to Fragment.

Export the four required Fragment cookies from your browser (developer tools → Application → Cookies →
`fragment.com`) and pass them as a dict or a JSON string.

Required keys:

- `stel_ssid`
- `stel_dt`
- `stel_token`
- `stel_ton_token`

## Common auth failures

- expired session cookies,
- not logged in on fragment.com,
- missing `stel_*` keys,
- stale cookies from another browser/profile.

The library reports all of these as `SessionExpiredError`: re-login on fragment.com and refresh the cookies.

## Next step

Proceed to [Quick Start](quickstart.md).
