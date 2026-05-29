import streamlit as st
import pandas as pd
import time
from datetime import datetime
from processor import get_latest_signals, chat_with_agent

def run_sync():
    with st.spinner("Syncing data with Bright Data..."):
        time.sleep(2)  # Simulate API delay
    return "Data synchronized successfully!"

def render_custom_header():
    """Renders a stylized custom header for the dashboard."""
    st.markdown("""
        <style>
        .custom-title {
            font-family: 'sans-serif';
            padding-bottom: 20px;
            font-size: 2.8rem;
            font-weight: 700;
        }
        </style>
        <div class="custom-title">OncoMarket Intelligence Hub 🧬</div>
    """, unsafe_allow_html=True)
    st.divider()

def configure_page():
    st.set_page_config(page_title="OncoMarket Intelligence Hub", layout="wide")
    render_custom_header()
    # ---------------- Sidebar Sync Form ----------------
    with st.sidebar.form(key="sync_data_form"):
        st.write("System Controls")
        sync_button = st.form_submit_button("Sync Data")
        
    if sync_button:
        status = run_sync()
        # Use a toast notification instead of a permanent success box
        st.toast("Data synchronized successfully!", icon="✅")
        
        # Record the sync time in session state
        st.session_state.last_synced = datetime.now().strftime("%I:%M %p")
        
    # Display the timestamp if it exists in session state
    if "last_synced" in st.session_state:
        st.sidebar.caption(f"Last synced: {st.session_state.last_synced}")

