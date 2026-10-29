from __future__ import annotations

import base64

from ton_core import Cell, OpCode

from pyfragment.exceptions import ParseError

TEXT_COMMENT_OPCODE = 0


def decode_boc(payload: object) -> Cell | None:
    """Fragment's base64 (or base64url) BOC payload as a cell, or ``None`` when there is none."""
    text = str(payload or "").strip()
    if not text:
        return None
    text += "=" * (-len(text) % 4)
    try:
        return Cell.one_from_boc(base64.b64decode(text, altchars=b"-_", validate=True))
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context="payload decode", exc=exc)) from exc


def body_comment(body: Cell | None) -> str | None:
    """The text comment a transfer body carries: directly, or as the forward payload of a jetton (USDT) transfer."""
    if body is None:
        return None
    try:
        reader = body.begin_parse()
        op = reader.load_uint(32)
        if op == OpCode.JETTON_TRANSFER:
            # TEP-74: query_id, amount, destination, response_destination, custom_payload, forward_ton_amount,
            # then forward_payload as Either Cell ^Cell (inline in the rest of this cell, or in a reference).
            reader.load_uint(64)
            reader.load_coins()
            reader.load_address()
            reader.load_address()
            reader.load_maybe_ref()
            reader.load_coins()
            reader = reader.load_ref().begin_parse() if reader.load_bit() else reader
            op = reader.load_uint(32)
        return reader.load_snake_string() if op == TEXT_COMMENT_OPCODE else None
    except Exception:
        # Too short, not UTF-8, or not a well-formed jetton transfer: no comment we can read.
        return None
