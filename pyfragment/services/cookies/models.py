from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CookieResult:
    cookies: dict[str, str]
    expires: str | None

    def __repr__(self) -> str:
        return f"CookieResult(cookies={self.cookies!r}, expires={self.expires!r})"
