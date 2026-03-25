import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Nexus-Gate Live Ops", layout="wide")
st.title("🛡️ Nexus AI Gateway: Live Governance")

# Mock Data for Demo (Replace with your Gateway's /metrics endpoint in the future)
metrics = {
    "Total Requests": 1250,
    "Cost Saved": "$42.30",
    "Avg TTFT": "140ms",
    "Security Blocks": 12
}

# Top KPI Cards
cols = st.columns(4)
cols[0].metric("Total Traffic", metrics["Total Requests"])
cols[1].metric("Net Savings", metrics["Cost Saved"], "+15%")
cols[2].metric("Performance (TTFT)", metrics["Avg TTFT"])
cols[3].metric("Threats Blocked", metrics["Security Blocks"], "-2", delta_color="inverse")

# Live Savings Chart
st.subheader("Financial ROI: Adaptive Triage vs. Flat-Rate Pro")
chart_data = pd.DataFrame({
    'Time': range(10),
    'Flat-Rate Cost': [i * 0.5 for i in range(10)],
    'Nexus-Gate Cost': [i * 0.12 for i in range(10)]
})
st.line_chart(chart_data, x="Time", y=["Flat-Rate Cost", "Nexus-Gate Cost"])

st.success("System Status: HEALING MODE ACTIVE (Auto-failover to Gemini Enabled)")
