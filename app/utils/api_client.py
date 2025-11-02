from typing import Dict, Any, Tuple

import httpx


class ApiClient:
    def __init__(self, config: dict, headers: dict, wallet_linker):
        self.config = config
        self.headers = headers
        self.wallet_linker = wallet_linker

    async def execute_transaction_request(self, tx_data: Dict[str, Any], account: Dict[str, Any]) -> Tuple[
        bool, Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            tx_resp = await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                                        headers=self.headers, data=tx_data)
            transaction = tx_resp.json()

            if transaction.get("need_verify"):
                if not await self.wallet_linker.link_wallet(account):
                    return False, {"success": False, "error": "Failed to link wallet"}

                tx_resp = await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                                            headers=self.headers, data=tx_data)
                transaction = tx_resp.json()

            return True, transaction
