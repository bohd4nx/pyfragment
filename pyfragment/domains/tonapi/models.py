from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WalletInfo:
    address: str
    state: str
    gram_balance: float
    usdt_balance: float

    def __repr__(self) -> str:
        return (
            f"WalletInfo(address='{self.address}', state='{self.state}', "
            f"gram_balance={self.gram_balance} GRAM (ex TON), usdt_balance={self.usdt_balance} USDT)"
        )
