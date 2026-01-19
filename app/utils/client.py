import logging
from typing import Any

import httpx


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
    def __init__(self, headers: dict, cookies: dict, wallet_linker):
        self.headers = headers
        self.cookies = cookies
        self.wallet_linker = wallet_linker

    async def execute_transaction_request(
            self,
            tx_data: dict[str, Any],
            account: dict[str, Any],
            fragment_hash: str,
    ) -> tuple[bool, dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            tx_resp = await client.post(f"https://fragment.com/api?hash={fragment_hash}",
                                        headers=self.headers, cookies=self.cookies, data=tx_data)
            transaction, error = parse_json_response(tx_resp, logging.getLogger(__name__), "transaction")
            if transaction is None:
                return False, {"success": False, "error": f"Invalid response from Fragment API: {error}"}

            if transaction.get("need_verify"):
                if not await self.wallet_linker.link_wallet(account, fragment_hash):
                    return False, {"success": False, "error": "Failed to link wallet"}

                tx_resp = await client.post(f"https://fragment.com/api?hash={fragment_hash}",
                                            headers=self.headers, cookies=self.cookies, data=tx_data)
                transaction, error = parse_json_response(tx_resp, logging.getLogger(__name__), "transaction")
                if transaction is None:
                    return False, {"success": False, "error": f"Invalid response from Fragment API: {error}"}

            return True, transaction
