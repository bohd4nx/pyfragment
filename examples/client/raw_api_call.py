"""
Example: send a raw request to any Fragment API method.

Use client.call() when you need to access a method that is not yet
wrapped by the library, or to inspect raw API responses directly.

method is an ApiMethod member or any plain method name.
page_url is optional — only set it when the target method belongs to a
specific Fragment page (Fragment derives the API hash per page).
Defaults to the Fragment base URL.

Fragment reports failures as HTTP 200 with an "error" field, so check for it.
"""

import asyncio

from pyfragment import FragmentClient
from pyfragment.enums import ApiMethod, ApiProvider, WalletVersion

SEED = "word1 word2 ... word24"
API_KEY = "YOUR_API_KEY"  # tonconsole.com (tonapi, default) or t.me/toncenter

# Option A: extract cookies directly from your browser (no manual copy-paste needed)
# COOKIES = get_cookies_from_browser("chrome").cookies  # or "firefox", "edge", "brave", ...

# Option B: provide cookies manually
COOKIES = {
    "stel_ssid": "YOUR_STEL_SSID",
    "stel_dt": "YOUR_STEL_DT",
    "stel_token": "YOUR_STEL_TOKEN",
    "stel_ton_token": "YOUR_STEL_TON_TOKEN",
}

METHOD = ApiMethod.SEARCH_STARS_RECIPIENT  # or any Fragment method name as a string
DATA = {"query": "username", "quantity": ""}  # the request payload of that method
PAGE_URL = "https://fragment.com/stars/buy"  # the Fragment page the method belongs to (optional)


async def main() -> None:
    async with FragmentClient(
        seed=SEED,
        api_key=API_KEY,
        cookies=COOKIES,
        wallet_version=WalletVersion.V5R1,  # or V4R2, HighloadV2, HighloadV3R1
        api_provider=ApiProvider.TONAPI,  # or ApiProvider.TONCENTER
    ) as client:
        result = await client.call(METHOD, DATA, page_url=PAGE_URL)
        if error := result.get("error"):
            print(f"Fragment answered with an error: {error}")
        else:
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
