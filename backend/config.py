import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BRIGHT_DATA_API_KEY       = os.getenv("BRIGHT_DATA_API_KEY", "")
    BRIGHT_DATA_SERP_URL      = "https://api.brightdata.com/serp/google"
    BRIGHT_DATA_UNLOCKER_URL  = "https://api.brightdata.com/request"
    BRIGHT_DATA_UNLOCKER_ZONE = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "web_unlocker1")
    BRIGHT_DATA_BROWSER_WS    = os.getenv("BRIGHT_DATA_BROWSER_WS", "")

    DEBUG      = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    PORT       = int(os.getenv("PORT", 5000))
    SECRET_KEY = os.getenv("SECRET_KEY", "oncomarket-dev-secret")
