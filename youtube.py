# ============================================================
# youtube.py
# ============================================================
# Fetches YouTube subscriber counts using the official
# YouTube Data API v3 (free, no login required).
#
# Imported by: main.py
# Requires:    YOUTUBE_API_KEY in config.py
#
# STANDALONE TEST:
#   Edit TEST_URLS at the bottom, then run:
#   python youtube.py
# ============================================================

import re
import requests

# Import API key from the central config file
from config import YOUTUBE_API_KEY

# Standard browser header to avoid request blocks
HEADERS = {"User-Agent": "Mozilla/5.0"}


# ------------------------------------------------------------
# URL CLEANING
# ------------------------------------------------------------

def clean_youtube_url(url):
    """
    Fixes common YouTube URL issues found in CSV data:

      1. Missing www — "youtube.com/..." won't redirect properly
         when fetched with requests, so we add www if missing.
         e.g. https://youtube.com/eyespyorg
              -> https://www.youtube.com/eyespyorg

      2. "Youtube" or "YouTube" appended directly to the URL
         with no separator — strips it off so the URL is valid.
         e.g. https://www.youtube.com/user/lionsclubsorgYoutube
              -> https://www.youtube.com/user/lionsclubsorg
    """
    if not url:
        return None

    url = url.strip()

    # Fix 1: normalize to www.youtube.com
    url = re.sub(r'https?://(www\.)?youtube\.com', 'https://www.youtube.com', url)

    # Fix 2: remove "Youtube" or "YouTube" appended to the end
    url = re.sub(r'YouTube$', '', url, flags=re.IGNORECASE).rstrip('/')

    return url


# ------------------------------------------------------------
# CHANNEL ID EXTRACTION
# ------------------------------------------------------------

def extract_youtube_channel_id(url):
    """
    Extracts the YouTube channel ID (starts with UC...) from any
    YouTube URL format.

    Supported formats:
        /channel/UC...    direct channel ID — extracted instantly
        /@handle          new handle format  — page fetch required
        /user/name        legacy format      — page fetch required
        /c/name           legacy custom URL  — page fetch required
        /channelname      short custom URL   — page fetch required

    For non-direct URLs, the page HTML is fetched because YouTube
    always embeds the canonical channel ID in its page source.
    """
    if not url:
        return None

    url = clean_youtube_url(url)
    if not url:
        return None

    # Case 1: channel ID is directly in the URL — no fetch needed
    match = re.search(r'/channel/(UC[\w-]+)', url)
    if match:
        return match.group(1)

    # Case 2: all other formats — fetch page and find the embedded ID
    # YouTube embeds the canonical channel ID in every page's source
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text

        # Primary pattern in YouTube page source
        match = re.search(r'"channelId"\s*:\s*"(UC[\w-]+)"', html)
        if match:
            return match.group(1)

        # Fallback pattern also present in YouTube page source
        match2 = re.search(r'"externalId"\s*:\s*"(UC[\w-]+)"', html)
        if match2:
            return match2.group(1)

    except Exception as e:
        print(f"  [YouTube channel ID error] {e}")

    return None


# ------------------------------------------------------------
# SUBSCRIBER COUNT
# ------------------------------------------------------------

def get_youtube_subscribers(url):
    """
    Returns the subscriber count for a YouTube channel using the
    official YouTube Data API v3.

    Steps:
        1. Clean and normalize the URL
        2. Extract the channel ID
        3. Call the YouTube API with the channel ID
        4. Return the subscriber count as an integer
    """
    if not url:
        return None

    channel_id = extract_youtube_channel_id(url)
    if not channel_id:
        print(f"  [YouTube] Could not extract channel ID from: {url}")
        return None

    try:
        api_url  = "https://www.googleapis.com/youtube/v3/channels"
        params   = {
            "part": "statistics",
            "id":   channel_id,
            "key":  YOUTUBE_API_KEY,
        }
        response = requests.get(api_url, params=params, timeout=10).json()

        if not response.get("items"):
            print(f"  [YouTube] No results for channel ID: {channel_id}")
            return None

        return int(response["items"][0]["statistics"]["subscriberCount"])

    except Exception as e:
        print(f"  [YouTube ERROR] {e}")
        return None


# ============================================================
# STANDALONE TEST
# ============================================================
# Edit TEST_URLS below to test different YouTube URL formats.
# Run with:  python youtube.py
# ============================================================

if __name__ == "__main__":

    TEST_URLS = [
        "https://www.youtube.com/@mkbhd",                                   # handle format
        "https://www.youtube.com/channel/UCBcRF18a7Qf58cCRy5xuWwQ",        # direct channel ID
        "https://www.youtube.com/user/lionsclubsorg",                       # legacy /user/ format
        "https://www.youtube.com/user/lionsclubsorgYoutube",                # corrupted suffix
        "https://www.youtube.com/channel/UCEWd5at9r83fEENXFF6OCogYoutube",  # corrupted suffix
        "https://youtube.com/eyespyorg",                                    # missing www
        "https://youtube.com/eyespyorgYoutube",                             # missing www + corrupted
    ]

    for url in TEST_URLS:
        print(f"URL      : {url}")
        print(f"Cleaned  : {clean_youtube_url(url)}")
        print(f"ChannelID: {extract_youtube_channel_id(url)}")
        print(f"Subs     : {get_youtube_subscribers(url)}")
        print()