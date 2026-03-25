# ============================================================
# linkedin.py
# ============================================================
# Scrapes LinkedIn company/school follower counts using Playwright.
#
# Imported by: main.py
# Requires:    linkedin_cookies.json (see FIRST TIME SETUP below)
#
# FIRST TIME SETUP:
#   LinkedIn requires login to reliably show follower counts.
#   You only need to do this once (or when cookies expire):
#       python linkedin_login_save.py
#   This opens a browser, you log in, and saves your session
#   to linkedin_cookies.json. Sessions last ~2-4 weeks.
#
#   Without cookies ~80% of pages work.
#   With cookies ~95%+ of pages work.
#
# STANDALONE TEST:
#   Edit TEST_URL at the bottom, then run:
#   python linkedin.py
# ============================================================

import re
import os
from playwright.sync_api import sync_playwright
from utils import parse_shorthand

# Cookie file path — use absolute path so it always resolves
# correctly regardless of which directory you run the script from
SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
LINKEDIN_COOKIES = os.path.join(SCRIPT_DIR, "linkedin_cookies.json")


# ------------------------------------------------------------
# URL CLEANING
# ------------------------------------------------------------

def clean_linkedin_url(url):
    """
    Normalizes a LinkedIn URL to the base company/school page.

    Problems in CSV data this fixes:
      - /posts/?feedView=all causes a redirect away from the main
        page so the follower count never loads
      - /in/ URLs are personal profiles with no follower count
      - Fragment identifiers (#) and trailing slashes
    """
    if not url:
        return None

    url = url.strip()

    # Skip personal profiles — /in/ pages have no follower count
    if "/in/" in url:
        print(f"  [LinkedIn SKIP] Personal profile skipped: {url}")
        return None

    # Remove fragment (#) and everything after it
    url = url.split("#")[0]

    # Remove /posts/ and everything after it
    # e.g. /company/nasa/posts/?feedView=all -> /company/nasa
    url = re.sub(r'/posts/.*$', '', url, flags=re.IGNORECASE)

    # Remove page suffixes that navigate away from the main page
    for suffix in ['/about', '/jobs', '/people', '/videos', '/life']:
        if url.endswith(suffix):
            url = url[:-len(suffix)]

    return url.rstrip('/')


# ------------------------------------------------------------
# BROWSER CONTEXT
# ------------------------------------------------------------

def make_linkedin_context(browser):
    """
    Creates a Playwright browser context with a realistic browser
    identity and loads the saved LinkedIn login session if available.

    USER AGENT NOTE:
        The user_agent string identifies the browser as Chrome on Mac.
        This does not need to change per user — it contains no personal
        information and just makes the browser look real to LinkedIn.
    """
    kwargs = dict(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )

    if os.path.exists(LINKEDIN_COOKIES):
        kwargs["storage_state"] = LINKEDIN_COOKIES
        print(f"  [LinkedIn] Loading saved session from {LINKEDIN_COOKIES}")
    else:
        print(f"  [LinkedIn WARN] No cookies file found at {LINKEDIN_COOKIES}")
        print(f"  Run linkedin_login_save.py for better results.")

    return browser.new_context(**kwargs)


# ------------------------------------------------------------
# FOLLOWER COUNT EXTRACTION
# ------------------------------------------------------------

