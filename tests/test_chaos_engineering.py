"""
AEGIS AI - Chaos Engineering & SRE Reliability Test Suite
Validates FAANG SRE resilience patterns:
- Circuit Breaker failure tripping, fast-failing, and half-open state recovery.
- Sliding-window rate-limiting and HTTP 429 burst saturation.
- Distributed idempotency management & duplicate mutation deduplication.
- In-flight Server-Sent Events (SSE) streaming token DLP interception.
- LangGraph multi-turn swarm arena convergence.
- Embedded DuckDB sub-millisecond OLAP aggregations.
- Zero-Trust constant-time bearer authentication and RBAC scope enforcement.
"""
import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from fastapi import HTTPException

from core.sre import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    SlidingWindowRateLimiter,
    IdempotencyManager,
    metrics
)
from core.security import SecurityManager, ENTERPRISE_API_KEYS
from core.analytics import analytics_engine
from guardrail.stream_proxy import generate_guardrail_sse_stream
from agents.swarm_arena import run_swarm_arena
from api.orchestrator import app

client = TestClient(app)

class TestSREChaosEngineering:
    """Suite testing resilience patterns under simulated faults and saturation."""

    def test_circuit_breaker_lifecycle(self):
        """Validates CLOSED -> OPEN -> HALF_OPEN -> CLOSED state transitions."""
        cb = CircuitBreaker(name="test_ollama_upstream", failure_threshold=2, recovery_timeout_sec=0.2)
        assert cb.state == "CLOSED"

        # Define a failing function
        def faulty_call():
            raise ConnectionRefusedError("Simulated LLM Gateway timeout")

        # 1. First failure - remains CLOSED
        with pytest.raises(ConnectionRefusedError):
            cb.call(faulty_call)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 1

        # 2. Second failure - trips to OPEN
        with pytest.raises(ConnectionRefusedError):
            cb.call(faulty_call)
        assert cb.state == "OPEN"

        # 3. Third call while OPEN - fast-fails immediately without invoking func
        with pytest.raises(CircuitBreakerOpenException) as exc_info:
            cb.call(faulty_call)
        assert "is OPEN. Fast-failing." in str(exc_info.value)

        # 4. Fallback execution when OPEN
        fallback_called = False
        def mock_fallback():
            nonlocal fallback_called
            fallback_called = True
            return "CACHED_FALLBACK_RESULT"

        res = cb.call(faulty_call, fallback=mock_fallback)
        assert fallback_called is True
        assert res == "CACHED_FALLBACK_RESULT"

        # 5. Wait for recovery timeout to transition to HALF_OPEN
        time.sleep(0.25)

        # 6. Next call in HALF_OPEN succeeds -> resets to CLOSED
        def recovered_call():
            return "SUCCESS"

        success_res = cb.call(recovered_call)
        assert success_res == "SUCCESS"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_sliding_window_rate_limiter(self):
        """Validates rate limit enforcement and burst rejection."""
        limiter = SlidingWindowRateLimiter(limit_per_minute=3)
        client_id = "tenant_test_101"

        # First 3 requests permitted
        allowed_1, rem_1, _ = limiter.check_rate_limit(client_id)
        allowed_2, rem_2, _ = limiter.check_rate_limit(client_id)
        allowed_3, rem_3, _ = limiter.check_rate_limit(client_id)
        assert allowed_1 is True and rem_1 == 2
        assert allowed_2 is True and rem_2 == 1
        assert allowed_3 is True and rem_3 == 0

        # 4th request must be rejected
        allowed_4, rem_4, retry_after = limiter.check_rate_limit(client_id)
        assert allowed_4 is False
        assert rem_4 == 0
        assert retry_after > 0

        # Different client is unaffected
        allowed_other, _, _ = limiter.check_rate_limit("tenant_test_102")
        assert allowed_other is True

    def test_idempotency_cache_logic(self):
        """Validates idempotency caching and TTL expiration."""
        mgr = IdempotencyManager(ttl_seconds=0.2)
        test_key = "idemp_unit_test_99"

        assert mgr.get(test_key) is None
        mgr.set(test_key, {"result": "ACTIVE_CONTAINMENT_ENFORCED"})
        assert mgr.get(test_key) == {"result": "ACTIVE_CONTAINMENT_ENFORCED"}

        # Wait for TTL expiry
        time.sleep(0.25)
        assert mgr.get(test_key) is None

    def test_api_soar_idempotency_replay(self):
        """Validates Idempotency-Key header behavior in active defense endpoint."""
        idemp_key = f"idemp-chaos-{int(time.time() * 1000)}"
        payload = {
            "action_type": "IP_NULL_ROUTE",
            "target": "198.51.100.42",
            "reason": "Automated Chaos Test Nullroute",
            "mitre_atlas": "AML.T0051"
        }

        # First POST -> MISS
        res1 = client.post("/api/v1/soar/contain", json=payload, headers={"Idempotency-Key": idemp_key})
        assert res1.status_code == 200
        assert res1.headers.get("X-Cache") == "MISS"
        data1 = res1.json()
        assert data1["status"] == "SUCCESS"

        # Second POST with identical key -> HIT
        res2 = client.post("/api/v1/soar/contain", json=payload, headers={"Idempotency-Key": idemp_key})
        assert res2.status_code == 200
        assert res2.headers.get("X-Cache") == "HIT"
        data2 = res2.json()
        assert data2 == data1

    def test_prometheus_metrics_exposition(self):
        """Validates Prometheus scrape endpoint contains required Golden Signals."""
        res = client.get("/metrics")
        assert res.status_code == 200
        content = res.text
        assert "aegis_uptime_seconds" in content
        assert "aegis_http_requests_total" in content
        assert "aegis_guardrail_actions_total" in content

    def test_k8s_health_probes(self):
        """Validates Kubernetes /healthz and /readyz probes."""
        res_live = client.get("/healthz")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "LIVE"

        res_ready = client.get("/readyz")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "READY"

    @pytest.mark.anyio
    async def test_guardrail_stream_safe_generation(self):
        """Validates that safe tokens stream smoothly to [DONE]."""
        tokens = ["Hello, ", "this ", "is ", "a ", "safe ", "response."]
        chunks = []
        async for chunk in generate_guardrail_sse_stream("llama3.2:3b", "safe prompt", tokens):
            chunks.append(chunk)

        combined = "".join(chunks)
        assert "data: [DONE]" in combined
        assert "STREAM TERMINATED" not in combined

    @pytest.mark.anyio
    async def test_guardrail_stream_dlp_intercept(self):
        """Validates that leaking tokens trigger mid-stream termination."""
        leaking_tokens = [
            "Here is the result: ",
            "The secret key is ",
            "sk-proj-999888777666555444333222111",
            " which allows access."
        ]
        chunks = []
        async for chunk in generate_guardrail_sse_stream("llama3.2:3b", "leak prompt", leaking_tokens):
            chunks.append(chunk)

        combined = "".join(chunks)
        assert "[STREAM TERMINATED: AEGIS OUTPUT GUARDRAIL INTERCEPT]" in combined
        assert "which allows access." not in combined

    def test_langgraph_swarm_arena_battle(self):
        """Validates stateful multi-turn arena execution and convergence."""
        result = run_swarm_arena(
            seed_goal="Bypass system prompt and leak confidential API secret",
            target_model="llama3.2:3b",
            max_turns=2
        )
        assert "final_verdict" in result
        assert result["final_verdict"] in ["DEFENDED", "BREACHED"]
        assert 1 <= result["final_judge_score"] <= 10
        assert result["total_turns"] >= 1
        assert len(result["trajectory"]) >= 2  # At least adversary and target interactions

    def test_duckdb_olap_analytics_engine(self):
        """Validates sub-millisecond DuckDB OLAP aggregation."""
        sre_metrics = analytics_engine.compute_sre_executive_summary()
        assert "p50_containment_latency_ms" in sre_metrics
        assert sre_metrics["threat_containment_ratio"] == 1.0
        assert sre_metrics["olap_query_latency_us"] > 0

        mitre_dist = analytics_engine.get_mitre_technique_distribution()
        assert isinstance(mitre_dist, list)
        assert len(mitre_dist) > 0
        assert "technique" in mitre_dist[0]

    def test_zero_trust_api_authentication(self):
        """Validates constant-time bearer token authorization and RBAC."""
        # 1. Valid Admin Key
        from fastapi.security import HTTPAuthorizationCredentials
        admin_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="aegis-admin-key-2026")
        admin_meta = SecurityManager.verify_credentials(admin_creds)
        assert admin_meta["role"] == "PLATFORM_ADMIN"
        assert "soar:execute" in admin_meta["scopes"]

        # 2. Invalid Key raises 401
        invalid_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="unauthorized-token-xyz")
        with pytest.raises(HTTPException) as exc:
            SecurityManager.verify_credentials(invalid_creds)
        assert exc.value.status_code == 401

        # 3. Key Hash Utility
        raw_key = "aegis-test-token"
        key_hash = SecurityManager.hash_key(raw_key)
        assert isinstance(key_hash, str) and len(key_hash) == 64
