# Social-Media-Scraper

A Python tool that reads social media URLs from a CSV file and automatically extracts follower and subscriber counts for YouTube, Instagram, Facebook, X, and LinkedIn. Results are written back to a new CSV file.



## How It Works

The script reads each row of your CSV, visits each social media page, extracts the follower count, and saves the results to an output CSV. Each platform uses a different method:

| Platform | Method | Login Required |
|---|---|---|
| YouTube | Official YouTube Data API v3 | No (API key only) |
| Instagram | Playwright headless browser | Yes (cookies) |
| Facebook | Playwright headless browser | No |
| X  | Playwright headless browser | No |
| LinkedIn | Playwright headless browser | Yes (cookies) |



## File Overview

```
social-media-scraper/
    config.py                 ← settings: API key, file names, column names
    utils.py                  ← shared helper function
    main.py                   ← main runner: reads CSV, runs all scrapers, writes output
    youtube.py                ← YouTube scraper (official API)
    instagram.py              ← Instagram scraper (Playwright + cookies)
    facebook.py               ← Facebook scraper (Playwright)
    x_twitter.py              ← X/Twitter scraper (Playwright)
    linkedin.py               ← LinkedIn scraper (Playwright + cookies)
    instagram_login_save.py   ← one-time setup: saves Instagram login session
    linkedin_login_save.py    ← one-time setup: saves LinkedIn login session
```



## Installation

**1. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/Social-Media-Scraper.git
cd Social-Media-Scraper
```

**2. Install required libraries:**
```bash
pip install requests playwright
playwright install chromium
```



## Setup

### 1. `config.py` — Configure Before Running

Open `config.py` and update the following:

**YouTube API Key:**
```python
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"
```
See the YouTube API setup section below for instructions on getting your key.

**File Names:**
```python
INPUT_FILE  = "your_input.csv"    # name of your input CSV file
OUTPUT_FILE = "output.csv"        # name of the output CSV that gets created
```

**Column Names:**
These must exactly match the column headers in your CSV file. If your CSV uses different column names, update them here.
```python
# Input columns — the columns containing social media URLs
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
```



### 2. YouTube API Key Setup

YouTube is the only platform using an official API. It is free and does not require a login session.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (name it anything)
3. Click **Enable APIs and Services** → search **YouTube Data API v3** → click **Enable**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy the key and paste it into `config.py`:
```python
YOUTUBE_API_KEY = "AIzaSy..."
```

The free tier allows 10,000 requests per day which is more than enough for typical use.



### 3. Instagram Cookie Setup (One Time)

Instagram blocks logged-out visitors with a login wall. To bypass this, the scraper uses your saved login session. You only need to do this once — sessions typically last **2 to 4 weeks**.

**Run the setup script:**
```bash
python instagram_login_save.py
```

A real Chrome browser window will open. Log in to Instagram normally, wait until your feed fully loads, then go back to the terminal and press Enter. Your session will be saved to `instagram_cookies.json`.

**When to re-run:**
If you see this warning while running the scraper, your session has expired:
```
[Instagram WARN] Login wall detected — cookies may be missing or expired.
```

> **Important:** `instagram_cookies.json` contains your active login session. Never share this file or upload it to GitHub.



### 4. LinkedIn Cookie Setup (One Time)

LinkedIn requires login to reliably show follower counts on company and school pages. The setup process is identical to Instagram.

**Run the setup script:**
```bash
python linkedin_login_save.py
```

A browser window will open. Log in to LinkedIn, wait until your feed fully loads, then press Enter in the terminal. Your session is saved to `linkedin_cookies.json`.

**When to re-run:**
If you see this warning while running the scraper:
```
[LinkedIn WARN] Hit login wall for: ...
```

> **Important:** `linkedin_cookies.json` contains your active login session. Never share this file or upload it to GitHub.

**Without cookies:** LinkedIn still works on approximately 80% of public company pages. With cookies it reaches approximately 95%.



## Running the Scraper

Once setup is complete, place your CSV file in the same folder as the scripts and run:

```bash
python main.py
```

The script will:
1. Load all rows from your input CSV
2. Skip any cell that already has a value (safe to re-run on a partially filled CSV)
3. Fetch follower counts for each platform
4. Save results to the output CSV specified in `config.py`

**Example output:**
```
Loaded 95 rows
Columns found: ['listing_title', 'facebook', 'facebook_followers', ...]

