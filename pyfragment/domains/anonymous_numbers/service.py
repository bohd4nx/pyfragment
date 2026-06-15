from __future__ import annotations

from typing import TYPE_CHECKING

from pyfragment.domains.anonymous_numbers.number import get_login_code, terminate_sessions, toggle_login_codes
from pyfragment.domains.base import BaseService
from pyfragment.domains.anonymous_numbers.models import LoginCodeResult, TerminateSessionsResult

if TYPE_CHECKING:
    pass


class AnonymousNumbersService(BaseService):
    async def get_login_code(self, number: str) -> LoginCodeResult:
        return await get_login_code(self._client, number)

    async def toggle_login_codes(self, number: str, can_receive: bool) -> None:
        return await toggle_login_codes(self._client, number, can_receive)

    async def terminate_sessions(self, number: str) -> TerminateSessionsResult:
        return await terminate_sessions(self._client, number)
