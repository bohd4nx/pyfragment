from typing import Any
import logging

import httpx

from app.core import config


def parse_json_response(
    response: httpx.Response,
    logger: logging.Logger,
    context: str,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return response.json(), None
    except Exception as e:
        logger.error(f"Failed to parse {context} response: {e}")
        logger.error(f"Response content: {response.content[:200]}")
        return None, str(e)


class ApiClient:
    def __init__(self, headers: dict, wallet_linker):
        self.headers = headers
        self.wallet_linker = wallet_linker

    async def execute_transaction_request(
            self,
            tx_data: dict[str, Any],
            account: dict[str, Any],
    ) -> tuple[bool, dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            tx_resp = await client.post(f"https://fragment.com/api?hash={config.HASH}",
                                        headers=self.headers, data=tx_data)
            transaction = tx_resp.json()

            if transaction.get("need_verify"):
                if not await self.wallet_linker.link_wallet(account):
                    return False, {"success": False, "error": "Failed to link wallet"}

                tx_resp = await client.post(f"https://fragment.com/api?hash={config.HASH}",
                                            headers=self.headers, data=tx_data)
                transaction = tx_resp.json()

            return True, transaction
