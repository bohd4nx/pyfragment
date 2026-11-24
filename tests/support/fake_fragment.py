"""A scripted stand-in for Fragment's API: tests say what each method answers and read back what was sent.

It replaces ``FragmentTransport.call`` and ``fetch_page`` of one client, so everything above the transport (domain
functions, validation, error mapping, parsers) runs for real. A method nobody scripted fails the test.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Call:
    method: str
    data: dict[str, Any]
    page_url: str


class FakeFragment:
    def __init__(self) -> None:
        self.calls: list[Call] = []
        self.fetched: list[str] = []
        self._replies: dict[str, list[dict[str, Any] | Exception]] = defaultdict(list)
        self._pages: dict[str, str] = {}

    def reply(self, method: str, *responses: dict[str, Any] | Exception) -> FakeFragment:
        """Script the answers of ``method``, one per call; the last one repeats when the script runs out."""
        self._replies[str(method)].extend(responses)
        return self

    def page(self, url: str, html: str) -> FakeFragment:
        self._pages[url] = html
        return self

    async def call(self, method: str, data: dict[str, Any] | None, page_url: str) -> dict[str, Any]:
        key = str(method)
        self.calls.append(Call(key, dict(data or {}), page_url))
        script = self._replies.get(key)
        if not script:
            raise AssertionError(f"unscripted Fragment call: {key}")
        answer = script.pop(0) if len(script) > 1 else script[0]
        if isinstance(answer, Exception):
            raise answer
        return answer

    async def fetch_page(self, url: str) -> str:
        self.fetched.append(url)
        if url not in self._pages:
            raise AssertionError(f"unscripted Fragment page: {url}")
        return self._pages[url]

    def sent(self, method: str) -> list[Call]:
        """The calls made to ``method``, in order."""
        return [call for call in self.calls if call.method == str(method)]

    @property
    def methods(self) -> list[str]:
        return [call.method for call in self.calls]
