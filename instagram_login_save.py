# ============================================================
# instagram_login_save.py
# ============================================================
# PURPOSE:
#   Saves your Instagram login session to a file so the scraper
#   can access Instagram pages without hitting the login wall.
#
# WHEN TO RUN:
#   - Run this ONCE before using instagram.py or main.py
#   - Re-run if you see "Hit login wall" warnings (session expired)
#   - Sessions typically last 2-4 weeks
#
# HOW TO RUN:
#   python instagram_login_save.py
#
# WHAT IT DOES:
#   Opens a real Chrome browser window, you log in manually,
#   then it saves your session cookies to instagram_cookies.json
#
# IMPORTANT:
#   instagram_cookies.json contains your login session.
#   Do not share it or upload it to GitHub.
# ============================================================

from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    # Open a visible browser window so you can log in manually
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page    = context.new_page()

    # Navigate to Instagram login page
    page.goto("https://www.instagram.com/accounts/login/")

    print("="*50)
    print("A browser window has opened.")
    print("Log in to Instagram, then come back here.")
    print("="*50)
    input("Press Enter once you are fully logged in...")

    # Save the login session (cookies + local storage) to a file
    context.storage_state(path="instagram_cookies.json")

    print("Done! Session saved to instagram_cookies.json")
    browser.close()