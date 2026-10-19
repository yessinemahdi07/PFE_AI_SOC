import subprocess
import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="AI-Native SOC Orchestrator", version="4.0 - Enterprise Pipeline")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class CampaignResponse(BaseModel):
    status: str
    duration_seconds: float
    steps_completed: list

def run_script(path):
    print(f"[*] Executing: {path}")
    res = subprocess.run([sys.executable, os.path.join(PROJECT_ROOT, path)], capture_output=True, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(f"[!] Error in {path}:\n{res.stderr}")
        return False
    return True

@app.post("/campaign/run", response_model=CampaignResponse)
def run_campaign():
    start = datetime.now()
    steps = []
    
    if not run_script("red_agent/red_agent_v3_pyrit.py"): raise HTTPException(500, "Red Agent failed")
    steps.append("PyRIT Red Agent")
    
    if not run_script("blue_agent/blue_agent_v3_soc.py"): raise HTTPException(500, "Blue Agent failed")
    steps.append("LLM Blue Agent")
    
    if not run_script("risk_engine/risk_engine.py"): raise HTTPException(500, "Risk Engine failed")
    steps.append("Threat Intel Engine")
    
    if not run_script("siem_connector/wazuh_indexer_connector.py"): raise HTTPException(500, "Wazuh Ingestion failed")
    steps.append("Wazuh SIEM")
    
    if not run_script("siem_connector/thehive_master.py"): raise HTTPException(500, "TheHive Case Creation failed")
    steps.append("TheHive Cases")
    
    if not run_script("reporting/reporting_engine.py"): raise HTTPException(500, "Reporting failed")
    steps.append("Automated PDF Report")

    return CampaignResponse(
        status="success", 
        duration_seconds=round((datetime.now() - start).total_seconds(), 2), 
        steps_completed=steps
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
