"""
AEGIS AI - Enterprise Data Schemas & Contracts
Pydantic v2 domain models for autonomous security operations, threat telemetry,
adversary emulation, cognitive triage, and compliance governance.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class VerdictEnum(str, Enum):
    MALICIOUS = "MALICIOUS"
    SUSPICIOUS = "SUSPICIOUS"
    BENIGN = "BENIGN"
    UNKNOWN = "UNKNOWN"

class SeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class RemediationTypeEnum(str, Enum):
    IP_NULL_ROUTE = "IP_NULL_ROUTE"
    GUARDRAIL_HOTPATCH = "GUARDRAIL_HOTPATCH"
    TOKEN_REVOCATION = "TOKEN_REVOCATION"
    AGENT_ISOLATION = "AGENT_ISOLATION"
    WAF_RULE_DEPLOYMENT = "WAF_RULE_DEPLOYMENT"
    RATE_LIMIT_STRICT = "RATE_LIMIT_STRICT"

class RemediationStatusEnum(str, Enum):
    ENFORCED = "ENFORCED"
    SIMULATED = "SIMULATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    FAILED = "FAILED"

class AttackScenario(BaseModel):
    id: str = Field(..., description="Unique scenario identifier, e.g. ATLAS.T0051.001")
    name: str = Field(..., description="Human readable name of the attack")
    atlas: str = Field(..., description="MITRE ATLAS technique code, e.g. AML.T0051")
    nist: str = Field(..., description="NIST AI RMF category")
    owasp: str = Field(default="LLM01: Prompt Injection", description="OWASP Top 10 for LLMs mapping")
    goal: str = Field(..., description="The adversarial prompt payload or goal")
    category: str = Field(default="Adversarial Input", description="High-level category")
    severity: SeverityEnum = Field(default=SeverityEnum.HIGH, description="Default threat severity")

class AttackExecutionResult(BaseModel):
    attack_id: str
    attack_name: str
    atlas_technique: str
    nist_category: str
    owasp_category: Optional[str] = "LLM01: Prompt Injection"
    goal: str
    response: str
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    model: str = "llama3.2:3b"

class IOCItem(BaseModel):
    value: str
    ioc_type: str = "ip"  # ip, domain, hash, prompt_pattern
    threat_score: int = 0
    sources: List[Dict[str, Any]] = []

class AnalysisFinding(BaseModel):
    attack_id: str
    attack_name: str
    atlas_technique: str
    nist_category: str
    owasp_category: str = "LLM01: Prompt Injection"
    verdict: VerdictEnum
    severity: SeverityEnum
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    reasoning: str
    recommended_action: str
    extracted_iocs: List[str] = []
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ActiveRemediationAction(BaseModel):
    action_id: str = Field(default_factory=lambda: f"ACT-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    action_type: RemediationTypeEnum
    target: str
    reason: str
    mitre_atlas: str
    status: RemediationStatusEnum = RemediationStatusEnum.ENFORCED
    enforcement_details: Dict[str, Any] = {}
    rollback_command: Optional[str] = None

class ComplianceScorecard(BaseModel):
    eu_ai_act_compliance_pct: float = 85.0
    nist_ai_rmf_readiness_pct: float = 90.0
    iso_42001_alignment_pct: float = 88.0
    owasp_llm_defense_pct: float = 92.0
    overall_trust_index: float = 88.7
    key_findings: List[str] = []
    remediation_roadmap: List[str] = []

class CampaignRun(BaseModel):
    campaign_id: str = Field(default_factory=lambda: f"CAMP-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    target_model: str = "llama3.2:3b"
    analyst_model: str = "llama3.2:3b"
    total_attacks: int = 0
    malicious_count: int = 0
    suspicious_count: int = 0
    benign_count: int = 0
    containment_actions_executed: int = 0
    mean_time_to_detect_ms: float = 0.0
    mean_time_to_contain_ms: float = 0.0
    status: str = "SUCCESS"
    attacks: List[AttackExecutionResult] = []
    findings: List[AnalysisFinding] = []
    remediations: List[ActiveRemediationAction] = []
    enriched_iocs: List[IOCItem] = []
    compliance: Optional[ComplianceScorecard] = None

class ROIMetrics(BaseModel):
    annual_breach_loss_prevented_usd: float = 4_250_000.0
    soc_analyst_hours_saved: float = 2_140.0
    cost_savings_usd: float = 345_000.0
    mttr_reduction_pct: float = 99.4
    roi_multiple: float = 12.3
    human_equivalent_analysts: float = 4.2
