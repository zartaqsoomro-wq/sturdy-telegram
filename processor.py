from typing import List, Dict, Any
import pandas as pd
from data_schema import MarketSignal

# Removed Langchain imports to fix ImportError
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

def get_latest_signals() -> pd.DataFrame:
    """
    Retrieves the latest market signals.
    Queries Google News via Bright Data and processes with AI/ML API.
    
    Returns:
        pd.DataFrame: A DataFrame of MarketSignal objects formatted for the UI.
    """
    from backend.services.serp_client import SerpClient
    from backend.services.data_processor import DataProcessor
    
    try:
        serp = SerpClient()
        ai = DataProcessor()
        
        # Fetch real-world clinical trial data from Bright Data
        raw_data = serp.search_news("Triple-Negative Breast Cancer clinical trial updates")
        extracted_signals = ai.extract_signals(raw_data)
        
        # Process into MarketSignal models to ensure schema validity
        processed_signals = [MarketSignal(**item) for item in extracted_signals if isinstance(item, dict)]
    except Exception as e:
        print(f"[-] Error in pipeline: {e}")
        processed_signals = []
    
    # ---------------------------------------------------------
    # BACKGROUND MEMORY FEEDING (Non-blocking for UI)
    # ---------------------------------------------------------
    import threading
    import asyncio
    
    def background_memory_task(signals):
        """Function executed in background to prevent blocking Streamlit"""
        from backend.services.cognee_client import CogneeClient
        async def store_all():
            try:
                cognee_client = CogneeClient()
                for signal in signals:
                    memory_text = f"Company {signal.company} is handling a {signal.phase} trial. Summary: {signal.summary}"
                    # We trigger the cognify process without holding up the UI
                    await cognee_client.store_signal(memory_text)
            except Exception as e:
                print(f"[-] Background memory failed: {e}")
        
        # Run the async loop inside this background thread
        asyncio.run(store_all())

    # Start the daemon thread if we have signals (it dies gracefully when app stops)
    if processed_signals:
        threading.Thread(target=background_memory_task, args=(processed_signals,), daemon=True).start()
    # ---------------------------------------------------------

    # Convert list of Pydantic models to a list of dicts, then to a DataFrame
    # so Streamlit can easily render it as a table.
    data = [signal.model_dump() for signal in processed_signals]
    df = pd.DataFrame(data)
    
    # Fallback to prevent UI crash if no data is returned
    if df.empty:
        df = pd.DataFrame(columns=["trial_id", "company", "phase", "summary", "confidence_score"])
    
    # Reorder and rename columns for a professional UI presentation
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