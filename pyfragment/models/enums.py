from __future__ import annotations

from enum import StrEnum
from typing import Any

from tonutils.contracts.wallet import WalletV4R2, WalletV5R1


class PaymentMethod(StrEnum):
    TON = "ton"
    USDT_TON = "usdt_ton"


class WalletVersion(StrEnum):
    V4R2 = "V4R2"
    V5R1 = "V5R1"


WALLET_CLASSES: dict[WalletVersion, Any] = {
    WalletVersion.V4R2: WalletV4R2,
    WalletVersion.V5R1: WalletV5R1,
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


__all__ = ["PaymentMethod", "SupportedBrowser", "WALLET_CLASSES", "WalletVersion"]
