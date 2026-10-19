# 🧠 Project Overview & Technical Implementation

## 1. Introduction
The **AI-Native SOC Orchestrator** is an autonomous, AI-driven pipeline that bridges AI agent security with traditional enterprise SOC workflows. It demonstrates how offensive AI (Red Team) and defensive AI (Blue Team) can be integrated with industry-standard tools like Wazuh and TheHive.

## 2. Environment & Stack
- **AI Frameworks:** Microsoft PyRIT (Attacks), Ollama + Llama 3.2 3B (Analysis).
- **Infrastructure:** VMware (Wazuh OVA & Ubuntu Server), Docker (TheHive, Cortex, Cassandra, Elasticsearch).
- **Orchestration:** FastAPI (Python).
- **Frontend:** Streamlit Cloud, Plotly.

## 3. Component Implementation

### 3.1 Red Team Agent (PyRIT)
The Red Agent executes a 12-attack campaign against a local LLM using Microsoft PyRIT. Attacks are mapped to **MITRE ATLAS** (e.g., AML.T0051 Prompt Injection) and the **NIST AI RMF**. 

### 3.2 Blue Team Agent (LLM SOC Analyst)
The Blue Agent acts as a Tier 1 SOC Analyst. It parses the PyRIT JSON output and uses Llama 3.2 to evaluate the LLM's response. It assigns a Verdict (MALICIOUS/SUSPICIOUS), a Severity, and a containment recommendation.

### 3.3 Threat Intelligence Engine
Extracts IOCs from the Blue Agent's report and enriches them using AlienVault OTX, AbuseIPDB, and VirusTotal APIs to generate a composite Risk Score (0-100).

### 3.4 Enterprise Integration
- **Wazuh SIEM:** Alerts are injected directly into the Wazuh Indexer (port 9200) via the OpenSearch API for centralized logging.
- **TheHive:** The `thehive_master.py` script interfaces with TheHive REST API to automatically create incident tickets for detected threats.

### 3.5 Command Center (Streamlit)
A premium, cloud-hosted dashboard providing a unified view of the campaign, MITRE/NIST coverage (via Plotly), AI analysis cards, and SIEM/Case Management status.

## 4. Automation Pipeline
The entire process is triggered by a single FastAPI endpoint (`POST /campaign/run`). The pipeline executes sequentially: Red Team -> Blue Team -> Threat Intel -> Wazuh -> TheHive -> Report. **Execution time: ~90 seconds.**
