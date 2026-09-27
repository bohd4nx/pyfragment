"""Shared test constants for the pyfragment test suite.

pyfragment is an async Python client for the Fragment API — a unified toolkit
to manage Telegram assets: purchase Stars and Premium, top up GRAM (ex TON) and Ads balances,
run giveaways, manage anonymous numbers, and explore the marketplace for usernames,
numbers, and gifts.
"""

import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_html(name: str) -> str:
    """Real fragment.com markup captured for the parser tests (see tests/fixtures/README.md)."""
    return (FIXTURES / name).read_text()


def fixture_json(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((FIXTURES / name).read_text())
    return result


# Credentials and config
VALID_SEED: str = "abandon " * 23 + "about"
VALID_API_KEY: str = "A" * 68
VALID_COOKIES: dict[str, str] = {
    "stel_ssid": "x",
    "stel_dt": "x",
    "stel_token": "x",
    "stel_ton_token": "x",
}

# Generic test data
FAKE_HASH: str = "abc123"
FAKE_RECIPIENT: str = "recipient_token"
FAKE_REQ_ID: str = "req_42"
FAKE_TX_HASH: str = "deadbeef" * 8
FAKE_TX_BOC: str = "te6ccgEBAQEAAgAAAA=="
FAKE_ACCOUNT: dict[str, Any] = {"address": "0:abc", "publicKey": "pub", "chain": "-239", "walletStateInit": "base64=="}
FAKE_TRANSACTION: dict[str, Any] = {"transaction": {"messages": [{"address": "0:abc", "amount": "100000000", "payload": ""}]}}

# client.call()
FAKE_RESPONSE: dict[str, Any] = {"status": "ok", "data": {"value": 42}}

# get_wallet()
FAKE_ADDRESS: str = "UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5"
FAKE_BALANCE_NANOGRAM: int = 1_500_000_000  # 1.5 GRAM (ex TON)

# recharge_ads
FAKE_ADS_ACCOUNT: str = "@mychannel"

# Anonymous number
FAKE_HTML_WITH_CODE: str = """
<table>
  <tr>
    <td class="table-cell-value">12345</td>
  </tr>
  <tr>
    <td>session data</td>
  </tr>
</table>
"""
FAKE_HTML_NO_CODE: str = "<table><tr><td>no code here</td></tr></table>"
FAKE_TERMINATE_HASH: str = "terminate_hash_abc123"
