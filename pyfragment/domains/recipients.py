from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyfragment.enums import ApiError, ApiMethod
from pyfragment.exceptions import (
    AlreadySubscribedError,
    ChannelNotFoundError,
    FragmentAPIError,
    UserNotFoundError,
)
from pyfragment.schemas import RecipientSearch, error_text, has_error

if TYPE_CHECKING:
    from pyfragment.client import FragmentClient


def _recipient_or_raise(result: dict[str, Any], not_found_error: ApiError, not_found: FragmentAPIError) -> str:
    recipient = RecipientSearch.from_response(result).recipient
    if recipient:
        return recipient
    # An error other than "nothing found" (rate limit, expired session, ...) must not pose as a missing recipient.
    if (error := error_text(result)) and not has_error(result, not_found_error):
        raise FragmentAPIError(error)
    raise not_found


async def find_user(client: FragmentClient, method: ApiMethod, page_url: str, data: dict[str, Any], username: str) -> str:
    """Resolve a Telegram user to Fragment's recipient token."""
    result = await client.call(method, data, page_url=page_url)
    if has_error(result, ApiError.ALREADY_SUBSCRIBED):
        raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
    if has_error(result, ApiError.NOT_A_USER):
        raise UserNotFoundError(UserNotFoundError.NOT_A_USER.format(username=username))
    return _recipient_or_raise(
        result, ApiError.NO_USERS_FOUND, UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username))
    )


async def find_channel(client: FragmentClient, method: ApiMethod, page_url: str, data: dict[str, Any], channel: str) -> str:
    """Resolve a Telegram channel to Fragment's recipient token."""
    result = await client.call(method, data, page_url=page_url)
    return _recipient_or_raise(
        result, ApiError.NO_CHANNELS_FOUND, ChannelNotFoundError(ChannelNotFoundError.NOT_FOUND.format(channel=channel))
    )
