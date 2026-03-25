# ============================================================
# main.py
# ============================================================
# The main runner. Reads your CSV, runs all scrapers, and
# writes the follower counts back to a new CSV file.
#
# HOW TO RUN:
#   python main.py
#
# FIRST TIME SETUP (do these once before running):
#   1. Add your YouTube API key to config.py
#   2. Set INPUT_FILE in config.py to your CSV filename
#   3. Run: python instagram_login_save.py  (saves Instagram session)
#   4. Run: python linkedin_login_save.py   (saves LinkedIn session)
#
# WHAT IT DOES:
#   1. Reads all rows from your input CSV
#   2. For each row, checks which social media URLs exist
#   3. Skips any cell that already has a value (safe to re-run)
#   4. Calls the appropriate scraper for each platform
#   5. Writes all results to a new output CSV
# ============================================================

import csv
import os
import time
import random
from playwright.sync_api import sync_playwright

# --- Import settings from config.py ---
from config import (
    INPUT_FILE, OUTPUT_FILE,
    INSTAGRAM_COOKIES, LINKEDIN_COOKIES,
    YOUTUBE_URL_COL,   INSTAGRAM_URL_COL, FACEBOOK_URL_COL,
    X_URL_COL,         LINKEDIN_URL_COL,
    YOUTUBE_COUNT_COL, INSTAGRAM_COUNT_COL, FACEBOOK_COUNT_COL,
    X_COUNT_COL,       LINKEDIN_COUNT_COL,
)

# --- Import scraper functions from each platform file ---
from youtube   import get_youtube_subscribers   # uses official YouTube API
from instagram import get_instagram_followers   # uses Playwright + cookies
from facebook  import get_facebook_followers    # uses Playwright
from x_twitter import get_x_followers          # uses Playwright
from linkedin  import get_linkedin_followers    # uses Playwright + cookies


# ------------------------------------------------------------
# BROWSER CONTEXT SETUP
# ------------------------------------------------------------

def make_context(browser, cookies_file=None):
    """
    Creates a Playwright browser context with a realistic browser
    identity to reduce bot detection.

    USER AGENT NOTE:
        The user_agent string below identifies the browser as
        "Chrome 120 on a Mac". This does NOT need to be changed
        per user — it's just a label that makes the browser look
        like a real desktop browser to websites. It contains no
        personal information.

    If a cookies_file path is provided and the file exists,
    the saved login session is loaded into this context.
    This is how Instagram and LinkedIn authentication works.
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

    # Load saved login session if the cookies file exists
    if cookies_file and os.path.exists(cookies_file):
        kwargs["storage_state"] = cookies_file

    return browser.new_context(**kwargs)


# ------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------

def main():

    # --- Load the input CSV ---
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader    = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows      = list(reader)

    print(f"Loaded {len(rows)} rows")
    print(f"Columns found: {fieldnames}\n")

    # Warn if cookie files are missing — scraper will still run
    # but Instagram and LinkedIn may hit login walls
    for label, path in [
        ("Instagram", INSTAGRAM_COOKIES),
        ("LinkedIn",  LINKEDIN_COOKIES),
    ]:
        if not os.path.exists(path):
            print(f"WARNING: {path} not found — {label} may hit a login wall.")
            print(f"         Run {label.lower()}_login_save.py to fix this.\n")

    # Add output columns to fieldnames if they don't exist yet in the CSV
    for col in [
        YOUTUBE_COUNT_COL, INSTAGRAM_COUNT_COL, FACEBOOK_COUNT_COL,
        X_COUNT_COL, LINKEDIN_COUNT_COL,
    ]:
        if col not in fieldnames:
            fieldnames.append(col)

    total = len(rows)

    # --- Launch Playwright and create isolated contexts per platform ---
    # Each platform gets its own browser context so cookies and session
    # state never bleed between platforms. LinkedIn in particular is
    # sensitive to contexts that have been used by other sites.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Facebook uses a generic context (no login needed)
        facebook_context  = make_context(browser)

        # Instagram and LinkedIn use their saved cookie sessions
        instagram_context = make_context(browser, INSTAGRAM_COOKIES)
        linkedin_context  = make_context(browser, LINKEDIN_COOKIES)

        # X works without cookies for most public profiles
        x_context         = make_context(browser)

        # Create one page per context
        facebook_page  = facebook_context.new_page()
        instagram_page = instagram_context.new_page()
        x_page         = x_context.new_page()
        linkedin_page  = linkedin_context.new_page()

        # --- Process each row in the CSV ---
        for i, row in enumerate(rows):
            print(f"\nRow {i+1}/{total}")

            # YOUTUBE — official API, no browser needed
            yt_url = row.get(YOUTUBE_URL_COL, "").strip()
            if yt_url and not row.get(YOUTUBE_COUNT_COL):
                print("  Fetching YouTube...")
                row[YOUTUBE_COUNT_COL] = get_youtube_subscribers(yt_url)
                time.sleep(random.uniform(1, 2))

            # INSTAGRAM — requires instagram_cookies.json
            ig_url = row.get(INSTAGRAM_URL_COL, "").strip()
            if ig_url and not row.get(INSTAGRAM_COUNT_COL):
                print("  Fetching Instagram...")
                row[INSTAGRAM_COUNT_COL] = get_instagram_followers(ig_url, instagram_page)
                time.sleep(random.uniform(2, 3))

            # FACEBOOK — public pages, no login needed
            fb_url = row.get(FACEBOOK_URL_COL, "").strip()
            if fb_url and not row.get(FACEBOOK_COUNT_COL):
                print("  Fetching Facebook...")
                row[FACEBOOK_COUNT_COL] = get_facebook_followers(fb_url, facebook_page)
                time.sleep(random.uniform(2, 3))

            # X / TWITTER — public profiles, no login needed
            x_url = row.get(X_URL_COL, "").strip()
            if x_url and not row.get(X_COUNT_COL):
                print("  Fetching X...")
                row[X_COUNT_COL] = get_x_followers(x_url, x_page)
                time.sleep(random.uniform(2, 3))

            # LINKEDIN — requires linkedin_cookies.json for best results
            li_url = row.get(LINKEDIN_URL_COL, "").strip()
            if li_url and not row.get(LINKEDIN_COUNT_COL):
                print("  Fetching LinkedIn...")
                row[LINKEDIN_COUNT_COL] = get_linkedin_followers(li_url, linkedin_page)
                time.sleep(random.uniform(2, 3))

        browser.close()

    # --- Write results to output CSV ---
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()