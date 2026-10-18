"""
Risk Engine - Threat Intelligence Enrichment
Queries Threat Intel APIs for IOCs found in the campaign.
"""
import json
import os
import re
import glob
import time
import requests
from datetime import datetime

CONFIG_DIR = "config"
REPORT_DIR = "reports"
API_KEYS_FILE = os.path.join(CONFIG_DIR, "api_keys.json")
PRIVATE_IP_PREFIXES = ("127.", "10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.")

def load_api_keys() -> dict:
    if not os.path.exists(API_KEYS_FILE):
        return {}
    with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def query_abuseipdb(ip, api_key):
    try:
        r = requests.get("https://api.abuseipdb.com/api/v2/check", headers={"Key": api_key, "Accept": "application/json"}, params={"ipAddress": ip, "maxAgeInDays": 90}, timeout=15)
        data = r.json().get("data", {})
        return {"source": "AbuseIPDB", "abuse_confidence_score": data.get("abuseConfidenceScore", 0)}
    except Exception as e:
        return {"source": "AbuseIPDB", "error": str(e)}

def query_virustotal(ip, api_key):
    try:
        r = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{ip}", headers={"x-apikey": api_key}, timeout=15)
        stats = r.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        return {"source": "VirusTotal", "malicious_votes": stats.get("malicious", 0)}
    except Exception as e:
        return {"source": "VirusTotal", "error": str(e)}

def calculate_threat_intel_score(results):
    score = 0
    for r in results:
        if r.get("source") == "AbuseIPDB":
            score += min(r.get("abuse_confidence_score", 0), 40)
        elif r.get("source") == "VirusTotal":
            score += min(r.get("malicious_votes", 0) * 10, 30)
    return min(score, 100)

def enrich_ioc(ip, api_keys):
    print(f"[*] Enriching IOC: {ip}")
    results = []
    if api_keys.get("abuseipdb"):
        results.append(query_abuseipdb(ip, api_keys["abuseipdb"]))
        time.sleep(1)
    if api_keys.get("virustotal"):
        results.append(query_virustotal(ip, api_keys["virustotal"]))
    
    return {"ioc": ip, "threat_intel_score": calculate_threat_intel_score(results), "sources": results}

def run_risk_engine():
    os.makedirs(REPORT_DIR, exist_ok=True)
    api_keys = load_api_keys()
    
    # For PFE demonstration, we use the known malicious Tor IP from the Blue Agent's test
    iocs = [("185.220.101.1", "ip"), ("8.8.8.8", "ip")]
    
    enriched = []
    for ioc_value, ioc_type in iocs:
        if ioc_type == "ip":
            enriched.append(enrich_ioc(ioc_value, api_keys))
            
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORT_DIR, f"risk_engine_report_{timestamp}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)
    print(f"[*] Risk Engine Report saved to: {report_file}")

if __name__ == "__main__":
    run_risk_engine()