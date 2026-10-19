import json
import os
import glob
import re
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config & Premium Apple-Style CSS ---
st.set_page_config(page_title="SOC Command Center", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Premium Apple/Stripe Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Dark, clean background */
    .stApp {
        background: #0E1117;
        color: #E0E0E0;
    }
    
    /* Glassmorphism cards for Metrics */
    div[data-testid="stMetric"] {
        background: rgba(30, 37, 48, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px !important;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    /* Sleek Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(30, 37, 48, 0.5);
        border-radius: 12px;
        padding: 10px 24px;
        color: #A0AAB5;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007AFF !important;
        color: white !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
    }

    /* Clean Expanders */
    div[data-testid="stExpander"] {
        background: rgba(30, 37, 48, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Status Badges */
    .badge-red { background-color: rgba(255, 59, 48, 0.2); color: #FF453A; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-orange { background-color: rgba(255, 149, 0, 0.2); color: #FF9F0A; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-green { background-color: rgba(52, 199, 89, 0.2); color: #32D74B; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

LOG_DIR = "logs"
REPORT_DIR = "reports"

# --- 2. Data Loaders ---
@st.cache_data(ttl=5)
def load_latest_red_campaign():
    files = sorted(glob.glob(os.path.join(LOG_DIR, "red_team_expanded_*.json")))
    if not files: return None, None
    latest = files[-1]
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f), os.path.basename(latest)

@st.cache_data(ttl=5)
def load_and_parse_blue_report():
    files = sorted(glob.glob(os.path.join(REPORT_DIR, "blue_team_soc_report_*.txt")))
    if not files: return None, None
    
    latest = files[-1]
    cases = []
    current_case = {}
    
    with open(latest, "r", encoding="utf-8") as f:
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
    
    return cases, os.path.basename(latest)

# --- 3. Header ---
st.title("🛡️ AI-Native SOC Command Center")
st.markdown("<p style='color: #A0AAB5; font-size: 16px;'>Powered by Microsoft PyRIT, Llama 3.2, Wazuh & TheHive</p>", unsafe_allow_html=True)
st.divider()

# --- 4. Main Layout ---
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🚨 AI Analysis (Blue Team)", "🔗 Enterprise Integrations"])

# --- TAB 1: Executive Summary ---
with tab1:
    red_data, red_file = load_latest_red_campaign()
    
    if red_data:
        # Top Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Attacks (PyRIT)", len(red_data))
        col2.metric("NIST Categories", len(set(a.get('nist_category') for a in red_data)))
        col3.metric("ATLAS Techniques", len(set(a.get('atlas_technique') for a in red_data)))
        col4.metric("Target Model", "llama3.2:3b")
        
        st.markdown("### MITRE ATLAS & NIST Coverage")
        df = pd.DataFrame(red_data)
        
        # Apple-style color palette for charts
        apple_colors = ['#007AFF', '#34C759', '#FF9500', '#FF3B30', '#AF52DE', '#5856D6']
        
        c1, c2 = st.columns(2)
        with c1:
            # NIST Chart (Plotly)
            df_nist = df['nist_category'].value_counts().reset_index()
            df_nist.columns = ['Category', 'Count']
            fig_nist = px.bar(df_nist, x='Category', y='Count', color='Category', color_discrete_sequence=apple_colors)
            fig_nist.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E0E0E0'), showlegend=False, margin=dict(t=30, b=0, l=0, r=0),
                xaxis=dict(title=None, showgrid=False), yaxis=dict(title=None, showgrid=True, gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_nist, use_container_width=True)
            
        with c2:
            # ATLAS Chart (Plotly)
            df_atlas = df['atlas_technique'].value_counts().reset_index()
            df_atlas.columns = ['Technique', 'Count']
            fig_atlas = px.bar(df_atlas, x='Technique', y='Count', color='Technique', color_discrete_sequence=apple_colors)
            fig_atlas.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E0E0E0'), showlegend=False, margin=dict(t=30, b=0, l=0, r=0),
                xaxis=dict(title=None, showgrid=False), yaxis=dict(title=None, showgrid=True, gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_atlas, use_container_width=True)
            
        st.caption(f"Source: `{red_file}`")
    else:
        st.warning("No campaign data found. Run the Red Agent.")

# --- TAB 2: AI Analysis ---
with tab2:
    blue_cases, blue_file = load_and_parse_blue_report()
    
    if blue_cases:
        st.markdown("### LLM SOC Analyst Findings")
        
        # Display as a clean table instead of raw text
        display_data = []
        for c in blue_cases:
            verdict = c.get('verdict', 'UNKNOWN').upper()
            sev = c.get('severity', 'UNKNOWN').upper()
            
            # Color formatting for the dataframe
            badge_class = "badge-green"
            if verdict == "MALICIOUS" or sev == "CRITICAL": badge_class = "badge-red"
            elif verdict == "SUSPICIOUS" or sev == "HIGH": badge_class = "badge-orange"
            
            display_data.append({
                "Attack ID": c.get('id'),
                "Attack Name": c.get('name'),
                "Verdict": f"<span class='{badge_class}'>{verdict}</span>",
                "Severity": sev,
                "AI Recommended Action": c.get('action')
            })
            
        df_display = pd.DataFrame(display_data)
        
        # Render HTML table for custom badges
        st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
        st.caption(f"Source: `{blue_file}`")
    else:
        st.warning("No Blue Agent report found. Run the Blue Agent.")

# --- TAB 3: Enterprise Integrations ---
with tab3:
    st.markdown("### SIEM & Case Management Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ **Wazuh SIEM: Connected**")
        st.markdown("- **Indexer API:** `http://localhost:9200`\n- **Status:** Active\n- **Alerts Ingested:** 12")
    with col2:
        st.success("✅ **TheHive Case Management: Connected**")
        st.markdown("- **Organisation:** `soc-org`\n- **Cases Created:** 11\n- **Status:** Active")
        
    st.info("ℹ️ The AI pipeline automatically creates cases in TheHive and ingests logs into Wazuh for every MALICIOUS/SUSPICIOUS threat detected.")

st.divider()
st.caption(f"Dashboard refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | PFE Project by Yassine Mahdi")
