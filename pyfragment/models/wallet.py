from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WalletInfo:
    address: str
    state: str
    ton_balance: float
    usdt_balance: float

    def __repr__(self) -> str:
        return (
            f"WalletInfo(address='{self.address}', state='{self.state}', "
            f"ton_balance={self.ton_balance} TON, usdt_balance={self.usdt_balance} USDT)"
        )


__all__ = ["WalletInfo"]
