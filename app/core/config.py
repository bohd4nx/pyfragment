import logging
import os
import sys
from typing import Dict

from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        required_keys = ['COOKIES', 'SEED', 'HASH', 'API_KEY']
        missing_keys = []

        self._config = {}

        for key in required_keys:
            value = os.getenv(key, '').strip()
            if not value:
                missing_keys.append(key)
            self._config[key.lower()] = value

        if missing_keys:
            logger.error(f"Missing required environment variables: {', '.join(missing_keys)}")
            logger.error("Create .env file based on .env.example and fill all fields")
            sys.exit(1)

        logger.info("Configuration loaded successfully")

    def get_config(self) -> Dict[str, str]:
        return self._config.copy()

    def get(self, key: str, default: str = '') -> str:
        return self._config.get(key, default)
