"""WalletInfo's repr."""

from decimal import Decimal

from pyfragment import WalletInfo


class TestWalletInfoRepr:
    def test_small_balances_are_fixed_point(self) -> None:
        info = WalletInfo(address="UQCtest", state="active", gram_balance=Decimal("0.000000001"), usdt_balance=Decimal("0"))
        text = repr(info)
        assert "E" not in text and "0.000000001" in text

    def test_unknown_usdt_balance_says_so(self) -> None:
        info = WalletInfo(address="UQCtest", state="uninit", gram_balance=Decimal("0"), usdt_balance=None)
        assert "usdt_balance=unknown" in repr(info)
