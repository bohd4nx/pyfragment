"""What the wallet signs: the payment, the seqno, the expiry and the key, for every wallet kind."""

import asyncio
import time
from collections.abc import Callable
from typing import Any

import pytest
from ton_core import Address, ContractState, PrivateKey, mnemonic_to_private_key, multichain_mnemonic_to_private_key
from tonutils.exceptions import ContractError

from pyfragment import FragmentClient, ProviderError
from pyfragment.domains.wallet.transfers import process_transaction
from pyfragment.enums import PaymentMethod, WalletVersion
from tests.domains.wallet.helpers import asked, highload_expiry, link, payload_hash, signed_header, sizes, tg_chain
from tests.support.data import BIP39_SEED, BIP39_SEED_12_WORDS, TG_ROTATED_SEED
from tests.support.fake_ton import FakeTon, provider_error
from tests.support.signing import (
    external_message_body,
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


class TestSignedPayment:
    async def test_pays_what_fragment_asked_for_with_a_valid_signature(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient]
    ) -> None:
        client, message = make_client(), asked()
        await process_transaction(client, link())
        account = client.ton_wallet.account_info()

        destination, body = external_message_body(fake_ton.sent[0])
        assert destination == Address(account["address"])
        assert signature_is_valid(body, bytes.fromhex(account["publicKey"]))
        action = first_send_action(split_signature(body)[0])
        assert action.destination == Address(message["address"])
        assert action.amount == int(message["amount"])
        assert action.bounce is False
        # Fragment's payload cell is signed byte for byte, not decoded and re-encoded.
        assert action.body.hash == payload_hash(message["payload"])

    async def test_usdt_transfer_body_is_signed_untouched(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        sent = await process_transaction(client, link(payload=USDT_STARS_PAYLOAD, amount="50000000"), PaymentMethod.USDT_GRAM)

        action = first_send_action(split_signature(external_message_body(fake_ton.sent[0])[1])[0])
        assert action.amount == 50_000_000
        assert action.body.hash == payload_hash(USDT_STARS_PAYLOAD)
        # The payment reference rides in the jetton transfer's forward payload.
        assert sent.comment == "50 Telegram Stars \n\nRef#m9JhZwApQ"

    async def test_a_forged_signature_does_not_verify(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        await process_transaction(client, link())
        _, body = external_message_body(fake_ton.sent[0])
        public_key = bytes.fromhex(client.ton_wallet.account_info()["publicKey"])

        assert signature_is_valid(body, public_key)
        assert not signature_is_valid(body, public_key, signature_override=bytes(64))
        assert not signature_is_valid(body, bytes(reversed(public_key)))


class TestEveryWalletKind:
    @pytest.mark.parametrize("options", WALLETS)
    @pytest.mark.parametrize("state", [ContractState.UNINIT, ContractState.ACTIVE])
    async def test_signs_a_valid_transfer(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient], options: dict[str, Any], state: ContractState
    ) -> None:
        version = WalletVersion(options["wallet_version"])
        fake_ton.state, fake_ton.seqno = state, 0 if state == ContractState.UNINIT else 7
        if version == WalletVersion.TG and state == ContractState.ACTIVE:
            tg_chain(fake_ton)
        client = make_client(**options)

        await process_transaction(client, link())
        account = client.ton_wallet.account_info()

        destination, body = external_message_body(fake_ton.sent[0])
        assert destination == Address(account["address"])
        # An undeployed wallet deploys itself with the state_init Fragment was given, a deployed one doesn't.
        assert has_state_init(fake_ton.sent[0]) == (state == ContractState.UNINIT)
        signed, signature = split_body(body, version)
        assert signature_matches(signed, signature, bytes.fromhex(account["publicKey"]))
        assert sizes(fake_ton, version) == [1]

    @pytest.mark.parametrize("options", WALLETS)
    async def test_carries_a_batch_in_one_signed_message(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient], options: dict[str, Any]
    ) -> None:
        version = WalletVersion(options["wallet_version"])
        if version == WalletVersion.TG:
            tg_chain(fake_ton)
        batch = 3 if version == WalletVersion.V4R2 else 5  # V4R2 carries at most 4 messages
        client = make_client(max_batch=batch, **options)

        intents = await asyncio.gather(*(process_transaction(client, link()) for _ in range(batch)))
        account = client.ton_wallet.account_info()

        assert len(fake_ton.sent) == 1
        assert len({intent.msg_hash for intent in intents}) == 1
        signed, signature = split_body(external_message_body(fake_ton.sent[0])[1], version)
        assert signature_matches(signed, signature, bytes.fromhex(account["publicKey"]))
        assert sizes(fake_ton, version) == [batch]

    def test_multichain_phrase_uses_the_bip39_key_not_the_ton_scheme_one(
        self, make_client: Callable[..., FragmentClient]
    ) -> None:
        # TEP-3: BIP-39 seed, Ed25519 key at m/44'/607'/0'. The same words must never fall back to the TON scheme.
        account = make_client(seed=BIP39_SEED, mnemonic_type="multichain").ton_wallet.account_info()
        assert account["publicKey"] == multichain_mnemonic_to_private_key(BIP39_SEED.split())[0].hex()
        assert account["publicKey"] != mnemonic_to_private_key(BIP39_SEED.split())[0].hex()


