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
from ton_core import Address, Builder, Cell, NetworkGlobalID, SignatureDomain, verify_sign
from tonutils.clients import TonapiClient
from tonutils.types import ContractInfo

from pyfragment import FragmentClient
from pyfragment.enums import WALLET_CLASSES, PaymentMethod, WalletVersion
from pyfragment.services.tonapi.transaction import process_transaction
from tests.shared import VALID_SEED, fixture_json

NETWORK = NetworkGlobalID.MAINNET
SIGN_ACTION_OPCODE = 0x0EC3C86D  # action_send_msg of a W5 wallet
SIGNATURE_BITS = 512

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


def _external_message_body(boc: bytes) -> tuple[Address, Cell]:
    """Split an ``ext_in_msg_info`` message into its destination and its (inline or referenced) body."""
    message = Cell.one_from_boc(boc).begin_parse()
    assert message.load_uint(2) == 0b10  # external inbound
    assert message.load_uint(2) == 0  # no source
    destination = message.load_address()
    message.load_coins()  # import fee
    if message.load_bool():  # a wallet that isn't deployed yet ships its state_init
        if message.load_bool():
            message.load_ref()
        else:
            message.load_bits(2)  # split_depth, special
            for _ in range(3):  # code, data, library
                message.load_maybe_ref()
    body = message.load_ref() if message.load_bool() else message.to_cell()
    return destination, body


def _split_signature(body: Cell) -> tuple[Cell, bytes]:
    """Separate a W5 body into the signed cell and its trailing signature."""
    reader = body.begin_parse()
    signed_bits = reader.load_bits(reader.remaining_bits - SIGNATURE_BITS)
    signature = reader.load_bytes(SIGNATURE_BITS // 8)
    signed = Builder()
    signed.store_bits(signed_bits)
    for ref in body.refs:
        signed.store_ref(ref)
    return signed.end_cell(), signature


def _signature_is_valid(body: Cell, public_key: bytes, signature_override: bytes | None = None) -> bool:
    signed, signature = _split_signature(body)
    data = SignatureDomain(NETWORK).data_to_sign(signed.hash)
    return bool(verify_sign(public_key, data, signature_override or signature))


@dataclass
class SendAction:
    destination: Address
    amount: int
    bounce: bool
    body: Cell


def _first_send_action(signed: Cell) -> SendAction:
    """Read the one transfer a W5 wallet was asked to make out of its signed body."""
    reader = signed.begin_parse()
    reader.skip_bits(32 * 4)  # opcode, wallet id, valid until, seqno
    actions = reader.load_maybe_ref()
    assert actions is not None
    action = actions.begin_parse()
    action.load_ref()  # the (empty) list of earlier actions
    assert action.load_uint(32) == SIGN_ACTION_OPCODE
    action.load_uint(8)  # send mode
    message = action.load_ref().begin_parse()
    assert message.load_uint(1) == 0  # internal message
    message.load_bit()  # ihr_disabled
    bounce = message.load_bool()
    message.load_bit()  # bounced
    message.load_address()  # source
    destination = message.load_address()
    amount = message.load_coins()
    message.load_bit()  # no extra currencies
    message.load_coins()  # ihr fee
    message.load_coins()  # forward fee
    message.load_uint(64 + 32)  # created lt, created at
    assert not message.load_bool()  # no state_init
    body = message.load_ref() if message.load_bool() else message.to_cell()
    return SendAction(destination, amount, bounce, body)


@pytest.mark.asyncio
async def test_gram_purchase_is_signed_and_pays_what_fragment_asked_for() -> None:
    link = fixture_json("stars_transaction_link_response.json")
    asked = link["transaction"]["messages"][0]

    async with _broadcast(link, PaymentMethod.GRAM) as transfer:
        destination, body = _external_message_body(transfer.boc)
        assert destination == transfer.wallet_address
        assert _signature_is_valid(body, transfer.public_key)

        action = _first_send_action(_split_signature(body)[0])
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
        _, body = _external_message_body(transfer.boc)
        assert _signature_is_valid(body, transfer.public_key)

        action = _first_send_action(_split_signature(body)[0])
        assert action.amount == 50_000_000
        assert action.body.hash == Cell.one_from_boc(base64.urlsafe_b64decode(USDT_STARS_PAYLOAD + "=")).hash


@pytest.mark.asyncio
async def test_signature_check_rejects_a_forged_signature() -> None:
    async with _broadcast(fixture_json("stars_transaction_link_response.json"), PaymentMethod.GRAM) as transfer:
        _, body = _external_message_body(transfer.boc)

        assert _signature_is_valid(body, transfer.public_key)
        assert not _signature_is_valid(body, transfer.public_key, signature_override=bytes(64))
        other_key = bytes(reversed(transfer.public_key))
        assert not _signature_is_valid(body, other_key)
