from typing import Dict, Any

import httpx


class WalletLinker:
    def __init__(self, config: dict, headers: dict, transaction_processor):
        self.config = config
        self.headers = headers
        self.transaction_processor = transaction_processor

    async def link_wallet(self, account: Dict[str, Any]) -> bool:
        async with httpx.AsyncClient() as client:
            data = {
                'account': account,
                'device': "iPhone15,2",
                'method': 'linkWallet'
            }

            response = await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                                         headers=self.headers, data=data)
            result = response.json()

            if result.get("ok"):
                return True

            if "transaction" in result:
                success, _, _ = await self.transaction_processor.process_transaction(result)
                return success

            return False
