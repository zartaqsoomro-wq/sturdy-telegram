import asyncio
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse
from config import Config

# JS-rendered pages that need a real browser
DYNAMIC_TARGETS = [
    {
        "url":            "https://clinicaltrials.gov/search?cond=Triple+Negative+Breast+Cancer",
        "label":          "ClinicalTrials.gov Dynamic",
        "wait_selector":  "[data-testid='study-card']",
        "item_selector":  "[data-testid='study-card']",
        "title_selector": "h2",
        "text_selector":  "p",
    },
]


class BrowserClient:

    def scrape_dynamic_pages(self) -> list[dict]:
        """Sync wrapper — safe to call from Flask routes."""
        if not Config.BRIGHT_DATA_BROWSER_WS:
            print("[Browser] BRIGHT_DATA_BROWSER_WS not set — skipping")
            return []
        return asyncio.run(self._scrape_all())

    async def _scrape_all(self) -> list[dict]:
        from playwright.async_api import async_playwright

        all_items = []

        async with async_playwright() as pw:
            # Connect to Bright Data's cloud Chromium via WebSocket
            browser = await pw.chromium.connect_over_cdp(Config.BRIGHT_DATA_BROWSER_WS)
            print("[Browser] Connected to Bright Data Scraping Browser")

            for target in DYNAMIC_TARGETS:
                try:
                    items = await self._scrape_page(browser, target)
                    all_items.extend(items)
                    print(f"[Browser] '{target['label']}' → {len(items)} items")
                except Exception as e:
                    print(f"[Browser] Failed '{target['label']}': {e}")

            await browser.close()

        print(f"[Browser] Total: {len(all_items)} items")
        return all_items

    async def _scrape_page(self, browser, target: dict) -> list[dict]:
        page       = await browser.new_page()
        items      = []
        fetched_at = datetime.now(timezone.utc).isoformat()

        try:
            await page.goto(target["url"], wait_until="networkidle", timeout=60_000)

            if target.get("wait_selector"):
                await page.wait_for_selector(target["wait_selector"], timeout=15_000)

            containers = await page.query_selector_all(target["item_selector"])

            for container in containers[:10]:
                title_el = await container.query_selector(target["title_selector"])
                text_el  = await container.query_selector(target["text_selector"])
                link_el  = await container.query_selector("a[href]")

                title = (await title_el.inner_text()).strip() if title_el else ""
                body  = (await text_el.inner_text()).strip()  if text_el  else ""
                href  = await link_el.get_attribute("href")   if link_el  else target["url"]

                if href and href.startswith("/"):
                    parsed = urlparse(target["url"])
                    href   = f"{parsed.scheme}://{parsed.netloc}{href}"

                if not title:
                    continue

                items.append({
                    "id":         hashlib.md5(f"{href}{title}".encode()).hexdigest()[:12],
                    "source":     "clinical_trials",
                    "url":        href or target["url"],
                    "title":      title,
                    "raw_text":   f"{title}. {body}".strip(),
                    "fetched_at": fetched_at,
                    "metadata":   {"label": target["label"]},
                })

        finally:
            await page.close()

        return items
