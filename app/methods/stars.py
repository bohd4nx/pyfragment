import base64
import logging
import time

import httpx
from tonutils.client import TonapiClient
from tonutils.wallet import WalletV5R1

from app.core import config
from app.utils import (
    TransactionProcessor,
    WalletLinker,
    ApiClient,
    clean_decode,
    parse_json_response,
    load_cookies,
    get_fragment_hash,
)

logger = logging.getLogger(__name__)


class FragmentStars:
    def __init__(self):
        self.headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,uk;q=0.8,ru;q=0.7",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://fragment.com",
            "referer": "https://fragment.com/stars/buy",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            "x-requested-with": "XMLHttpRequest",
        }

        self.cookies = load_cookies()

        self.transaction_processor = TransactionProcessor(clean_decode)
        self.wallet_linker = WalletLinker(self.headers, self.cookies, self.transaction_processor)
        self.api_client = ApiClient(self.headers, self.cookies, self.wallet_linker)

    @staticmethod
    async def _get_account_info():
        client = TonapiClient(api_key=config.API_KEY, is_testnet=False)
        wallet, pub_key, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=config.SEED)
        boc = wallet.state_init.serialize().to_boc()

        return {
            "address": wallet.address.to_str(False, False),
            "publicKey": pub_key.hex(),
            "chain": "-239",
            "walletStateInit": base64.b64encode(boc).decode()
        }

    async def buy_stars(self, username, amount):
        if amount < 50 or not isinstance(amount, int):
            return {"success": False, "error": "Amount must be an integer >= 50 stars"}

        fragment_hash = await get_fragment_hash(
            self.cookies,
            self.headers,
            "https://fragment.com/stars/buy",
        )
        if not fragment_hash:
            raise RuntimeError("Failed to fetch Fragment hash")

        account = await self._get_account_info()

        async with httpx.AsyncClient() as client:
            search_data = {"query": username, "quantity": "", "method": "searchStarsRecipient"}
            search_resp = await client.post(f"https://fragment.com/api?hash={fragment_hash}",
                                            headers=self.headers, cookies=self.cookies, data=search_data)

            search_result, error = parse_json_response(search_resp, logger, "search")
            if search_result is None:
                return {"success": False, "error": f"Invalid response from Fragment API: {error}"}

            recipient = search_result.get("found", {}).get("recipient")
            if not recipient:
                return {"success": False, "error": "User not found"}

            init_data = {"recipient": recipient, "quantity": amount, "method": "initBuyStarsRequest"}
            init_resp = await client.post(f"https://fragment.com/api?hash={fragment_hash}",
                                          headers=self.headers, cookies=self.cookies, data=init_data)

            init_result, error = parse_json_response(init_resp, logger, "init")
            if init_result is None:
                return {"success": False, "error": f"Invalid response from Fragment API: {error}"}

            req_id = init_result.get("req_id")
            if not req_id:
                return {"success": False, "error": "Failed to initialize purchase"}

            tx_data = {
                'account': account,
                'device': "iPhone15,2",
                'transaction': 1,
                'id': req_id,
                'show_sender': 0,
                'method': 'getBuyStarsLink'
            }

            request_success, transaction_result = await self.api_client.execute_transaction_request(
                tx_data,
                account,
                fragment_hash,
            )

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
