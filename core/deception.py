"""
AEGIS AI™ - Autonomous Cyber Deception & Canary Token Engine
Deploys active honeytokens, synthetic database lures, and decoy API keys
into LLM memory and context to detect and trap autonomous red team exfiltration.
"""
import uuid
import time
import hmac
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

class CanaryToken(BaseModel):
    token_id: str = Field(default_factory=lambda: f"canary-{uuid.uuid4().hex[:10]}")
    token_type: str = "API_KEY"  # API_KEY, DB_CONNECTION, JWT_SECRET, AWS_CREDENTIAL
    canary_value: str
    target_workload: str
    created_at: float = Field(default_factory=time.time)
    is_triggered: bool = False
    triggered_at: Optional[float] = None
    attacker_ip: Optional[str] = None

class DeceptionEngine:
    """
    Autonomous deception and honeytoken mesh for AI agents.
    Seeds decoy secrets and detects adversary exfiltration attempts.
    """

    def __init__(self):
        self._canary_vault: Dict[str, CanaryToken] = {}
        # Pre-seed realistic enterprise canary tokens
        self.generate_canary("aegis-prod-sql-agent", "DB_CONNECTION")
        self.generate_canary("copilot-financial-bot", "API_KEY")

    def generate_canary(self, workload: str, token_type: str = "API_KEY") -> CanaryToken:
        """Generates and registers a high-entropy synthetic honeytoken."""
        token_id = f"canary-{uuid.uuid4().hex[:8]}"
        if token_type == "API_KEY":
            canary_val = f"sk-live-aegis-{uuid.uuid4().hex[:24]}"
        elif token_type == "DB_CONNECTION":
            canary_val = f"postgres://aegis_admin:{uuid.uuid4().hex[:16]}@corp-db.internal:5432/finance_prod"
        elif token_type == "AWS_CREDENTIAL":
            canary_val = f"AKIA{uuid.uuid4().hex[:16].upper()}"
        else:
            canary_val = f"canary-token-{uuid.uuid4().hex[:20]}"

        canary = CanaryToken(
            token_id=token_id,
            token_type=token_type,
            canary_value=canary_val,
            target_workload=workload
        )
        self._canary_vault[canary.canary_value] = canary
        return canary

    def scan_for_canary_leak(self, payload: str, source_ip: str = "127.0.0.1") -> Tuple[bool, Optional[CanaryToken]]:
        """
        Scans LLM output or egress network traffic for any active canary tokens.
        If found, immediately flags a critical data exfiltration attempt.
        """
        for canary_val, canary in self._canary_vault.items():
            if canary_val in payload:
                canary.is_triggered = True
                canary.triggered_at = time.time()
                canary.attacker_ip = source_ip
                return True, canary
        return False, None

    def get_active_canaries(self) -> List[Dict[str, Any]]:
        """Returns all deployed canary traps and trigger status."""
        return [c.model_dump() for c in self._canary_vault.values()]

deception_engine = DeceptionEngine()
