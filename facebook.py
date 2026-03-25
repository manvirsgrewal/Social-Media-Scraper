# ============================================================
# facebook.py
# ============================================================
# Scrapes Facebook page follower counts using Playwright.
# No login required — works on public pages.
#
# Imported by: main.py
#
# STANDALONE TEST:
#   Edit TEST_URL at the bottom, then run:
#   python facebook.py
# ============================================================

import re
from playwright.sync_api import sync_playwright

# parse_shorthand() converts "26M" -> 26000000, "1.6K" -> 1600
from utils import parse_shorthand


# ------------------------------------------------------------
# FOLLOWER COUNT EXTRACTION
# ------------------------------------------------------------

def get_facebook_followers(url, page):
    """
    Loads a Facebook page using Playwright and tries multiple
    methods to extract the follower count.

    Multiple methods are needed because Facebook's HTML structure
    varies by page type (business page, group, personal page, etc.)
    and numbers may appear as shorthand (26M) or full integers.
    """
    if not url:
        return None

    try:
        # Use desktop Facebook — Playwright handles JS-rendered content
        url = url.strip().replace("m.facebook.com", "www.facebook.com")
        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)

        content = page.content()

        # Method 1: JSON blob embedded in page source
        # Facebook stores: "text":"26M followers"
        match = re.search(
            r'"text"\s*:\s*"([\d.,]+[KMBkmb]?)\s+followers"',
            content, re.IGNORECASE
        )
        if match:
            return parse_shorthand(match.group(1))

        # Method 2: visible HTML — <strong>26M</strong> followers
        match2 = re.search(
            r'<strong[^>]*>([\d.,]+[KMBkmb]?)</strong>\s*followers',
            content, re.IGNORECASE
        )
        if match2:
            return parse_shorthand(match2.group(1))

        # Method 3: JSON integer — "followers_count":26000000
        match3 = re.search(r'"followers_count"\s*:\s*(\d+)', content)
        if match3:
            return int(match3.group(1))

        # Method 4: plain text — "26M people follow" or "26M followers"
        match4 = re.search(
            r'([\d,.]+[KMBkmb]?)\s+(?:people follow|followers)',
            content, re.IGNORECASE
        )
        if match4:
            return parse_shorthand(match4.group(1))

        # Method 5: visible span elements containing "followers"
        try:
            els = page.locator("span:has-text('followers')").all()
            for el in els:
                text = el.inner_text()
                m = re.search(r'([\d,.]+[KMBkmb]?)\s+followers', text, re.IGNORECASE)
                if m:
                    return parse_shorthand(m.group(1))
        except Exception:
            pass

        print(f"  [Facebook WARN] No follower count found for: {url}")

    except Exception as e:
        print(f"  [Facebook ERROR] {e}")

    return None


# ============================================================
# STANDALONE TEST
# ============================================================
# Edit TEST_URL below to test any Facebook page.
# Run with:  python facebook.py
# ============================================================

if __name__ == "__main__":
    TEST_URL = "https://www.facebook.com/nasa"

    print("Testing Facebook scraper...")
    print(f"URL: {TEST_URL}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

        page.goto(TEST_URL, timeout=20000)
        page.wait_for_timeout(3000)
        content = page.content()

        # DEBUG: show raw HTML snippets containing "followers"
        # Useful for diagnosing why a page isn't returning a count
        snippets = re.findall(r'.{0,80}followers.{0,80}', content, re.IGNORECASE)
        print("Raw HTML snippets containing 'followers':")
        for s in snippets[:5]:
            print(f"  {s.strip()}")
        print()

        count = get_facebook_followers(TEST_URL, page)
        print(f"Followers: {count}")

        browser.close()