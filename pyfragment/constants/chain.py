from __future__ import annotations

from typing import Any

# Smallest units: 1 GRAM (ex TON) = 10^9 nanograms, 1 USDT = 10^6 units
GRAM_DECIMALS: int = 9
USDT_DECIMALS: int = 6

# TVM exit code of a get-method called on a contract that isn't deployed (toncenter reports it as an error)
TVM_EXIT_ACCOUNT_NOT_FOUND: int = -13

# TON Connect network id of the mainnet, as sent in the wallet account payload
MAINNET_CHAIN_ID: str = "-239"

# USDT-TON jetton master contract address on GRAM (ex TON) mainnet
USDT_GRAM_MASTER_ADDRESS: str = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

# How long a signed transfer stays valid: after that the wallet rejects it, so it can never land late
MESSAGE_TTL: int = 60

# How often a transfer looks for the previous one to land before taking the next seqno (about a quarter of a block)
SEQNO_POLL_INTERVAL: float = 1.0

# TON Connect device info sent during wallet connection handshake.
# Based on wallets-v2.json from config.ton.org/wallets-v2.json — updated 2026-10.
DEVICE_INFO: dict[str, Any] = {
    "platform": "iphone",
    "appName": "Tonkeeper",
    "appVersion": "26.10.1",
    "maxProtocolVersion": 2,
    "features": [
        {"name": "SendTransaction", "maxMessages": 255, "extraCurrencySupported": True},
        {"name": "SignData", "types": ["text", "binary", "cell"]},
    ],
}
