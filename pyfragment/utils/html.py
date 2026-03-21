import re

# Matches the login code inside a table-cell-value element.
CODE_RE = re.compile(r'class="[^"]*table-cell-value[^"]*"[^>]*>([^<]+)<')
# Counts active session rows in the HTML table.
ROW_RE = re.compile(r"<tr[\s>]")


def parse_login_code(html: str) -> tuple[str | None, int]:
    """Extract the pending login code and active session count from a Fragment numbers page HTML snippet.

    Args:
        html: Raw HTML string returned by the Fragment API.

    Returns:
        A tuple of ``(code, active_sessions)`` where ``code`` is ``None`` if no
        pending code is present, and ``active_sessions`` is the number of ``<tr>``
        rows found (each row represents one active session).
    """
    match = CODE_RE.search(html)
    code = match.group(1).strip() if match else None
    active_sessions = len(ROW_RE.findall(html))
    return code, active_sessions
