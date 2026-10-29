from __future__ import annotations

import re
from decimal import Decimal

from pyfragment.domains.purchases.models import PremiumPackage, StarsPackage
from pyfragment.utils.money import parse_amount

# GRAM price: integer and fractional parts are split for custom CSS decimal styling.
# Whole-number fallback handles prices without a fractional part.
_GRAM_PRICE_RE = re.compile(r'icon-ton">([\d,]*)<span class="mini-frac">(\.\d+)</span>')
_GRAM_PRICE_WHOLE_RE = re.compile(r'icon-ton">([\d,]+)</div>')

# Stars package: radio value → USD price → GRAM price, all within the same label block.
_STARS_PACKAGE_RE = re.compile(
    r'value="(\d+)".*?icon-usd">([\d,.]+)</div>.*?icon-ton">([\d,]*)<span class="mini-frac">(\.\d+)</span>',
    re.DOTALL,
)

# Premium package: months radio → GRAM price → USD price, all within the same label block.
_PREMIUM_PACKAGE_RE = re.compile(
    r'name="months"\s+value="(\d+)".*?icon-ton">([\d,]*)<span class="mini-frac">(\.\d+)</span>.*?tm-radio-desc">&#036;([\d.]+)</div>',
    re.DOTALL,
)


def parse_gram_price(html: str) -> Decimal | None:
    m = _GRAM_PRICE_RE.search(html)
    if m:
        return Decimal((m.group(1).replace(",", "") or "0") + m.group(2))
    m = _GRAM_PRICE_WHOLE_RE.search(html)
    if m:
        return Decimal(m.group(1).replace(",", ""))
    return None


def parse_stars_packages(html: str) -> list[StarsPackage]:
    packages = []
    for stars_str, usd_str, gram_int, gram_frac in _STARS_PACKAGE_RE.findall(html):
        usd = parse_amount(usd_str)
        if usd is None:
            continue
        gram = Decimal((gram_int.replace(",", "") or "0") + gram_frac)
        packages.append(StarsPackage(stars=int(stars_str), gram=gram, usd=usd))
    return packages


def parse_premium_packages(html: str) -> list[PremiumPackage]:
    packages = []
    for months_str, gram_int, gram_frac, usd_str in _PREMIUM_PACKAGE_RE.findall(html):
        usd = parse_amount(usd_str)
        if usd is None:
            continue
        gram = Decimal((gram_int.replace(",", "") or "0") + gram_frac)
        packages.append(PremiumPackage(months=int(months_str), gram=gram, usd=usd))
    return packages
