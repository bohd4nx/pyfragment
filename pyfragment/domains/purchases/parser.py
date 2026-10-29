from __future__ import annotations

import re
from decimal import Decimal

from pyfragment.domains.purchases.models import PremiumPackage, StarsPackage
from pyfragment.utils.money import parse_amount


def _parse_gram(int_part: str, frac_part: str) -> Decimal:
    return parse_amount(int_part + frac_part) or Decimal(0)


# GRAM price: integer and fractional parts are split for custom CSS decimal styling.
# Whole-number fallback handles prices without a fractional part.
_GRAM_PRICE_RE = re.compile(r'icon-ton">([\d,]*)<span class="mini-frac">(\.\d+)</span>')
_GRAM_PRICE_WHOLE_RE = re.compile(r'icon-ton">([\d,]+)</div>')

# Stars package: radio value → USD price → GRAM price, all within the same label block.
# The mini-frac span is optional: whole-number prices render without it.
_STARS_PACKAGE_RE = re.compile(
    r'value="(\d+)".*?icon-usd">([\d,.]+)</div>.*?icon-ton">([\d,]*)(?:<span class="mini-frac">(\.\d+)</span>)?',
    re.DOTALL,
)

# Premium package: months radio → GRAM price → USD price, all within the same label block.
# The mini-frac span is optional: whole-number prices render without it.
_PREMIUM_PACKAGE_RE = re.compile(
    r'name="months"\s+value="(\d+)".*?icon-ton">([\d,]*)(?:<span class="mini-frac">(\.\d+)</span>)?.*?tm-radio-desc">&#036;([\d.]+)</div>',
    re.DOTALL,
)


def parse_gram_price(html: str) -> Decimal | None:
    m = _GRAM_PRICE_RE.search(html)
    if m:
        return _parse_gram(m.group(1), m.group(2))
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
        packages.append(StarsPackage(stars=int(stars_str), gram=_parse_gram(gram_int, gram_frac), usd=usd))
    return packages


def parse_premium_packages(html: str) -> list[PremiumPackage]:
    packages = []
    for months_str, gram_int, gram_frac, usd_str in _PREMIUM_PACKAGE_RE.findall(html):
        usd = parse_amount(usd_str)
        if usd is None:
            continue
        packages.append(PremiumPackage(months=int(months_str), gram=_parse_gram(gram_int, gram_frac), usd=usd))
    return packages
