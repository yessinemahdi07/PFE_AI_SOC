# PFE: AI-Native SOC Orchestrator

**Student:** Yassine Mahdi  
**Institution:** ESPRIT — Cybersecurity Engineering  
**Internship:** TDS by Nomios (Dec 2026 — May 2027)  

---

## 1. Project Objective
Build an AI-native SOC orchestrator that automates Red/Blue Team exercises using Microsoft PyRIT, local LLMs (Ollama), and Wazuh SIEM.

## 2. Architecture

[FastAPI Orchestrator]
        |
        v
[Red Agent - PyRIT v0.10.0] --> 12 Attacks mapped to MITRE ATLAS & NIST AI RMF
        |
        v
[Blue Agent - LLM SOC Analyst] --> Llama 3.2 evaluates response, assigns Verdict/Severity/Action
        |
        v
[Risk Engine] --> Queries Threat Intel APIs for IOCs
        |
        v
[Wazuh SIEM] --> Alerts ingested via Indexer Connector
        |
        v
[Streamlit Dashboard] --> Visualizes MITRE, NIST, and SIEM Status

## 3. Components

### 3.1 Red Agent (`red_agent/red_agent_v3_pyrit.py`)
- **Stack:** Microsoft PyRIT v0.10.0 + Ollama (Qwen3 4B)
- **Function:** Executes 12 distinct attack scenarios sequentially.
- **Frameworks:** Cross-mapped to MITRE ATLAS (AI techniques) and NIST AI RMF (risk categories).
- **Coverage:** Prompt Injection, Data Leakage, Malware Generation, Evasion, PII Exfiltration.

### 3.2 Blue Agent (`blue_agent/blue_agent_v3_soc.py`)
- **Stack:** Python + Ollama (Llama 3.2 3B)
- **Function:** Acts as a Senior SOC Analyst. Ingests PyRIT JSON and uses LLM to evaluate the AI's response.
- **Output:** Verdict (MALICIOUS/SUSPICIOUS/BENIGN), Severity, and Recommended Action.

### 3.3 Risk Engine (`risk_engine/risk_engine.py`)
- **Stack:** Python + AlienVault OTX, AbuseIPDB, VirusTotal APIs
- **Function:** Extracts IOCs from reports, enriches with Threat Intel.

### 3.4 SIEM Integration (`siem_connector/wazuh_indexer_connector.py`)
- **Stack:** Python + Wazuh Indexer (OpenSearch API)
- **Function:** Pushes alerts directly to the Wazuh database.

### 3.5 Dashboard (`dashboard/dashboard.py`)
- **Stack:** Streamlit
- **Function:** Real-time visualization of MITRE ATLAS coverage, NIST categories, and SIEM status.