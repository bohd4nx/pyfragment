import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.core.exceptions import ConfigError

logger = logging.getLogger(__name__)


class Config:
    SEED: str
    API_KEY: str

    def __init__(self) -> None:
        env_path = Path(__file__).resolve().parents[2] / ".env"

        if not env_path.exists():
            raise ConfigError(
                ".env file not found. "
                "Copy .env.example to .env and fill in SEED and API_KEY."
            )

        load_dotenv(env_path)

        missing = [k for k in ("SEED", "API_KEY") if not os.getenv(k, "").strip()]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Open .env and fill in all required fields."
            )

        self.SEED = os.getenv("SEED", "").strip()
        self.API_KEY = os.getenv("API_KEY", "").strip()

try:
    config = Config()
except ConfigError as e:
    logger.error("Configuration error: %s", e)
    sys.exit(1)
