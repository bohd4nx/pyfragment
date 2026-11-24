"""Reading the login code and the session count out of Fragment's number panel."""

import pytest

from pyfragment.domains.anonymous_numbers.parser import parse_login_code

WITH_CODE = """
<table>
  <tr><td class="table-cell-value">12345</td></tr>
  <tr><td>session data</td></tr>
</table>
"""


def test_code_and_one_session_per_row() -> None:
    assert parse_login_code(WITH_CODE) == ("12345", 2)


def test_no_pending_code() -> None:
    assert parse_login_code("<table><tr><td>no code here</td></tr></table>") == (None, 1)


def test_the_code_is_trimmed_and_found_among_other_classes() -> None:
    html = '<tr><td class="x table-cell-value y">  98765 </td></tr>'

    assert parse_login_code(html) == ("98765", 1)


@pytest.mark.parametrize("html", ["", "<div>nothing</div>"])
def test_nothing_to_parse(html: str) -> None:
    assert parse_login_code(html) == (None, 0)
