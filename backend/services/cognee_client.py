import os
import asyncio
from backend.config import Config

# 1. The key is entered
os.environ["OPENAI_API_KEY"] = Config.AIML_API_KEY
os.environ["LLM_API_KEY"] = Config.AIML_API_KEY
os.environ["OPENAI_API_BASE"] = "https://api.aimlapi.com"

# 2. WE'RE PUSHING THE LIMITS OF THE MODEL
os.environ["LLM_MODEL"] = "gpt-4o"
os.environ["OPENAI_MODEL"] = "gpt-4o"

import cognee

class CogneeClient:
    def __init__(self):
        """
        Initializes the Cognee memory client.
        """
        pass

    async def store_signal(self, text_content: str, metadata: dict = None):
        """
        Adds unstructured market text to Cognee memory and triggers the cognify process.
        """
        print(f"[*] Cognifying new market signal memory into the graph...")
        try:
            # On passe le texte brut et on le traite
            await cognee.add(text_content)
            await cognee.cognify()
            print("[+] Graph memory updated successfully.")
        except Exception as e:
            print(f"[-] Cognee storage error: {e}")

    async def search_memory(self, user_query: str) -> str:
        """
        Searches the vector and graph database for relevant historical business context.
        """
        print(f"[*] Querying Cognee graph memory for: '{user_query}'")
        try:
            results = await cognee.search(user_query)
            
            if not results:
                return "No historical graph context found for this query."
                
            context_string = "Historical Graph Context:\n"
            for result in results:
                # Si le résultat est sous forme de dictionnaire, on extrait le texte
                if isinstance(result, dict) and 'search_result' in result:
                    context_string += f"- {result['search_result'][0]}\n"
                else:
                    context_string += f"- {result}\n"
            return context_string
            
        except Exception as e:
            print(f"[-] Cognee search error: {e}")
            return f"Error retrieving graph memory: {str(e)}"

# --- Quick standalone test ---
if __name__ == "__main__":
    client = CogneeClient()
    
    async def test_pipeline():
        await client.store_signal("AstraZeneca's Datroway received FDA approval for metastatic TNBC on May 2026.")
        context = await client.search_memory("What do we know about AstraZeneca and TNBC?")
        print("\n[+] Retracted Context from Cognee:")
        print(context)

    asyncio.run(test_pipeline())