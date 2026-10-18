import subprocess
import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AI-Native SOC Orchestrator", version="3.0")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class CampaignResponse(BaseModel):
    status: str
    duration: float
    steps: list

def run_script(path):
    res = subprocess.run([sys.executable, os.path.join(PROJECT_ROOT, path)], capture_output=True, text=True, cwd=PROJECT_ROOT)
    return res.returncode == 0

@app.post("/campaign/run", response_model=CampaignResponse)
def run_campaign():
    start = datetime.now()
    steps = []
    if not run_script("red_agent/red_agent_v3_pyrit.py"): raise HTTPException(500, "Red Agent failed")
    steps.append("PyRIT Red Agent")
    if not run_script("blue_agent/blue_agent_v3_soc.py"): raise HTTPException(500, "Blue Agent failed")
    steps.append("LLM Blue Agent")
    if not run_script("risk_engine/risk_engine.py"): raise HTTPException(500, "Risk Engine failed")
    steps.append("Risk Engine")
    if not run_script("siem_connector/thehive_master.py"): raise HTTPException(500, "TheHive failed")
    steps.append("TheHive Cases")
    if not run_script("reporting/reporting_engine.py"): raise HTTPException(500, "Reporting failed")
    steps.append("PDF Report")
    return CampaignResponse(status="success", duration=round((datetime.now() - start).total_seconds(), 2), steps=steps)
