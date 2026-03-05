import logging
from typing import Any

import httpx

from app.core.exceptions import RequestError, WalletError
from app.utils.wallet import link_wallet

logger = logging.getLogger(__name__)


def parse_json_response(response: httpx.Response, context: str) -> dict[str, Any]:
    try:
        return response.json()
    except Exception as exc:
        raise RequestError(
            f"Fragment API returned an unparseable response for '{context}': {exc}"
        ) from exc


async def execute_transaction_request(
        client: httpx.AsyncClient,
        headers: dict,
        cookies: dict,
        account: dict[str, Any],
        tx_data: dict[str, Any],
        fragment_hash: str,
) -> dict[str, Any]:
    url = f"https://fragment.com/api?hash={fragment_hash}"

    resp = await client.post(url, headers=headers, cookies=cookies, data=tx_data)
    transaction = parse_json_response(resp, tx_data.get("method", "transaction"))

    if transaction.get("need_verify"):
        if not await link_wallet(client, headers, cookies, account, fragment_hash):
            raise WalletError(
                "Failed to link your TON wallet to Fragment. "
                "Make sure the wallet matching your cookies is used."
            )
        resp = await client.post(url, headers=headers, cookies=cookies, data=tx_data)
        transaction = parse_json_response(resp, tx_data.get("method", "transaction"))

    return transaction

