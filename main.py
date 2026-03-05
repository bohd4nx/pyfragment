import asyncio
import logging

from app.core import setup_logging
from app.methods import buy_premium, buy_stars, topup_ton

logger = logging.getLogger(__name__)


async def topup_ton_example():
    logger.info("Starting TON topup example")

    # @bohd4nx - target username, 100 - TON amount (integer 1-1000000000 (one billion))
    result = await topup_ton("@bohd4nx", 100)

    if result["success"]:
        data = result["data"]
        logger.info(f"TON topup successful: {data['amount']} TON sent to {data['username']}")
        logger.info(f"Transaction ID: {data['transaction_id']}")
    else:
        logger.error(f"TON topup failed: {result['error']}")


async def buy_premium_example():
    logger.info("Starting Premium purchase example")

    # @bohd4nx - target username, 12 - months duration (3, 6, or 12 only)
    result = await buy_premium("@bohd4nx", 12)

    if result["success"]:
        data = result["data"]
        logger.info(f"Premium purchase successful: {data['months']} months sent to {data['username']}")
        logger.info(f"Transaction ID: {data['transaction_id']}")
    else:
        logger.error(f"Premium purchase failed: {result['error']}")


async def buy_stars_example():
    logger.info("Starting Stars purchase example")

    # @bohd4nx - target username, 1000000 - stars amount (integer 50-1000000 (one million))
    result = await buy_stars("@bohd4nx", 1000000)

    if result["success"]:
        data = result["data"]
        logger.info(f"Stars purchase successful: {data['amount']} stars sent to {data['username']}")
        logger.info(f"Transaction ID: {data['transaction_id']}")
    else:
        logger.error(f"Stars purchase failed: {result['error']}")


async def main():
    setup_logging()
    logger.info("Starting Fragment API by @bohd4nx - examples")

    await topup_ton_example()
    await buy_premium_example()
    await buy_stars_example()

    logger.info("All examples completed")


if __name__ == "__main__":
    logger.info("Fragment API by @bohd4nx - Usage Examples")
    logger.info("Supported username formats: @username, username")
    logger.info("Limits: TON minimum 1, Premium 3/6/12 months, Stars minimum 50")
    logger.info("Setup: Copy .env.example to .env and fill all fields")

    asyncio.run(main())
