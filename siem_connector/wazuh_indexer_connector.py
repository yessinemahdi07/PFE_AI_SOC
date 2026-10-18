"""
Wazuh Indexer Connector
PFE: AI-Native SOC Orchestrator
Student: Yassine Mahdi

Reads the latest Blue Agent report and pushes alerts directly to the Wazuh Indexer (OpenSearch).
Bypasses the Wazuh API to avoid authentication issues.
"""

import json
import os
import glob
import requests
import urllib3
from datetime import datetime

# Suppress self-signed cert warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
# IMPORTANT: This assumes you have an SSH tunnel running:
# ssh -L 9200:127.0.0.1:9200 -p 2222 wazuh-user@localhost
INDEXER_URL = "https://localhost:9200"
INDEXER_USER = "admin"
INDEXER_PASS = "admin"
REPORT_DIR = "reports"


def get_latest_blue_report():
    """Find the latest Blue Agent text report and parse alerts."""
    reports = sorted(glob.glob(os.path.join(REPORT_DIR, "blue_team_report_*.txt")))
    if not reports:
        print("[!] No Blue Agent reports found.")
        return None
    
    latest = reports[-1]
    print(f"[*] Reading latest Blue Agent report: {latest}")
    
    alerts = []
    with open(latest, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    current_attack = {}
    for line in lines:
        line = line.strip()
        if line.startswith("[AML."):
            if current_attack:
                alerts.append(current_attack)
            current_attack = {"attack_id": line.split("]")[0].strip("[")}
        elif line.startswith("Risk Score:"):
            current_attack["risk_score"] = line.split(":")[1].strip()
        elif line.startswith("Verdict:"):
            current_attack["verdict"] = line.split(":")[1].strip()
        elif line.startswith("Response:"):
            current_attack["response"] = line.split(":", 1)[1].strip()
    
    if current_attack:
        alerts.append(current_attack)
    
    return alerts


def push_to_indexer(alert):
    """Send an alert directly to the Wazuh Indexer (OpenSearch)."""
    date_str = datetime.now().strftime("%Y.%m.%d")
    index_name = f"wazuh-alerts-4.x-{date_str}"
    url = f"{INDEXER_URL}/{index_name}/_doc"
    
    # Format the alert as a Wazuh-compatible document
    doc = {
        "timestamp": datetime.now().isoformat(),
        "rule": {
            "level": 12 if alert.get("verdict") == "MALICIOUS" else 7,
            "description": f"AI Red/Blue Team Alert: {alert.get('attack_id', 'Unknown')}",
            "id": "100001"
        },
        "agent": {
            "id": "000",
            "name": "ai-soc-orchestrator"
        },
        "data": {
            "attack_id": alert.get("attack_id"),
            "risk_score": alert.get("risk_score"),
            "verdict": alert.get("verdict"),
            "response": alert.get("response", "")[:200]
        },
        "location": "ai-soc-orchestrator"
    }
    
    try:
        response = requests.post(
            url, 
            auth=(INDEXER_USER, INDEXER_PASS), 
            json=doc, 
            verify=False, 
            timeout=10
        )
        if response.status_code in (200, 201):
            print(f"[+] Pushed alert: {alert.get('attack_id')} ({alert.get('verdict')})")
            return True
        else:
            print(f"[!] Failed to push {alert.get('attack_id')}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[!] Error pushing {alert.get('attack_id')}: {e}")
        return False


def run_connector():
    """Main entry point: read latest Blue report and push to Indexer."""
    print("=" * 60)
    print("WAZUH INDEXER CONNECTOR - AI-Native SOC Orchestrator")
    print("=" * 60)
    
    alerts = get_latest_blue_report()
    if not alerts:
        return
    
    print(f"\n[*] Found {len(alerts)} alerts to push to Indexer.")
    
    success_count = 0
    for alert in alerts:
        if push_to_indexer(alert):
            success_count += 1
            
    print(f"\n[*] Successfully pushed {success_count}/{len(alerts)} alerts.")


if __name__ == "__main__":
    run_connector()