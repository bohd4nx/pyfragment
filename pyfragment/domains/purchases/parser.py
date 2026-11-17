from __future__ import annotations

import re
from decimal import Decimal

from pyfragment.domains.purchases.models import PremiumPackage, StarsPackage
from pyfragment.utils.money import parse_amount


def parse_gram(int_part: str, frac_part: str) -> Decimal:
    return parse_amount(int_part + frac_part) or Decimal(0)


# Fragment renders the fraction in its own span (CSS styling); whole-number prices have none.
_GRAM_PRICE_RE = re.compile(r'icon-ton">([\d,]*)<span class="mini-frac">(\.\d+)</span>')
_GRAM_PRICE_WHOLE_RE = re.compile(r'icon-ton">([\d,]+)</div>')

# Radio value → USD price → GRAM price, all within one label block.
_STARS_PACKAGE_RE = re.compile(
    r'value="(\d+)".*?icon-usd">([\d,.]+)</div>.*?icon-ton">([\d,]*)(?:<span class="mini-frac">(\.\d+)</span>)?',
    re.DOTALL,
)

# Months radio → GRAM price → USD price, all within one label block.
_PREMIUM_PACKAGE_RE = re.compile(
    r'name="months"\s+value="(\d+)".*?icon-ton">([\d,]*)(?:<span class="mini-frac">(\.\d+)</span>)?.*?tm-radio-desc">&#036;([\d.]+)</div>',
    re.DOTALL,
)


def parse_gram_price(html: str) -> Decimal | None:
    m = _GRAM_PRICE_RE.search(html)
    if m:
        return parse_gram(m.group(1), m.group(2))
    m = _GRAM_PRICE_WHOLE_RE.search(html)
    if m:
        return parse_amount(m.group(1))
    return None


def parse_stars_packages(html: str) -> list[StarsPackage]:
    packages = []
    for stars_str, usd_str, gram_int, gram_frac in _STARS_PACKAGE_RE.findall(html):
        usd = parse_amount(usd_str)
        if usd is None:
            continue
        packages.append(StarsPackage(stars=int(stars_str), gram=parse_gram(gram_int, gram_frac), usd=usd))
    return packages


def parse_premium_packages(html: str) -> list[PremiumPackage]:
    packages = []
    for months_str, gram_int, gram_frac, usd_str in _PREMIUM_PACKAGE_RE.findall(html):
        usd = parse_amount(usd_str)
        if usd is None:
            continue
        packages.append(PremiumPackage(months=int(months_str), gram=parse_gram(gram_int, gram_frac), usd=usd))
    return packages
