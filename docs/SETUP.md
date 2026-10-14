# Setup Guide

**PFE: AI-Native SOC Orchestrator**  
**Student:** Yassine Mahdi  
**Repository:** github.com/yessinemahdi07/PFE_AI_SOC

---

## 1. Prerequisites

Install the following before running the pipeline:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.13+ | https://www.python.org/downloads/ |
| Ollama | Latest | https://ollama.com/download |
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop/ |
| Git | Latest | https://git-scm.com/download/win |

---

## 2. Hardware Requirements

Minimum specs for running the full pipeline:

- CPU: 6 cores (AMD Ryzen 5 5600H or equivalent)
- RAM: 16 GB (24 GB recommended)
- GPU: 4 GB VRAM (RTX 3050 Ti or equivalent) - optional for LLM acceleration
- Disk: 50 GB free (for models, VMs, reports)

---

## 3. Installation Steps

### Step 1: Clone the Repository

Open PowerShell and run:

git clone https://github.com/yessinemahdi07/PFE_AI_SOC.git
cd PFE_AI_SOC

### Step 2: Install Python Dependencies

pip install -r requirements.txt

Dependencies installed:
- fastapi (REST API)
- uvicorn (ASGI server)
- requests (HTTP client for Threat Intel APIs)
- pyyaml (config parsing)
- fpdf2 (PDF generation)
- streamlit (dashboard)
- sqlalchemy (database ORM - future use)
- pydantic (data validation)

### Step 3: Install Ollama Models

ollama pull llama3.2:3b
ollama pull qwen3:8b

Verify:

ollama list

Expected output:
- llama3.2:3b (2.0 GB)
- qwen3:8b (5.2 GB)

### Step 4: Configure API Keys

Copy the example config:

Copy-Item config\api_keys.example.json config\api_keys.json

Edit config\api_keys.json with your real API keys:

{
    "alienvault_otx": "YOUR_OTX_API_KEY_HERE",
    "abuseipdb": "YOUR_ABUSEIPDB_API_KEY_HERE",
    "virustotal": "YOUR_VIRUSTOTAL_API_KEY_HERE"
}

Get free API keys:
- AlienVault OTX: https://otx.alienvault.com
- AbuseIPDB: https://www.abuseipdb.com/api
- VirusTotal: https://www.virustotal.com/gui/join-us

CRITICAL: Do NOT commit api_keys.json to Git. It is already in .gitignore.

---

## 4. Running the Pipeline

### Option A: Full Pipeline via FastAPI

Terminal 1 - Start the API:
python api\orchestrator.py

Terminal 2 - Trigger the full campaign:
Invoke-RestMethod -Uri "http://localhost:8000/campaign/run" -Method Post

Expected runtime: ~37 seconds

### Option B: Run Components Individually

Step 1 - Red Agent (LLM attacks):
python red_agent\red_agent.py

Step 2 - Blue Agent (detection):
python blue_agent\blue_agent.py

Step 3 - Risk Engine (Threat Intel):
python risk_engine\risk_engine.py

Step 4 - Reporting Engine (PDF):
python reporting\reporting_engine.py

### Option C: Launch the Dashboard

streamlit run dashboard\dashboard.py

Open browser at http://localhost:8501

---

## 5. Verify Installation

Run these commands to confirm everything works:

python --version
ollama list
pip list | findstr "fastapi streamlit fpdf2"
Test-Path config\api_keys.json

Expected:
- Python 3.13+
- llama3.2:3b and qwen3:8b
- fastapi, streamlit, fpdf2 installed
- api_keys.json exists (True)

---

## 6. Troubleshooting

### Ollama not responding

Check if Ollama is running:
ollama list

If empty, start the service:
ollama serve

### API key errors

Verify api_keys.json has valid keys:
Get-Content config\api_keys.json

### Streamlit port conflict

If port 8501 is in use:
streamlit run dashboard\dashboard.py --server.port 8502

### fpdf2 horizontal space error

If PDF generation fails with "Not enough horizontal space":
Ensure multi_cell uses explicit width (e.g., 190) instead of 0.

---

## 7. Project Structure

PFE_AI_SOC/
├── api/                  # FastAPI orchestrator
├── blue_agent/           # Blue Team detection
├── config/               # API keys (gitignored)
├── dashboard/            # Streamlit dashboard
├── docs/                 # Documentation
├── logs/                 # Red Agent JSON logs
├── red_agent/            # Red Team attack generator
├── reporting/            # PDF report generator
├── reports/              # Generated reports
├── risk_engine/          # Threat Intel enrichment
├── requirements.txt      # Python dependencies
├── .gitignore            # Git exclusions
└── README.md             # Project overview

---

## 8. Next Steps

- Phase 2: Wazuh SIEM integration (Docker)
- Phase 3: TheHive case management
- Phase 4: Attack-path analysis
- Phase 5: Full PFE documentation and defense

---

**End of Setup Guide**