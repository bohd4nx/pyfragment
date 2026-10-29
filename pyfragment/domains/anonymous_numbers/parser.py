from __future__ import annotations

import re

# Login code sits in a table cell styled with "table-cell-value".
_CODE_RE = re.compile(r'class="[^"]*table-cell-value[^"]*"[^>]*>([^<]+)<')
# Each active session is one <tr> row in the sessions table.
_ROW_RE = re.compile(r"<tr[\s>]")


def parse_login_code(html: str) -> tuple[str | None, int]:
    match = _CODE_RE.search(html)
    code = match.group(1).strip() if match else None
    active_sessions = len(_ROW_RE.findall(html))
    return code, active_sessions
