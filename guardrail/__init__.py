"""
AEGIS AI - Inline Semantic Guardrail & Proxy
"""
from guardrail.engine import inline_guardrail, InlineGuardrailEngine, GuardrailInspectionResult
from guardrail.inline_proxy import router as guardrail_router

__all__ = ["inline_guardrail", "InlineGuardrailEngine", "GuardrailInspectionResult", "guardrail_router"]
