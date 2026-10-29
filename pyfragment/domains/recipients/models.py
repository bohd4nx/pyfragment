from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recipient:
    """A Telegram user or channel Fragment found for a purchase."""

    recipient: str  # Fragment's recipient token
    username: str  # the query as passed by the caller
    name: str | None  # display name
    photo: str | None  # avatar, as the HTML <img> tag Fragment renders
    myself: bool  # the recipient is the account the Fragment session belongs to

    def __repr__(self) -> str:
        return f"Recipient(username='{self.username}', name={self.name!r}, myself={self.myself})"
