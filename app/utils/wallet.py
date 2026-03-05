import base64
import json
import logging
from typing import Any

import httpx
from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV5R1

from app.core import config
from app.core.constants import DEVICE
from app.core.exceptions import TransactionError, WalletError
from app.utils.transaction import process_transaction

logger = logging.getLogger(__name__)


async def get_account_info() -> dict[str, Any]:
    try:
        client = ToncenterV3Client(api_key=config.API_KEY, is_testnet=False)
        wallet, pub_key, _, _ = WalletV5R1.from_mnemonic(client=client, mnemonic=config.SEED)
        boc = wallet.state_init.serialize().to_boc()
        return {
            "address":         wallet.address.to_str(False, False),
            "publicKey":       pub_key.hex(),
            "chain":           "-239",
            "walletStateInit": base64.b64encode(boc).decode(),
        }
    except Exception as exc:
        raise WalletError(f"Failed to retrieve wallet account info: {exc}") from exc


async def link_wallet(
    client: httpx.AsyncClient,
    headers: dict,
    cookies: dict,
    account: dict[str, Any],
    fragment_hash: str,
) -> bool:
    resp = await client.post(
        f"https://fragment.com/api?hash={fragment_hash}",
        headers=headers,
        cookies=cookies,
        data={
            "account": json.dumps(account),
            "device":  DEVICE,
            "method": "linkWallet",
        },
    )
    result = resp.json()

    if result.get("ok"):
        return True

    if "transaction" in result:
        try:
            await process_transaction(result)
            return True
        except (TransactionError, WalletError):
            return False

    return False
