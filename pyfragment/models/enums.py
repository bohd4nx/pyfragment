from __future__ import annotations

from typing import Literal

PaymentMethod = Literal["ton", "usdt_ton"]
WalletVersion = Literal["V4R2", "V5R1"]

__all__ = ["PaymentMethod", "WalletVersion"]
