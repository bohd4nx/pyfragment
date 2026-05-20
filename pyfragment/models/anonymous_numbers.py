from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LoginCodeResult:
    number: str
    code: str | None
    active_sessions: int

    def __repr__(self) -> str:
        code_str = f"'{self.code}'" if self.code else "None"
        return f"LoginCodeResult(number='{self.number}', code={code_str}, active_sessions={self.active_sessions})"


@dataclass
class TerminateSessionsResult:
    number: str
    message: str | None

    def __repr__(self) -> str:
        return f"TerminateSessionsResult(number='{self.number}', message={self.message!r})"


__all__ = ["LoginCodeResult", "TerminateSessionsResult"]
