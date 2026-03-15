import base64

from pytoniq_core import Cell

from fragmentapi.types import RequestError


def clean_decode(payload: str) -> str:
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
        raise RequestError(RequestError.UNPARSEABLE.format(context="payload decode", exc=exc)) from exc
