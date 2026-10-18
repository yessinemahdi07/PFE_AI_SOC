"""
Wazuh API Connector
Pushes alerts via the official Wazuh REST API (port 55000).
"""

import json
import os
import glob
import requests
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Config (Requires SSH tunnel: ssh -L 55000:127.0.0.1:55000 -p 2222 wazuh-user@localhost)
API_URL = "https://localhost:55000"
API_USER = "wazuh"
API_PASS = "wazuh" # Change this if you successfully reset the password earlier
REPORT_DIR = "reports"

def get_token():
    url = f"{API_URL}/security/user/authenticate"
    try:
        r = requests.get(url, auth=(API_USER, API_PASS), verify=False, timeout=10)
        r.raise_for_status()
        print("[*] Authenticated with Wazuh API.")
        return r.json().get("data", {}).get("token")
    except Exception as e:
        print(f"[!] Auth failed: {e}")
        return None

def get_alerts():
    reports = sorted(glob.glob(os.path.join(REPORT_DIR, "blue_team_report_*.txt")))
    if not reports:
        return []
    latest = reports[-1]
    print(f"[*] Reading: {latest}")
    alerts = []
    current = {}
    with open(latest, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[AML."):
                if current: alerts.append(current)
                current = {"attack_id": line.split("]")[0].strip("[")}
            elif line.startswith("Risk Score:"):
                current["risk_score"] = line.split(":")[1].strip()
            elif line.startswith("Verdict:"):
                current["verdict"] = line.split(":")[1].strip()
            elif line.startswith("Response:"):
                current["response"] = line.split(":", 1)[1].strip()
    if current: alerts.append(current)
    return alerts

def push_alert(token, alert):
    url = f"{API_URL}/events"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    event = {
        "events": [
            json.dumps({
                "timestamp": datetime.now().isoformat(),
                "rule": {
                    "level": 12 if alert.get("verdict") == "MALICIOUS" else 7,
                    "description": f"AI API Alert: {alert.get('attack_id')}",
                    "id": "100002"
                },
                "agent": {"id": "000", "name": "ai-api-connector"},
                "data": alert,
                "location": "ai-soc-orchestrator"
            })
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=event, verify=False, timeout=10)
        if r.status_code == 200:
            print(f"[+] Pushed via API: {alert['attack_id']}")
            return True
        else:
            print(f"[!] Failed: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"[!] Error: {e}")
        return False

if __name__ == "__main__":
    token = get_token()
    if token:
        alerts = get_alerts()
        print(f"[*] Pushing {len(alerts)} alerts via API...")
        for a in alerts:
            push_alert(token, a)