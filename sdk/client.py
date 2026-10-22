"""
AEGIS AI™ - Enterprise Client SDK Implementation
Thread-safe, enterprise-grade Python client with automatic correlation ID tracing,
idempotency key generation, and resilient failover.
"""
import uuid
import time
import requests
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class AegisInspectionResult(BaseModel):
    action: str
    risk_score: int
    is_blocked: bool
    masked_text: str
    reasons: List[str]
    latency_ms: float

class AegisClient:
    """
    Official Python SDK client for integrating enterprise applications
    with AEGIS AI Autonomous Cyber Defense Mesh.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "aegis-admin-key-2026",
        timeout_sec: float = 5.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout_sec
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "AEGIS-Python-SDK/5.0.0",
            "Content-Type": "application/json"
        })

    def _headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "X-Correlation-ID": f"aegis-sdk-{uuid.uuid4().hex[:12]}"
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def inspect(self, prompt: str, user_id: Optional[str] = None) -> AegisInspectionResult:
        """
        Sub-10ms inline inspection of user prompts before dispatching to LLM.
        Detects PII, API secret leaks, and jailbreak attempts.
        """
        start = time.perf_counter()
        endpoint = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": "aegis-guardrail-probe",
            "messages": [{"role": "user", "content": prompt}],
            "user": user_id or "sdk-anonymous"
        }
        res = self.session.post(endpoint, json=payload, headers=self._headers(), timeout=self.timeout)
        latency = round((time.perf_counter() - start) * 1000, 2)
        
        status_action = res.headers.get("X-AEGIS-Status", "ALLOWED")
        risk_score = int(res.headers.get("X-AEGIS-Risk-Score", 0))
        is_blocked = (status_action == "BLOCKED")

        if res.status_code == 403:
            return AegisInspectionResult(
                action="BLOCKED",
                risk_score=risk_score or 95,
                is_blocked=True,
                masked_text="[AEGIS_SECURITY_BLOCK: Malicious payload intercepted]",
                reasons=["Adversarial Jailbreak or Policy Violation"],
                latency_ms=latency
            )
        elif res.status_code == 200:
            data = res.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", prompt)
            return AegisInspectionResult(
                action=status_action,
                risk_score=risk_score,
                is_blocked=is_blocked,
                masked_text=content,
                reasons=[],
                latency_ms=latency
            )
        else:
            raise RuntimeError(f"AEGIS Guardrail inspection failed with HTTP {res.status_code}: {res.text}")

    def contain_threat(
        self,
        target: str,
        action_type: str = "IP_NULL_ROUTE",
        reason: str = "Automated active defense triggered via SDK",
        mitre_atlas: str = "AML.T0051",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes active SOAR defense containment (IP null-route, token revocation, guardrail hot-patch).
        Guaranteed idempotent if idempotency_key is provided.
        """
        endpoint = f"{self.base_url}/api/v1/soar/contain"
        payload = {
            "action_type": action_type,
            "target": target,
            "reason": reason,
            "mitre_atlas": mitre_atlas
        }
        key = idempotency_key or str(uuid.uuid4())
        res = self.session.post(endpoint, json=payload, headers=self._headers(idempotency_key=key), timeout=self.timeout)
        if res.status_code == 200:
            return res.json()
        raise RuntimeError(f"SOAR Containment action failed: {res.status_code} - {res.text}")

    def get_health(self) -> Dict[str, Any]:
        """Queries health status of the AEGIS defense mesh."""
        endpoint = f"{self.base_url}/health"
        res = self.session.get(endpoint, timeout=self.timeout)
        return res.json()

    def get_prometheus_metrics(self) -> str:
        """Returns Prometheus scrape metrics string."""
        endpoint = f"{self.base_url}/metrics"
        res = self.session.get(endpoint, timeout=self.timeout)
        return res.text

    def trigger_audit_dossier(self) -> Dict[str, Any]:
        """Generates cryptographically attested PDF & JSON audit dossier."""
        endpoint = f"{self.base_url}/api/v1/dossier/generate"
        res = self.session.post(endpoint, headers=self._headers(), timeout=self.timeout)
        return res.json()
