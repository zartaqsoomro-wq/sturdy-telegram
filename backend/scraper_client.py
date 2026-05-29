import time
import hashlib
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from config import Config

# Static TNBC pages to scrape
SCRAPE_TARGETS = [
    {
        "url":   "https://www.biopharmadive.com/topic/breast-cancer/",
        "label": "BioPharma Dive",
    },
    {
        "url":   "https://www.fiercebiotech.com/search/node/triple%20negative%20breast%20cancer",
        "label": "FierceBiotech",
    },
    {
        "url":   "https://clinicaltrials.gov/search?cond=Triple+Negative+Breast+Cancer&aggFilters=status:rec",
        "label": "ClinicalTrials.gov",
    },
]


class ScraperClient:

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {Config.BRIGHT_DATA_API_KEY}",
            "Content-Type": "application/json",
        }

    def scrape_tnbc_sources(self) -> list[dict]:
        """
        Scrapes all target pages through Bright Data Web Unlocker.
        Returns a flat list of raw data dicts.
        """
        all_items = []

        for target in SCRAPE_TARGETS:
            try:
                html  = self._fetch(target["url"])
                items = self._extract(html, target)
                all_items.extend(items)
                print(f"[Scraper] '{target['label']}' → {len(items)} items")
            except Exception as e:
                print(f"[Scraper] Failed '{target['label']}': {e}")
            time.sleep(1)

        print(f"[Scraper] Total: {len(all_items)} items")
        return all_items

    def _fetch(self, url: str) -> str:
        """Routes request through Bright Data Web Unlocker (handles anti-bot)."""
        response = requests.post(
            Config.BRIGHT_DATA_UNLOCKER_URL,
            headers=self.headers,
            json={"zone": Config.BRIGHT_DATA_UNLOCKER_ZONE, "url": url, "format": "raw"},
            timeout=60,
        )
        response.raise_for_status()
        return response.text

    def _extract(self, html: str, target: dict) -> list[dict]:
        """Extracts article listings from HTML using a generic strategy."""
        soup       = BeautifulSoup(html, "lxml")
        fetched_at = datetime.now(timezone.utc).isoformat()
        source_url = target["url"]
        base       = urlparse(source_url)
        base_origin = f"{base.scheme}://{base.netloc}"

        # Try article tags first, then li items, then div cards
        containers = (
            soup.find_all("article") or
            soup.find_all("li", class_=lambda c: c and "item" in c.lower()) or
            soup.find_all("div", class_=lambda c: c and ("card" in c.lower() or "result" in c.lower()))
        )

        items = []
        for container in containers[:10]:
            title_tag = container.find(["h1", "h2", "h3", "h4"])
            link_tag  = container.find("a", href=True)
            text_tag  = container.find("p")

            title = title_tag.get_text(strip=True) if title_tag else ""
            body  = text_tag.get_text(strip=True)  if text_tag  else ""
            href  = link_tag["href"]                if link_tag  else source_url

            if href.startswith("/"):
                href = base_origin + href
            elif not href.startswith("http"):
                href = source_url

            if not title:
                continue

            items.append({
                "id":         hashlib.md5(f"{href}{title}".encode()).hexdigest()[:12],
                "source":     "biotech_news",
                "url":        href,
                "title":      title,
                "raw_text":   f"{title}. {body}".strip(),
                "fetched_at": fetched_at,
                "metadata":   {"source_label": target["label"]},
            })

        return items
