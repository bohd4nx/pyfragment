# Stars Prices

Query the current GRAM and USD prices for Stars without making a purchase.

## Methods

```python
await client.get_stars_price(amount: int) -> Decimal
await client.get_stars_packages() -> list[StarsPackage]
```

## `get_stars_price`

Returns the GRAM cost for the exact `amount` of Stars you want to buy.

**Parameters**

- `amount`: integer from `50` to `10_000_000`; raises `ConfigurationError` outside this range

**Return**

`Decimal` — the GRAM price for that amount.

```python
from decimal import Decimal

price: Decimal = await client.get_stars_price(100)
print(price)  # e.g. 1.2309
```

## `get_stars_packages`

Returns all predefined Stars packages Fragment offers, each with a live GRAM and USD price.

**Return**

`list[StarsPackage]` — ordered as Fragment returns them.

Each `StarsPackage` has:

- `stars: int`
- `gram: Decimal`
- `usd: Decimal`

```python
packages: list[StarsPackage] = await client.get_stars_packages()
for p in packages:
    print(p.stars, p.gram, p.usd)
```

## Errors

- `ConfigurationError`: `amount` out of range (only `get_stars_price`)
- `FragmentAPIError`: Fragment returned no price or no packages
