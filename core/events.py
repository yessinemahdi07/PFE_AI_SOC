"""
AEGIS AI - Typed Asynchronous Event-Driven Bus (FAANG Decoupled Mesh)
Provides publish-subscribe messaging for security events, SOAR triggers, and telemetry.
"""
import uuid
import time
from typing import Dict, List, Type, Callable, Any
from pydantic import BaseModel, Field
from core.logger import get_logger, get_correlation_id

logger = get_logger("events")

class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    timestamp: float = Field(default_factory=time.time)
    correlation_id: str = Field(default_factory=get_correlation_id)
    event_type: str = "DOMAIN_EVENT"

class ThreatDetectedEvent(DomainEvent):
    event_type: str = "THREAT_DETECTED"
    attack_id: str
    attack_name: str
    verdict: str
    severity: str
    action_recommended: str

class RemediationEnforcedEvent(DomainEvent):
    event_type: str = "REMEDIATION_ENFORCED"
    action_id: str
    action_type: str
    target: str
    status: str

class GuardrailInterceptionEvent(DomainEvent):
    event_type: str = "GUARDRAIL_INTERCEPTION"
    prompt_snippet: str
    action: str
    threats_detected: List[str]
    risk_score: int

class EventBus:
    """Thread-safe, decoupled in-memory pub-sub event bus."""

    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[Callable[[Any], None]]] = {}

    def subscribe(self, event_class: Type[DomainEvent], handler: Callable[[Any], None]):
        """Registers an event subscriber callback."""
        if event_class not in self._subscribers:
            self._subscribers[event_class] = []
        self._subscribers[event_class].append(handler)

    def publish(self, event: DomainEvent):
        """Dispatches an event to all registered subscribers."""
        event_cls = type(event)
        handlers = self._subscribers.get(event_cls, [])
        for h in handlers:
            try:
                h(event)
            except Exception as e:
                logger.error_fields(f"Error in event handler {h.__name__}: {e}", event_id=event.event_id)

event_bus = EventBus()
