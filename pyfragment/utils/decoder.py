import base64

from pytoniq_core import Cell

from pyfragment.types import ParseError


def clean_decode(payload: str) -> str:
    """Decode a base64-encoded BOC payload to a plain-text comment string.

    Fragment transaction payloads are BOC-serialised TVM cells. This function
    base64-decodes the payload, parses the cell, skips the 32-bit op-code
    prefix, and reads the snake-encoded UTF-8 comment.

    Args:
        payload: Base64url-encoded BOC string (padding is added automatically).

    Returns:
        Decoded comment string, or ``""`` for an empty payload.

    Raises:
        ParseError: If the payload cannot be decoded or parsed.
    """
    s = payload.strip()
    if not s:
        return ""
    s += "=" * (-len(s) % 4)
    try:
        boc = base64.b64decode(s)
        cell = Cell.one_from_boc(boc)
        sl = cell.begin_parse()
        sl.load_uint(32)  # op code — always 0 for text comment
        return sl.load_snake_string().strip()
    except Exception as exc:
        raise ParseError(ParseError.UNPARSEABLE.format(context="payload decode", exc=exc)) from exc
