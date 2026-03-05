import base64
import logging

from pytoniq_core import Cell

logger = logging.getLogger(__name__)


# OLD decoder (manual base64 + regex, kept for reference):
#
# import re, string
# def clean_decode(payload: str) -> str:
#     s = re.sub(r'[^A-Za-z0-9+/=]', '', payload.strip())
#     s += '=' * (-len(s) % 4)
#     text = base64.b64decode(s).decode('utf-8', errors='ignore')
#     text = ''.join(c for c in text if c in string.printable or c.isspace())
#     match = re.search(r'([0-9]*\s*Telegram .*?Ref#[A-Za-z0-9]+)', text, re.S)
#     return match.group(1).strip() if match else text.strip()


def clean_decode(payload: str) -> str:
    logger.debug("Original payload: %s", payload)

    # Pad and decode base64 → BOC bytes
    s = payload.strip()
    if not s:
        return ""
    s += "=" * (-len(s) % 4)
    boc = base64.b64decode(s)

    # Parse BOC cell and read snake-encoded text (skipping 32-bit op prefix)
    cell = Cell.one_from_boc(boc)
    sl = cell.begin_parse()
    sl.load_uint(32)  # op code — always 0 for text comment
    result = sl.load_snake_string().strip()

    logger.debug("Decoded payload: %s", result.replace("\n", " "))
    return result
