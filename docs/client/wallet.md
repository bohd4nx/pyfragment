# Wallet

Methods for managing the wallet linked to your Fragment account.

## Methods

```python
await client.link_wallet()      -> None
await client.disconnect_wallet() -> None
```

## link\_wallet

```python
await client.link_wallet()
```

Links the connected TON wallet to your Fragment account. Run this **once** after connecting a new wallet via TON Connect. Without it, Fragment returns a verification error on all purchase flows even with a valid `stel_ton_token` cookie and completed KYC.

You do not need to sign anything: the library uses the existing `stel_ton_token` session cookie, which already carries the TON Connect proof.

**When to call:**
- After connecting a new wallet via TON Connect for the first time.
- If you get `VerificationError` despite having a valid `stel_ton_token` and completed identity verification.

```python
async with FragmentClient(...) as client:
    await client.link_wallet()
    print("Wallet linked.")
```

## disconnect\_wallet

```python
await client.disconnect_wallet()
```

Disconnects the linked TON wallet from Fragment (`tonLogOut`). After calling this, purchases and other wallet-dependent operations will fail until a wallet is reconnected and linked again.

```python
async with FragmentClient(...) as client:
    await client.disconnect_wallet()
```

## Errors

- `SessionExpiredError`: session cookies are invalid or expired.
