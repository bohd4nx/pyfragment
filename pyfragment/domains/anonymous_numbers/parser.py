from __future__ import annotations

import re

CODE_RE = re.compile(r'class="[^"]*table-cell-value[^"]*"[^>]*>([^<]+)<')
ROW_RE = re.compile(r"<tr[\s>]")


def parse_login_code(html: str) -> tuple[str | None, int]:
    match = CODE_RE.search(html)
    code = match.group(1).strip() if match else None
    active_sessions = len(ROW_RE.findall(html))
    return code, active_sessions
