# API Reference

**PFE: AI-Native SOC Orchestrator**  
**Student:** Yassine Mahdi  
**Base URL:** http://localhost:8000

---

## 1. Overview

The FastAPI Orchestrator exposes REST endpoints that trigger and monitor the full Red/Blue Team pipeline.

Start the server:

python api\orchestrator.py

Default port: 8000

---

## 2. Endpoints

### GET /

Service information.

Request:
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get

Response:
{
    "service": "AI-Native SOC Orchestrator",
    "status": "running",
    "endpoints": {
        "GET /": "Service info",
        "GET /health": "Health check",
        "POST /campaign/run": "Run full Red/Blue campaign",
        "GET /reports/latest": "Get latest campaign report info"
    }
}

---

### GET /health

Health check endpoint.

Request:
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get

Response:
{
    "status": "healthy",
    "timestamp": "2026-10-14T01:16:12.719158"
}

---

### POST /campaign/run

Execute the full pipeline: Red Agent -> Blue Agent -> Risk Engine -> Reporting Engine.

Request:
Invoke-RestMethod -Uri "http://localhost:8000/campaign/run" -Method Post

Response:
{
    "status": "success",
    "timestamp": "2026-10-14T01:17:09.980485",
    "steps_completed": [
        "red_agent",
        "blue_agent",
        "risk_engine",
        "reporting_engine"
    ],
    "duration_seconds": 36.87
}

Runtime: ~37 seconds (varies with LLM inference speed)

Steps executed:
1. Red Agent: Generates 8 LLM attacks across 4 MITRE ATLAS techniques
2. Blue Agent: Detects attacks, assigns risk scores, calculates accuracy
3. Risk Engine: Enriches IOCs with 3 Threat Intel APIs
4. Reporting Engine: Generates professional PDF report

---

### GET /reports/latest

Get info about the latest generated PDF report.

Request:
Invoke-RestMethod -Uri "http://localhost:8000/reports/latest" -Method Get

Response (if report exists):
{
    "latest_report": "SOC_Campaign_Report_20261014_005714.pdf",
    "path": "C:\\Users\\Elwel\\PFE_AI_SOC\\reports\\SOC_Campaign_Report_20261014_005714.pdf",
    "timestamp": "2026-10-14T01:20:00.000000"
}

Response (if no report exists):
{
    "message": "No PDF reports found. Run a campaign first."
}

---

## 3. Error Handling

All endpoints return standard HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 500 | Internal error (script failure) |

Error response format:
{
    "detail": "Red Agent failed: <error message>"
}

---

## 4. Pipeline Flow

POST /campaign/run triggers the following sequence:

Step 1: Red Agent
  - Script: red_agent/red_agent.py
  - Timeout: 600 seconds
  - Output: logs/red_team_campaign_<timestamp>.json

Step 2: Blue Agent
  - Script: blue_agent/blue_agent.py
  - Reads: Latest red_team_campaign JSON
  - Output: reports/blue_team_report_<timestamp>.txt

Step 3: Risk Engine
  - Script: risk_engine/risk_engine.py
  - Reads: Latest blue_team_report
  - Output: reports/risk_engine_report_<timestamp>.json

Step 4: Reporting Engine
  - Script: reporting/reporting_engine.py
  - Reads: Latest campaign + risk reports
  - Output: reports/SOC_Campaign_Report_<timestamp>.pdf

If any step fails, the API returns HTTP 500 and stops the pipeline.

---

## 5. Usage Examples

### Example 1: Run Full Campaign

Start API:
python api\orchestrator.py

In another terminal:
Invoke-RestMethod -Uri "http://localhost:8000/campaign/run" -Method Post | ConvertTo-Json

### Example 2: Check Service Health

Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get

### Example 3: Get Latest Report Path

Invoke-RestMethod -Uri "http://localhost:8000/reports/latest" -Method Get

### Example 4: Full Pipeline with Status Check

Invoke-RestMethod -Uri "http://localhost:8000/campaign/run" -Method Post | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/reports/latest" -Method Get | ConvertTo-Json

---

## 6. Integration Notes

### With External SIEM (Phase 2)

The pipeline outputs JSON logs that can be ingested by Wazuh or Elastic:

- logs/red_team_campaign_<timestamp>.json
- reports/risk_engine_report_<timestamp>.json

Example Wazuh integration:
- Configure Wazuh to monitor the logs/ folder
- Parse JSON fields: attack_id, atlas_technique, risk_score
- Trigger alerts on verdict == "MALICIOUS"

### With TheHive (Phase 3)

The pipeline can create cases in TheHive for each campaign:

- POST /api/case with campaign metadata
- Attach PDF report
- Assign to SOC L1/L2 analysts

---

## 7. Performance Metrics

From test campaigns (October 2026):

| Metric | Value |
|--------|-------|
| Total pipeline runtime | ~37 seconds |
| Red Agent runtime | ~30 seconds (8 attacks) |
| Blue Agent runtime | ~1 second |
| Risk Engine runtime | ~5 seconds (2 IOCs, 3 APIs each) |
| Reporting runtime | ~1 second |
| Detection accuracy | 100% (8/8) |
| MITRE ATLAS coverage | 4 techniques |

---

## 8. Security Considerations

- API keys stored in config/api_keys.json (gitignored)
- No sensitive data sent to external APIs except IOC values
- IOC types validated before enrichment (IP, hash, URL, domain)
- Private IPs excluded from Threat Intel queries
- All endpoints bound to localhost by default (0.0.0.0 for network access)

---

## 9. Future Endpoints (Planned)

| Endpoint | Purpose | Phase |
|----------|---------|-------|
| POST /campaign/schedule | Schedule recurring campaigns | Phase 2 |
| GET /alerts | List all generated alerts | Phase 2 |
| POST /containment/trigger | Auto-contain on Risk Score > 80 | Phase 3 |
| GET /attack-path/<campaign_id> | Attack-path analysis | Phase 3 |
| POST /thehive/case | Create TheHive case | Phase 3 |

---

**End of API Reference**