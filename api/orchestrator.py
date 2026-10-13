"""
FastAPI Orchestrator
PFE: AI-Native SOC Orchestrator
Student: Yassine Mahdi
Internship: TDS by Nomios (Dec 2026 - May 2027)

REST API that orchestrates the full Red/Blue Team pipeline.
"""

import subprocess
import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="AI-Native SOC Orchestrator",
    description="Automated Red/Blue Team pipeline with MITRE ATLAS mapping",
    version="1.0.0"
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CampaignResponse(BaseModel):
    status: str
    timestamp: str
    steps_completed: list
    duration_seconds: float


def run_script(relative_path: str) -> dict:
    """Run a Python script and capture output."""
    script_path = os.path.join(PROJECT_ROOT, relative_path)
    if not os.path.exists(script_path):
        return {"success": False, "error": f"Script not found: {script_path}"}

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=PROJECT_ROOT
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Script timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/")
def root():
    return {
        "service": "AI-Native SOC Orchestrator",
        "status": "running",
        "endpoints": {
            "GET /": "Service info",
            "GET /health": "Health check",
            "POST /campaign/run": "Run full Red/Blue campaign",
            "GET /reports/latest": "Get latest campaign report info"
        }
    }


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/campaign/run", response_model=CampaignResponse)
def run_campaign():
    """Execute the full pipeline: Red -> Blue -> Risk -> Report."""
    start_time = datetime.now()
    steps_completed = []

    # Step 1: Red Agent
    print("[*] Step 1/4: Running Red Agent...")
    red_result = run_script("red_agent/red_agent.py")
    if not red_result["success"]:
        raise HTTPException(status_code=500, detail=f"Red Agent failed: {red_result.get('error')}")
    steps_completed.append("red_agent")

    # Step 2: Blue Agent
    print("[*] Step 2/4: Running Blue Agent...")
    blue_result = run_script("blue_agent/blue_agent.py")
    if not blue_result["success"]:
        raise HTTPException(status_code=500, detail=f"Blue Agent failed: {blue_result.get('error')}")
    steps_completed.append("blue_agent")

    # Step 3: Risk Engine
    print("[*] Step 3/4: Running Risk Engine...")
    risk_result = run_script("risk_engine/risk_engine.py")
    if not risk_result["success"]:
        raise HTTPException(status_code=500, detail=f"Risk Engine failed: {risk_result.get('error')}")
    steps_completed.append("risk_engine")

    # Step 4: Reporting Engine
    print("[*] Step 4/4: Generating PDF Report...")
    report_result = run_script("reporting/reporting_engine.py")
    if not report_result["success"]:
        raise HTTPException(status_code=500, detail=f"Reporting failed: {report_result.get('error')}")
    steps_completed.append("reporting_engine")

    duration = (datetime.now() - start_time).total_seconds()

    return CampaignResponse(
        status="success",
        timestamp=datetime.now().isoformat(),
        steps_completed=steps_completed,
        duration_seconds=round(duration, 2)
    )


@app.get("/reports/latest")
def latest_report():
    """Get the latest generated report info."""
    reports_dir = os.path.join(PROJECT_ROOT, "reports")
    if not os.path.exists(reports_dir):
        return {"error": "Reports directory not found"}

    pdf_reports = sorted(
        [f for f in os.listdir(reports_dir) if f.endswith(".pdf")]
    )
    if not pdf_reports:
        return {"message": "No PDF reports found. Run a campaign first."}

    latest = pdf_reports[-1]
    return {
        "latest_report": latest,
        "path": os.path.join(reports_dir, latest),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)