Row 1/95
  Fetching YouTube...
  Fetching Instagram...
  Fetching Facebook...
  Fetching X...
  Fetching LinkedIn...

Done! Output saved to: output.csv
```



## CSV Format

Your input CSV should have URL columns and empty count columns that the scraper will fill in:

| listing_title | youtube | youtube_subscribers | instagram | instagram_followers |
|---|---|---|---|---|
| NASA | https://www.youtube.com/nasa | | https://www.instagram.com/nasa | |

The column names must match what is set in `config.py`.

**Supported YouTube URL formats** — all handled automatically:
```
https://www.youtube.com/channel/UCxxxxxx    direct channel ID
https://www.youtube.com/@channelhandle      handle format
https://www.youtube.com/user/channelname    legacy format
https://www.youtube.com/channelname         short custom URL
```

**Supported LinkedIn URL formats** — cleaned automatically:
```
/company/name/posts/?feedView=all  →  stripped to /company/name
/school/name/                      →  works as-is
/in/personalprofile                →  skipped (no follower count on personal profiles)
```



## Individual Platform Testing

Each scraper can be run independently to test a specific URL without processing the full CSV. Edit the `TEST_URL` variable at the bottom of the file, then run it directly.

```bash
python youtube.py      # test YouTube subscriber fetching
python instagram.py    # test Instagram follower fetching
python facebook.py     # test Facebook follower fetching
python x_twitter.py    # test X/Twitter follower fetching
python linkedin.py     # test LinkedIn follower fetching
```

**What each standalone test shows:**

- `youtube.py` — prints the cleaned URL, extracted channel ID, and subscriber count
- `instagram.py` — prints the raw meta description tag so you can see exactly what Instagram returns
- `facebook.py` — prints raw HTML snippets containing "followers" to show what patterns are on the page
- `x_twitter.py` — opens a **visible browser window** so you can confirm the page loaded correctly
- `linkedin.py` — opens a **visible browser window**, prints meta tag content, and shows the follower count

> `x_twitter.py` and `linkedin.py` open a visible Chrome window during standalone testing. This is intentional — it lets you visually confirm the page is not showing a login wall. The window stays open until you press Enter. When `main.py` runs the full pipeline it uses a hidden browser for speed.



## Troubleshooting

**Instagram returns None for every URL:**
Your cookies have expired. Re-run `python instagram_login_save.py`.

**LinkedIn redirects to authwall:**
Your cookies have expired. Re-run `python linkedin_login_save.py`. Make sure to wait until your LinkedIn feed fully loads before pressing Enter during setup.

**YouTube returns None:**
- Check that your API key is correctly set in `config.py`
- Verify the YouTube URL is valid and the channel exists
- Check your daily quota at [console.cloud.google.com](https://console.cloud.google.com) (free tier: 10,000 requests/day)

**Facebook returns None:**
Some pages do not publicly display follower counts, or the page may be a personal profile rather than a business page. This is a platform limitation.

**Network / DNS errors:**
```
Failed to resolve 'www.instagram.com'
```
Your network is blocking outbound requests. Try running on a personal WiFi network — school and corporate networks often block scraping traffic.

**Re-running on a partially filled CSV:**
The script skips any cell that already contains a value. You can safely re-run `main.py` on a previous output CSV and it will only fetch the missing values.



## Notes

- Random delays between requests (1–3 seconds) are built in to reduce rate limiting
- Each platform uses its own isolated browser session so cookies never interfere between platforms
- The scraper works on public pages only — private accounts return None
- Instagram and LinkedIn cookie sessions expire after approximately 2–4 weeks and need to be refreshed by re-running the login save scripts
