from __future__ import annotations

import sys
from enum import Enum
from typing import Any

from tonutils.contracts.wallet import WalletHighloadV2, WalletHighloadV3R1, WalletV4R2, WalletV5R1

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):  # noqa: F811
        pass


class PaymentMethod(StrEnum):
    GRAM = "ton"
    USDT_GRAM = "usdt_ton"

    # Not supported yet
    USDT_ETH = "usdt_eth"
    USDT_POL = "usdt_pol"
    USDC_ETH = "usdc_eth"
    USDC_BASE = "usdc_base"
    USDC_POL = "usdc_pol"


class WalletVersion(StrEnum):
    V4R2 = "V4R2"
    V5R1 = "V5R1"
    HighloadV2 = "HighloadV2"
    HighloadV3R1 = "HighloadV3R1"


WALLET_CLASSES: dict[WalletVersion, Any] = {
    WalletVersion.V4R2: WalletV4R2,
    WalletVersion.V5R1: WalletV5R1,
    WalletVersion.HighloadV2: WalletHighloadV2,
    WalletVersion.HighloadV3R1: WalletHighloadV3R1,
}


class SupportedBrowser(StrEnum):
    ARC = "arc"
    BRAVE = "brave"
    CHROME = "chrome"
    CHROMIUM = "chromium"
    CHROMIUM_BASED = "chromium_based"
    EDGE = "edge"
    FIREFOX = "firefox"
    FIREFOX_BASED = "firefox_based"
    LIBREWOLF = "librewolf"
    OPERA = "opera"
    OPERA_GX = "opera_gx"
    SAFARI = "safari"
    VIVALDI = "vivaldi"
