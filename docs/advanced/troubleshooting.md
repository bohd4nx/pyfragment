# Troubleshooting

When something breaks, start here. Most issues are caused by cookies, session state, or wallet balance.

## Auth/session errors

Symptoms:

- Fragment page hash cannot be extracted,
- bad status loading Fragment pages,
- missing request IDs with no further detail.

Actions:

- re-login on fragment.com,
- refresh cookies,
- ensure all `stel_*` keys are present.
- verify constructor payload in [Library and Configuration](../getting-started/configuration.md).

**Re-login + fresh cookies solves the majority of auth errors.** If Fragment returned a specific reason (e.g.
`"Amount is invalid"`), the exception message is that reason directly — that's a request validation error, not a
session problem, so re-logging in won't help; check the amount/recipient instead.

## Cookie extraction errors

Symptoms:

- browser not supported,
- cannot read browser profile,
- required cookies not found.

Actions:

- install `pyfragment[browser]`,
- close locked browser profiles,
- use manual cookies if needed.

## Balance/transaction failures

Symptoms:

- low TON/USDT balance errors,
- broadcast failures,
- duplicate seqno retries.

Actions:

- keep GRAM (ex TON) reserve for fees,
- ensure USDT is on the **Fragment-linked wallet**,
- retry after short delay when seqno collisions happen.
- check operation constraints in Stars/Premium/Ads method pages.

## `confirmed` is `False` after a successful purchase

The transaction already broadcast successfully — `transaction_id` is set and the payment happened. `confirmed` is a
separate, best-effort signal: after broadcasting, the client reports the transaction to Fragment and waits up to ~60s
for Fragment's own backend to acknowledge it. A `False` value just means that acknowledgement didn't arrive in time
(slow Fragment backend, network blip); it does not mean the purchase failed or should be retried. See
[Result Models](../reference/models.md#confirmed).

## A purchase failed and left an open invoice

If a purchase/giveaway/topup fails *after* Fragment already opened an invoice (for example KYC is required or the
wallet fails to sign), the invoice stays open until it expires on its own; Fragment offers no way to cancel a GRAM or
USDT invoice (`cancelInvoice` answers "Bad request" for it). Nothing is charged for an invoice that was never paid.
If the failure happened during the broadcast itself, the transaction may still have reached the chain, so check your
GRAM (ex TON)/USDT balance and recent transactions before retrying.

## SSL-related broadcast failures

If you get SSL-related errors during **TON transaction broadcast** (not Fragment page loading — those use curl_cffi with bundled SSL):

```bash
pip install --upgrade certifi
```

On macOS, also run Python's `Install Certificates.command` if needed.
