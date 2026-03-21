"""Shared test constants for the pyfragment test suite.

pyfragment is an async Python client for Fragment.com — purchase Telegram Premium
and Stars, run Stars and Premium giveaways for channels, top up TON Ads balance,
and manage anonymous numbers, all through a clean typed API.
"""

from typing import Any

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
FAKE_ACCOUNT: dict[str, Any] = {"address": "0:abc", "publicKey": "pub", "chain": "-239", "walletStateInit": "base64=="}
FAKE_TRANSACTION: dict[str, Any] = {"transaction": {"messages": [{"address": "0:abc", "amount": "100000000", "payload": ""}]}}

# client.call()
FAKE_RESPONSE: dict[str, Any] = {"status": "ok", "data": {"value": 42}}

# get_wallet()
FAKE_ADDRESS: str = "UQCppfw5DxWgdVHf3zkmZS8k1mt9oAUYxQLwq2fz3nhO8No5"
FAKE_BALANCE_NANOTON: int = 1_500_000_000  # 1.5 TON

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
