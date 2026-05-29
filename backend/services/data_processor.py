import os
import json
from openai import OpenAI
from backend.config import Config
"""
Doc: https://docs.aimlapi.com/
"""
class DataProcessor:
    def __init__(self):
        """
        Initializes the AI/ML API client to process raw web data into business signals.
        """
        # Read the API key from the centralized Config class
        self.api_key = Config.AIML_API_KEY
        
        # Pre-flight check: Halt execution if the key is missing
        if not self.api_key or self.api_key.strip() == "":
            print("\n[-] CRITICAL ERROR: AIML_API_KEY is missing in the configuration!")
            print("    Please add AIML_API_KEY=your_real_key to the .env file.\n")
            raise ValueError("Missing or invalid AI/ML API Key.")
        
        # AI/ML API uses the standard OpenAI SDK, just pointing to their URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.aimlapi.com" 
        )
        
        # We use a fast, smart model available on AI/ML API
        self.model = "gpt-4o" 

    def extract_signals(self, serp_data: dict) -> list:
        """
        Takes the raw wrapper from Bright Data, hunts down the 'news' array, 
        and uses LLM to find business or clinical signals.
        """
        import json
        print("[*] Processing raw data with AI/ML API...")
        
        # --- Built-in function to search for 'news' throughout the JSON ---
        def find_news_list(obj):
            if isinstance(obj, dict):
                if "news" in obj and isinstance(obj["news"], list):
                    return obj["news"]
                for key, value in obj.items():
                    if isinstance(value, str):
                        try:
                            # Try to parse the JSON if Bright Data has converted it to a string
                            parsed = json.loads(value)
                            res = find_news_list(parsed)
                            if res: return res
                        except json.JSONDecodeError:
                            pass
                    else:
                        res = find_news_list(value)
                        if res: return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_news_list(item)
                    if res: return res
            return []
        # -----------------------------------------------------------------

        # 1. We use our smart search engine
        news_list = find_news_list(serp_data)
        
        if not news_list:
            print("[-] No news found to process. Bright Data returned empty or blocked.")
            return []

        # 2. We're preparing a clean text for the AI
        context_text = ""
        for article in news_list:
            context_text += f"- Title: {article.get('title')}\n"
            context_text += f"  Source: {article.get('source')}\n"
            context_text += f"  Description: {article.get('description')}\n\n"

        # 3. The "Business Value" Challenge (GTM Track) - Using the strict Pydantic format
        system_prompt = """
        You are an expert Oncology Market Intelligence Agent. 
        Read the provided news updates about TNBC (Triple-Negative Breast Cancer).
        Extract key business signals.
        Return a JSON object containing a SINGLE array named "signals".
        EACH object inside the "signals" array MUST have exactly these keys:
        - "trial_id" (String: Ex: 'NCT0123' or 'Phase 2 Alert')
        - "company" (String: Name of the biotech/pharma)
        - "phase" (String: 'Phase 1', 'Phase 2', 'Pre-clinical', etc.)
        - "summary" (String: One sentence business summary of the news)
        - "confidence_score" (Float between 0.5 and 1.0 based on source reliability)
        """

        try:
            # 4. Call for AI
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={ "type": "json_object" }, # Force le format JSON
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the daily data:\n{context_text}"}
                ]
            )
            
            # 5. We return the cleaned result (by isolating the "signals" array)
            ai_result = json.loads(response.choices[0].message.content).get("signals", [])
            print(f"[+] {len(ai_result)} signals successfully extracted by AI.")
            return ai_result

        except Exception as e:
            print(f"[-] AI Processing Error: {e}")
            return [{"error": "Failed to process data"}]
        
# --- Quick test block ---
if __name__ == "__main__":
    print("[*] Starting DataProcessor standalone test...")
    
    file_path = "test_output.json"
    
    if not os.path.exists(file_path):
        print(f"[-] File '{file_path}' not found. Please run serp_client first.")
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_serp_data = json.load(f)
            
        processor = DataProcessor()
        signals = processor.extract_signals(raw_serp_data)
        
        print("\n[+] Final AI Output (Structured Signals):")
        print(json.dumps(signals, indent=2))