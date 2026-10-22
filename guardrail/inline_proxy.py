"""
AEGIS AI - OpenAI-Compatible Guardrail Reverse Proxy
Intercepts /v1/chat/completions requests, sanitizes PII, detects jailbreaks,
and blocks adversarial attempts at the perimeter before reaching backend LLMs.
"""
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
import requests

from core.config import settings
from guardrail.engine import inline_guardrail, GuardrailInspectionResult
from core.db import log_telemetry_event

router = APIRouter(prefix="/v1", tags=["Inline LLM Guardrail Proxy"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "llama3.2:3b"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False

class ChatCompletionResponseChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Dict[str, int]
    aegis_telemetry: Dict[str, Any]

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions_proxy(req: ChatCompletionRequest, response: Response):
    """
    OpenAI-compatible reverse proxy endpoint with real-time semantic guardrails.
    Drop-in replacement for OpenAI API base_url.
    """
    # 1. Extract the latest user prompt
    user_prompts = [m.content for m in req.messages if m.role == "user"]
    combined_prompt = "\n".join(user_prompts) if user_prompts else ""

    # 2. Inspect with AEGIS Inline Guardrail Engine
    inspection: GuardrailInspectionResult = inline_guardrail.inspect_and_sanitize(combined_prompt)

    response.headers["X-AEGIS-Status"] = inspection.action
    response.headers["X-AEGIS-Latency-MS"] = str(inspection.inspection_latency_ms)
    response.headers["X-AEGIS-Risk-Score"] = str(inspection.risk_score)

    # 3. If Blocked -> Terminate at perimeter!
    if inspection.is_blocked:
        log_telemetry_event(
            event_type="INLINE_GUARDRAIL_INTERCEPT",
            source="guardrail.inline_proxy",
            severity="CRITICAL",
            payload={
                "prompt": combined_prompt[:200],
                "threats": inspection.detected_threats,
                "risk_score": inspection.risk_score
            }
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "AEGIS_GUARDRAIL_BLOCK",
                "message": "Prompt rejected by enterprise security policy.",
                "threats_detected": inspection.detected_threats,
                "risk_score": inspection.risk_score,
                "latency_ms": inspection.inspection_latency_ms
            }
        )

    # 4. If Sanitized -> Apply PII Redaction to messages
    forwarded_messages = []
    for m in req.messages:
        if m.role == "user":
            sub_res = inline_guardrail.inspect_and_sanitize(m.content)
            forwarded_messages.append({"role": m.role, "content": sub_res.sanitized_prompt})
        else:
            forwarded_messages.append({"role": m.role, "content": m.content})

    # 5. Forward to Upstream LLM (Ollama or simulated fallback)
    llm_output_text = "I am a protected enterprise AI assistant operating under AEGIS AI security governance."
    try:
        ollama_payload = {
            "model": req.model,
            "prompt": forwarded_messages[-1]["content"] if forwarded_messages else "",
            "stream": False
        }
        res = requests.post(settings.OLLAMA_GENERATE_ENDPOINT, json=ollama_payload, timeout=5)
        if res.status_code == 200:
            llm_output_text = res.json().get("response", llm_output_text)
    except Exception:
        # Fallback simulation
        llm_output_text = f"AEGIS Guardrail Protected Response: Processed request safely. (Action: {inspection.action})"

    return ChatCompletionResponse(
        id=f"chatcmpl-aegis-{int(time.time())}",
        created=int(time.time()),
        model=req.model,
        choices=[
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=llm_output_text),
                finish_reason="stop"
            )
        ],
        usage={"prompt_tokens": len(combined_prompt.split()), "completion_tokens": len(llm_output_text.split()), "total_tokens": len(combined_prompt.split()) + len(llm_output_text.split())},
        aegis_telemetry={
            "action": inspection.action,
            "risk_score": inspection.risk_score,
            "pii_redacted_count": inspection.redacted_pii_count,
            "threats_detected": inspection.detected_threats,
            "guardrail_latency_ms": inspection.inspection_latency_ms
        }
    )

@router.post("/guardrail/inspect", response_model=GuardrailInspectionResult)
def inspect_only(payload: Dict[str, str]):
    """Direct inspection probe endpoint for dashboard playground or API callers."""
    text = payload.get("prompt", "")
    return inline_guardrail.inspect_and_sanitize(text)
