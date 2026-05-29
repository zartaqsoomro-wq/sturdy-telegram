from datetime import datetime, timezone
from flask import Blueprint, jsonify, request

from services.serp_client    import SerpClient
from services.scraper_client import ScraperClient
from services.browser_client import BrowserClient
from services.data_processor import DataProcessor

bp = Blueprint("oncomarket", __name__)

# --- Service instances (created once, reused per request) ---
_serp    = SerpClient()
_scraper = ScraperClient()
_browser = BrowserClient()
_proc    = DataProcessor()

# --- In-memory stores ---
_raw_cache     = []   # filled by POST /api/fetch
_signals_store = []   # filled by POST /api/signals
_last_fetched  = ""


# ── GET /health ───────────────────────────────────────────────────────────────
# Simple liveness check. Hit this first to confirm server is running.

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": _now()}), 200


# ── POST /api/fetch ───────────────────────────────────────────────────────────
# Triggers live data fetch from Bright Data.
#
# Query params:
#   sources = serp, scraper, browser  (default: serp,scraper)
#   force   = true  (re-fetch even if cache exists)
#
# Example: POST /api/fetch?sources=serp,scraper&force=true

@bp.route("/api/fetch", methods=["POST"])
def fetch_data():
    global _raw_cache, _last_fetched

    sources = request.args.get("sources", "serp,scraper").split(",")
    force   = request.args.get("force", "false").lower() == "true"

    if _raw_cache and not force:
        return jsonify({
            "status":        "cached",
            "items_fetched": len(_raw_cache),
            "message":       f"Cached data from {_last_fetched}. Use ?force=true to re-fetch.",
        }), 200

    all_raw = []
    errors  = []

    if "serp" in sources:
        try:
            all_raw.extend(_serp.fetch_tnbc_news())
        except Exception as e:
            errors.append(f"SERP: {e}")

    if "scraper" in sources:
        try:
            all_raw.extend(_scraper.scrape_tnbc_sources())
        except Exception as e:
            errors.append(f"Scraper: {e}")

    if "browser" in sources:
        try:
            all_raw.extend(_browser.scrape_dynamic_pages())
        except Exception as e:
            errors.append(f"Browser: {e}")

    cleaned       = _proc.clean_and_filter(all_raw)
    _raw_cache    = cleaned
    _last_fetched = _now()

    return jsonify({
        "status":        "success" if not errors else "partial",
        "items_fetched": len(cleaned),
        "errors":        errors,
        "fetched_at":    _last_fetched,
    }), 200


# ── GET /api/raw-data ─────────────────────────────────────────────────────────
# Returns cached raw items. William's AI agent calls this.
#
# Query params:
#   limit  = number of items to return  (default: 20)
#   source = filter by source           (serp_news / biotech_news / clinical_trials)
#
# Example: GET /api/raw-data?limit=10&source=serp_news

@bp.route("/api/raw-data", methods=["GET"])
def get_raw_data():
    limit  = int(request.args.get("limit", 20))
    source = request.args.get("source", None)

    items = _raw_cache
    if source:
        items = [i for i in items if i.get("source") == source]

    return jsonify({
        "status":       "success",
        "total":        len(items[:limit]),
        "last_fetched": _last_fetched or "never",
        "items":        items[:limit],
    }), 200


# ── POST /api/signals ─────────────────────────────────────────────────────────
# AI agent POSTs structured market signals here after processing.
#
# Request body:
# {
#   "signals": [
#     {
#       "id": "abc123",
#       "company_name": "Merck",
#       "drug_name": "Keytruda",
#       "event_type": "clinical_trial",
#       "impact_level": "high",
#       "headline": "Keytruda hits endpoint in TNBC Phase 3",
#       "summary": "2-3 sentence summary...",
#       "source_url": "https://...",
#       "published_at": "2025-05-20",
#       "tags": ["phase-3", "immunotherapy"]
#     }
#   ]
# }

@bp.route("/api/signals", methods=["POST"])
def store_signals():
    global _signals_store

    body = request.get_json(silent=True)
    if not body or "signals" not in body:
        return jsonify({"status": "error", "message": "Send JSON with a 'signals' list"}), 400

    _signals_store = body["signals"]
    print(f"[Routes] Stored {len(_signals_store)} signals")

    return jsonify({"status": "success", "stored": len(_signals_store)}), 200


# ── GET /api/signals ──────────────────────────────────────────────────────────
# dashboard calls this to get signal cards.
#
# Query params:
#   limit       = number of signals   (default: 20)
#   impact      = high / medium / low
#   event_type  = clinical_trial / funding / drug_approval / research_paper / partnership
#
# Example: GET /api/signals?impact=high&limit=10

@bp.route("/api/signals", methods=["GET"])
def get_signals():
    limit       = int(request.args.get("limit", 20))
    impact      = request.args.get("impact", None)
    event_type  = request.args.get("event_type", None)

    signals = _signals_store

    if impact:
        signals = [s for s in signals if s.get("impact_level") == impact]
    if event_type:
        signals = [s for s in signals if s.get("event_type") == event_type]

    return jsonify({
        "status":       "success",
        "total":        len(signals[:limit]),
        "last_updated": _last_fetched or "never",
        "signals":      signals[:limit],
    }), 200


# ── GET /api/status ───────────────────────────────────────────────────────────
# Quick debug check — shows what's in cache right now.

@bp.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "raw_items_cached": len(_raw_cache),
        "signals_stored":   len(_signals_store),
        "last_fetched":     _last_fetched or "never",
    }), 200


# ── Helper ────────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc).isoformat()
