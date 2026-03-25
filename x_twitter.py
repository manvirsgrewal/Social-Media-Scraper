# ============================================================
# x_twitter.py
# ============================================================
# Scrapes X (Twitter) follower counts using Playwright.
# No login required for most public profiles.
#
# Imported by: main.py
#
# WHY PLAYWRIGHT:
#   X renders all page content via JavaScript. A plain HTTP
#   request only gets an empty HTML shell — the follower count
#   never appears. Playwright runs a real browser so the
#   JavaScript executes and the count becomes visible.
#
# STANDALONE TEST:
#   Edit TEST_URL at the bottom, then run:
#   python x_twitter.py
# ============================================================

import re
from playwright.sync_api import sync_playwright

# parse_shorthand() converts "89.7M" -> 89700000
from utils import parse_shorthand


# ------------------------------------------------------------
# FOLLOWER COUNT EXTRACTION
# ------------------------------------------------------------

def get_x_followers(url, page):
    """
    Loads an X profile using Playwright and extracts the
    follower count.

    X renders its follower link with href="/username/verified_followers"
    (not just "/followers"), so both selectors are tried.
    Falls back to a JSON blob in the page source if needed.
    """
    if not url:
        return None

    try:
        page.goto(url.strip(), timeout=20000)
        page.wait_for_timeout(4000)

        # Method 1: anchor tag linking to follower pages
        # X uses /verified_followers in the DOM (not just /followers)
        selectors = [
            "a[href$='/verified_followers'] span",
            "a[href$='/followers'] span",
        ]
        for selector in selectors:
            try:
                el   = page.locator(selector).first
                text = el.inner_text(timeout=5000)
                if text:
                    return parse_shorthand(text)
            except Exception:
                continue

        # Method 2: JSON blob embedded in page source
        # X stores: "followers_count":89700000
        content = page.content()
        match = re.search(r'"followers_count"\s*:\s*(\d+)', content)
        if match:
            return int(match.group(1))

        print(f"  [X WARN] No follower count found for: {url}")

    except Exception as e:
        print(f"  [X ERROR] {e}")

    return None


# ============================================================
# STANDALONE TEST
# ============================================================
# Edit TEST_URL below to test any X profile.
# Run with:  python x_twitter.py
#
# headless=False opens a visible browser window so you can
# see exactly what loads — useful for debugging login walls.
# ============================================================

if __name__ == "__main__":
    TEST_URL = "https://x.com/NASA"

    print("Testing X scraper...")
    print(f"URL: {TEST_URL}\n")

    with sync_playwright() as p:
        # headless=False so you can visually confirm what the browser loads
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

        page.goto(TEST_URL, timeout=20000)
        page.wait_for_timeout(4000)

        current_url = page.url
        print(f"Final URL after load: {current_url}")

        # Check if X redirected to a login wall
        if "login" in current_url or "i/flow" in current_url:
            print("  !! X redirected to login page.")
            print("  Some profiles require login to view counts.")
        else:
            # DEBUG: print raw HTML snippets containing "followers"
            content  = page.content()
            snippets = re.findall(r'.{0,80}followers.{0,80}', content, re.IGNORECASE)
            print("Raw HTML snippets containing 'followers':")
            for s in snippets[:5]:
                print(f"  {s.strip()}")
            print()

            count = get_x_followers(TEST_URL, page)
            print(f"Followers: {count}")

        input("\nPress Enter to close the browser...")
        browser.close()