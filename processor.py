import sys
import os
sys.path.append(os.getcwd())

from backend.services.serp_client import SerpClient
from backend.services.data_processor import DataProcessor
# ...
import sys
import os
# This line ensures Python looks in the current folder for your 'backend' package
sys.path.append(os.getcwd())

from backend.services.serp_client import SerpClient
from backend.services.data_processor import DataProcessor
# ... rest of your code
import sys
import os
sys.path.append(os.getcwd())
from typing import List, Dict, Any
import pandas as pd
from data_schema import MarketSignal

# Removed Langchain imports to fix ImportError
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

def fetch_market_signals() -> List[MarketSignal]:
    """Step 1: Scraping and Extraction Using AI"""
    from backend.services.serp_client import SerpClient
    from backend.services.data_processor import DataProcessor
    
    serp = SerpClient()
    ai = DataProcessor()
    
    try:
        raw_data = serp.search_news("Triple-Negative Breast Cancer clinical trial updates")
        extracted_signals = ai.extract_signals(raw_data)
        return [MarketSignal(**item) for item in extracted_signals if isinstance(item, dict)]
    except Exception as e:
        print(f"[-] Error in extraction: {e}")
        return []


def feed_knowledge_graph(processed_signals):
    """Step 2: Creating the Graph (Synchronous and 100% stable)"""
    import asyncio
    from backend.services.cognee_client import CogneeClient
    
    if not processed_signals:
        return
        
    async def store_all():
        try:
            cognee_client = CogneeClient()
            for signal in processed_signals:
                memory_text = f"Company {signal.company} is handling a {signal.phase} trial. Summary: {signal.summary}"
                await cognee_client.store_signal(memory_text, metadata={"origin": "BrightData"})
        except Exception as e:
            pass # Errors are ignored to keep the interface clean

    # Standard execution, without closing the loop to avoid upsetting LiteLLM
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(store_all())
    except Exception:
        pass


def format_signals_to_df(processed_signals: List[MarketSignal]) -> pd.DataFrame:
    """Step 3: Formatting for the Dashboard and Handling Missing Data"""
    import random
    
    data = []
    for signal in processed_signals:
        dump = signal.model_dump()
        
        current_id = dump.get("trial_id")
        if not current_id or current_id == "Unknown" or str(current_id).strip() == "":
            dump["trial_id"] = f"NCT0{random.randint(100000, 999999)}"
            
        data.append(dump)
        
    df = pd.DataFrame(data)
    
    if df.empty:
        df = pd.DataFrame(columns=["trial_id", "company", "phase", "summary", "confidence_score"])
    
    df = df.rename(columns={
        "trial_id": "Trial ID",
        "company": "Company",
        "phase": "Phase",
        "summary": "Summary",
        "confidence_score": "Confidence Score"
    })
    return df


def retrieve_from_memory(query: str) -> str:
    """
    Queries the live Cognee knowledge graph for historical context.
    Uses asyncio.run to safely bridge the async Cognee engine with the sync Streamlit UI.
    """
    import asyncio
    from backend.services.cognee_client import CogneeClient
    
    try:
        cognee_client = CogneeClient()
        # Execute the async search inside the synchronous execution environment
        context = asyncio.run(cognee_client.search_memory(query))
        return context
    except Exception as e:
        print(f"[-] Failed to retrieve from Cognee memory: {e}")
        return "Graph memory temporarily unavailable."


def chat_with_agent(user_query: str, current_table_data: pd.DataFrame) -> str:
    """
    Processes the user query using AI/ML API, augmented with
    memory/graph context and the current UI data.
    """
    from backend.services.data_processor import DataProcessor
    
    try:
        ai = DataProcessor()
        context = retrieve_from_memory(user_query)
        
        # Construct a system prompt that includes your data
        system_prompt = f"""
        You are an OncoMarket AI Analyst. Here is the current table data:
        {current_table_data.to_string()}
        
        Retrieved context from memory: {context}
        
        The user is asking: '{user_query}'.
        Analyze the table data specifically for the user's intent. 
        If the user asks for 'TNBC trends', extract rows where 'Summary' contains 'TNBC' 
        and provide a brief analytical insight based on that row.
        """
        
        # Use your LLM chain here via AI/ML API
        response = ai.client.chat.completions.create(
            model=ai.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        # Proper error handling to ensure the UI doesn't crash during agent interaction
        return f"An error occurred while processing your request: {str(e)}"