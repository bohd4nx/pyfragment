from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from tonutils.contracts.wallet import ExternalMessage, TONTransferBuilder

from pyfragment.domains.wallet.models import TransferIntent
from pyfragment.enums import PaymentMethod
from pyfragment.utils.ton import body_comment, decode_boc
from pyfragment.utils.transaction import deadline, extract_message, parse_destination, unsigned_int

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


@dataclass(frozen=True)
class TransferRequest:
    """One Fragment payment waiting to be signed, alone or together with others, into an external message."""

    builder: TONTransferBuilder
    destination: str
    amount_nano: int
    comment: str | None
    payment_method: PaymentMethod
    req_id: str | None
    deadline: int | None  # Fragment's own validUntil for the invoice
    on_prepared: Callable[[TransferIntent], Awaitable[None]] | None

    def intent(self, external: ExternalMessage, valid_until: int) -> TransferIntent:
        return TransferIntent(
            msg_hash=str(external.normalized_hash),
            boc=external.as_b64,
            destination=self.destination,
            amount_nano=self.amount_nano,
            comment=self.comment,
            payment_method=self.payment_method,
            req_id=self.req_id,
            valid_until=valid_until,
        )


async def process_transaction(
    client: BaseClient,
    transaction_data: dict[str, Any],
    payment_method: PaymentMethod = PaymentMethod.GRAM,
    req_id: str | None = None,
) -> TransferIntent:
    """Sign and send Fragment's transaction from the wallet, once.

    Payments queued together go out in one message and share its ``msg_hash`` and ``boc``.
    """
    message = extract_message(transaction_data)
    amount_nano = unsigned_int(message.get("amount"))
    body = decode_boc(message.get("payload"))

    request = TransferRequest(
        builder=TONTransferBuilder(destination=parse_destination(message), amount=amount_nano, body=body),
        destination=str(message["address"]),
        amount_nano=amount_nano,
        comment=body_comment(body),
        payment_method=payment_method,
        req_id=req_id,
        deadline=deadline(transaction_data),
        on_prepared=client.on_transfer_prepared,
    )
    return await client.ton_wallet.transfer(request)
