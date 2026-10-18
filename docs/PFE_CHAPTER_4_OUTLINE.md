\# Chapter 4: Realization and Experimentation



\## 4.1 Introduction

Brief overview of the implementation phase. The AI-Native SOC Orchestrator was built using Python, Ollama (Llama 3.2 3B), and Wazuh 4.14.8. The architecture follows a modular design: Red Agent → Blue Agent → Risk Engine → SIEM Connector.



\## 4.2 Environment Setup

\- \*\*Host Machine:\*\* AMD Ryzen 5 5600H, 24GB RAM, RTX 3050 Ti

\- \*\*Virtualization:\*\* VMware Workstation Pro 17.6.4

\- \*\*SIEM:\*\* Wazuh 4.14.8 (Amazon Linux 2023)

\- \*\*LLM Runtime:\*\* Ollama (Llama 3.2 3B)

\- \*\*Programming Language:\*\* Python 3.13



\## 4.3 Component Implementation



\### 4.3.1 Red Agent (Attack Generation)

\- \*\*File:\*\* `red\_agent/red\_agent.py`

\- \*\*Function:\*\* Generates 8 adversarial prompts against a local LLM.

\- \*\*MITRE ATLAS Coverage:\*\* AML.T0050, AML.T0051, AML.T0054, AML.T0057.

\- \*\*Output:\*\* JSON log with payload, response, ground-truth label.



\### 4.3.2 Blue Agent (Detection)

\- \*\*File:\*\* `blue\_agent/blue\_agent.py`

\- \*\*Function:\*\* Reads Red Agent logs, detects injection/refusal patterns, assigns risk scores.

\- \*\*Evaluation:\*\* 100% detection accuracy (8/8 attacks).



\### 4.3.3 Risk Engine (Threat Intel)

\- \*\*File:\*\* `risk\_engine/risk\_engine.py`

\- \*\*Function:\*\* Extracts IOCs, classifies type (IP, hash, URL, domain), queries AlienVault OTX / AbuseIPDB / VirusTotal.

\- \*\*Output:\*\* Composite score (0-100).



\### 4.3.4 SIEM Integration (Wazuh)

\- \*\*File:\*\* `siem\_connector/wazuh\_indexer\_connector.py`

\- \*\*Function:\*\* Pushes alerts directly to the Wazuh Indexer (port 9200).

\- \*\*Verification:\*\* 8/8 alerts successfully ingested and visible in Wazuh Discover.



\### 4.3.5 Automated Reporting

\- \*\*File:\*\* `reporting/reporting\_engine.py`

\- \*\*Function:\*\* Generates professional PDF after every campaign.



\### 4.3.6 Dashboard

\- \*\*File:\*\* `dashboard/dashboard.py`

\- \*\*Function:\*\* Real-time visualization (attacks, SIEM status, Threat Intel).



\## 4.4 Wazuh Deployment (VMware)

\- OVA import, AMD CPU compatibility fix, AZERTY keyboard config.

\- Indexer cluster: green, 26 shards active.

\- Dashboard access via SSH tunnel.



\## 4.5 Campaign Execution (End-to-End)

\- \*\*Step 1:\*\* Red Agent executes 8 attacks.

\- \*\*Step 2:\*\* Blue Agent detects, assigns scores.

\- \*\*Step 3:\*\* Risk Engine enriches IOCs.

\- \*\*Step 4:\*\* SIEM Connector pushes to Wazuh.

\- \*\*Step 5:\*\* Dashboard and PDF report generated.

\- \*\*Total runtime:\*\* \~37 seconds.



\## 4.6 Results and Discussion

\- \*\*Detection Accuracy:\*\* 100% (8/8).

\- \*\*SIEM Ingestion:\*\* 100% (8/8).

\- \*\*MITRE ATLAS Coverage:\*\* 4 distinct techniques.

\- \*\*Pipeline Runtime:\*\* 37 seconds.

\- \*\*Limitations:\*\* Wazuh API connector required custom decoders (future work); VMware NAT port forwarding bug required SSH tunnel workaround.



\## 4.7 Conclusion

The AI-Native SOC Orchestrator was successfully implemented and tested. All components are operational, and the integration between AI agents and the Wazuh SIEM was verified.

