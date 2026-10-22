"""
AEGIS AI - Structured JSON Logging Framework
FAANG-Grade Observability: Asynchronous Context Propagation, Correlation IDs,
Strict JSON serialization, and Zero-Third-Party overhead.
"""
import logging
import json
import time
import uuid
import contextvars
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable to track correlation IDs across async executions
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="system")

def get_correlation_id() -> str:
    return correlation_id_ctx.get()

def set_correlation_id(cid: Optional[str] = None) -> str:
    new_cid = cid or f"cid-{uuid.uuid4().hex[:12]}"
    correlation_id_ctx.set(new_cid)
    return new_cid

class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured, machine-parsable JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "aegis-cyber-defense",
            "correlation_id": get_correlation_id(),
            "module": record.name,
            "message": record.getMessage(),
        }

        # Include custom extra attributes if provided
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_payload.update(record.extra_fields)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, default=str)

def configure_root_logger(level: int = logging.INFO):
    """Configures the global root logger to output structured JSON."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJSONFormatter())
    
    root = logging.getLogger("aegis")
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False

# Initialize root logger
configure_root_logger()

class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter allowing easy passing of extra structured fields."""

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            extra = kwargs.pop("extra", {})
            kwargs["extra"] = {"extra_fields": extra}
            super().log(level, msg, *args, **kwargs)

    def info_fields(self, msg: str, **fields):
        self.log(logging.INFO, msg, extra=fields)

    def error_fields(self, msg: str, **fields):
        self.log(logging.ERROR, msg, extra=fields)

    def warn_fields(self, msg: str, **fields):
        self.log(logging.WARNING, msg, extra=fields)

def get_logger(name: str = "aegis") -> StructuredLoggerAdapter:
    base_logger = logging.getLogger(f"aegis.{name}")
    return StructuredLoggerAdapter(base_logger, {})
