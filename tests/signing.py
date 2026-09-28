"""Read a signed W5 wallet message back: split off the signature, verify it, and decode the transfer it carries.

Used by the signing tests and by ``scripts/live_signing_check.py`` (no pytest needed).
"""

from dataclasses import dataclass

from ton_core import Address, Builder, Cell, NetworkGlobalID, SignatureDomain, verify_sign

NETWORK = NetworkGlobalID.MAINNET
SIGN_ACTION_OPCODE = 0x0EC3C86D  # action_send_msg of a W5 wallet
SIGNATURE_BITS = 512


def external_message_body(boc: bytes) -> tuple[Address, Cell]:
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


def split_signature(body: Cell) -> tuple[Cell, bytes]:
    """Separate a W5 body into the signed cell and its trailing signature."""
    reader = body.begin_parse()
    signed_bits = reader.load_bits(reader.remaining_bits - SIGNATURE_BITS)
    signature = reader.load_bytes(SIGNATURE_BITS // 8)
    signed = Builder()
    signed.store_bits(signed_bits)
    for ref in body.refs:
        signed.store_ref(ref)
    return signed.end_cell(), signature


def signature_is_valid(body: Cell, public_key: bytes, signature_override: bytes | None = None) -> bool:
    signed, signature = split_signature(body)
    data = SignatureDomain(NETWORK).data_to_sign(signed.hash)
    return bool(verify_sign(public_key, data, signature_override or signature))


@dataclass
class SendAction:
    destination: Address
    amount: int
    bounce: bool
    body: Cell


def first_send_action(signed: Cell) -> SendAction:
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
