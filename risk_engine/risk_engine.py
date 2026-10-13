"""
Risk Engine - Threat Intelligence Enrichment
PFE: AI-Native SOC Orchestrator
Student: Yassine Mahdi
Internship: TDS by Nomios (Dec 2026 - May 2027)

Queries free Threat Intel APIs (AlienVault OTX, AbuseIPDB, VirusTotal)
to enrich IOCs and calculate final risk scores.
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

# Private IP ranges to exclude from enrichment (no point querying them)
PRIVATE_IP_PREFIXES = ("127.", "10.", "192.168.", "172.16.", "172.17.",
                       "172.18.", "172.19.", "172.20.", "172.21.", "172.22.",
                       "172.23.", "172.24.", "172.25.", "172.26.", "172.27.",
                       "172.28.", "172.29.", "172.30.", "172.31.")


# --- API Key Loading ---

def load_api_keys() -> dict:
    """Load API keys from config file."""
    if not os.path.exists(API_KEYS_FILE):
        print(f"[!] API keys file not found: {API_KEYS_FILE}")
        return {}
    with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Threat Intel Queries ---

def query_abuseipdb(ip: str, api_key: str) -> dict:
    """Query AbuseIPDB for IP reputation."""
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": api_key, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", {})
        return {
            "source": "AbuseIPDB",
            "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
            "total_reports": data.get("totalReports", 0),
            "country": data.get("countryCode", "Unknown"),
            "is_whitelisted": data.get("isWhitelisted", False)
        }
    except Exception as e:
        return {"source": "AbuseIPDB", "error": str(e)}


def query_alienvault_otx(ip: str, api_key: str) -> dict:
    """Query AlienVault OTX for IP threat intel."""
    url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general"
    headers = {"X-OTX-API-KEY": api_key}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        pulse_info = data.get("pulse_info", {})
        return {
            "source": "AlienVault OTX",
            "pulse_count": pulse_info.get("count", 0),
            "reputation": data.get("reputation", 0),
            "country": data.get("country_name", "Unknown")
        }
    except Exception as e:
        return {"source": "AlienVault OTX", "error": str(e)}


def query_virustotal(ip: str, api_key: str) -> dict:
    """Query VirusTotal for IP reputation."""
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": api_key}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        return {
            "source": "VirusTotal",
            "malicious_votes": stats.get("malicious", 0),
            "suspicious_votes": stats.get("suspicious", 0),
            "harmless_votes": stats.get("harmless", 0),
            "reputation": data.get("reputation", 0),
            "country": data.get("country", "Unknown")
        }
    except Exception as e:
        return {"source": "VirusTotal", "error": str(e)}


# --- Risk Scoring ---

def calculate_threat_intel_score(results: list) -> int:
    """Calculate a composite Threat Intel score (0-100)."""
    score = 0

    for r in results:
        source = r.get("source")

        if source == "AbuseIPDB":
            score += min(r.get("abuse_confidence_score", 0), 40)

        elif source == "AlienVault OTX":
            pulse_count = r.get("pulse_count", 0)
            score += min(pulse_count * 5, 30)

        elif source == "VirusTotal":
            malicious = r.get("malicious_votes", 0)
            score += min(malicious * 10, 30)

    return min(score, 100)


def enrich_ioc(ip: str, api_keys: dict) -> dict:
    """Enrich a single IOC with all available threat intel sources."""
    print(f"[*] Enriching IOC: {ip}")

    results = []
    if api_keys.get("abuseipdb"):
        print("[*] Querying AbuseIPDB...")
        results.append(query_abuseipdb(ip, api_keys["abuseipdb"]))
        time.sleep(1)

    if api_keys.get("alienvault_otx"):
        print("[*] Querying AlienVault OTX...")
        results.append(query_alienvault_otx(ip, api_keys["alienvault_otx"]))
        time.sleep(1)

    if api_keys.get("virustotal"):
        print("[*] Querying VirusTotal...")
        results.append(query_virustotal(ip, api_keys["virustotal"]))

    ti_score = calculate_threat_intel_score(results)

    return {
        "ioc": ip,
        "threat_intel_score": ti_score,
        "sources": results,
        "timestamp": datetime.now().isoformat()
    }


# --- Blue Agent Integration ---

def extract_iocs_from_blue_report() -> list:
    """
    Extract IOCs from the latest Blue Agent report.
    Scans for IP addresses, excluding private/local ranges.
    """
    blue_reports = sorted(glob.glob(os.path.join(REPORT_DIR, "blue_team_report_*.txt")))
    if not blue_reports:
        print("[!] No Blue Agent reports found.")
        return []

    latest_report = blue_reports[-1]
    print(f"[*] Extracting IOCs from: {latest_report}")

    with open(latest_report, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to extract IPv4 addresses
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    found_ips = re.findall(ip_pattern, content)

    # Filter out private/local IPs
    public_ips = set()
    for ip in found_ips:
        if not ip.startswith(PRIVATE_IP_PREFIXES):
            public_ips.add(ip)

    return list(public_ips)


# --- Main Entry Point ---

def run_risk_engine(iocs: list):
    """Main entry point: enrich a list of IOCs."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    api_keys = load_api_keys()

    if not api_keys:
        print("[!] No API keys loaded. Aborting.")
        return

    enriched = []
    for ip in iocs:
        result = enrich_ioc(ip, api_keys)
        enriched.append(result)
        print(f"[+] {ip} -> Threat Intel Score: {result['threat_intel_score']}/100\n")

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORT_DIR, f"risk_engine_report_{timestamp}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"[*] Report saved to: {report_file}")
    return enriched


if __name__ == "__main__":
    # Step 1: Extract IOCs from Blue Agent report
    iocs = extract_iocs_from_blue_report()

    # Step 2: Fallback to test IOCs if no public IOCs were found
    if not iocs:
        print("[!] No public IOCs found in Blue Agent report. Using test IOCs.")
        iocs = ["8.8.8.8", "185.220.101.1"]

    print(f"[*] Enriching {len(iocs)} IOC(s): {iocs}\n")
    run_risk_engine(iocs)