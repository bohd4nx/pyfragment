"""Shared test fixtures, constants, and helpers for the pyfragment test suite."""

import json
from pathlib import Path
from typing import Any

from pyfragment import TransferIntent
from pyfragment.enums import PaymentMethod

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_html(name: str) -> str:
    """Real fragment.com markup captured for the parser tests (see tests/fixtures/README.md)."""
    return (FIXTURES / name).read_text()


def fixture_json(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((FIXTURES / name).read_text())
    return result


# Credentials and config
# Throwaway TON mnemonics generated for the tests (the wallets are empty); they must pass the library's phrase check.
VALID_SEED: str = (
    "much faith taxi kiss brick siege egg can arrive there because genuine trash virus obtain direct bid liar flash group "
    "liquid stay mean already"
)
VALID_SEED_12_WORDS: str = "range blast planet dove tonight tomato dream must vacuum asthma chimney shrimp"
# Well-formed multichain (BIP-39) phrases (the standard BIP-39 test vectors) that are not TON phrases: tonutils would
# derive some TON-scheme wallet from them without complaint.
BIP39_SEED: str = "abandon " * 23 + "art"
BIP39_SEED_12_WORDS: str = "abandon " * 11 + "about"
# A Telegram Wallet phrase after a key rotation: words 1-12 keep the address, words 13-24 are the current key.
TG_ROTATED_SEED: str = BIP39_SEED_12_WORDS + " " + "zoo " * 11 + "wrong"
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
FAKE_CONFIRM_METHOD: str = "confirmReq"  # named by Fragment in the transaction payload, not a fixed API method
FAKE_TX_HASH: str = "deadbeef" * 8
FAKE_TX_BOC: str = "te6ccgEBAQEAAgAAAA=="
FAKE_ACCOUNT: dict[str, Any] = {"address": "0:abc", "publicKey": "pub", "chain": "-239", "walletStateInit": "base64=="}
FAKE_TRANSACTION: dict[str, Any] = {"transaction": {"messages": [{"address": "0:abc", "amount": "100000000", "payload": ""}]}}
FAKE_COMMENT: str = "50 Telegram Stars \n\nRef#kpJ55h3BW"
# What process_transaction() reports for a transfer it sent.
FAKE_SENT: TransferIntent = TransferIntent(
    msg_hash=FAKE_TX_HASH,
    boc=FAKE_TX_BOC,
    destination="0:abc",
    amount_nano=100_000_000,
    comment=FAKE_COMMENT,
    payment_method=PaymentMethod.GRAM,
    req_id=FAKE_REQ_ID,
    valid_until=1_900_000_000,
)

# client.call()
FAKE_RESPONSE: dict[str, Any] = {"status": "ok", "data": {"value": 42}}


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
