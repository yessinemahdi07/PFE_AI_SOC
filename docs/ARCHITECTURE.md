# PFE: AI-Native SOC Orchestrator

**Student:** Yassine Mahdi  
**Institution:** ESPRIT — Cybersecurity Engineering  
**Internship:** TDS by Nomios (Dec 2026 — May 2027)  
**Repository:** github.com/yessinemahdi07/PFE_AI_SOC

---

## 1. Project Objective

Build an AI-native Security Operations Center (SOC) orchestrator that automates:

- Red Team attack simulation against LLMs
- Blue Team detection and risk scoring
- Threat Intelligence enrichment via public APIs
- Automated PDF reporting
- Real-time dashboard visualization

All attacks and detections are mapped to **MITRE ATLAS** (AI-specific threats) and **MITRE ATT&CK** (traditional threats).

---

## 2. Architecture

[FastAPI Orchestrator]
        |
        |-- POST /campaign/run
        |
        v
[Red Agent] --> [Blue Agent] --> [Risk Engine] --> [Reporting Engine]
   |                  |                |                    |
   |                  |                |                    |
   v                  v                v                    v
Ollama +          Regex +         AlienVault OTX +      fpdf2
Llama 3.2         Risk Score      AbuseIPDB +           PDF
                  Accuracy        VirusTotal
8 attacks
4 ATLAS
techniques

        |
        v
[Streamlit Dashboard]
  - Metrics cards
  - Attack table
  - Threat Intel cards
  - ATLAS bar chart

---

## 3. Components

### 3.1 Red Agent (`red_agent/red_agent.py`)

- Stack: Python + Ollama (Llama 3.2 3B)
- Function: Generates 8 adversarial prompts against a local LLM
- MITRE ATLAS Coverage:
  - AML.T0050 - Manipulate LLM Instructions
  - AML.T0051 - LLM Prompt Injection
  - AML.T0054 - LLM Jailbreak
  - AML.T0057 - LLM Data Leakage
- Output: JSON log with payload, response, elapsed time, ground-truth label

### 3.2 Blue Agent (`blue_agent/blue_agent.py`)

- Stack: Python + regex pattern matching
- Function: Reads Red Agent logs, detects injection/refusal patterns, assigns risk scores
- Detection Patterns: Mapped to all 4 ATLAS techniques
- Output: Text report with MALICIOUS/SUSPICIOUS/BENIGN verdicts and accuracy metrics

### 3.3 Risk Engine (`risk_engine/risk_engine.py`)

- Stack: Python + AlienVault OTX, AbuseIPDB, VirusTotal APIs
- Function: Extracts IOCs from Blue Agent report, classifies IOC type, enriches with Threat Intel
- IOC Classification: IP, MD5, SHA1, SHA256, URL, domain
- Output: JSON report with composite Threat Intel score (0-100)

### 3.4 Reporting Engine (`reporting/reporting_engine.py`)

- Stack: Python + fpdf2
- Function: Generates professional PDF after every campaign
- Sections: Executive Summary, Attack Breakdown, Threat Intel Enrichment, Recommendations
- Output: SOC_Campaign_Report_timestamp.pdf

### 3.5 Streamlit Dashboard (`dashboard/dashboard.py`)

- Stack: Streamlit
- Function: Real-time visualization of campaign results
- Views: Metrics cards, attack table, Threat Intel expanders, ATLAS coverage bar chart

### 3.6 FastAPI Orchestrator (`api/orchestrator.py`)

- Stack: FastAPI + Uvicorn
- Function: Single REST endpoint triggers the full pipeline
- Endpoints:
  - GET / - Service info
  - GET /health - Health check
  - POST /campaign/run - Full pipeline execution
  - GET /reports/latest - Latest PDF report info
- Runtime: ~37 seconds end-to-end

---

## 4. MITRE ATLAS Mapping

| Attack ID | Technique | Description |
|-----------|-----------|-------------|
| AML.T0051.001 | LLM Prompt Injection | Direct prompt injection |
| AML.T0051.002 | LLM Prompt Injection | Delimiter injection |
| AML.T0054.001 | LLM Jailbreak | DAN jailbreak |
| AML.T0054.002 | LLM Jailbreak | Role-play jailbreak |
| AML.T0057.001 | LLM Data Leakage | Training data extraction |
| AML.T0057.002 | LLM Data Leakage | Context data extraction |
| AML.T0050.001 | Manipulate LLM Instructions | System override |
| AML.T0050.002 | Manipulate LLM Instructions | Instruction suppression |

---

## 5. Setup Guide

### Prerequisites

- Python 3.13+
- Ollama (with llama3.2:3b and qwen3:8b models pulled)
- Docker Desktop (for Phase 2 SIEM integration)

### Installation

git clone https://github.com/yessinemahdi07/PFE_AI_SOC.git
cd PFE_AI_SOC
pip install -r requirements.txt
Copy-Item config\api_keys.example.json config\api_keys.json
(Edit config\api_keys.json with your real API keys)

### Running the Pipeline

Full pipeline via API:
python api\orchestrator.py
Invoke-RestMethod -Uri "http://localhost:8000/campaign/run" -Method Post

Individual components:
python red_agent\red_agent.py
python blue_agent\blue_agent.py
python risk_engine\risk_engine.py
python reporting\reporting_engine.py

Dashboard:
streamlit run dashboard\dashboard.py

---

## 6. Evaluation Metrics

- Detection Accuracy: 100% (8/8 attacks correctly classified)
- Pipeline Runtime: ~37 seconds end-to-end
- MITRE ATLAS Coverage: 4 distinct techniques
- Threat Intel Sources: 3 APIs (OTX, AbuseIPDB, VirusTotal)

---

## 7. Future Work

- Phase 2: Wazuh SIEM integration + TheHive case management
- Phase 3: Attack-path analysis + auto-containment (Risk Score > 80)
- Phase 4: Full integration + PFE report + defense

---

## 8. References

- MITRE ATLAS: https://atlas.mitre.org
- MITRE ATT&CK: https://attack.mitre.org
- OWASP Top 10 for LLMs: https://owasp.org/www-project-top-10-for-large-language-model-applications/