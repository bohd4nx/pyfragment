from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pyfragment.enums import PaymentMethod


@dataclass
class WalletInfo:
    address: str
    state: str
    gram_balance: Decimal  # exact, in GRAM (ex TON)
    usdt_balance: Decimal | None  # exact, in USDT; None when the USDT lookup failed (balance unknown)

    def __repr__(self) -> str:
        usdt = format(self.usdt_balance, "f") if self.usdt_balance is not None else "unknown"
        return (
            f"WalletInfo(address='{self.address}', state='{self.state}', "
            f"gram_balance={format(self.gram_balance, 'f')} GRAM (ex TON), usdt_balance={usdt} USDT)"
        )


@dataclass(frozen=True)
class TransferIntent:
    """A signed transfer about to be sent: everything needed to identify it on-chain later.

    Passed to ``FragmentClient(on_transfer_prepared=...)`` after signing and before sending; store it to verify the
    purchase on-chain (e.g. by ``msg_hash``) if the process dies before the purchase result is returned.
    """

    msg_hash: str  # normalized hash of the signed external message: the purchase's transaction_id
    boc: str  # the signed external message, base64
    destination: str  # the address the wallet pays (Fragment's, or the USDT jetton wallet for USDT payments)
    amount_nano: int  # GRAM (ex TON) attached to the transfer, in nanograms
    comment: str | None  # Fragment's payment reference, e.g. "50 Telegram Stars \n\nRef#kpJ55h3BW"
    payment_method: PaymentMethod
    req_id: str | None  # Fragment's invoice id
    valid_until: int  # unix time after which the wallet rejects the transfer: it can never land later
