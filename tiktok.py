# ============================================================
# tiktok.py
# ============================================================
# Scrapes follower counts from public TikTok profile pages.
#
# METHOD:
#   Loads the TikTok profile page with Playwright and extracts
#   the follower count from the embedded __UNIVERSAL_DATA__
#   JSON blob that TikTok injects into every profile page.
#   Falls back to parsing the <meta> description tag if the
#   JSON blob is not found.
#
# NO LOGIN REQUIRED — works on public profiles without cookies.
#
# STANDALONE TEST:
#   Edit TEST_URL at the bottom and run:  python tiktok.py
#   A visible browser window will open so you can confirm the
#   page loaded correctly. Press Enter to close.
# ============================================================

import re
import json
import time
import random

from playwright.sync_api import sync_playwright


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def _parse_count_string(text: str) -> str | None:
    """
    Converts TikTok's abbreviated count strings to plain integers.

    TikTok displays follower counts in two ways depending on size:
      - Abbreviated : "1.2M Followers", "45.6K Followers"
      - Full number : "1234567 Followers"

    This function handles both formats and returns a plain integer
    string (e.g. "1200000") suitable for writing to the CSV.

    Returns None if no recognisable number is found.
    """
    if not text:
        return None

    text = text.strip()

    # Match patterns like "1.2M", "45.6K", "3.1B" or plain integers
    match = re.search(r"([\d,]+\.?\d*)\s*([KkMmBb]?)\s*[Ff]ollower", text)
    if not match:
        # Try without the "Follower" suffix — sometimes it's just the number
        match = re.search(r"([\d,]+\.?\d*)\s*([KkMmBb]?)", text)
    if not match:
        return None

    number_str = match.group(1).replace(",", "")
    suffix     = match.group(2).upper()

    try:
        number = float(number_str)
    except ValueError:
        return None

    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    number = int(number * multipliers.get(suffix, 1))

    return str(number)


def _extract_from_universal_data(html: str) -> str | None:
    """
    TikTok injects a __UNIVERSAL_DATA__ JSON object into every
    profile page. It contains the full user stats including the
    exact follower count as an integer.

    This is the most reliable extraction method because it uses
    structured data rather than fragile HTML/regex patterns.
    """
    match = re.search(
        r'<script[^>]*id=["\']__UNIVERSAL_DATA__["\'][^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    if not match:
        # Also try the window.__UNIVERSAL_DATA__ assignment form
        match = re.search(
            r'window\.__UNIVERSAL_DATA__\s*=\s*(\{.*?\});\s*</script>',
            html, re.DOTALL
        )
    if not match:
        return None

    try:
        data = json.loads(match.group(1))
    except (json.JSONDecodeError, IndexError):
        return None

    # Navigate the nested structure:
    # __DEFAULT_SCOPE__ -> webapp.user-detail -> userInfo -> stats -> followerCount
    try:
        scope     = data.get("__DEFAULT_SCOPE__", {})
        user_data = scope.get("webapp.user-detail", {})
        stats     = user_data["userInfo"]["stats"]
        count     = stats.get("followerCount")
        if count is not None:
            return str(int(count))
    except (KeyError, TypeError):
        pass

    # Fallback: recursively search for "followerCount" anywhere in the blob
    return _recursive_find(data, "followerCount")


def _recursive_find(obj, key: str) -> str | None:
    """Walk a nested dict/list and return the first value for `key`."""
    if isinstance(obj, dict):
        if key in obj:
            return str(obj[key])
        for v in obj.values():
            result = _recursive_find(v, key)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _recursive_find(item, key)
            if result is not None:
                return result
    return None


def _extract_from_meta(html: str) -> str | None:
    """
    Fallback: parse the <meta name="description"> tag.

    TikTok's meta description typically reads:
      "45.6K Followers, 123 Following, 1.2M Likes - Watch awesome..."
    """
    match = re.search(
        r'<meta\s+name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
        html, re.IGNORECASE
    )
    if match:
        return _parse_count_string(match.group(1))

    # Also try og:description
    match = re.search(
        r'<meta\s+property=["\']og:description["\'][^>]*content=["\']([^"\']*)["\']',
        html, re.IGNORECASE
    )
    if match:
        return _parse_count_string(match.group(1))

    return None


# ------------------------------------------------------------
# MAIN SCRAPER FUNCTION
# ------------------------------------------------------------

def get_tiktok_followers(url: str, page) -> str | None:
    """
    Fetches the follower count for a TikTok profile.

    Parameters
    ----------
    url  : Full TikTok profile URL, e.g. https://www.tiktok.com/@username
    page : A Playwright Page object (passed in from main.py)

    Returns
    -------
    Follower count as a plain integer string (e.g. "1200000"),
    or None if the count could not be extracted.
    """
    url = url.strip()
    if not url:
        return None

    # Normalise URL — ensure it has a scheme
    if not url.startswith("http"):
        url = "https://" + url

    print(f"    [TikTok] Visiting: {url}")

    try:
        # TikTok aggressively detects and blocks headless browsers.
        # Waiting for 'networkidle' gives scripts time to inject
        # the __UNIVERSAL_DATA__ blob before we grab the HTML.
        page.goto(url, wait_until="networkidle", timeout=30_000)
        time.sleep(random.uniform(2, 3))   # let JS finish rendering
        html = page.content()
    except Exception as e:
        print(f"    [TikTok ERROR] Failed to load page: {e}")
        return None

    # --- Strategy 1: structured JSON blob (most reliable) ---
    count = _extract_from_universal_data(html)
    if count:
        print(f"    [TikTok] Found via JSON blob: {count}")
        return count

    # --- Strategy 2: meta description tag (fallback) ---
    count = _extract_from_meta(html)
    if count:
        print(f"    [TikTok] Found via meta tag: {count}")
        return count

    # --- Nothing worked ---
    print(f"    [TikTok WARN] Could not extract follower count for: {url}")
    print(f"    [TikTok WARN] TikTok may be blocking the headless browser.")
    return None


# ------------------------------------------------------------
# STANDALONE TEST
# (Edit TEST_URL and run:  python tiktok.py)
# ------------------------------------------------------------

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    TEST_URL = "https://www.tiktok.com/@lions.international"

    with sync_playwright() as p:
        # Visible browser so you can confirm the page loaded correctly
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = context.new_page()

        result = get_tiktok_followers(TEST_URL, page)
        print(f"\nResult: {result}")

        input("\nPress Enter to close the browser...")
        browser.close()