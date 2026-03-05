import logging

from tonutils.clients import ToncenterClient
from tonutils.contracts.wallet import WalletV5R1

from app.core import config
from app.core.exceptions import TransactionError, WalletError
from app.utils.decoder import clean_decode

logger = logging.getLogger(__name__)


async def process_transaction(transaction_data: dict) -> str:
    logger.debug("transaction_data: %s", transaction_data)

    if "transaction" not in transaction_data or "messages" not in transaction_data["transaction"]:
        raise TransactionError(
            "Fragment returned an invalid transaction payload. "
            "The API response is missing expected 'transaction.messages' data."
        )

    client = ToncenterClient(api_key=config.API_KEY)
    wallet, _, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=config.SEED)

    # Check balance before broadcasting
    try:
        await wallet.refresh()
        balance_ton = wallet.balance / 1_000_000_000
        if balance_ton < 0.056:
            raise WalletError(
                f"TON wallet balance is too low: {balance_ton:.2f} TON. "
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

