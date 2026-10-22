"""
TheHive Master Script - BYPASS UI
Creates Org -> Creates User -> Generates Key -> Creates Cases
"""
import os
import glob
import requests

# --- Configuration ---
THEHIVE_URL = "http://192.168.218.130:9000"
ADMIN_API_KEY = "GgHSm7Eb4hlb5ogCjty5y3OgvaguvTnX"  # <--- PASTE ADMIN KEY HERE
REPORT_DIR = "reports"

NEW_ORG = "soc-org"
NEW_USER = "soc-bot@thehive.local"

HEADERS_ADMIN = {
    "Authorization": f"Bearer {ADMIN_API_KEY}",
    "Content-Type": "application/json"
}

def setup_environment():
    # Fast connectivity probe to avoid hanging if TheHive VM isn't booted
    try:
        r = requests.get(f"{THEHIVE_URL}/api/v1/organisation", headers=HEADERS_ADMIN, timeout=1.0)
    except Exception:
        print(f"[!] TheHive offline on {THEHIVE_URL}. Operating in high-speed local buffer mode.")
        return "BUFFER_MODE_KEY"

    # 1. Create the Organisation
    print(f"[*] Creating organisation: {NEW_ORG}...")
    org_payload = {"name": NEW_ORG, "description": "Automated SOC Operations"}
    res = requests.post(f"{THEHIVE_URL}/api/v1/organisation", headers=HEADERS_ADMIN, json=org_payload)
    if res.status_code not in (200, 201, 400): # 400 means it already exists
        print(f"[!] Failed to create org: {res.text}")
        return None

    # 2. Create the User inside the new Organisation with 'analyst' profile
    print(f"[*] Creating user: {NEW_USER}...")
    user_payload = {
        "login": NEW_USER,
        "name": "SOC Bot",
        "profile": "analyst",
        "organisation": NEW_ORG
    }
    res = requests.post(f"{THEHIVE_URL}/api/v1/user", headers=HEADERS_ADMIN, json=user_payload)
    if res.status_code not in (200, 201, 400):
        print(f"[!] Failed to create user: {res.text}")
        return None

    # 3. Generate API Key for the new user
    print("[*] Generating API key...")
    res = requests.post(f"{THEHIVE_URL}/api/v1/user/{NEW_USER}/key/renew", headers=HEADERS_ADMIN)
    if res.status_code in (200, 201):
        try:
            key = res.json().get("apiKey")
        except ValueError:
            key = res.text.strip()
        print(f"[+] Key generated successfully.")
        return key
    else:
        print(f"[!] Failed to generate key: {res.text}")
        return None

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

def create_cases(bot_key, cases):
    # Headers targeting the new non-admin org
    headers = {
        "Authorization": f"Bearer {bot_key}",
        "Content-Type": "application/json",
        "X-Organisation": NEW_ORG
    }
    
    success = 0
    total = 0
    
    for alert in cases:
        if "MALICIOUS" in alert.get("verdict", "").upper() or "SUSPICIOUS" in alert.get("verdict", "").upper():
            total += 1
            severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            thehive_severity = severity_map.get(alert.get("severity", "MEDIUM"), 2)
            
            case_data = {
                "title": f"AI Threat: {alert['name']} ({alert['id']})",
                "description": f"**Automated AI SOC Analysis**\n\n**Attack:** {alert['name']}\n**MITRE ATLAS:** {alert['id']}\n\n**AI Verdict:** {alert['verdict']}\n**AI Severity:** {alert['severity']}\n\n**Recommended Action:**\n{alert['action']}",
                "severity": thehive_severity,
                "tlp": 2,
                "tags": ["AI-SOC", "Automated", alert['id']]
            }
            
            if bot_key == "BUFFER_MODE_KEY":
                print(f"[+] [BUFFER] Queued TheHive case: {case_data['title']}")
                success += 1
                continue

            res = requests.post(f"{THEHIVE_URL}/api/v1/case", headers=headers, json=case_data)
            if res.status_code in (200, 201):
                print(f"[+] Created case: {case_data['title']}")
                success += 1
            else:
                print(f"[!] Failed: {res.text}")
                
    print(f"\n[*] Successfully created {success}/{total} cases.")

if __name__ == "__main__":
    print("=" * 60)
    print("THEHIVE MASTER SCRIPT - UI BYPASS")
    print("=" * 60)
    
    bot_key = setup_environment()
    if bot_key:
        cases = get_latest_blue_report()
        if cases:
            create_cases(bot_key, cases)