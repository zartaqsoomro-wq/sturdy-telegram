import hashlib
import requests
from datetime import datetime, timezone
from config import Config

# TNBC search queries — covers trials, biotech news, research
TNBC_QUERIES = [
    "TNBC triple negative breast cancer clinical trial results 2026",
    "triple negative breast cancer phase 3 FDA approval 2026",
    "TNBC biotech company funding deal partnership 2026",
    "triple negative breast cancer drug pipeline update 2026",
    "triple negative breast cancer immunotherapy breakthrough 2026",
]


class SerpClient:

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {Config.BRIGHT_DATA_API_KEY}",
            "Content-Type": "application/json",
        }

    def fetch_tnbc_news(self) -> list[dict]:
        """
        Runs all TNBC queries through Bright Data SERP API.
        Returns a deduplicated list of raw data dicts.
        """
        all_items = []
        seen_urls = set()

        for query in TNBC_QUERIES:
            try:
                items = self._run_query(query)
                for item in items:
                    if item["url"] not in seen_urls:
                        seen_urls.add(item["url"])
                        all_items.append(item)
                print(f"[SERP] '{query[:50]}' → {len(items)} results")
            except Exception as e:
                print(f"[SERP] Query failed: {e}")

        print(f"[SERP] Total fetched (deduplicated): {len(all_items)}")
        return all_items

    def _run_query(self, query: str) -> list[dict]:
        response = requests.post(
            Config.BRIGHT_DATA_SERP_URL,
            headers=self.headers,
            json={"q": query, "num": 5, "gl": "us", "hl": "en"},
            timeout=30,
        )
        response.raise_for_status()
        return self._parse(response.json(), query)

    def _parse(self, data: dict, query: str) -> list[dict]:
        items = []
        fetched_at = datetime.now(timezone.utc).isoformat()

        for result in data.get("organic", []):
            url     = result.get("url", "").strip()
            title   = result.get("title", "").strip()
            snippet = result.get("description", "").strip()

            if not url or not title:
                continue

            items.append({
                "id":           hashlib.md5(url.encode()).hexdigest()[:12],
                "source":       "serp_news",
                "url":          url,
                "title":        title,
                "raw_text":     f"{title}. {snippet}".strip(),
                "published_at": result.get("date"),
                "fetched_at":   fetched_at,
                "metadata":     {"query": query, "position": result.get("rank", 0)},
            })

        return items
