"""Building Fragment transactions and reading back what the wallet put on the wire."""

import asyncio
import base64
import time
from collections.abc import Callable
from typing import Any

from ton_core import Address, Cell, PrivateKey, WalletTgData, multichain_mnemonic_to_private_key

from tests.support.data import BIP39_SEED_12_WORDS
from tests.support.fake_ton import FakeTon
from tests.support.fixtures import response
from tests.support.signing import (
    count_internal_messages,
    external_message_body,
    split_body,
    split_leading_signature,
    split_signature,
    w5_header,
)


def link(valid_for: int | None = 300, **message: Any) -> dict[str, Any]:
    """Fragment's real getBuyStarsLink answer, valid for ``valid_for`` more seconds (``None``: no deadline)."""
    result = response("stars_transaction_link.json")
    if valid_for is None:
        del result["transaction"]["validUntil"]
    else:
        result["transaction"]["validUntil"] = int(time.time()) + valid_for
    result["transaction"]["messages"][0].update(message)
    return result


def asked(transaction: dict[str, Any] | None = None) -> dict[str, Any]:
    """The one message of a Fragment transaction: what the wallet has to pay."""
    return (transaction or link())["transaction"]["messages"][0]


def signed_header(boc: bytes) -> tuple[int, int]:
    """``(valid_until, seqno)`` a W5 wallet signed into a sent message."""
    _, body = external_message_body(boc)
    return w5_header(split_signature(body)[0])


def seqnos(ton: FakeTon) -> list[int]:
    return [signed_header(boc)[1] for boc in ton.sent]


def sizes(ton: FakeTon, wallet_version: str = "V5R1") -> list[int]:
    """How many payments each sent message carried."""
    message = asked()
    result = []
    for boc in ton.sent:
        signed, _ = split_body(external_message_body(boc)[1], wallet_version)
        result.append(count_internal_messages(signed, Address(message["address"]), int(message["amount"])))
    return result


def highload_expiry(boc: bytes, wallet_version: str) -> int:
    """When a signed highload message stops being accepted."""
    _, body = external_message_body(boc)
    if wallet_version == "HighloadV2":
        signed, _ = split_leading_signature(body)
        reader = signed.begin_parse()
        reader.skip_bits(32)  # subwallet id
        return int(reader.load_uint(64) >> 32)  # bounded query id: expiry << 32 | query id
    signed, _ = split_leading_signature(body, signed_in_ref=True)
    reader = signed.begin_parse()
    reader.skip_bits(32 + 8 + 23)  # subwallet id, (message ref), send mode, query id
    created_at = reader.load_uint(64)
    return int(created_at + reader.load_uint(22))  # created_at + timeout


def payload_hash(payload: str) -> bytes:
    padded = payload + "=" * (-len(payload) % 4)
    return Cell.one_from_boc(base64.urlsafe_b64decode(padded)).hash


def tg_chain(ton: FakeTon, seed: str = BIP39_SEED_12_WORDS, seqno: int = 7) -> None:
    """Give ``ton`` the on-chain key of a deployed Telegram Wallet, as the contract's data cell holds it."""
    words = seed.split()
    key = PrivateKey(multichain_mnemonic_to_private_key(words[12:] if len(words) == 24 else words)[1])
    ton.data_raw = WalletTgData(public_key=key.public_key, seqno=seqno).serialize().to_boc().hex()


def land(ton: FakeTon, index: int = 0) -> None:
    """Put the ``index``-th sent message into a block (for a ``FakeTon`` whose ``landing_delay`` never fires)."""
    ton._land(ton.sent[index])


async def until(condition: Callable[[], bool], timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise TimeoutError("condition not met")
        await asyncio.sleep(0.001)
