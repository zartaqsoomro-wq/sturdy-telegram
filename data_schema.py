from pydantic import BaseModel
from typing import List, Optional

class MarketSignal(BaseModel):
    trial_id: str
    company: str
    phase: str
    summary: str
    confidence_score: float

# This ensures the scraper and processor speak the same language
