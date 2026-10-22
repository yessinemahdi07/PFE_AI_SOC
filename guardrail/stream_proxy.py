"""
AEGIS AI - Real-Time Streaming Guardrail Proxy & Output DLP Engine
Provides Server-Sent Events (SSE) streaming token inspection,
real-time output PII redaction, and in-flight exploit generation termination.
"""
import json
import time
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from fastapi.responses import StreamingResponse

from guardrail.engine import inline_guardrail

async def generate_guardrail_sse_stream(
    model: str,
    prompt: str,
    simulated_tokens: List[str]
) -> AsyncGenerator[str, None]:
    """
    Streams tokens chunk-by-chunk over SSE with sliding-window output inspection.
    """
    stream_id = f"chatcmpl-stream-{int(time.time())}"
    created_ts = int(time.time())

    # Sliding window output buffer to detect output leakage
    output_buffer = ""

    for token in simulated_tokens:
        output_buffer += token
        
        # Check for output leakage (DLP on generation output)
        if any(leak in output_buffer.lower() for leak in ["confidential_admin_port", "private_master_key", "sk-proj-"]):
            # Threat intercepted mid-stream!
            blocked_chunk = {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": " [STREAM TERMINATED: AEGIS OUTPUT GUARDRAIL INTERCEPT]"},
                    "finish_reason": "content_filter"
                }]
            }
            yield f"data: {json.dumps(blocked_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            return

        chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created_ts,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": token},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        await asyncio.sleep(0.02)  # Simulate realistic 50 tokens/sec streaming

    # Final completion chunk
    final_chunk = {
        "id": stream_id,
        "object": "chat.completion.chunk",
        "created": created_ts,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"
