# 🛠️ AEGIS AI — Production SRE Runbook & Incident Playbook
### **Site Reliability Engineering (SRE) On-Call Manual**

---

## 1. Incident Severity Definitions & Escalation Matrix

| Severity | Definition | Response Time | Incident Commander | Communication Cadence |
|---|---|---|---|---|
| **SEV-0** | Complete platform outage, active data exfiltration breach, or $>10\%$ error rate. | **$\le 5\text{ mins}$** | VP of Eng / Staff SRE | Every 15 mins to Executive Staff |
| **SEV-1** | P99 latency $> 50\text{ms}$, inline proxy rejecting legitimate traffic, or SIEM disconnect. | **$\le 15\text{ mins}$** | Senior SRE / On-Call Lead | Every 30 mins to SecOps |
| **SEV-2** | Elevated rate-limiting, non-critical background swarm timeout. | **$\le 1\text{ hour}$** | On-Call SRE | Updates via Jira / Slack `#sre-alerts` |
| **SEV-3** | Minor telemetry delays, dashboard aesthetic glitch. | **$\le 24\text{ hours}$** | Assigned Engineer | Regular sprint backlog |

---

## 2. Observability & Diagnostic Commands

### Check Kubernetes / Container Liveness & Health
```bash
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/readyz
```

### Inspect Prometheus Golden Signals
```bash
curl -s http://localhost:8000/metrics | grep aegis_http
```

### Trace a Request by Correlation ID
Every inbound request stamps an `X-Correlation-ID`. Filter application logs:
```bash
grep "cid-abc123456789" logs/*.log
```

---

## 3. Incident Playbooks

### Playbook A: P99 Guardrail Latency Spike ($> 20\text{ms}$)
1. **Identify Bottleneck:** Check `curl -s http://localhost:8000/metrics | grep aegis_guardrail`
2. **Review Regex Complexity:** Verify if an unanchored regex was introduced via a dynamic hot-patch.
3. **Emergency Action:** Revert recent hot-patches via CLI:
   ```bash
   python -c "from guardrail.engine import inline_guardrail; inline_guardrail.dynamic_hotpatches.clear()"
   ```

### Playbook B: Circuit Breaker Tripped to `OPEN` State
1. **Identify Target:** Check structured JSON logs for:
   `"message": "CircuitBreaker [...] tripped to OPEN state"`
2. **Verify Upstream Ollama Service:**
   ```bash
   curl -i http://localhost:11434/
   ```
3. If Ollama crashed due to OOM:
   ```bash
   ollama serve &
   ```
   The circuit breaker will enter `HALF_OPEN` after 5 seconds and automatically heal.

### Playbook C: Active Exploit Mitigation Rollback
If a benign user is accidentally blocked by a strict null-route or token revocation:
1. Lookup the action in the database:
   ```sql
   SELECT * FROM remediations WHERE target LIKE '%185.220.101.1%' ORDER BY timestamp DESC LIMIT 1;
   ```
2. Execute the rollback command provided in `rollback_command`:
   ```bash
   iptables -D INPUT -s 185.220.101.1 -j DROP
   ```

---

## 4. Disaster Recovery & Clean Re-deployment

### Containerized Re-deploy
```bash
docker-compose down
docker-compose up --build -d
```

### Verify Service Readiness
```bash
python -m unittest discover -s tests -p "test_*.py"
```
Ensure all 18 unit and integration tests pass before routing production customer traffic.
