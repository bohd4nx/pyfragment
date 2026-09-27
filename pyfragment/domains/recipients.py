from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyfragment.enums import ApiError, ApiMethod
from pyfragment.exceptions import ChannelNotFoundError, UserNotFoundError
from pyfragment.schemas import RecipientSearch, has_error

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


async def find_user(client: FragmentClient, method: ApiMethod, page_url: str, data: dict[str, Any], username: str) -> str:
    """Resolve a Telegram user to Fragment's recipient token."""
    result = await client.call(method, data, page_url=page_url)
    if has_error(result, ApiError.NOT_A_USER):
        raise UserNotFoundError(UserNotFoundError.NOT_A_USER.format(username=username))
    recipient = RecipientSearch.from_response(result).recipient
    if not recipient:
        raise UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))
    return recipient


async def find_channel(client: FragmentClient, method: ApiMethod, page_url: str, data: dict[str, Any], channel: str) -> str:
    """Resolve a Telegram channel to Fragment's recipient token."""
    result = await client.call(method, data, page_url=page_url)
    recipient = RecipientSearch.from_response(result).recipient
    if not recipient:
        raise ChannelNotFoundError(ChannelNotFoundError.NOT_FOUND.format(channel=channel))
    return recipient