def get_linkedin_followers(url, page, already_loaded=False):
    """
    Loads a LinkedIn company/school page and extracts the
    follower count from the meta description tag.

    LinkedIn's meta description always contains:
        "Company Name | 6,920,597 followers on LinkedIn."

    Parameters:
        url            : LinkedIn page URL (cleaned automatically)
        page           : Playwright page object passed from main.py
        already_loaded : Set True in standalone test to avoid loading
                         the page a second time after the debug section.
                         Always False when called from main.py.
    """
    if not url:
        return None

    cleaned_url = clean_linkedin_url(url)
    if not cleaned_url:
        return None

    def try_extract(pg):
        """Attempt to read follower count from the current page."""

        # Method 1: meta description — most reliable for LinkedIn
        # LinkedIn always populates this with follower count when logged in
        for selector in ['meta[name="description"]', 'meta[property="og:description"]']:
            try:
                text = pg.locator(selector).get_attribute("content", timeout=5000)
                if not text:
                    continue
                # Encode to ASCII to strip hidden Unicode characters
                # that can silently prevent regex from matching
                ascii_text = text.encode("ascii", errors="replace").decode("ascii")
                match = re.search(r'([\d,]+)\s+followers', ascii_text, re.IGNORECASE)
                if match:
                    return int(match.group(1).replace(",", ""))
            except Exception:
                continue

        # Method 2: visible elements containing "followers" text
        for selector in [
            "span:has-text('followers')",
            "p:has-text('followers')",
            "li:has-text('followers')",
        ]:
            try:
                els = pg.locator(selector).all()
                for el in els:
                    text = el.inner_text()
                    if not text:
                        continue
                    ascii_text = text.encode("ascii", errors="replace").decode("ascii")
                    match = re.search(r'([\d,]+)\s+followers', ascii_text, re.IGNORECASE)
                    if match:
                        return int(match.group(1).replace(",", ""))
            except Exception:
                continue

        return None

    try:
        if not already_loaded:
            page.goto(cleaned_url, timeout=20000)
            page.wait_for_timeout(4000)

        # Check for login/authwall redirect
        current_url = page.url
        if "login" in current_url or "authwall" in current_url:
            print(f"  [LinkedIn WARN] Hit login wall for: {url}")
            print(f"  Run linkedin_login_save.py to refresh your session.")
            return None

        # First extraction attempt
        result = try_extract(page)
        if result:
            return result

        # Retry once with a longer wait
        # LinkedIn sometimes returns a partial page on first load
        print(f"  [LinkedIn] Retrying {cleaned_url}...")
        page.goto(cleaned_url, timeout=20000)
        page.wait_for_timeout(5000)

        result = try_extract(page)
        if result:
            return result

        print(f"  [LinkedIn WARN] No follower count found for: {url}")

    except Exception as e:
        print(f"  [LinkedIn ERROR] {e}")

    return None


# ============================================================
# STANDALONE TEST
# ============================================================
# Edit TEST_URL below to test any LinkedIn company/school page.
# Run with:  python linkedin.py
#
# headless=False opens a visible browser window so you can
# see exactly what loads — useful for confirming login worked.
#
# NOTE: Run linkedin_login_save.py first for best results.
# ============================================================

if __name__ == "__main__":
    TEST_URL = "https://www.linkedin.com/company/florida-agency-for-persons-with-disabilities/"

    print("Testing LinkedIn scraper...")
    print(f"URL:         {TEST_URL}")

    cleaned = clean_linkedin_url(TEST_URL)
    print(f"Cleaned URL: {cleaned}\n")

    if not cleaned:
        print("URL was skipped (personal profile or invalid).")
        exit()

    print(f"Looking for cookies at: {LINKEDIN_COOKIES}")
    print(f"Cookies file exists: {os.path.exists(LINKEDIN_COOKIES)}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = make_linkedin_context(browser)
        page    = context.new_page()

        # Load the page ONCE here for the debug section
        page.goto(cleaned, timeout=20000)
        page.wait_for_timeout(4000)

        current_url = page.url
        print(f"\nFinal URL after load: {current_url}\n")

        if "login" in current_url or "authwall" in current_url:
            print("  !! LinkedIn redirected to login/authwall.")
            print("  Your cookies may be missing or expired.")
            print("  Re-run linkedin_login_save.py to refresh.")
        else:
            # DEBUG: print what the meta tags actually contain
            for selector in ['meta[name="description"]', 'meta[property="og:description"]']:
                try:
                    val = page.locator(selector).get_attribute("content", timeout=5000)
                    print(f"{selector}:")
                    print(f"  {repr(val[:120]) if val else 'None'}")
                    print()
                except Exception:
                    print(f"{selector}: NOT FOUND\n")

            # Pass already_loaded=True so the function reads the
            # already-open page instead of loading it a second time
            # (a second load can trigger bot detection on LinkedIn)
            count = get_linkedin_followers(TEST_URL, page, already_loaded=True)
            print(f"Followers: {count}")

        input("\nPress Enter to close the browser...")
        browser.close()