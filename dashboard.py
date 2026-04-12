import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Nexus-Gate Log Viewer", layout="wide", page_icon="🛡️")

st.title("🛡️ Nexus-Gate: Gateway Log Viewer")
st.markdown("Monitor real-time routing decisions, model assignments, and cache efficiency.")

LOG_FILE = "gateway.log"

def load_logs():
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()
    
    data = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                continue
    return pd.DataFrame(data)

# Auto-refresh logic
if st.button("🔄 Refresh Logs"):
    st.rerun()

logs = load_logs()

if not logs.empty:
    # Summary Metrics
    total_reqs = len(logs)
    cache_hits = len(logs[logs['cache_hit'] == True])
    avg_latency = logs['latency_ms'].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", total_reqs)
    col2.metric("Cache Hit Rate", f"{(cache_hits/total_reqs)*100:.1f}%")
    col3.metric("Avg Latency", f"{avg_latency:.0f} ms")

# Log Table
    st.subheader("Recent Request History")
    
    # Process metadata for display
    display_logs = logs.copy()
    if 'metadata' in display_logs.columns:
        display_logs['semantic_score'] = display_logs['metadata'].apply(lambda x: x.get('semantic_anchor', None) if isinstance(x, dict) else None)
    else:
        display_logs['semantic_score'] = None
    
    # Reverse logs for latest first
    st.dataframe(
        display_logs.iloc[::-1], 
        width="stretch",
        column_config={
            "timestamp": "Time",
            "prompt_snippet": "Prompt",
            "model": "Model Used",
            "reason": "Routing Reason",
            "semantic_score": st.column_config.NumberColumn("Semantic Complexity", format="%.3f"),
            "latency_ms": st.column_config.NumberColumn("Latency (ms)", format="%d"),
            "cache_hit": "Cache Hit?"
        }
    )
else:
    st.info("No logs found. Send some prompts to the gateway to see them here!")
    st.code("curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"user_id\": \"test\", \"text\": \"hello\"}'")

