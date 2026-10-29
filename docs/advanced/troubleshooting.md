# Troubleshooting

When something breaks, start here. Most issues are caused by cookies, session state, or wallet balance.

## Auth/session errors

`SessionExpiredError` covers every way Fragment reports a logged-out session: HTTP 401/403, "Access denied", a missing
request id, or a page without the API hash.

Actions:

- re-login on fragment.com,
- refresh cookies,
- ensure all `stel_*` keys are present.
- verify constructor payload in [Library and Configuration](../getting-started/configuration.md).

If Fragment returned a specific reason (e.g. `"Amount is invalid"`), the exception is a `FragmentAPIError` whose message
is that reason — a request validation error, not a session problem, so re-logging in won't help. `HTTPStatusError` with
a 5xx `status` means Fragment is temporarily unavailable (retry it yourself in a moment; the library only repeats HTTP 429).

## Wrong or empty wallet

If `get_wallet()` shows an address your wallet app doesn't, the `wallet_version` or `mnemonic_type` is wrong: see
[Wallets](../getting-started/configuration.md#wallets). Don't pay from that configuration.

## Balance/transaction failures

- `InsufficientBalanceError`: `balance`, `required` and `currency` say what is missing. The gas reserve
  (`gas_reserve`, 0.33 GRAM by default) is required on top of the payment.
- `ProviderError`: tonapi/toncenter failed (a rejected API key shows up here with the provider's message, e.g.
  `401 invalid token`). Nothing was sent.
- USDT has to be on the **Fragment-linked wallet**.

## `confirmed` is `False` after a successful purchase

The transaction already broadcast successfully — `transaction_id` is set and the payment happened. `confirmed` is a
separate, best-effort signal: after broadcasting, the client reports the transaction to Fragment and waits up to ~60s
(`confirm_timeout`) for Fragment's own backend to acknowledge it. A `False` value just means that acknowledgement didn't arrive in time
(slow Fragment backend, network blip); it does not mean the purchase failed or should be retried. See
[Result Models](../reference/models.md#confirmed).

## A purchase failed and left an open invoice

If a purchase/giveaway/topup fails *after* Fragment already opened an invoice (for example KYC is required or the
wallet fails to sign), the invoice stays open until it expires on its own; Fragment offers no way to cancel a GRAM or
USDT invoice (`cancelInvoice` answers "Bad request" for it). Nothing is charged for an invoice that was never paid.
See [Payment Safety](../client/transfers.md) for how the library handles transfer errors.

## SSL-related broadcast failures

If a broadcast error mentions SSL during **TON transaction broadcast** (not Fragment page loading — those use curl_cffi with bundled SSL):

```bash
pip install --upgrade certifi
```

On macOS, also run Python's `Install Certificates.command` if needed.
