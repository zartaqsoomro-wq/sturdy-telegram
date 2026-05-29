all files explanation
🚀
app.py
Start the server — run this file
Does what
Creates the Flask app, sets up CORS so any frontend can call it, registers all routes from routes.py, adds JSON error handlers so you never get ugly HTML error pages.
Why needed
Every Flask project needs one entry point. Without this file, the server never starts.
How to use
python app.py — that's it. Server starts on port 5000.
⚙️
config.py
All settings, reads from .env
Does what
Reads your Bright Data API key, WebSocket URL, zone name, port, and debug flag from the .env file and makes them available as Config.WHATEVER anywhere in the project.
Why needed
You never hardcode API keys in code. If a key needs to change, you change it in one place — .env — not scattered across 4 files.
Example
Config.BRIGHT_DATA_API_KEY — every service file reads from here.
🛣️
routes.py
All 5 API endpoints — the backbone
Does what
Defines every URL the server responds to. Creates instances of all 4 service classes. Holds the two in-memory caches (_raw_cache and _signals_store) that act as the shared data store.
Why needed
Flask doesn't know what to do with any incoming request until you define routes. This file is where all the request handling logic lives.
Key pattern
Service instances are created once at module load (_serp = SerpClient()) and reused for every request — no wasted reconnection overhead.
🔍
services/serp_client.py
Google news via Bright Data SERP API
Does what
Sends 5 pre-written TNBC search queries to Bright Data's SERP API. Gets back Google search results as clean JSON — title, snippet, URL, date. Deduplicates by URL across all 5 queries.
Why this and not Google directly
Google blocks direct scraping. Bright Data SERP API gives you clean structured JSON from Google, no CAPTCHAs, no blocks, no HTML parsing needed.
Output shape
{"id", "source": "serp_news", "url", "title", "raw_text", "published_at", "fetched_at", "metadata"}
🕷️
services/scraper_client.py
Static pages via Web Unlocker + BeautifulSoup
Does what
Sends HTTP requests through Bright Data Web Unlocker proxy to BioPharma Dive, FierceBiotech, and ClinicalTrials.gov. Gets back raw HTML, then uses BeautifulSoup to find article containers and extract title + body text.
Why Web Unlocker
News sites have bot detection — if you send a normal requests.get() they block you. Web Unlocker routes your request through real residential IPs so the site thinks it's a real person browsing.
Extraction trick
Tries <article> tags first, then <li>, then <div class="card"> — works across different site layouts without custom CSS selectors per site.
🌐
services/browser_client.py
JS pages via Playwright + cloud Chromium
Does what
Connects Playwright (browser automation library) to a real Chromium browser hosted in Bright Data's cloud. Navigates to ClinicalTrials.gov, waits for React to render the trial cards, then extracts them.
Why a real browser
ClinicalTrials.gov is a React app. If you fetch it with HTTP, you get an empty HTML shell — the actual content gets injected by JavaScript after load. Only a real browser that runs JavaScript can see the actual data.
Flask trick
Playwright is async but Flask is sync. asyncio.run() wraps the async code so it can be called safely from a normal Flask route.
🧹
services/data_processor.py
Clean, filter, deduplicate raw scraped data
Does what
Takes the combined raw output from all 3 scrapers and runs a 4-step pipeline: strip HTML/whitespace → discard stubs under 40 chars → keep only items mentioning TNBC keywords → truncate at 6000 chars → remove duplicate IDs.
Why needed
Raw scraped data is noisy — nav links, cookie banners, unrelated articles. If you send this directly to William's LLM it wastes tokens and produces garbage signals. Clean data in = clean signals out.
Key filter
Checks for keywords like tnbc, triple negative, pembrolizumab, clinical trial, fda etc. Anything without these is discarded.
🔑
.env.example + .env
Your secret keys — never committed to git
Does what
.env.example is a template showing which keys you need. You copy it to .env and fill in real values. config.py reads from .env at startup.
Why never commit .env
If you push your API key to GitHub, anyone can use it. The .env.example shows the structure without real values — that's safe to commit. The actual .env stays on your machine only.
What goes inside
BRIGHT_DATA_API_KEY, BRIGHT_DATA_UNLOCKER_ZONE, BRIGHT_DATA_BROWSER_WS, FLASK_DEBUG, PORT
📦
services/__init__.py
Empty file — tells Python this folder is a package
Does what
It's completely empty. Its only job is to exist.
Why needed
Python needs this file to treat the services/ folder as an importable package. Without it, from services.serp_client import SerpClient crashes with ModuleNotFoundError — even though the file is right there.
