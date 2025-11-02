import base64
import logging
import re
import string
import time

import httpx
from tonutils.client import TonapiClient
from tonutils.wallet import WalletV5R1

from app.core.config import Config
from app.utils import TransactionProcessor, WalletLinker, ApiClient

logger = logging.getLogger(__name__)


class FragmentPremium:
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
            'referer': 'https://fragment.com/premium/buy',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
            'x-requested-with': 'XMLHttpRequest'
        }

        self.transaction_processor = TransactionProcessor(self.config, self._clean_decode)
        self.wallet_linker = WalletLinker(self.config, self.headers, self.transaction_processor)
        self.api_client = ApiClient(self.config, self.headers, self.wallet_linker)

    @staticmethod
    def _clean_decode(s):
        b = base64.b64decode(re.sub(r'[^A-Za-z0-9+/=]', '', s.strip()) + "=" * (-len(s) % 4))
        t = next(
            (b[i:].decode('utf-8', 'ignore') for i in range(20) if
             b[i:].decode('utf-8', 'ignore').startswith("Telegram Premium")),
            b.decode('utf-8', 'ignore')
        )
        return ''.join(c for c in t if c in string.printable or c in '\n\r\t ').strip()

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

    async def buy_premium(self, username, months):
        if months not in [3, 6, 12]:
            return {"success": False, "error": "Invalid duration. Use 3, 6, or 12 months"}

        account = await self._get_account_info()

        async with httpx.AsyncClient() as client:
            search_data = {"query": username, "months": months, "method": "searchPremiumGiftRecipient"}
            search_resp = await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                                            headers=self.headers, data=search_data)
            search_result = search_resp.json()

            recipient = search_result.get("found", {}).get("recipient")
            if not recipient:
                return {"success": False, "error": "User not found"}

            update_data = {"mode": "new", "lv": "false", "dh": str(int(time.time())), "method": "updatePremiumState"}
            await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                              headers=self.headers, data=update_data)

            init_data = {"recipient": recipient, "months": months, "method": "initGiftPremiumRequest"}
            init_resp = await client.post(f"https://fragment.com/api?hash={self.config['hash']}",
                                          headers=self.headers, data=init_data)
            init_result = init_resp.json()

            req_id = init_result.get("req_id")
            if not req_id:
                return {"success": False, "error": "Failed to initialize purchase"}

            tx_data = {
                'account': account,
                'device': {"appVersion": "5.4.3", "platform": "iphone",
                           "features": ["SendTransaction", {"maxMessages": 255, "name": "SendTransaction"},
                                        {"types": ["text", "binary", "cell"], "name": "SignData"}],
                           "appName": "Tonkeeper", "maxProtocolVersion": 2},
                'transaction': 1,
                'id': req_id,
                'show_sender': 1,
                'ref': "OprzztcdJ",
                'method': 'getGiftPremiumLink'
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
                    "months": months,
                    "timestamp": int(time.time())
                }
            }

        return {"success": False, "error": error}
