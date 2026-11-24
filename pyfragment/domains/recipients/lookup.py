from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyfragment.domains.recipients.models import Recipient
from pyfragment.enums import ApiError, ApiMethod
from pyfragment.exceptions import (
    AlreadySubscribedError,
    ChannelNotFoundError,
    FragmentAPIError,
    UserNotFoundError,
)
from pyfragment.schemas import RecipientSearch
from pyfragment.utils.errors import error_text, has_error

if TYPE_CHECKING:
    from pyfragment.client.base import BaseClient


def recipient_or_raise(result: dict[str, Any], query: str, not_found_error: ApiError, not_found: FragmentAPIError) -> Recipient:
    found = RecipientSearch.from_response(result)
    if found.recipient:
        return Recipient(
            recipient=found.recipient,
            username=query,
            name=found.name,
            photo=found.photo,
            myself=found.myself,
        )
    # An error other than "nothing found" (rate limit, expired session, ...) must not pose as a missing recipient.
    if (error := error_text(result)) and not has_error(result, not_found_error):
        raise FragmentAPIError(error)
    raise not_found


async def find_user(client: BaseClient, method: ApiMethod, page_url: str, data: dict[str, Any], username: str) -> Recipient:
    result = await client.call(method, data, page_url=page_url)
    if has_error(result, ApiError.ALREADY_SUBSCRIBED):
        raise AlreadySubscribedError(AlreadySubscribedError.PREMIUM_ACTIVE)
    if has_error(result, ApiError.NOT_A_USER):
        raise UserNotFoundError(UserNotFoundError.NOT_A_USER.format(username=username))
    return recipient_or_raise(
        result,
        username,
        ApiError.NO_USERS_FOUND,
        UserNotFoundError(UserNotFoundError.NOT_FOUND.format(username=username)),
    )


async def find_channel(client: BaseClient, method: ApiMethod, page_url: str, data: dict[str, Any], channel: str) -> Recipient:
    result = await client.call(method, data, page_url=page_url)
    if has_error(result, ApiError.NOT_A_CHANNEL):
        raise ChannelNotFoundError(ChannelNotFoundError.NOT_A_CHANNEL.format(channel=channel))
    return recipient_or_raise(
        result,
        channel,
        ApiError.NO_CHANNELS_FOUND,
        ChannelNotFoundError(ChannelNotFoundError.NOT_FOUND.format(channel=channel)),
    )
