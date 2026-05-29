import re

# At least one of these must appear in the text to keep the item
TNBC_KEYWORDS = [
    "tnbc", "triple negative", "triple-negative", "breast cancer",
    "oncology", "pembrolizumab", "atezolizumab", "sacituzumab",
    "olaparib", "keytruda", "trodelvy", "tecentriq",
    "clinical trial", "phase 1", "phase 2", "phase 3",
    "fda", "ema", "breakthrough therapy", "biotech",
    "drug pipeline", "overall survival", "progression-free",
]

MIN_LENGTH = 40     # discard stubs shorter than this
MAX_LENGTH = 6000   # truncate so William's LLM prompt doesn't overflow


class DataProcessor:

    def clean_and_filter(self, items: list[dict]) -> list[dict]:
        """
        Input:  raw dicts from all 3 Bright Data clients
        Output: cleaned, filtered, deduplicated dicts ready for William's AI layer
        """
        cleaned  = []
        seen_ids = set()

        for item in items:
            try:
                result = self._process(item)
                if result is None:
                    continue
                if result["id"] in seen_ids:
                    continue
                seen_ids.add(result["id"])
                cleaned.append(result)
            except Exception as e:
                print(f"[Processor] Error on item {item.get('id')}: {e}")

        print(f"[Processor] {len(items)} in → {len(cleaned)} clean items out")
        return cleaned

    def _process(self, item: dict) -> dict | None:
        clean_text = self._clean_text(item.get("raw_text", ""))

        if len(clean_text) < MIN_LENGTH:
            return None

        combined = (item.get("title", "") + " " + clean_text).lower()
        if not any(kw in combined for kw in TNBC_KEYWORDS):
            return None

        if len(clean_text) > MAX_LENGTH:
            clean_text = clean_text[:MAX_LENGTH] + "…"

        return {**item, "raw_text": clean_text}

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)   # strip HTML tags
        text = re.sub(r"\s+", " ", text)         # collapse whitespace
        text = re.sub(r"[^\x20-\x7E]", "", text) # remove non-printable chars
        return text.strip()
