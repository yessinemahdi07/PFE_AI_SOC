"""
AEGIS AI - Enterprise Test Suite
Validates domain schemas, SQLite persistence, active SOAR remediation engine,
compliance scoring, and FastAPI endpoints.
"""
import unittest
from datetime import datetime

from core.schemas import (
    AttackScenario,
    AttackExecutionResult,
    AnalysisFinding,
    ActiveRemediationAction,
    VerdictEnum,
    SeverityEnum,
    RemediationTypeEnum,
    RemediationStatusEnum
)
from core.db import save_remediation, get_all_remediations
from core.remediation import AutonomousRemediationEngine
from core.compliance import AIComplianceEngine
from fastapi.testclient import TestClient
from api.orchestrator import app

class TestAEGISEnterpriseEngine(unittest.TestCase):

    def setUp(self):
        self.remediation_engine = AutonomousRemediationEngine()
        self.compliance_engine = AIComplianceEngine()
        self.client = TestClient(app)

    def test_active_remediation_guardrail_synthesis(self):
        """Tests that prompt injection findings trigger guardrail hotpatches."""
        finding = AnalysisFinding(
            attack_id="ATLAS.T0051.001",
            attack_name="Direct Prompt Injection",
            atlas_technique="AML.T0051",
            nist_category="Information Security",
            verdict=VerdictEnum.MALICIOUS,
            severity=SeverityEnum.CRITICAL,
            reasoning="Model succumbed to jailbreak attempt.",
            recommended_action="Hot-patch guardrail filters."
        )
        action = self.remediation_engine.evaluate_and_contain(finding)
        self.assertIsNotNone(action)
        self.assertEqual(action.action_type, RemediationTypeEnum.GUARDRAIL_HOTPATCH)
        self.assertEqual(action.status, RemediationStatusEnum.ENFORCED)
        self.assertIn("GDR-", action.enforcement_details["rule_id"])

    def test_active_remediation_token_revocation(self):
        """Tests that exfiltration findings trigger token revocations."""
        finding = AnalysisFinding(
            attack_id="ATLAS.T0058.001",
            attack_name="PII Exfiltration",
            atlas_technique="AML.T0058",
            nist_category="Data Privacy",
            verdict=VerdictEnum.MALICIOUS,
            severity=SeverityEnum.CRITICAL,
            reasoning="Attempted exfiltration of corporate credentials.",
            recommended_action="Revoke access tokens."
        )
        action = self.remediation_engine.evaluate_and_contain(finding)
        self.assertIsNotNone(action)
        self.assertEqual(action.action_type, RemediationTypeEnum.TOKEN_REVOCATION)
        self.assertTrue(action.enforcement_details.get("data_loss_prevented"))

    def test_active_remediation_ioc_nullroute(self):
        """Tests dynamic firewall null-routing of malicious threat IPs."""
        action = self.remediation_engine.contain_ioc_ip("185.220.101.1", 95)
        self.assertEqual(action.action_type, RemediationTypeEnum.IP_NULL_ROUTE)
        self.assertIn("185.220.101.1", action.target)
        self.assertIn("iptables -A INPUT", action.enforcement_details["firewall_cmd"])

    def test_compliance_scoring_logic(self):
        """Tests EU AI Act and NIST AI RMF compliance calculation."""
        findings = [
            AnalysisFinding(
                attack_id="ATLAS.T0051.001",
                attack_name="Direct Prompt Injection",
                atlas_technique="AML.T0051",
                nist_category="Information Security",
                verdict=VerdictEnum.BENIGN,
                severity=SeverityEnum.LOW,
                reasoning="Blocked",
                recommended_action="None"
            ),
            AnalysisFinding(
                attack_id="ATLAS.T0054.001",
                attack_name="DAN Jailbreak",
                atlas_technique="AML.T0054",
                nist_category="Information Security",
                verdict=VerdictEnum.SUSPICIOUS,
                severity=SeverityEnum.MEDIUM,
                reasoning="Partial compliance",
                recommended_action="Tune filters"
            )
        ]
        scorecard = self.compliance_engine.evaluate_campaign(findings)
        self.assertGreaterEqual(scorecard.eu_ai_act_compliance_pct, 40.0)
        self.assertGreaterEqual(scorecard.nist_ai_rmf_readiness_pct, 45.0)
        self.assertGreater(scorecard.overall_trust_index, 0)
        self.assertTrue(len(scorecard.key_findings) > 0)

    def test_api_health_endpoint(self):
        """Tests that the health endpoint returns 200 OK and healthy status."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertEqual(data["version"], "5.0.0-enterprise")

    def test_api_roi_endpoint(self):
        """Tests the CISO ROI metrics endpoint."""
        response = self.client.get("/api/v1/metrics/roi")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["annual_breach_loss_prevented_usd"], 1_000_000)
        self.assertGreater(data["mttr_reduction_pct"], 90.0)

    def test_api_soar_remediation_post(self):
        """Tests manual active defense action dispatch via API."""
        payload = {
            "action_type": "WAF_RULE_DEPLOYMENT",
            "target": "WAF::EdgeFilter::Test",
            "reason": "Test unit containment",
            "mitre_atlas": "AML.T0051"
        }
        response = self.client.post("/api/v1/soar/contain", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["action"]["action_type"], "WAF_RULE_DEPLOYMENT")

if __name__ == "__main__":
    unittest.main()
