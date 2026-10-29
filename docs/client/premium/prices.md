# Premium Prices

Query the current GRAM and USD prices for Telegram Premium subscriptions without making a purchase.

## Method

```python
await client.get_premium_packages() -> list[PremiumPackage]
```

Returns all Telegram Premium subscription options with live prices fetched from Fragment.

## Return

`list[PremiumPackage]` — ordered as Fragment presents them on the page (12 → 6 → 3 months).

Each `PremiumPackage` has:

- `months: int` — subscription duration
- `gram: Decimal` — current GRAM price
- `usd: Decimal` — reference USD price

## Example

```python
packages: list[PremiumPackage] = await client.get_premium_packages()
for p in packages:
    print(p.months, p.gram, p.usd)
```

## Errors

- `FragmentAPIError`: Fragment returned no packages
- `SessionExpiredError`: session cookies are invalid or expired
