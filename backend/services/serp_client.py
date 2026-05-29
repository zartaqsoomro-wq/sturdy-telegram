import requests
import json
from backend.config import Config
"""
Doc: https://docs.brightdata.com/scraping-automation/serp-api/introduction
"""
class SerpClient:
    def __init__(self):
        """
        Initializes the Bright Data SERP API client using the REST API.
        Performs a pre-flight check on credentials.
        """
        self.api_key = Config.BRIGHT_DATA_API_KEY
        self.endpoint = Config.BRIGHT_DATA_SERP_URL
        
        # Pre-flight check: Prevent unnecessary HTTP requests if the key is missing
        if not self.api_key or self.api_key == "CLE_API_PROVISOIRE" or self.api_key.strip() == "":
            print("\n[-] CRITICAL ERROR: Bright Data API Key is missing!")
            print("    Please add BRIGHT_DATA_API_KEY=your_real_key to the .env file.\n")
            raise ValueError("Missing or invalid Bright Data API Key.")

        # Set up the headers for authentication
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search_news(self, query: str) -> dict:
        """
        Fetches Google News search results using Bright Data Universal API (/request).
        """
        import urllib.parse
        print(f"[*] Fetching SERP data for query: '{query}'")
        
        encoded_query = urllib.parse.quote(query)
        
        google_url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&hl=en&gl=us&brd_json=1"
        
        payload = {
            "zone": "serp_api1",
            "url": google_url,
            "format": "json",
            "data_format": "parsed"
        }
        
        try:
            response = requests.post(
                self.endpoint, 
                headers=self.headers, 
                json=payload,
                timeout=45
            )
            response.raise_for_status()
            
            print("[+] Successfully fetched data from Bright Data.")
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[-] Error fetching SERP data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"    API Response: {e.response.text}")
            return {"news": []}

# --- Quick test block ---
if __name__ == "__main__":
    import json
    
    client = SerpClient()
    results = client.search_news("Triple-Negative Breast Cancer clinical trial")
    
    # We save the complete result to a local JSON file
    with open("test_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n[+] The data has been saved to the 'test_output.json' file in the root directory of your project. !")
    print("    Open this file in your code editor to explore its structure.")