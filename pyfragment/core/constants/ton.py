from __future__ import annotations

from typing import Any

USDT_TON_MASTER_ADDRESS: str = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

DEVICE_INFO: dict[str, Any] = {
    "platform": "iphone",
    "appName": "Tonkeeper",
    "appVersion": "26.04.0",
    "maxProtocolVersion": 2,
    "features": [
        "SendTransaction",
        {"name": "SendTransaction", "maxMessages": 255},
        {"name": "SignData", "types": ["text", "binary", "cell"]},
    ],
}
