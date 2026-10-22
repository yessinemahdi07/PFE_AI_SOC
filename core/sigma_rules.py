"""
AEGIS AI™ - Automated Detection Engineering & Sigma / YARA-L Rule Synthesizer
Converts discovered AI attack techniques, prompt injections, and tool exploits
into production-ready Sigma (YAML), Google Chronicle (YARA-L), and Wazuh XML rules.
"""
import uuid
import time
from typing import Dict, Any, List

class DetectionRuleSynthesizer:
    """
    Automates SIEM detection engineering for AI workloads.
    """

    @staticmethod
    def generate_sigma_rule(
        title: str,
        technique_id: str = "AML.T0051",
        pattern_str: str = "(?i)(ignore previous|override admin)",
        severity: str = "high"
    ) -> str:
        """Generates industry-standard Sigma detection rule (YAML)."""
        rule_id = str(uuid.uuid4())
        return f"""title: AEGIS AI - {title}
id: {rule_id}
status: production
description: Autonomous detection of adversarial AI exploit or prompt injection targeting LLM gateway.
references:
    - https://atlas.mitre.org/techniques/{technique_id}/
author: AEGIS AI Autonomous Blue Swarm
date: {time.strftime('%Y/%m/%d')}
tags:
    - attack.initial_access
    - mitre_atlas.{technique_id.lower().replace('.', '_')}
logsource:
    category: application
    product: aegis_ai_gateway
detection:
    selection:
        payload|re: '{pattern_str}'
    condition: selection
falsepositives:
    - Authorized red team exercises
    - Security benchmark audits
level: {severity}
"""

    @staticmethod
    def generate_yaral_rule(
        title: str,
        technique_id: str = "AML.T0051",
        pattern_str: str = "ignore previous"
    ) -> str:
        """Generates Google Chronicle YARA-L detection rule."""
        rule_name = f"aegis_ai_{title.lower().replace(' ', '_').replace('-', '_')}"
        return f"""rule {rule_name} {{
  meta:
    author = "AEGIS AI Cognitive Defense Swarm"
    description = "Detects adversarial AI prompt manipulation or tool hijacking"
    mitre_atlas = "{technique_id}"
    severity = "HIGH"

  events:
    $e.metadata.event_type = "USER_CONVERSATION"
    $e.target.application = "aegis-llm-gateway"
    re.regex($e.target.query, `{pattern_str}`)

  condition:
    $e
}}
"""

    @staticmethod
    def generate_wazuh_rule(
        rule_id: int,
        title: str,
        pattern_str: str = "ignore previous"
    ) -> str:
        """Generates Wazuh XML detection rule."""
        return f"""<group name="aegis_ai_defense,">
  <rule id="{rule_id}" level="12">
    <decoded_as>json</decoded_as>
    <field name="threat_signature">{pattern_str}</field>
    <description>AEGIS AI - {title}</description>
    <mitre>
      <id>AML.T0051</id>
    </mitre>
  </rule>
</group>
"""

rule_synthesizer = DetectionRuleSynthesizer()
