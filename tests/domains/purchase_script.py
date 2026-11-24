"""Scripting the Fragment side of a whole invoice-based purchase."""

from typing import Any

from pyfragment.domains.payments import PurchaseFlow
from tests.support import fixtures
from tests.support.fake_fragment import FakeFragment

INVOICE = fixtures.response("stars_invoice.json")
LINK = fixtures.response("stars_transaction_link.json")
CONFIRM_METHOD: str = LINK["confirm_method"]
CONFIRMED = {"need_update": False}


def script_purchase(
    fragment: FakeFragment,
    flow: PurchaseFlow,
    search: tuple[str, dict[str, Any]],
    confirmed: bool = True,
    replies: dict[str, dict[str, Any] | Exception] | None = None,
) -> None:
    """Every call of the happy path answers; ``replies`` swap the answer of a method, e.g. to make it fail."""
    search_method, search_reply = search
    answers: dict[str, list[dict[str, Any] | Exception]] = {
        search_method: [search_reply],
        flow.state_method: [{}, CONFIRMED if confirmed else {}],
        flow.init_method: [INVOICE],
        flow.link_method: [LINK],
        CONFIRM_METHOD: [{}],
    }
    for method, reply in (replies or {}).items():
        answers[str(method)] = [reply]
    for method, script in answers.items():
        fragment.reply(method, *script)
