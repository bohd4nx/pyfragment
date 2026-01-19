import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_cookies() -> dict[str, Any]:
    cookies_path = Path(__file__).resolve().parents[2] / "cookies.json"

    if not cookies_path.exists():
        logger.error("cookies.json file not found!")
        return {}

    try:
        with cookies_path.open("r", encoding="utf-8") as file:
            cookies = json.load(file)

        required_keys = ["stel_ssid", "stel_dt", "stel_token", "stel_ton_token"]
        missing_or_empty = [
            key for key in required_keys
            if not str(cookies.get(key, "")).strip()
        ]

        if missing_or_empty:
            logger.warning(
                "cookies.json has missing or empty values: %s",
                ", ".join(missing_or_empty)
            )

        return cookies
    except Exception as exc:
        logger.error(f"Failed to load cookies.json: {exc}")
        return {}
