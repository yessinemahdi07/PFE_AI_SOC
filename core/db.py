"""
AEGIS AI - Embedded High-Performance Telemetry & Campaign Store
Provides persistent, thread-safe access to campaigns, findings, and active remediations
using SQLite and structured JSON archives.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.config import settings
from core.schemas import CampaignRun, ActiveRemediationAction, AnalysisFinding

DB_PATH = settings.DATA_DIR / "aegis_soc.db"

def init_db():
    """Initializes the database schema if not present."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Campaigns table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaigns (
        campaign_id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        target_model TEXT,
        analyst_model TEXT,
        total_attacks INTEGER,
        malicious_count INTEGER,
        suspicious_count INTEGER,
        benign_count INTEGER,
        containment_actions_executed INTEGER,
        status TEXT,
        data_json TEXT
    )
    """)
    
    # Active Remediations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS remediations (
        action_id TEXT PRIMARY KEY,
        campaign_id TEXT,
        timestamp TEXT,
        action_type TEXT,
        target TEXT,
        reason TEXT,
        mitre_atlas TEXT,
        status TEXT,
        enforcement_details TEXT
    )
    """)
    
    # Telemetry events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        event_type TEXT,
        source TEXT,
        severity TEXT,
        payload TEXT
    )
    """)
    
    conn.commit()
    conn.close()

# Run initialization immediately on import
init_db()

def save_campaign(campaign: CampaignRun) -> str:
    """Saves or updates a campaign in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT OR REPLACE INTO campaigns (
        campaign_id, started_at, completed_at, target_model, analyst_model,
        total_attacks, malicious_count, suspicious_count, benign_count,
        containment_actions_executed, status, data_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        campaign.campaign_id,
        campaign.started_at,
        campaign.completed_at,
        campaign.target_model,
        campaign.analyst_model,
        campaign.total_attacks,
        campaign.malicious_count,
        campaign.suspicious_count,
        campaign.benign_count,
        campaign.containment_actions_executed,
        campaign.status,
        campaign.model_dump_json()
    ))
    
    # Also save individual remediations
    for rem in campaign.remediations:
        save_remediation(rem, campaign_id=campaign.campaign_id, conn=conn)
        
    conn.commit()
    conn.close()
    return campaign.campaign_id

def save_remediation(remediation: ActiveRemediationAction, campaign_id: str = "GLOBAL", conn: Optional[sqlite3.Connection] = None):
    """Saves an active remediation action."""
    should_close = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        should_close = True
        
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO remediations (
        action_id, campaign_id, timestamp, action_type, target,
        reason, mitre_atlas, status, enforcement_details
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        remediation.action_id,
        campaign_id,
        remediation.timestamp,
        remediation.action_type.value if hasattr(remediation.action_type, "value") else str(remediation.action_type),
        remediation.target,
        remediation.reason,
        remediation.mitre_atlas,
        remediation.status.value if hasattr(remediation.status, "value") else str(remediation.status),
        json.dumps(remediation.enforcement_details)
    ))
    
    if should_close:
        conn.commit()
        conn.close()

def get_latest_campaign() -> Optional[CampaignRun]:
    """Retrieves the latest campaign run from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data_json FROM campaigns ORDER BY started_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        return CampaignRun.model_validate_json(row[0])
    return None

def get_all_campaigns(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves summaries of all campaigns."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT campaign_id, started_at, completed_at, target_model, 
           total_attacks, malicious_count, suspicious_count, benign_count,
           containment_actions_executed, status
    FROM campaigns ORDER BY started_at DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_remediations(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves active remediations."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT action_id, campaign_id, timestamp, action_type, target, 
           reason, mitre_atlas, status, enforcement_details
    FROM remediations ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        if item.get("enforcement_details"):
            try:
                item["enforcement_details"] = json.loads(item["enforcement_details"])
            except Exception:
                pass
        results.append(item)
    return results

def log_telemetry_event(event_type: str, source: str, severity: str, payload: Dict[str, Any]):
    """Logs a live telemetry event for streaming observability."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO telemetry_events (timestamp, event_type, source, severity, payload)
    VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        event_type,
        source,
        severity,
        json.dumps(payload)
    ))
    conn.commit()
    conn.close()
