"""
Example: extract Fragment cookies directly from your browser.

get_cookies_from_browser() reads the Fragment session cookies from a locally
installed browser — no manual copy-paste required.

Supported browsers: arc, brave, chrome, chromium, chromium_based, edge,
                    firefox, firefox_based, librewolf, opera, opera_gx,
                    safari, vivaldi.

The returned CookieResult.cookies dict can be passed directly to FragmentClient.
"""

from pyfragment import CookieError, get_cookies_from_browser


def main() -> None:
    try:
        result = get_cookies_from_browser("chrome")  # or "firefox", "edge", "brave", ...
    except CookieError as e:
        print(f"Could not read cookies: {e}")
        return

    print(f"Cookies expire: {result.expires}")
    print(f"Keys found: {list(result.cookies.keys())}")

    # Pass the extracted cookies directly to FragmentClient
    # async with FragmentClient(seed=SEED, api_key=API_KEY, cookies=result.cookies) as client:
    #     ...


if __name__ == "__main__":
    main()
