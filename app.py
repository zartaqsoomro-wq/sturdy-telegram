import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from processor import fetch_market_signals, feed_knowledge_graph, format_signals_to_df, chat_with_agent

CACHE_FILE = "latest_signals_cache.json"

def load_local_cache() -> pd.DataFrame:
    """Loads data from the local JSON file if it exists, otherwise returns empty DataFrame."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception:
            pass
    return pd.DataFrame(columns=["Trial ID", "Company", "Phase", "Summary", "Confidence Score"])

def save_local_cache(df: pd.DataFrame):
    """Saves the current dataframe safely to a local JSON file."""
    try:
        records = df.to_dict(orient="records")
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def render_custom_header():
    """Renders a stylized custom header for the dashboard."""
    st.markdown("""
        <style>
        .custom-title { font-family: 'sans-serif'; padding-bottom: 20px; font-size: 2.8rem; font-weight: 700; }
        </style>
        <div class="custom-title">OncoMarket Intelligence Hub 🧬</div>
    """, unsafe_allow_html=True)
    st.divider()

def configure_page():
    st.set_page_config(page_title="OncoMarket Intelligence Hub", layout="wide")
    render_custom_header()
    
    st.sidebar.write("### System Controls")
    sync_button = st.sidebar.button("🔄 Sync Live Data", type="primary", use_container_width=True)
        
    if sync_button:
        with st.spinner("📡 Step 1: Web Scraping & AI Extraction (~5s)..."):
            signals = fetch_market_signals()
            new_data = format_signals_to_df(signals)
            
            # Immediate physical backup to local storage
            save_local_cache(new_data)
            
            # Store raw signals for Cognee processing later in the pipeline
            st.session_state.raw_signals = signals
            st.session_state.signals_df = new_data
            st.session_state.last_synced = datetime.now().strftime("%H:%M:%S")
            
            # 🚩 Flag to trigger Cognee at the end of the page render loop
            st.session_state.needs_cognify = True
            
        # Force immediate UI refresh to display the data table
        st.rerun()
        
    if "last_synced" in st.session_state:
        st.sidebar.caption(f"Last synced: {st.session_state.last_synced}")

def main():
    configure_page()
    
    st.markdown("""<style>[data-testid="stMetricValue"] { color: #2196F3 !important; }</style>""", unsafe_allow_html=True)

    # FAILSAFE: Load from local JSON file if browser memory gets wiped out
    if "signals_df" not in st.session_state:
        st.session_state.signals_df = load_local_cache()

    signals_df = st.session_state.signals_df

    # Metrics Layout (Dynamically reading from active data state)
    total_trials = str(len(signals_df))
    high_conf_count = str(len(signals_df[signals_df["Confidence Score"] >= 0.90])) if not signals_df.empty else "0"
    avg_conf = f"{signals_df['Confidence Score'].mean():.2f}" if not signals_df.empty else "0.00"

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Trials", total_trials)
    col2.metric("High-Confidence Signals", high_conf_count)
    col3.metric("Average Confidence", avg_conf)
    
    st.divider()
    
    # Safe fallback view if the application has never been synchronized once
    if signals_df.empty:
        st.info("👋 Welcome! Click 'Sync Live Data' in the sidebar to run the automated intelligence pipeline.")
        return

    # Data display & filtering setup
    st.subheader("Market Signals")
    st.sidebar.divider()
    st.sidebar.subheader("Filter Market Signals")
    
    available_companies = signals_df["Company"].unique().tolist()
    selected_companies = st.sidebar.multiselect("Select Companies:", options=available_companies, default=available_companies)
    confidence_threshold = st.sidebar.slider("Minimum Confidence Score:", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
    
    filtered_df = signals_df[(signals_df["Company"].isin(selected_companies)) & (signals_df["Confidence Score"] >= confidence_threshold)]
    
    st.dataframe(filtered_df, width="stretch", hide_index=True, column_config={"Summary": st.column_config.TextColumn("Trial Summary", width="large")})
    
    # Visual Data Storytelling section
    st.divider()
    st.subheader("Market Signal Profiling")
    import plotly.express as px
    chart_col1, chart_col2 = st.columns(2)
    if not filtered_df.empty:
        with chart_col1:
            fig_pie = px.pie(filtered_df, names='Phase', title='Clinical Phase Distribution', hole=0.4)
            fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, width="stretch")
        with chart_col2:
            sorted_df = filtered_df.sort_values('Confidence Score', ascending=False)
            fig_bar = px.bar(sorted_df, x='Company', y='Confidence Score', color='Phase', title='Confidence by Sponsor', text='Confidence Score')
            fig_bar.update_layout(yaxis_range=[0, 1.05], margin=dict(t=40, b=0, l=0, r=0))
            fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            st.plotly_chart(fig_bar, width="stretch")
            
    # Deep Dive Focus: Trial Inspector
    st.divider()
    st.subheader("Deep Dive: Trial Inspector")
    trial_ids = filtered_df["Trial ID"].tolist()
    if trial_ids:
        selected_trial_id = st.selectbox("Select a Trial ID to inspect:", options=trial_ids)
        if selected_trial_id:
            trial_row = filtered_df[filtered_df["Trial ID"] == selected_trial_id].iloc[0]
            with st.expander(f"📄 Detailed Profile: {selected_trial_id} ({trial_row['Company']})", expanded=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(f"**🏥 Company:** {trial_row['Company']}\n**🔬 Phase:** {trial_row['Phase']}\n**📈 Confidence:** `{trial_row['Confidence Score']:.2f}`")
                with c2:
                    st.markdown("**📝 Trial Summary:**")
                    st.info(trial_row['Summary'])
    
    # RAG Graph Chat Interface
    st.divider()
    st.subheader("Agent Intelligence")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    chat_container = st.container()
    with st.form(key="agent_chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask the agent about TNBC trends:", key="tnbc_input")
        submit_button = st.form_submit_button(label="Ask Analyst")
    
    if submit_button and user_input:
        with st.spinner("🧠 Agent is querying the Cognee Knowledge Graph..."):
            response_text = chat_with_agent(user_input, signals_df)
        st.session_state.chat_history.append({"query": user_input, "response": response_text})
        st.session_state.chat_history = st.session_state.chat_history[-5:]
        
    with chat_container:
        for chat in st.session_state.chat_history:
            st.markdown(f"**👤 You:** {chat['query']}\n**🧬 Analyst:** {chat['response']}")
            st.write("---")

    # ---------------------------------------------------------
    # SEQUENTIAL RENDERING (Executed safely AFTER UI loading)
    # ---------------------------------------------------------
    if st.session_state.get("needs_cognify", False):
        st.divider()
        with st.spinner("🧠 Agent is updating Knowledge Graph with new data (takes ~60s, you can continue exploring the dashboard)..."):
            feed_knowledge_graph(st.session_state.raw_signals)
        st.session_state.needs_cognify = False
        st.toast("✅ Knowledge Graph updated successfully!")

if __name__ == "__main__":
    main()