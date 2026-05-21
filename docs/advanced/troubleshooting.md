# Troubleshooting

When something breaks, start here. Most issues are caused by cookies, session state, or wallet balance.

## Auth/session errors

Symptoms:

- Fragment page hash cannot be extracted,
- bad status loading Fragment pages,
- missing request IDs.

Actions:

- re-login on fragment.com,
- refresh cookies,
- ensure all `stel_*` keys are present.
- verify constructor payload in [Library and Configuration](../getting-started/configuration.md).

**Re-login + fresh cookies solves the majority of auth errors.**

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

- keep TON reserve for fees,
- ensure USDT is on the **Fragment-linked wallet**,
- retry after short delay when seqno collisions happen.
- check operation constraints in Stars/Premium/Ads method pages.

## SSL-related broadcast failures

If you get SSL-related transaction errors:

```bash
pip install --upgrade certifi
```

On macOS, also run Python's `Install Certificates.command` if needed.
