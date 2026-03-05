import base64
import logging
import re
import string

logger = logging.getLogger(__name__)


def clean_decode(payload: str) -> str:
    logger.debug("Original payload: %s", payload)

    # Strip non-Base64 chars and decode
    s = re.sub(r'[^A-Za-z0-9+/=]', '', payload.strip())
    s += '=' * (-len(s) % 4)
    text = base64.b64decode(s).decode('utf-8', errors='ignore')

    # Keep only printable characters
    text = ''.join(c for c in text if c in string.printable or c.isspace())

    # Extract "Telegram … Ref#XXXX" block
    match = re.search(r'([0-9]*\s*Telegram .*?Ref#[A-Za-z0-9]+)', text, re.S)
    result = match.group(1).strip() if match else text.strip()

    logger.debug("Decoded result: %s", result)
    return result

