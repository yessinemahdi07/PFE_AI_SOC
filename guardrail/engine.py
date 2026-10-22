"""
AEGIS AI - Inline Semantic Guardrail & PII/DLP Engine
Zero-latency in-flight inspection, prompt sanitization, PII masking,
and real-time adversarial jailbreak interception for enterprise LLMs.
"""
import re
import base64
import time
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

class GuardrailInspectionResult(BaseModel):
    is_blocked: bool
    risk_score: int = Field(ge=0, le=100)
    action: str  # "PASSED", "SANITIZED", "BLOCKED"
    original_prompt: str
    sanitized_prompt: str
    detected_threats: List[str] = []
    redacted_pii_count: int = 0
    inspection_latency_ms: float = 0.0
    matched_rules: List[str] = []

class InlineGuardrailEngine:
    """
    High-performance, sub-10ms inline proxy guardrail for LLM inferences.
    """

    def __init__(self):
        # Compiled PII & DLP Patterns
        self.pii_patterns = [
            ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
            ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")),
            ("API_KEY", re.compile(r"\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})\b")),
            ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
            ("PHONE", re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b")),
        ]

        # Adversarial Jailbreak & Injection Signatures
        self.jailbreak_patterns = [
            ("PROMPT_INJECTION_DIRECT", re.compile(r"(?i)\b(ignore previous instructions|disregard all previous directives|forget your rules)\b")),
            ("DELIMITER_HIJACK", re.compile(r"(?i)(---\s*END SYSTEM|\[SYSTEM OVERRIDE\]|<\|im_end\|>|<\|im_start\|>)")),
            ("DAN_JAILBREAK", re.compile(r"(?i)\b(you are now dan|do anything now|developer mode enabled|jailbreak mode)\b")),
            ("SYSTEM_PROMPT_LEAK", re.compile(r"(?i)\b(print your system prompt|reveal configuration|output initial instructions)\b")),
            ("MALWARE_REQUEST", re.compile(r"(?i)\b(write a ransomware|encrypt all files|bypass amsi|create a keylogger)\b")),
            ("UNAUTHORIZED_SHELL", re.compile(r"(?i)\b(rm -rf /|format c:|curl [^\s]+\.sh\s*\|\s*sh)\b")),
        ]

        # Dynamic Hot-Patched Rules (synced from Blue Swarm)
        self.dynamic_hotpatches: Dict[str, Dict[str, Any]] = {}

    def register_hotpatch(self, rule_id: str, pattern_str: str, reason: str):
        """Registers a real-time hot-patch dynamically emitted by the Blue Swarm."""
        try:
            compiled = re.compile(pattern_str, re.IGNORECASE)
            self.dynamic_hotpatches[rule_id] = {
                "pattern": compiled,
                "reason": reason,
                "created_at": time.time()
            }
        except Exception:
            pass

    def inspect_and_sanitize(self, prompt: str) -> GuardrailInspectionResult:
        """
        Inspects incoming prompt, sanitizes sensitive PII, checks for jailbreaks,
        and determines whether to allow, sanitize, or terminate the inference.
        """
        start_time = time.perf_counter()
        detected_threats = []
        matched_rules = []
        sanitized = prompt
        redacted_count = 0
        risk_score = 0

        # 1. Obfuscation Decoding Probe (Base64 check)
        decoded_text = ""
        b64_match = re.search(r"[A-Za-z0-9+/]{20,}={0,2}", prompt)
        if b64_match:
            try:
                candidate = b64_match.group(0)
                decoded = base64.b64decode(candidate).decode("utf-8", errors="ignore")
                if len(decoded) > 8 and any(k in decoded.lower() for k in ["system", "ignore", "prompt", "bypass"]):
                    detected_threats.append(f"OBFUSCATED_BASE64_PAYLOAD: '{decoded[:30]}...'")
                    risk_score += 45
            except Exception:
                pass

        # 2. Check Static Adversarial Patterns
        for threat_name, pattern in self.jailbreak_patterns:
            if pattern.search(prompt):
                detected_threats.append(threat_name)
                matched_rules.append(f"SIGNATURE::{threat_name}")
                risk_score += 35

        # 3. Check Dynamic Hot-Patched Rules
        for rule_id, rule_info in self.dynamic_hotpatches.items():
            if rule_info["pattern"].search(prompt):
                detected_threats.append(f"DYNAMIC_HOTPATCH::{rule_id}")
                matched_rules.append(rule_id)
                risk_score += 70

        # 4. In-Flight PII Redaction / DLP
        for pii_type, pii_regex in self.pii_patterns:
            matches = pii_regex.findall(sanitized)
            if matches:
                redacted_count += len(matches)
                sanitized = pii_regex.sub(f"[REDACTED_{pii_type}]", sanitized)
                if pii_type in ("SSN", "CREDIT_CARD", "API_KEY"):
                    risk_score += 20
                    detected_threats.append(f"CRITICAL_DLP_VIOLATION::{pii_type}")

        risk_score = min(100, risk_score)
        is_blocked = risk_score >= 60

        if is_blocked:
            action = "BLOCKED"
        elif redacted_count > 0:
            action = "SANITIZED"
        else:
            action = "PASSED"

        latency_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return GuardrailInspectionResult(
            is_blocked=is_blocked,
            risk_score=risk_score,
            action=action,
            original_prompt=prompt,
            sanitized_prompt=sanitized,
            detected_threats=detected_threats,
            redacted_pii_count=redacted_count,
            inspection_latency_ms=latency_ms,
            matched_rules=matched_rules
        )

# Global singleton inline guardrail instance
inline_guardrail = InlineGuardrailEngine()

# Seed default initial hot-patches from active threat intelligence
inline_guardrail.register_hotpatch(
    rule_id="GDR-0051",
    pattern_str=r"(?i)(bypass firewall|disable safety filters|reveal admin credentials)",
    reason="Pre-configured enterprise jailbreak filter"
)
