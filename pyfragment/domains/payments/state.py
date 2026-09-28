from __future__ import annotations

import random
from typing import Any

from pyfragment.enums import StateMode


def state_nonce() -> str:
    # Fragment accepts a pseudo-random request nonce in state update/poll methods.
    return str(random.randint(100_000_000, 2_147_483_647))


def new_state_params(**extra: Any) -> dict[str, Any]:
    """Parameters of the ``update*State`` call Fragment's frontend makes when a purchase page opens."""
    return {"mode": StateMode.NEW, "lv": "false", "dh": state_nonce(), **extra}
