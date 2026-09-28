"""Sign real Fragment transactions with a throwaway wallet and verify the signed message end to end.

Nothing is sent: the mocked provider records the external message the wallet broadcasts, and the tests
check that its signature is valid for the wallet's key and that it pays what Fragment asked for.
"""

import base64
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from ton_core import Address, Cell, NetworkGlobalID
from tonutils.clients import TonapiClient
from tonutils.types import ContractInfo

from pyfragment import FragmentClient
from pyfragment.enums import WALLET_CLASSES, PaymentMethod, WalletVersion
from pyfragment.services.tonapi.transaction import process_transaction
from tests.shared import VALID_SEED, fixture_json
from tests.signing import external_message_body, first_send_action, signature_is_valid, split_signature

NETWORK = NetworkGlobalID.MAINNET

# A real USDT transfer payload Fragment produced for 50 Stars: a jetton `transfer` with a text comment attached.
USDT_STARS_PAYLOAD = (
    "te6ccgEBAgEAfgABqA-KfqVP885dhccidjC3GwgBCkiH8LM_zUu0afyGCTWJwX1mDjdlf2rMa9UoQlD4UHUAF1jLlcMomlo5RJTwl8jnDDdfdhc7EgQQWPqFQ"
    "9IjyLPCAwEASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNtOUpoWndBcFE"
)


@dataclass
class SignedTransfer:
    """What the wallet put on the wire for one Fragment transaction."""

    boc: bytes
    wallet_address: Address
    public_key: bytes
    tx_hash: str
    returned_boc: bytes


@asynccontextmanager
async def _broadcast(transaction: dict[str, Any], payment_method: PaymentMethod) -> AsyncIterator[SignedTransfer]:
    """Run process_transaction against a provider that answers from memory and records what is broadcast."""
    sent: list[bytes] = []

    async def send_message(boc_hex: str) -> None:
        sent.append(bytes.fromhex(boc_hex))

    ton = TonapiClient(network=NETWORK, api_key=None)
    ton.get_info = AsyncMock(return_value=ContractInfo(balance=10_000_000_000))  # type: ignore[method-assign]
    ton.send_message = send_message  # type: ignore[method-assign]

    @asynccontextmanager
    async def provider(_client: FragmentClient) -> AsyncIterator[TonapiClient]:
        yield ton

    client = FragmentClient(
        seed=VALID_SEED, api_key="A" * 68, cookies={k: "x" for k in ("stel_ssid", "stel_dt", "stel_token", "stel_ton_token")}
    )
    wallet, public_key, _, _ = WALLET_CLASSES[WalletVersion.V5R1].from_mnemonic(client=ton, mnemonic=VALID_SEED)
    with (
        patch("pyfragment.services.tonapi.transaction.make_ton_client", provider),
        patch("pyfragment.services.tonapi.account.get_usdt_balance", AsyncMock(return_value=100.0)),
    ):
        tx_hash, returned_boc = await process_transaction(client, transaction, payment_method=payment_method)

    assert len(sent) == 1
    yield SignedTransfer(sent[0], wallet.address, public_key.as_bytes, tx_hash, base64.b64decode(returned_boc))


@pytest.mark.asyncio
async def test_gram_purchase_is_signed_and_pays_what_fragment_asked_for() -> None:
    link = fixture_json("stars_transaction_link_response.json")
    asked = link["transaction"]["messages"][0]

    async with _broadcast(link, PaymentMethod.GRAM) as transfer:
        destination, body = external_message_body(transfer.boc)
        assert destination == transfer.wallet_address
        assert signature_is_valid(body, transfer.public_key)

        action = first_send_action(split_signature(body)[0])
        assert action.destination == Address(asked["address"])
        assert action.amount == int(asked["amount"]) == 460_900_000
        assert action.bounce is False
        assert action.body.begin_parse().load_uint(32) == 0  # a text comment
        comment = action.body.begin_parse()
        comment.skip_bits(32)
        assert comment.load_snake_string() == "50 Telegram Stars \n\nRef#kpJ55h3BW"


@pytest.mark.asyncio
async def test_returned_boc_is_exactly_what_was_broadcast() -> None:
    async with _broadcast(fixture_json("stars_transaction_link_response.json"), PaymentMethod.GRAM) as transfer:
        assert transfer.returned_boc == transfer.boc
        assert len(transfer.tx_hash) == 64


@pytest.mark.asyncio
async def test_usdt_purchase_signs_the_jetton_transfer_body_untouched() -> None:
    link = fixture_json("stars_transaction_link_response.json")
    link["transaction"]["messages"][0]["payload"] = USDT_STARS_PAYLOAD
    link["transaction"]["messages"][0]["amount"] = "50000000"

    async with _broadcast(link, PaymentMethod.USDT_GRAM) as transfer:
        _, body = external_message_body(transfer.boc)
        assert signature_is_valid(body, transfer.public_key)

        action = first_send_action(split_signature(body)[0])
        assert action.amount == 50_000_000
        assert action.body.hash == Cell.one_from_boc(base64.urlsafe_b64decode(USDT_STARS_PAYLOAD + "=")).hash


@pytest.mark.asyncio
async def test_signature_check_rejects_a_forged_signature() -> None:
    async with _broadcast(fixture_json("stars_transaction_link_response.json"), PaymentMethod.GRAM) as transfer:
        _, body = external_message_body(transfer.boc)

        assert signature_is_valid(body, transfer.public_key)
        assert not signature_is_valid(body, transfer.public_key, signature_override=bytes(64))
        other_key = bytes(reversed(transfer.public_key))
        assert not signature_is_valid(body, other_key)
