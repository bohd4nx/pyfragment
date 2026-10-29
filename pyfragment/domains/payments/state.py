from __future__ import annotations

import random


def state_nonce() -> str:
    # Fragment accepts a pseudo-random request nonce in state update/poll methods.
    return str(random.randint(100_000_000, 2_147_483_647))
