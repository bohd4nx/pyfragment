import base64
import logging
import re
import string

logger = logging.getLogger(__name__)


def clean_decode(payload: str) -> str:
    logger.debug(f"Original payload: {payload}")

    # Decode raw bytes first
    clean = ''.join(c for c in payload if c.isalnum() or c in '+/=')
    clean += '=' * (-len(clean) % 4)
    raw_bytes = base64.b64decode(clean)
    logger.debug(f"Raw decoded bytes: {raw_bytes}")

    # 1. Clean Base64
    s = re.sub(r'[^A-Za-z0-9+/=]', '', payload.strip())
    s += '=' * (-len(s) % 4)

    # 2. Base64 -> bytes
    b = base64.b64decode(s)

    # 3. Decode UTF-8, ignoring invalid bytes
    t = b.decode('utf-8', errors='ignore')

    # 4. Remove binary characters, keep only printable + whitespace
    t = ''.join(c for c in t if c in string.printable or c.isspace())

    # 5. Extract the main text with Ref#
    match = re.search(r'([0-9]*\s*Telegram .*?Ref#[A-Za-z0-9]+)', t, re.S)
    if match:
        result = match.group(1).strip()
    else:
        result = t.strip()

    logger.debug(f"Cleaned result: {result}")

    return result
