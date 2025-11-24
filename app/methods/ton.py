import base64
import logging
import time

import httpx
from tonutils.client import TonapiClient
from tonutils.wallet import WalletV5R1

from app.core.config import Config
from app.utils import TransactionProcessor, WalletLinker, ApiClient, clean_decode

logger = logging.getLogger(__name__)


class FragmentTon:
    def __init__(self):
        config_reader = Config()
        self.config = config_reader.get_config()

        self.headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US,en;q=0.9,uk;q=0.8,ru;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': self.config['cookies'],
            'origin': 'https://fragment.com',
            'referer': 'https://fragment.com/ads/topup',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
            'x-requested-with': 'XMLHttpRequest'
        }

        self.transaction_processor = TransactionProcessor(self.config, clean_decode)
        self.wallet_linker = WalletLinker(self.config, self.headers, self.transaction_processor)
        self.api_client = ApiClient(self.config, self.headers, self.wallet_linker)

    async def _get_account_info(self):
        client = TonapiClient(api_key=self.config['api_key'], is_testnet=False)
        wallet, pub_key, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=self.config['seed'])
        boc = wallet.state_init.serialize().to_boc()

        return {
            "address": wallet.address.to_str(False, False),
            "publicKey": pub_key.hex(),
            "chain": "-239",
            "walletStateInit": base64.b64encode(boc).decode()
        }

    async def topup_ton(self, username, amount):
        if amount < 1 or not isinstance(amount, int):
            return {"success": False, "error": "Amount must be an integer >= 1 TON"}

        account = await self._get_account_info()

        async with httpx.AsyncClient() as client:
            update_data = {"mode": "new", "method": "updateAdsTopupState"}
            await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                              headers=self.headers, data=update_data)

            search_data = {"query": username, "method": "searchAdsTopupRecipient"}
            search_resp = await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                                            headers=self.headers, data=search_data)

            try:
                search_result = search_resp.json()
            except Exception as e:
                logger.error(f"Failed to parse search response: {e}")
                return {"success": False, "error": f"Invalid response from Fragment API: {str(e)}"}

            recipient = search_result.get("found", {}).get("recipient")
            if not recipient:
                return {"success": False, "error": "User not found"}

            init_data = {"recipient": recipient, "amount": amount, "method": "initAdsTopupRequest"}
            init_resp = await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                                          headers=self.headers, data=init_data)

            try:
                init_result = init_resp.json()
            except Exception as e:
                logger.error(f"Failed to parse init response: {e}")
                logger.error(f"Response status: {init_resp.status_code}")
                logger.error(f"Response content: {init_resp.content[:200]}")
                return {"success": False, "error": f"Invalid response from Fragment API: {str(e)}"}

            req_id = init_result.get("req_id")
            if not req_id:
                return {"success": False, "error": "Failed to initialize topup"}

            tx_data = {
                'account': account,
                'device': {"appVersion": "5.4.3", "platform": "iphone",
                           "features": ["SendTransaction", {"maxMessages": 255, "name": "SendTransaction"},
                                        {"types": ["text", "binary", "cell"], "name": "SignData"}],
                           "appName": "Tonkeeper", "maxProtocolVersion": 2},
                'transaction': 1,
                'id': req_id,
                'show_sender': 1,
                'method': 'getAdsTopupLink'
            }

            request_success, transaction_result = await self.api_client.execute_transaction_request(tx_data, account)

            if not request_success:
                return transaction_result

        success, error, tx_hash = await self.transaction_processor.process_transaction(transaction_result)

        if success:
            return {
                "success": True,
                "data": {
                    "transaction_id": tx_hash,
                    "username": username,
                    "amount": amount,
                    "timestamp": int(time.time())
                }
            }

        return {"success": False, "error": error}
