"""End-to-end integration test: buy 50 Stars for @bohd4nx.

Requires cookies.json and a valid .env (API_KEY + SEED).
Auto-skipped when cookies are unavailable (e.g. local runs without secrets).
"""

from app.methods.stars import buy_stars


async def test_buy_stars_e2e(cookies):
    result = await buy_stars("@bohd4nx", 50)
    assert result["success"] is True, result.get("error")
    assert result["data"]["transaction_id"]
