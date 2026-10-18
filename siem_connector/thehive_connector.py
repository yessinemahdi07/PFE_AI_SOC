"""
TheHive Connector - Official Library (v2)
"""
import os
import glob
from thehive4py import TheHiveApi

# --- Configuration ---
THEHIVE_URL = "http://192.168.218.130:9000"
API_KEY = "80WGO62P7VYCeFxz3Na/g9iMgWTiR4Ne"  # <--- PASTE THE KEY FROM THE UI HERE
REPORT_DIR = "reports"

def get_latest_blue_report():
    reports = sorted(glob.glob(os.path.join(REPORT_DIR, "blue_team_soc_report_*.txt")))
    if not reports:
        return None
    
    latest = reports[-1]
    print(f"[*] Reading report: {latest}")
    
    cases = []
    current_case = {}
    
    with open(latest, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[ATLAS."):
                if current_case:
                    cases.append(current_case)
                parts = line.split("]")
                current_case = {"id": parts[0].strip("["), "name": parts[1].strip()}
            elif line.startswith("VERDICT:"):
                current_case["verdict"] = line.split(":")[1].strip()
            elif line.startswith("SEVERITY:"):
                current_case["severity"] = line.split(":")[1].strip()
            elif line.startswith("ACTION:"):
                current_case["action"] = line.split(":", 1)[1].strip()
                
    if current_case:
        cases.append(current_case)
    return cases

def create_cases(cases):
    # Initialize the official TheHive API client
    # The 'organisation' parameter is required for v2
    hive = TheHiveApi(
        url=THEHIVE_URL,
        apikey=API_KEY,
        organisation="admin"
    )
    
    success = 0
    total = 0
    
    for alert in cases:
        if "MALICIOUS" in alert.get("verdict", "").upper() or "SUSPICIOUS" in alert.get("verdict", "").upper():
            total += 1
            severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            thehive_severity = severity_map.get(alert.get("severity", "MEDIUM"), 2)
            
            # Create the case dictionary
            case_data = {
                "title": f"AI Threat: {alert['name']} ({alert['id']})",
                "description": f"**Automated AI SOC Analysis**\n\n**Attack:** {alert['name']}\n**MITRE ATLAS:** {alert['id']}\n\n**AI Verdict:** {alert['verdict']}\n**AI Severity:** {alert['severity']}\n\n**Recommended Action:**\n{alert['action']}",
                "severity": thehive_severity,
                "tlp": 2,
                "tags": ["AI-SOC", "Automated", alert['id']]
            }
            
            # Send to TheHive using the v2 method
            try:
                response = hive.case.create(case=case_data)
                print(f"[+] Created case: {case_data['title']}")
                success += 1
            except Exception as e:
                print(f"[!] Failed: {e}")
                
    print(f"\n[*] Successfully created {success}/{total} cases.")

if __name__ == "__main__":
    print("=" * 60)
    print("THEHIVE AUTOMATION - OFFICIAL LIBRARY v2")
    print("=" * 60)
    
    cases = get_latest_blue_report()
    if cases:
        create_cases(cases)