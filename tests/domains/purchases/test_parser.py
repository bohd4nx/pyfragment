"""Reading prices and packages off Fragment's Stars and Premium pages."""

from decimal import Decimal

import pytest

from pyfragment import PremiumPackage, StarsPackage
from pyfragment.domains.purchases.parser import parse_gram_price, parse_premium_packages, parse_stars_packages
from tests.support import fixtures


class TestParseGramPrice:
    def test_price_with_a_fraction_span(self) -> None:
        assert parse_gram_price(fixtures.response("stars_prices.json")["cur_price"]) == Decimal("0.7677")

    def test_thousands_separator_is_dropped(self) -> None:
        html = 'icon-ton">2,288<span class="mini-frac">.01</span></div>'

        assert parse_gram_price(html) == Decimal("2288.01")

    def test_whole_number_price_has_no_fraction_span(self) -> None:
        assert parse_gram_price('<div class="icon-ton">12</div>') == Decimal("12")

    @pytest.mark.parametrize("html", ["", '<div class="icon-usd">0.75</div>'])
    def test_no_gram_price(self, html: str) -> None:
        assert parse_gram_price(html) is None


class TestParseStarsPackages:
    def test_every_package_of_the_page(self) -> None:
        packages = parse_stars_packages(fixtures.response("stars_prices.json")["options_html"])

        assert len(packages) == 22
        assert packages[0] == StarsPackage(stars=50, gram=Decimal("0.7677"), usd=Decimal("0.75"))
        assert packages[1] == StarsPackage(stars=75, gram=Decimal("1.1516"), usd=Decimal("1.13"))
        assert [p.stars for p in packages] == sorted(p.stars for p in packages)
        assert packages[-1].stars == 10_000_000

    def test_prices_over_a_thousand_keep_their_digits(self) -> None:
        packages = parse_stars_packages(fixtures.response("stars_prices.json")["options_html"])

        big = next(p for p in packages if p.stars == 1_000_000)
        assert big.usd > 1000
        assert big.gram > 1000

    @pytest.mark.parametrize("html", ["", "<div>no packages</div>"])
    def test_nothing_to_read(self, html: str) -> None:
        assert parse_stars_packages(html) == []


class TestParsePremiumPackages:
    def test_the_options_in_page_order(self) -> None:
        packages = parse_premium_packages(fixtures.html("premium_page_months.html"))

        assert packages == [
            PremiumPackage(months=12, gram=Decimal("29.66"), usd=Decimal("28.99")),
            PremiumPackage(months=6, gram=Decimal("16.36"), usd=Decimal("15.99")),
            PremiumPackage(months=3, gram=Decimal("12.27"), usd=Decimal("11.99")),
        ]

    def test_nothing_to_read(self) -> None:
        assert parse_premium_packages("<html></html>") == []


class TestReprs:
    def test_packages_show_their_prices(self) -> None:
        assert repr(StarsPackage(stars=50, gram=Decimal("0.7677"), usd=Decimal("0.75"))) == (
            "StarsPackage(stars=50, gram=0.7677, usd=0.75)"
        )
        assert repr(PremiumPackage(months=3, gram=Decimal("12.27"), usd=Decimal("11.99"))) == (
            "PremiumPackage(months=3, gram=12.27, usd=11.99)"
        )
