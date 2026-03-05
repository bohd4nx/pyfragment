import logging

from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV5R1

from app.core import config
from app.core.exceptions import TransactionError, WalletError
from app.utils.decoder import clean_decode

logger = logging.getLogger(__name__)


async def process_transaction(transaction_data: dict) -> str:
    if "transaction" not in transaction_data or "messages" not in transaction_data["transaction"]:
        raise TransactionError(
            "Fragment returned an invalid transaction payload. "
            "The API response is missing expected 'transaction.messages' data."
        )

    client = ToncenterV3Client(api_key=config.API_KEY, is_testnet=False)
    wallet, _, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=config.SEED)

    # Check balance before broadcasting
    try:
        balance = await wallet.balance()
        if float(balance) < 0.056:
            raise WalletError(
                f"TON wallet balance is too low: {balance} TON. "
                "Minimum required is 0.056 TON."
            )
    except WalletError:
        raise
    except Exception as exc:
        raise WalletError(f"Wallet balance check failed: {exc}") from exc

    try:
        message = transaction_data["transaction"]["messages"][0]
        payload = clean_decode(message["payload"])

        return await wallet.transfer(
            destination=message["address"],
            amount=int(message["amount"]) / 1_000_000_000,
            body=payload,
        )
    except (WalletError, TransactionError):
        raise
    except Exception as exc:
        raise TransactionError(f"Transaction broadcast failed: {exc}") from exc