class TestTelegramWalletRotation:
    async def test_rotated_wallet_keeps_its_address_and_signs_with_the_new_key(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient]
    ) -> None:
        anchor = make_client(seed=BIP39_SEED_12_WORDS, wallet_version="TG")
        rotated_key = PrivateKey(multichain_mnemonic_to_private_key(TG_ROTATED_SEED.split()[12:])[1])
        tg_chain(fake_ton, TG_ROTATED_SEED, seqno=3)
        client = make_client(seed=TG_ROTATED_SEED, wallet_version="TG")

        await process_transaction(client, link())

        account = client.ton_wallet.account_info()
        assert account["address"] == anchor.ton_wallet.account_info()["address"]
        assert account["publicKey"] == rotated_key.public_key.as_hex
        signed, signature = split_leading_signature(external_message_body(fake_ton.sent[0])[1])
        assert signature_matches(signed, signature, bytes.fromhex(rotated_key.public_key.as_hex))

    async def test_refuses_to_sign_with_a_key_the_chain_does_not_have(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient]
    ) -> None:
        # The phrase says the key was rotated, the chain still has the original one: signing would only burn the attempt.
        tg_chain(fake_ton, BIP39_SEED_12_WORDS, seqno=3)
        with pytest.raises(ContractError, match="rotated"):
            await process_transaction(make_client(seed=TG_ROTATED_SEED, wallet_version="TG"), link())
        assert fake_ton.sent == []


class TestSeqno:
    async def test_signs_the_on_chain_seqno(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        fake_ton.seqno = 41
        await process_transaction(client, link())
        assert signed_header(fake_ton.sent[0])[1] == 41

    async def test_read_failure_raises_instead_of_signing_seqno_zero(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        fake_ton.seqno_errors = [provider_error(500, "internal")]
        with pytest.raises(ProviderError) as exc_info:
            await process_transaction(client, link())
        assert exc_info.value.retryable
        assert fake_ton.sent == []

    async def test_undeployed_wallet_signs_seqno_zero_and_ships_its_state_init(
        self, fake_ton: FakeTon, client: FragmentClient
    ) -> None:
        fake_ton.state, fake_ton.seqno = ContractState.UNINIT, 0
        await process_transaction(client, link())
        assert signed_header(fake_ton.sent[0])[1] == 0
        assert has_state_init(fake_ton.sent[0])
        assert fake_ton.seqno_reads == 0

    async def test_deployed_wallet_does_not_ship_its_state_init(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        await process_transaction(client, link())
        assert not has_state_init(fake_ton.sent[0])

    async def test_highload_wallets_never_read_a_seqno(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient]
    ) -> None:
        await process_transaction(make_client(wallet_version="HighloadV3R1"), link())
        assert fake_ton.seqno_reads == 0


class TestExpiry:
    async def test_expires_with_fragments_deadline_when_that_is_sooner(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        sent = await process_transaction(client, link(valid_for=20))
        assert signed_header(fake_ton.sent[0])[0] == sent.valid_until
        assert sent.valid_until <= int(time.time()) + 20

    async def test_expires_within_a_minute_otherwise(self, fake_ton: FakeTon, client: FragmentClient) -> None:
        before = int(time.time())
        await process_transaction(client, link(valid_for=3600))
        assert before + 60 <= signed_header(fake_ton.sent[0])[0] <= int(time.time()) + 60

    @pytest.mark.parametrize("wallet_version", ["HighloadV2", "HighloadV3R1"])
    @pytest.mark.parametrize("seconds_left", [20, 3600])
    async def test_highload_transfers_expire_like_the_others(
        self, fake_ton: FakeTon, make_client: Callable[..., FragmentClient], wallet_version: str, seconds_left: int
    ) -> None:
        # No seqno here: the expiry is what keeps a highload transfer from paying an invoice Fragment already dropped.
        sent = await process_transaction(make_client(wallet_version=wallet_version), link(valid_for=seconds_left))
        expiry = highload_expiry(fake_ton.sent[0], wallet_version)
        assert expiry == sent.valid_until
        assert expiry <= int(time.time()) + min(seconds_left, 60)
