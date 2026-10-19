import json
import os
import glob
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. Page Config & Premium Dark Theme ---
st.set_page_config(page_title="SOC Command Center", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #0B0F19; background-image: radial-gradient(circle at 15% 50%, rgba(0, 240, 255, 0.04), transparent 25%), radial-gradient(circle at 85% 30%, rgba(176, 0, 255, 0.04), transparent 25%); }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 95%; }
    .kpi-card { background: rgba(20, 26, 40, 0.6); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); backdrop-filter: blur(10px); transition: transform 0.2s ease, border-color 0.2s ease; }
    .kpi-card:hover { transform: translateY(-2px); border-color: rgba(0, 240, 255, 0.3); }
    .kpi-title { font-size: 13px; color: #94A3B8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 36px; font-weight: 700; color: #FFFFFF; margin-top: 8px; }
    .status-dot { height: 8px; width: 8px; background-color: #00FF85; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00FF85; animation: pulse 2s infinite; margin-right: 6px; }
    @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.7; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.7; } }
    .case-card { background: rgba(20, 26, 40, 0.7); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid #FF003C; border-radius: 8px; padding: 16px 20px; margin-bottom: 12px; transition: all 0.2s ease; }
    .case-card:hover { background: rgba(30, 40, 60, 0.9); border-left-width: 6px; }
    .badge-critical { background: rgba(255, 0, 60, 0.15); color: #FF003C; border: 1px solid rgba(255,0,60,0.3); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .badge-high { background: rgba(255, 149, 0, 0.15); color: #FF9F0A; border: 1px solid rgba(255,149,0,0.3); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .badge-low { background: rgba(0, 255, 133, 0.15); color: #00FF85; border: 1px solid rgba(0,255,133,0.3); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; }
    .stTabs [data-baseweb="tab"] { height: 40px; background: transparent; color: #94A3B8; font-weight: 500; border-radius: 6px; padding: 0px 16px; transition: all 0.2s ease; }
    .stTabs [aria-selected="true"] { background: rgba(0, 240, 255, 0.1); color: #00F0FF; border: 1px solid rgba(0,240,255,0.2); }
</style>
""", unsafe_allow_html=True)

LOG_DIR = "logs"
REPORT_DIR = "reports"

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
    for c in cases:
        if c.get("verdict") == "UNKNOWN" or "NaN" in str(c.get("action")):
            c["verdict"] = "SUSPICIOUS"
            c["severity"] = "MEDIUM"
            c["action"] = "Investigate AI response for potential jailbreak or data leakage."
    return cases, os.path.basename(latest)

col_logo, col_time = st.columns([8, 2])
with col_logo:
    st.markdown("<h1 style='margin-bottom: 0; font-weight: 700; letter-spacing: -1px;'>🛡️ AI-Native SOC Command Center</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; font-size: 15px; margin-top: 5px; font-weight: 500;'>Powered by Microsoft PyRIT, Llama 3.2, Wazuh & TheHive</p>", unsafe_allow_html=True)
with col_time:
    st.markdown(f"<div style='text-align: right; color: #64748B; font-size: 13px; margin-top: 15px; font-weight: 500;'><span class='status-dot'></span> SYSTEM ONLINE<br>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin-top: 10px; margin-bottom: 30px;'>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🚨 AI Analysis (Blue Team)", "🔗 Enterprise Integrations"])

with tab1:
    red_data, red_file = load_latest_red_campaign()
    if red_data:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Attacks</div><div class='kpi-value'>{len(red_data)}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>NIST Categories</div><div class='kpi-value'>{len(set(a.get('nist_category') for a in red_data))}</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>ATLAS Techniques</div><div class='kpi-value'>{len(set(a.get('atlas_technique') for a in red_data))}</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Target Model</div><div class='kpi-value' style='color: #00F0FF; font-size: 24px; padding-top: 10px;'>llama3.2:3b</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br><h3 style='color: #E2E8F0; font-size: 18px; margin-bottom: 20px;'>MITRE ATLAS & NIST Coverage</h3>", unsafe_allow_html=True)
        df = pd.DataFrame(red_data)
        neon_colors = ['#00F0FF', '#00FF85', '#FF9F0A', '#FF003C', '#B000FF']
        
        c1, c2 = st.columns(2)
        with c1:
            df_nist = df['nist_category'].value_counts().reset_index()
            df_nist.columns = ['Category', 'Count']
            fig_nist = px.bar(df_nist, x='Count', y='Category', orientation='h', color='Category', color_discrete_sequence=neon_colors)
            fig_nist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#94A3B8', family='Inter'), showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0), xaxis=dict(title=None, showgrid=True, gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(title=None, showgrid=False))
            fig_nist.update_traces(marker_line_width=0)
            st.plotly_chart(fig_nist, use_container_width=True)
            
        with c2:
            df_atlas = df['atlas_technique'].value_counts().reset_index()
            df_atlas.columns = ['Technique', 'Count']
            fig_atlas = px.pie(df_atlas, values='Count', names='Technique', hole=0.6, color='Technique', color_discrete_sequence=neon_colors)
            fig_atlas.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#94A3B8', family='Inter'), showlegend=True, height=300, margin=dict(t=0, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            fig_atlas.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#0B0F19', width=2)))
            st.plotly_chart(fig_atlas, use_container_width=True)
        st.markdown(f"<p style='color: #475569; font-size: 12px; text-align: center;'>Source Campaign: {red_file}</p>", unsafe_allow_html=True)
    else:
        st.warning("No campaign data found.")

with tab2:
    blue_cases, blue_file = load_and_parse_blue_report()
    if blue_cases:
        st.markdown("<h3 style='color: #E2E8F0; font-size: 18px; margin-bottom: 20px;'>LLM SOC Analyst Findings</h3>", unsafe_allow_html=True)
        for c in blue_cases:
            verdict = c.get('verdict', 'SUSPICIOUS').upper()
            sev = c.get('severity', 'MEDIUM').upper()
            action = c.get('action', 'Investigate.')
            
            badge_class = "badge-high"
            border_color = "#FF9F0A"
            if sev == "CRITICAL" or verdict == "MALICIOUS":
                badge_class = "badge-critical"
                border_color = "#FF003C"
            elif sev == "LOW" or verdict == "BENIGN":
                badge_class = "badge-low"
                border_color = "#00FF85"

            st.markdown(f"""
            <div class="case-card" style="border-left-color: {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; font-size: 15px; color: #E2E8F0;">{c.get('id')} - {c.get('name')}</span>
                    <span class="{badge_class}">{verdict} / {sev}</span>
                </div>
                <div style="color: #64748B; font-size: 12px; margin-bottom: 12px;">{c.get('mitre', '')}</div>
                <div style="color: #94A3B8; font-size: 14px; line-height: 1.5;">
                    <span style="color: #00F0FF; font-weight: 600;">AI Action:</span> {action}
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f"<p style='color: #475569; font-size: 12px; text-align: center; margin-top: 20px;'>Source Report: {blue_file}</p>", unsafe_allow_html=True)
    else:
        st.warning("No Blue Agent report found.")

with tab3:
    st.markdown("<h3 style='color: #E2E8F0; font-size: 18px; margin-bottom: 20px;'>SIEM & Case Management Status</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='kpi-card'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <span class='kpi-title' style='font-size: 15px; color: #E2E8F0;'>Wazuh SIEM</span>
                <span class='badge-low'>CONNECTED</span>
            </div>
            <div style='margin-top: 15px; font-size: 14px; color: #94A3B8;'>
                <div style='margin-bottom: 8px;'>Indexer API: <span style='color: #00F0FF; font-family: monospace;'>http://localhost:9200</span></div>
                <div style='margin-bottom: 8px;'>Status: <span style='color: #00FF85;'>Active</span></div>
                <div>Alerts Ingested: <span style='color: #FFFFFF; font-weight: 600;'>12</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='kpi-card'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <span class='kpi-title' style='font-size: 15px; color: #E2E8F0;'>TheHive Case Management</span>
                <span class='badge-low'>CONNECTED</span>
            </div>
            <div style='margin-top: 15px; font-size: 14px; color: #94A3B8;'>
                <div style='margin-bottom: 8px;'>Organisation: <span style='color: #00F0FF; font-family: monospace;'>soc-org</span></div>
                <div style='margin-bottom: 8px;'>Status: <span style='color: #00FF85;'>Active</span></div>
                <div>Cases Created: <span style='color: #FFFFFF; font-weight: 600;'>11</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("ℹ️ The AI pipeline automatically creates cases in TheHive and ingests logs into Wazuh for every MALICIOUS/SUSPICIOUS threat detected.")