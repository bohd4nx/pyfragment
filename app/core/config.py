import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from app.core.constants import SUPPORTED_WALLET_VERSIONS, WalletVersion
from app.core.exceptions import ConfigError

logger = logging.getLogger(__name__)


class Config:
    SEED: str
    API_KEY: str
    WALLET_VERSION: WalletVersion

    def __init__(self) -> None:
        # Load .env if present; env vars already in the process take precedence
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        missing = [k for k in ("SEED", "API_KEY") if not os.getenv(k, "").strip()]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in SEED and API_KEY."
            )

        self.SEED = os.getenv("SEED", "").strip()
        self.API_KEY = os.getenv("API_KEY", "").strip()

        version = os.getenv("WALLET_VERSION", "V5R1").strip().upper()
        if version not in SUPPORTED_WALLET_VERSIONS:
            raise ConfigError(
                f"Unsupported WALLET_VERSION '{version}'. " f"Must be one of: {', '.join(sorted(SUPPORTED_WALLET_VERSIONS))}."
            )
        self.WALLET_VERSION: WalletVersion = version  # type: ignore[assignment]


config: Config | None = None
try:
    config = Config()
except ConfigError as e:
    logger.warning("Configuration not loaded: %s", e)
