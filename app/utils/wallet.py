from typing import Any

import httpx


class WalletLinker:
    def __init__(self, headers: dict, cookies: dict, transaction_processor):
        self.headers = headers
        self.cookies = cookies
        self.transaction_processor = transaction_processor

    async def link_wallet(self, account: dict[str, Any], fragment_hash: str) -> bool:
        async with httpx.AsyncClient() as client:
            data = {
                'account': account,
                'device': "iPhone15,2",
                'method': 'linkWallet'
            }

            response = await client.post(f"https://fragment.com/api?hash={fragment_hash}",
                                         headers=self.headers, cookies=self.cookies, data=data)
            result = response.json()

            if result.get("ok"):
                return True

            if "transaction" in result:
                success, _, _ = await self.transaction_processor.process_transaction(result)
                return success

            return False
