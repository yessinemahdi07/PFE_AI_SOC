"""
TheHive Ultimate Fixer
1. Grants manageCase permissions to the admin profile via API.
2. Creates cases from the Blue Agent report.
"""
import os
import glob
import requests
import json

# --- Configuration ---
THEHIVE_URL = "http://192.168.218.130:9000"
ADMIN_API_KEY = "SbBkjDtijm5wBORQqb5mznHPW9mo2i4Y"  # <--- PASTE YOUR ADMIN KEY HERE
REPORT_DIR = "reports"

HEADERS = {
    "Authorization": f"Bearer {ADMIN_API_KEY}",
    "Content-Type": "application/json"
}

def fix_admin_permissions():
    """Adds the manageCase permission to the admin profile."""
    print("[*] Fixing admin permissions via API...")
    url = f"{THEHIVE_URL}/api/profile/admin"
    
    # 1. Get current profile
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"[!] Failed to get admin profile: {response.text}")
        return False
        
    profile_data = response.json()
    permissions = profile_data.get("permissions", [])
    
    # 2. Add manageCase permissions if missing
    if "manageCase/create" not in permissions:
        permissions.append("manageCase/create")
        permissions.append("manageCase/update")
        
        # 3. Update profile
        update_data = {"permissions": permissions}
        update_res = requests.patch(url, headers=HEADERS, json=update_data)
        
        if update_res.status_code == 200:
            print("[+] Successfully granted manageCase permissions to admin.")
            return True
        else:
            print(f"[!] Failed to update profile: {update_res.text}")
            return False
    else:
        print("[*] Admin already has manageCase permissions.")
        return True

def get_latest_blue_report():
    reports = sorted(glob.glob(os.path.join(REPORT_DIR, "blue_team_soc_report_*.txt")))
    if not reports:
        print("[!] No reports found.")
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

def create_thehive_case(alert):
    url = f"{THEHIVE_URL}/api/case"
    severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    thehive_severity = severity_map.get(alert.get("severity", "MEDIUM"), 2)
    
    case_data = {
        "title": f"AI Threat: {alert['name']} ({alert['id']})",
        "description": f"**Automated AI SOC Analysis**\n\n**Attack:** {alert['name']}\n**MITRE ATLAS:** {alert['id']}\n\n**AI Verdict:** {alert['verdict']}\n**AI Severity:** {alert['severity']}\n\n**Recommended Action:**\n{alert['action']}",
        "severity": thehive_severity,
        "tlp": 2,
        "tags": ["AI-SOC", "Automated", alert['id']],
        "type": "AI-Agent-Attack",
        "source": "AI Red/Blue Team Pipeline"
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=case_data, timeout=10)
        if response.status_code in (200, 201):
            print(f"[+] Created case: {case_data['title']}")
            return True
        else:
            print(f"[!] Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[!] Error: {e}")
        return False

if __name__ == "__main__":
    if fix_admin_permissions():
        print("\n[*] Starting case creation...")
        cases = get_latest_blue_report()
        if cases:
            success = 0
            total = 0
            for alert in cases:
                if "MALICIOUS" in alert.get("verdict", "").upper() or "SUSPICIOUS" in alert.get("verdict", "").upper():
                    total += 1
                    if create_thehive_case(alert):
                        success += 1
            print(f"\n[*] Successfully created {success}/{total} cases.")