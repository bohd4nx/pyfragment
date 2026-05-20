from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


class BaseService:
    def __init__(self, client: FragmentClient) -> None:
        self._client = client
