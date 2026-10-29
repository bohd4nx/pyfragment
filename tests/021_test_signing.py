"""Sign real Fragment transactions with throwaway wallets of every supported kind and verify the signed message.

Nothing is sent: the in-memory provider records the external message the wallet broadcasts, and the tests check that
its signature is valid for the key the wallet gave Fragment, that it targets the wallet Fragment was told about, and that
it pays exactly what Fragment asked for, with Fragment's payload untouched.
"""

import base64
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from ton_core import Address, Cell, ContractState, PrivateKey, WalletTgData, multichain_mnemonic_to_private_key
from tonutils.exceptions import ContractError

from pyfragment import FragmentClient
from pyfragment.domains.wallet.transfer import process_transaction
from pyfragment.enums import PaymentMethod, WalletVersion
from tests.fake_ton import FakeTon, use_fake_ton
from tests.shared import (
    BIP39_SEED,
    BIP39_SEED_12_WORDS,
    TG_ROTATED_SEED,
    VALID_API_KEY,
    VALID_COOKIES,
    VALID_SEED,
    fixture_json,
)
from tests.signing import (
    external_message_body,
    find_internal_message,
    first_send_action,
    has_state_init,
    signature_is_valid,
    signature_matches,
    split_body,
    split_leading_signature,
    split_signature,
)

# A real USDT transfer payload Fragment produced for 50 Stars: a jetton `transfer` with a text comment attached.
USDT_STARS_PAYLOAD = (
    "te6ccgEBAgEAfgABqA-KfqVP885dhccidjC3GwgBCkiH8LM_zUu0afyGCTWJwX1mDjdlf2rMa9UoQlD4UHUAF1jLlcMomlo5RJTwl8jnDDdfdhc7EgQQWPqFQ"
    "9IjyLPCAwEASgAAAAA1MCBUZWxlZ3JhbSBTdGFycyAKClJlZiNtOUpoWndBcFE"
)


def stars_link() -> dict[str, Any]:
    """Fragment's real getBuyStarsLink answer, with a deadline that hasn't passed yet."""
    link = fixture_json("stars_transaction_link_response.json")
    link["transaction"]["validUntil"] = int(time.time()) + 300
    return link


@dataclass
class SignedTransfer:
    """What the wallet put on the wire for one Fragment transaction."""

    boc: bytes
    account: dict[str, Any]
    tx_hash: str
    returned_boc: bytes
    comment: str | None


@asynccontextmanager
async def _broadcast(
    transaction: dict[str, Any], payment_method: PaymentMethod = PaymentMethod.GRAM, ton: FakeTon | None = None, **options: Any
) -> AsyncIterator[SignedTransfer]:
    """Run process_transaction against an in-memory provider and hand back what was broadcast."""
    ton = ton or FakeTon()
    options.setdefault("seed", VALID_SEED)
    with use_fake_ton(ton), patch("pyfragment.domains.wallet.balance.get_usdt_balance", AsyncMock(return_value=10**9)):
        async with FragmentClient(api_key=VALID_API_KEY, cookies=VALID_COOKIES, **options) as client:
            sent = await process_transaction(client, transaction, payment_method=payment_method)
            account = client.ton_wallet.account_info()

    assert len(ton.sent) == 1
    yield SignedTransfer(ton.sent[0], account, sent.msg_hash, base64.b64decode(sent.boc), sent.comment)


# The W5 wallet, decoded field by field


@pytest.mark.asyncio
async def test_gram_purchase_is_signed_and_pays_what_fragment_asked_for() -> None:
    link = stars_link()
    asked = link["transaction"]["messages"][0]

    async with _broadcast(link) as transfer:
        destination, body = external_message_body(transfer.boc)
        assert destination == Address(transfer.account["address"])
        assert signature_is_valid(body, bytes.fromhex(transfer.account["publicKey"]))

        action = first_send_action(split_signature(body)[0])
        assert action.destination == Address(asked["address"])
        assert action.amount == int(asked["amount"]) == 460_900_000
        assert action.bounce is False
        # Fragment's payload cell is signed byte for byte, not decoded and re-encoded.
        assert action.body.hash == Cell.one_from_boc(base64.b64decode(asked["payload"])).hash
        assert transfer.comment == "50 Telegram Stars \n\nRef#kpJ55h3BW"


@pytest.mark.asyncio
async def test_returned_boc_is_exactly_what_was_broadcast() -> None:
    async with _broadcast(stars_link()) as transfer:
        assert transfer.returned_boc == transfer.boc
        assert len(transfer.tx_hash) == 64


@pytest.mark.asyncio
async def test_usdt_purchase_signs_the_jetton_transfer_body_untouched() -> None:
    link = stars_link()
    link["transaction"]["messages"][0]["payload"] = USDT_STARS_PAYLOAD
    link["transaction"]["messages"][0]["amount"] = "50000000"

    async with _broadcast(link, PaymentMethod.USDT_GRAM) as transfer:
        _, body = external_message_body(transfer.boc)
        assert signature_is_valid(body, bytes.fromhex(transfer.account["publicKey"]))

        action = first_send_action(split_signature(body)[0])
        assert action.amount == 50_000_000
        assert action.body.hash == Cell.one_from_boc(base64.urlsafe_b64decode(USDT_STARS_PAYLOAD + "=")).hash
        # The payment reference rides in the jetton transfer's forward payload.
        assert transfer.comment == "50 Telegram Stars \n\nRef#m9JhZwApQ"


