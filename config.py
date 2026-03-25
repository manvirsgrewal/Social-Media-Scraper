# ============================================================
# config.py
# ============================================================
# Central settings file. Every other script imports from here.
# If anything changes (API key, file names, column names),
# update it HERE and it will apply everywhere automatically.
# ============================================================


# ------------------------------------------------------------
# API KEYS
# YouTube is the only platform using an official API.
# Get your key at: https://console.cloud.google.com
#   1. Create a project
#   2. Enable "YouTube Data API v3"
#   3. Create credentials -> API Key
# ------------------------------------------------------------
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"


# ------------------------------------------------------------
# FILE NAMES
# INPUT_FILE  : the CSV you want to process
# OUTPUT_FILE : the new CSV that gets created with results
# Both files should be in the same folder as your scripts.
# ------------------------------------------------------------
INPUT_FILE  = "your_input.csv"
OUTPUT_FILE = "output.csv"


# ------------------------------------------------------------
# COOKIE FILES
# Instagram and LinkedIn require you to be logged in.
# These files store your login session so the scraper can
# access pages that are hidden behind a login wall.
#
# HOW TO GENERATE THEM (one time only):
#   Instagram : python instagram_login_save.py
#   LinkedIn  : python linkedin_login_save.py
#
# HOW LONG DO THEY LAST:
#   Typically 2-4 weeks. When expired, re-run the login script.
#
# IMPORTANT: Never share or commit these files — they contain
# your active login session.
# ------------------------------------------------------------
INSTAGRAM_COOKIES = "instagram_cookies.json"
LINKEDIN_COOKIES  = "linkedin_cookies.json"


# ------------------------------------------------------------
# CSV COLUMN NAMES
# These must exactly match the column headers in your CSV.
# If a column name changes in your sheet, update it here only.
# ------------------------------------------------------------

# Input columns — contain the social media URLs
YOUTUBE_URL_COL   = "youtube"
INSTAGRAM_URL_COL = "instagram"
FACEBOOK_URL_COL  = "facebook"
X_URL_COL         = "x__twitter"
LINKEDIN_URL_COL  = "linkedin_profile"

# Output columns — where follower counts get written
YOUTUBE_COUNT_COL   = "youtube_subscribers"
INSTAGRAM_COUNT_COL = "instagram_followers"
FACEBOOK_COUNT_COL  = "facebook_followers"
X_COUNT_COL         = "twitter_followers"
LINKEDIN_COUNT_COL  = "linkedin_followers"
