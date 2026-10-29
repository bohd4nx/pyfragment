# Payment Safety

Every purchase ends with a GRAM (ex TON) transfer signed by your wallet. This page explains what the library guarantees about it.

## What the library guarantees

- **A transfer is signed and sent once.** A second payment is never made.
- **A transfer expires.** The signed message is valid for at most 60 seconds, and never past the deadline Fragment set for the invoice. An already-expired invoice is not paid.
- **Send errors are logged, not raised.** The blockchain provider's answer to the send call is not the source of truth — toncenter answers 500 to some sends that went through. Fragment's confirmation API is.
- **Fragment's payload is signed byte for byte**, and the balance is checked before signing, in exact integer units.
- **Purchases from one client run one at a time.** If several processes share a seed, serialize their purchases yourself (for example with a lock in Redis). Keep the system clock synced (NTP).

## When a purchase fails

Every error has `retryable`. `True` means nothing was paid and the purchase can be started again safely.

```python
try:
    result = await client.purchase_stars("@username", amount=500)
except InsufficientBalanceError as error:
    print(f"need {error.required} {error.currency}, have {error.balance}")
except SessionExpiredError:
    ...  # refresh the Fragment cookies
except UserNotFoundError:
    ...  # recipient doesn't exist on Fragment
except FragmentError as error:
    if error.retryable:
        ...  # nothing was paid; safe to retry
    else:
        ...  # something unexpected happened
```

## Surviving a crash mid-purchase

Pass an async callback to receive the signed transfer before it is sent. If the process dies between signing and returning the result, the stored `msg_hash` lets you verify the payment externally (e.g. on a block explorer or with tonapi).

```python
from pyfragment import TransferIntent


async def save(intent: TransferIntent) -> None:
    await db.save_payment(intent.req_id, intent.msg_hash, intent.comment, intent.valid_until)


client = FragmentClient(..., on_transfer_prepared=save)
```

If the callback raises, nothing is sent.

`TransferIntent` fields: `msg_hash`, `boc`, `destination`, `amount_nano`, `comment`, `payment_method`, `req_id`, `valid_until`.

## `confirmed`

After paying, the client reports the transfer to Fragment and waits up to `confirm_timeout` seconds (default `60`, `0` to skip waiting) for Fragment to acknowledge it. `confirmed=False` doesn't mean the purchase failed — the payment is already on-chain. **Never retry a purchase just because `confirmed` is `False`.**

See [Result Models](../reference/models.md#confirmed).
