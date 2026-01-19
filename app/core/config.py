import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        env_path = Path(__file__).resolve().parents[2] / ".env"

        if not env_path.exists():
            logger.error(".env file not found!")
            sys.exit(1)

        load_dotenv(env_path)

        required_keys = ["SEED", "API_KEY"]
        missing_keys: list[str] = []

        for key in required_keys:
            value = os.getenv(key, "").strip()
            if not value:
                missing_keys.append(key)
            setattr(self, key, value)

        if missing_keys:
            logger.error(f"Missing required environment variables: {', '.join(missing_keys)}")
            logger.error("Create .env file based on .env.example and fill all fields")
            sys.exit(1)

        logger.info("Configuration loaded successfully")


config = Config()
