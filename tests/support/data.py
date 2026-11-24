"""Constants shared by the tests: throwaway credentials and canned values."""

from typing import Any

from pyfragment import TransferIntent
from pyfragment.enums import PaymentMethod

# Throwaway TON mnemonics generated for the tests (the wallets are empty); they pass the library's phrase check.
SEED: str = (
    "much faith taxi kiss brick siege egg can arrive there because genuine trash virus obtain direct bid liar flash group "
    "liquid stay mean already"
)
SEED_12_WORDS: str = "range blast planet dove tonight tomato dream must vacuum asthma chimney shrimp"
# The standard BIP-39 test vectors: well-formed multichain phrases that are not TON phrases.
BIP39_SEED: str = "abandon " * 23 + "art"
BIP39_SEED_12_WORDS: str = "abandon " * 11 + "about"
# A Telegram Wallet phrase after a key rotation: words 1-12 keep the address, words 13-24 are the current key.
TG_ROTATED_SEED: str = BIP39_SEED_12_WORDS + " " + "zoo " * 11 + "wrong"
API_KEY: str = "A" * 68
COOKIES: dict[str, str] = {"stel_ssid": "x", "stel_dt": "x", "stel_token": "x", "stel_ton_token": "x"}

REQ_ID = "REQ_ID"  # the placeholder the invoice fixtures carry
RECIPIENT_TOKEN = "RECIPIENT_TOKEN"  # the one in json/stars_recipient_found.json
TX_HASH = "deadbeef" * 8
TX_BOC = "te6ccgEBAQEAAgAAAA=="
COMMENT = "50 Telegram Stars \n\nRef#kpJ55h3BW"
ACCOUNT: dict[str, Any] = {"address": "0:abc", "publicKey": "pub", "chain": "-239", "walletStateInit": "base64=="}

# What process_transaction() reports for a transfer it sent.
SENT = TransferIntent(
    msg_hash=TX_HASH,
    boc=TX_BOC,
    destination="0:abc",
    amount_nano=100_000_000,
    comment=COMMENT,
    payment_method=PaymentMethod.GRAM,
    req_id=REQ_ID,
    valid_until=1_900_000_000,
)
