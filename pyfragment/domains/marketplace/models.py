from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class UsernamesResult:
    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return f"UsernamesResult(items={len(self.items)}, next_offset_id={self.next_offset_id!r})"


@dataclass
class NumbersResult:
    items: list[dict[str, Any]]
    next_offset_id: str | None

    def __repr__(self) -> str:
        return f"NumbersResult(items={len(self.items)}, next_offset_id={self.next_offset_id!r})"


@dataclass
class GiftsResult:
    items: list[dict[str, Any]]
    next_offset: int | None

    def __repr__(self) -> str:
        return f"GiftsResult(items={len(self.items)}, next_offset={self.next_offset!r})"


__all__ = ["GiftsResult", "NumbersResult", "UsernamesResult"]
