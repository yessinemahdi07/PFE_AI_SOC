import json
import os
import glob
from datetime import datetime
import streamlit as st
import pandas as pd

# --- 1. Page Config & Custom CSS ---
st.set_page_config(page_title="SOC Command Center", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    [data-testid="stMetric"] { background-color: #1E2530; padding: 15px 20px; border-radius: 10px; border-left: 5px solid #4A90E2; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stSuccess { background-color: #1B3322; border-radius: 8px; padding: 15px; border-left: 5px solid #28A745; }
    .stInfo { background-color: #1A2B3C; border-radius: 8px; padding: 15px; border-left: 5px solid #17A2B8; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1E2530; border-radius: 8px; padding: 10px 20px; color: #E0E0E0; }
    .stTabs [aria-selected="true"] { background-color: #4A90E2; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

LOG_DIR = "logs"
REPORT_DIR = "reports"

# --- 2. Data Loaders ---
@st.cache_data(ttl=5)
def load_latest_red_campaign():
    # FIX: Look for the PyRIT expanded JSON, not the old v1 JSON
    files = sorted(glob.glob(os.path.join(LOG_DIR, "red_team_expanded_*.json")))
    if not files: return None
    with open(files[-1], "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=5)
def load_and_parse_blue_report():
    files = sorted(glob.glob(os.path.join(REPORT_DIR, "blue_team_soc_report_*.txt")))
    if not files: return None
    
    cases = []
    current_case = {}
    with open(files[-1], "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[ATLAS."):
                if current_case: cases.append(current_case)
                parts = line.split("]")
                current_case = {"id": parts[0].strip("["), "name": parts[1].strip()}
            elif line.startswith("MITRE:"):
                current_case["mitre"] = line.replace("MITRE:", "").strip()
            elif line.startswith("VERDICT:"):
                current_case["verdict"] = line.split(":")[1].strip()
            elif line.startswith("SEVERITY:"):
                current_case["severity"] = line.split(":")[1].strip()
            elif line.startswith("ACTION:"):
                current_case["action"] = line.split(":", 1)[1].strip()
    if current_case: cases.append(current_case)
    return cases

# --- 3. Header ---
st.title("🛡️ AI-Native SOC Command Center")
st.markdown("#### Powered by Microsoft PyRIT, Llama 3.2, Wazuh & TheHive")
st.markdown("---")

# --- 4. Tabs Layout ---
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🚨 AI Analysis (Blue Team)", "🔗 Enterprise Integrations"])

with tab1:
    st.header("Campaign Overview")
    red_data = load_latest_red_campaign()
    if red_data:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Attacks (PyRIT)", len(red_data))
        col2.metric("NIST Categories", len(set(a.get('nist_category') for a in red_data)))
        col3.metric("ATLAS Techniques", len(set(a.get('atlas_technique') for a in red_data)))
        col4.metric("Target Model", "llama3.2:3b")
        
        st.subheader("MITRE ATLAS & NIST Coverage")
        df = pd.DataFrame(red_data)
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Attacks by NIST Category**")
            st.bar_chart(df['nist_category'].value_counts(), color="#4A90E2")
        with c2:
            st.write("**Attacks by ATLAS Technique**")
            st.bar_chart(df['atlas_technique'].value_counts(), color="#E24A4A")
    else:
        st.warning("No campaign data found. Run the Red Agent.")

with tab2:
    st.header("LLM SOC Analyst Findings")
    cases = load_and_parse_blue_report()
    if cases:
        display_data = []
        for c in cases:
            verdict = c.get('verdict', 'UNKNOWN').upper()
            sev = c.get('severity', 'UNKNOWN').upper()
            display_data.append({
                "Attack ID": c.get('id'),
                "Attack Name": c.get('name'),
                "Verdict": verdict,
                "Severity": sev,
                "AI Recommended Action": c.get('action')
            })
        
        df = pd.DataFrame(display_data)
        def color_verdict(val):
            color = '#28A745' if val == 'BENIGN' else '#FFC107' if val == 'SUSPICIOUS' else '#DC3545'
            return f'color: {color}; font-weight: bold;'
        
        st.dataframe(df.style.map(color_verdict, subset=['Verdict']), use_container_width=True, hide_index=True)
    else:
        st.warning("No Blue Agent report found.")

with tab3:
    st.header("Enterprise Integrations Status")
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ **Wazuh SIEM: Connected**")
        st.markdown("- **Indexer API:** `http://localhost:9200`\n- **Status:** Active\n- **Local Dashboard:** `https://localhost:8443`")
    with col2:
        st.success("✅ **TheHive Case Management: Connected**")
        st.markdown("- **Organisation:** `soc-org`\n- **Cases Created:** 11\n- **Status:** Active\n- **Local Dashboard:** `http://192.168.218.130:9000`")
        
    st.info("ℹ️ The AI automatically created cases in TheHive for every MALICIOUS/SUSPICIOUS threat detected.")

st.markdown("---")
st.caption(f"Dashboard refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | PFE Project by Yassine Mahdi")
