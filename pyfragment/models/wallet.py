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


@dataclass
class TonTransferResult:
    transaction_id: str
    destination: str
    amount: int

    def __repr__(self) -> str:
        return f"TonTransferResult(destination='{self.destination}', amount={self.amount} TON, tx='{self.transaction_id}')"


@dataclass
class UsdtTransferResult:
    transaction_id: str
    destination: str
    amount: int

    def __repr__(self) -> str:
        return f"UsdtTransferResult(destination='{self.destination}', amount={self.amount} USDT, tx='{self.transaction_id}')"


__all__ = ["TonTransferResult", "UsdtTransferResult", "WalletInfo"]