@pytest.mark.asyncio
async def test_signature_check_rejects_a_forged_signature() -> None:
    async with _broadcast(stars_link()) as transfer:
        _, body = external_message_body(transfer.boc)
        public_key = bytes.fromhex(transfer.account["publicKey"])

        assert signature_is_valid(body, public_key)
        assert not signature_is_valid(body, public_key, signature_override=bytes(64))
        assert not signature_is_valid(body, bytes(reversed(public_key)))


# Every wallet kind


WALLETS = [
    pytest.param({"wallet_version": "V5R1"}, id="v5r1-ton"),
    pytest.param({"wallet_version": "V4R2"}, id="v4r2-ton"),
    pytest.param(
        {"wallet_version": "V5R1", "mnemonic_type": "multichain", "seed": BIP39_SEED_12_WORDS}, id="v5r1-multichain-12"
    ),
    pytest.param({"wallet_version": "V4R2", "mnemonic_type": "multichain", "seed": BIP39_SEED}, id="v4r2-multichain-24"),
    pytest.param({"wallet_version": "TG", "seed": BIP39_SEED_12_WORDS}, id="telegram-wallet"),
    pytest.param({"wallet_version": "HighloadV2"}, id="highload-v2"),
    pytest.param({"wallet_version": "HighloadV3R1"}, id="highload-v3r1"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("options", WALLETS)
@pytest.mark.parametrize("state", [ContractState.UNINIT, ContractState.ACTIVE])
async def test_every_wallet_signs_a_valid_transfer(options: dict[str, Any], state: ContractState) -> None:
    link = stars_link()
    asked = link["transaction"]["messages"][0]
    version = WalletVersion(options["wallet_version"])
    ton = FakeTon(state=state, seqno=0 if state == ContractState.UNINIT else 7)
    if version == WalletVersion.TG and state == ContractState.ACTIVE:
        key = PrivateKey(multichain_mnemonic_to_private_key(BIP39_SEED_12_WORDS.split())[1])
        ton.data_raw = WalletTgData(public_key=key.public_key, seqno=7).serialize().to_boc().hex()

    async with _broadcast(link, ton=ton, **options) as transfer:
        destination, body = external_message_body(transfer.boc)
        assert destination == Address(transfer.account["address"])
        # An undeployed wallet deploys itself with the state_init Fragment was given, a deployed one doesn't.
        assert has_state_init(transfer.boc) == (state == ContractState.UNINIT)

        signed, signature = split_body(body, version)
        assert signature_matches(signed, signature, bytes.fromhex(transfer.account["publicKey"]))

        message = find_internal_message(signed, Address(asked["address"]), int(asked["amount"]))
        assert message is not None
        assert message.info.bounce is False
        assert message.body.hash == Cell.one_from_boc(base64.b64decode(asked["payload"])).hash


def test_multichain_phrase_uses_the_bip39_key_not_the_ton_scheme_one() -> None:
    # TEP-3: BIP-39 seed, Ed25519 key at m/44'/607'/0'. The same words must never fall back to the TON scheme.
    from ton_core import mnemonic_to_private_key

    account = FragmentClient(
        seed=BIP39_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, mnemonic_type="multichain"
    ).ton_wallet.account_info()
    assert account["publicKey"] == multichain_mnemonic_to_private_key(BIP39_SEED.split())[0].hex()
    assert account["publicKey"] != mnemonic_to_private_key(BIP39_SEED.split())[0].hex()


# Telegram Wallet key rotation


@pytest.mark.asyncio
async def test_rotated_telegram_wallet_keeps_its_address_and_signs_with_the_new_key() -> None:
    anchor = FragmentClient(seed=BIP39_SEED_12_WORDS, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="TG")
    rotated_key = PrivateKey(multichain_mnemonic_to_private_key(TG_ROTATED_SEED.split()[12:])[1])
    ton = FakeTon(seqno=3)
    ton.data_raw = WalletTgData(public_key=rotated_key.public_key, seqno=3).serialize().to_boc().hex()

    async with _broadcast(stars_link(), ton=ton, seed=TG_ROTATED_SEED, wallet_version="TG") as transfer:
        assert transfer.account["address"] == anchor.ton_wallet.account_info()["address"]
        assert transfer.account["publicKey"] == rotated_key.public_key.as_hex
        _, body = external_message_body(transfer.boc)
        signed, signature = split_leading_signature(body)
        assert signature_matches(signed, signature, bytes.fromhex(rotated_key.public_key.as_hex))


@pytest.mark.asyncio
async def test_telegram_wallet_refuses_to_sign_with_a_key_the_chain_does_not_have() -> None:
    # The phrase says the key was rotated, the chain still has the original one: signing would only burn the attempt.
    anchor_key = PrivateKey(multichain_mnemonic_to_private_key(BIP39_SEED_12_WORDS.split())[1])
    ton = FakeTon(seqno=3)
    ton.data_raw = WalletTgData(public_key=anchor_key.public_key, seqno=3).serialize().to_boc().hex()

    with use_fake_ton(ton), patch("pyfragment.domains.wallet.balance.get_usdt_balance", AsyncMock(return_value=0)):
        async with FragmentClient(
            seed=TG_ROTATED_SEED, api_key=VALID_API_KEY, cookies=VALID_COOKIES, wallet_version="TG"
        ) as client:
            with pytest.raises(ContractError, match="rotated"):
                await process_transaction(client, stars_link())
    assert ton.sent == []
