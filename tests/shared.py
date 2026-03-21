"""Shared test constants — imported by all test modules that need them."""

from typing import Any

# Shared test credentials

VALID_SEED: str = "abandon " * 23 + "about"
VALID_API_KEY: str = "A" * 68
VALID_COOKIES: dict[str, str] = {
    "stel_ssid": "x",
    "stel_dt": "x",
    "stel_token": "x",
    "stel_ton_token": "x",
}

# Fake values for mocked tests

FAKE_HASH: str = "abc123"
FAKE_RECIPIENT: str = "recipient_token"
FAKE_REQ_ID: str = "req_42"
FAKE_TX_HASH: str = "deadbeef" * 8
FAKE_ACCOUNT: dict[str, Any] = {"address": "0:abc", "publicKey": "pub", "chain": "-239", "walletStateInit": "base64=="}
FAKE_TRANSACTION: dict[str, Any] = {"transaction": {"messages": [{"address": "0:abc", "amount": "100000000", "payload": ""}]}}
