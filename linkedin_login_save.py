# ============================================================
# linkedin_login_save.py
# ============================================================
# PURPOSE:
#   Saves your LinkedIn login session to a file so the scraper
#   can access LinkedIn pages without hitting the login wall.
#
# WHEN TO RUN:
#   - Run this ONCE before using linkedin.py or main.py
#   - Re-run if you see "authwall" warnings (session expired)
#   - Sessions typically last 2-4 weeks
#
# HOW TO RUN:
#   python linkedin_login_save.py
#
# WHAT IT DOES:
#   Opens a real Chrome browser window, you log in manually,
#   then saves your session cookies to linkedin_cookies.json
#
# IMPORTANT:
#   linkedin_cookies.json contains your login session.
#   Do not share it or upload it to GitHub.
# ============================================================

import os
from playwright.sync_api import sync_playwright

# Save cookies to the same folder as this script
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "linkedin_cookies.json")

with sync_playwright() as p:

    # Use a realistic browser identity so LinkedIn accepts the session
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

    page.goto("https://www.linkedin.com/login")

    print("=" * 50)
    print("A browser window has opened.")
    print("Log in to LinkedIn, then come back here.")
    print("Wait until your feed fully loads before pressing Enter.")
    print("=" * 50)
    input("Press Enter once you are fully logged in...")

    # Save the full session state (cookies + localStorage)
    context.storage_state(path=SAVE_PATH)

    print(f"Done! Session saved to: {SAVE_PATH}")
    browser.close()