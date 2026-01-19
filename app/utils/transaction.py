import logging

from tonutils.client import TonapiClient, ToncenterV3Client
from tonutils.wallet import WalletV5R1
from tonutils.wallet.messages import TransferMessage

from app.core import config

logger = logging.getLogger(__name__)


class TransactionProcessor:
    def __init__(self, clean_decode_func):
        self._clean_decode = clean_decode_func

    @staticmethod
    async def _check_wallet_balance() -> tuple[bool, str | None]:
        client = ToncenterV3Client(is_testnet=False, rps=1, max_retries=1)
        wallet, _, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=config.SEED)

        try:
            balance = await wallet.balance()
        except Exception as exc:
            return False, f"Wallet balance check failed: {exc}"

        try:
            if float(balance) <= 0:
                return False, "Wallet balance is zero"
        except Exception:
            pass

        return True, None

    async def process_transaction(self, transaction_data: dict) -> tuple[bool, str | None, str | None]:
        if "transaction" not in transaction_data or "messages" not in transaction_data["transaction"]:
            return False, "Invalid transaction", None

        ready, reason = await self._check_wallet_balance()
        if not ready:
            return False, reason or "Wallet is not ready", None

        client = TonapiClient(api_key=config.API_KEY, is_testnet=False)
        wallet, _, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=config.SEED)

        try:
            message = transaction_data["transaction"]["messages"][0]
            payload = self._clean_decode(message["payload"])

            messages = [TransferMessage(
                destination=message["address"],
                amount=int(message["amount"]) / 1000000000,
                body=payload
            )]

            tx_hash = await wallet.batch_transfer_messages(messages=messages)
            return True, None, tx_hash
        except Exception as e:
            return False, str(e), None
