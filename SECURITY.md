# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report them privately via GitHub's [Security Advisory](https://github.com/bohd4nx/pyfragment/security/advisories/new) feature, or contact the maintainer directly at [@bohd4nx](https://t.me/bohd4nx) on Telegram.

Include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce or a proof-of-concept.
- Affected versions.

You will receive a response within 72 hours. Once the fix is released, the advisory will be published.

## Scope

This library handles sensitive credentials (TON seed phrases, Fragment session cookies, Tonapi keys). Please treat any finding that could expose or misuse these credentials as high severity.