def main():
    configure_page()
    
    # Custom CSS to make metric values blue
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            color: #2196F3 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Trials", "12")
    col2.metric("New Signals", "3")
    col3.metric("System Status", "Online")
    
    st.divider()
    
    # Data display
    st.subheader("Market Signals")
    signals_df = get_latest_signals()
    
    # ---------------- Sidebar Filters ----------------
    st.sidebar.divider()
    st.sidebar.subheader("Filter Market Signals")
    
    # Get unique companies for the multiselect
    available_companies = signals_df["Company"].unique().tolist()
    selected_companies = st.sidebar.multiselect(
        "Select Companies:", 
        options=available_companies, 
        default=available_companies
    )
    
    # Slider for Confidence Score
    confidence_threshold = st.sidebar.slider(
        "Minimum Confidence Score:", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.85, 
        step=0.01
    )
    
    # ---------------- Apply Filters ----------------
    filtered_df = signals_df[
        (signals_df["Company"].isin(selected_companies)) & 
        (signals_df["Confidence Score"] >= confidence_threshold)
    ]
    
    # ---------------- Proactive Alerting ----------------
    # Check for high-confidence/opportunity signals
    high_conf_trials = filtered_df[filtered_df["Confidence Score"] >= 0.90]
    if not high_conf_trials.empty:
        companies_str = ", ".join(high_conf_trials["Company"].unique())
        st.success(f"🟢 **High-Confidence Signals Detected:** {len(high_conf_trials)} trial(s) from {companies_str} are showing ≥ 0.90 confidence.")
        
    # Check for high-risk signals
    low_conf_trials = filtered_df[filtered_df["Confidence Score"] <= 0.85]
    if not low_conf_trials.empty:
        st.warning(f"⚠️ **High-Risk Signals Detected:** {len(low_conf_trials)} trial(s) are showing ≤ 0.85 confidence. Proceed with caution.")
    
    # 5. Render the dataframe with custom column configurations
    st.dataframe(
        filtered_df, 
        use_container_width=True,
        hide_index=True, # Often looks cleaner
        column_config={
            "Summary": st.column_config.TextColumn(
                "Trial Summary",
                width="large", # This forces the column to take up more horizontal space
                help="The clinical trial description and target."
            )
        }
    )
    
    # 6. Export Functionality
    # Convert the filtered dataframe to CSV bytes
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    
    # Provide the download button
    st.download_button(
        label="⬇️ Download Filtered Data (CSV)",
        data=csv_data,
        file_name="oncomarket_signals_export.csv",
        mime="text/csv",
        help="Export the current table view to CSV for offline modeling."
    )
    
    # ---------------- Visual Data Storytelling ----------------
    st.divider()
    st.subheader("Market Signal Profiling")
    
    # Import plotly here to avoid breaking the top-level if the package is missing
    import plotly.express as px
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Phase Distribution Pie Chart (Donut style)
        fig_pie = px.pie(
            filtered_df, 
            names='Phase', 
            title='Clinical Phase Distribution',
            hole=0.4, # Creates the donut look
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        # Clean up the layout for a premium feel
        fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with chart_col2:
        # Confidence Score Bar Chart
        # Sorting by confidence score to make the trend visually obvious
        sorted_df = filtered_df.sort_values('Confidence Score', ascending=False)
        fig_bar = px.bar(
            sorted_df, 
            x='Company', 
            y='Confidence Score', 
            color='Phase',
            title='Confidence by Sponsor',
            text='Confidence Score', # Display the number on the bar
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        # Cap the y-axis at 1.0 since it's a probability score
        fig_bar.update_layout(
            yaxis_range=[0, 1.05],
            margin=dict(t=40, b=0, l=0, r=0)
        )
        # Format the text on the bars
        fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    # ---------------- Deep Dive: Trial Inspector ----------------
    st.divider()
    st.subheader("Deep Dive: Trial Inspector")
    
    # Create a dropdown menu using the Trial IDs from our filtered view
    trial_ids = filtered_df["Trial ID"].tolist()
    
    if trial_ids:
        selected_trial_id = st.selectbox(
            "Select a Trial ID to inspect:", 
            options=trial_ids,
            help="Choose a trial to see isolated, deep-focus information."
        )
        
        # When a user selects one, extract its specific row data
        if selected_trial_id:
            trial_row = filtered_df[filtered_df["Trial ID"] == selected_trial_id].iloc[0]
            
            # Display cleanly formatted data inside an expander
            with st.expander(f"📄 Detailed Profile: {selected_trial_id} ({trial_row['Company']})", expanded=True):
                card_col1, card_col2 = st.columns([1, 2])
                
                with card_col1:
                    st.markdown(f"**🏥 Company:** {trial_row['Company']}")
                    st.markdown(f"**🔬 Phase:** {trial_row['Phase']}")
                    st.markdown(f"**📈 Confidence:** `{trial_row['Confidence Score']:.2f}`")
                    
                with card_col2:
                    st.markdown("**📝 Trial Summary:**")
                    st.info(trial_row['Summary'])
    else:
        st.warning("No trials match the current sidebar filters.")
    
    # ---------------- Chat Interface ----------------
    st.divider()
    st.subheader("Agent Intelligence")
    
    # 1. Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    # 2. Create a container to hold the conversation above the input box
    chat_container = st.container()
    
    # ---------------- Chat Form ----------------
    # clear_on_submit=True automatically clears the input box after sending
    with st.form(key="agent_chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask the agent about TNBC trends:", key="tnbc_input_unique")
        submit_button = st.form_submit_button(label="Ask Analyst")
    
    # 3. Process new inputs
    if submit_button and user_input:
        with st.spinner("Agent is querying knowledge graph..."):
            response_text = chat_with_agent(user_input, signals_df)
        
        # Add the new interaction to the list
        st.session_state.chat_history.append({"query": user_input, "response": response_text})
        
        # Keep only the last 5 interactions to prevent the screen from getting too long
        st.session_state.chat_history = st.session_state.chat_history[-5:]
        
    # 4. Render the conversation history inside the container
    with chat_container:
        for chat in st.session_state.chat_history:
            st.markdown(f"**👤 You:** {chat['query']}")
            st.markdown(f"**🧬 Analyst:** {chat['response']}")
            st.write("---") # Subtle visual separator between messages

if __name__ == "__main__":
    main()
