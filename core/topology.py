"""
AEGIS AI - Enterprise AI Attack Surface & Blast Radius Topology Engine
Computes interactive dependency graphs, trust boundaries, blast radius vectors,
and exploit propagation paths across enterprise LLMs, agents, tools, and databases.
"""
from typing import List, Dict, Any
from pydantic import BaseModel

class TopologyNode(BaseModel):
    id: str
    label: str
    category: str  # INGRESS, MODEL, TOOL, DATABASE, SOC
    risk_level: str  # SAFE, ELEVATED, CRITICAL
    status: str  # MONITORED, CONTAINED, VULNERABLE

class TopologyEdge(BaseModel):
    source: str
    target: str
    protocol: str
    is_compromised: bool = False
    blast_radius_weight: float = 1.0

class AttackSurfaceTopology(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    total_assets: int
    critical_blast_paths: int
    overall_posture_score: float

class TopologyEngine:
    """
    Constructs the enterprise AI attack surface graph and calculates blast radius.
    """

    def generate_topology(self) -> AttackSurfaceTopology:
        nodes = [
            # Ingress
            TopologyNode(id="USR_EXT", label="External User / Client", category="INGRESS", risk_level="ELEVATED", status="MONITORED"),
            TopologyNode(id="GW_AEGIS", label="AEGIS Inline Guardrail Proxy", category="INGRESS", risk_level="SAFE", status="CONTAINED"),
            
            # AI Agents & Workloads
            TopologyNode(id="LLM_COPILOT", label="Customer Copilot (Llama 3.2)", category="MODEL", risk_level="ELEVATED", status="MONITORED"),
            TopologyNode(id="LLM_SQL_AGENT", label="Autonomous SQL Agent (Agentic)", category="MODEL", risk_level="CRITICAL", status="VULNERABLE"),
            TopologyNode(id="LLM_FINANCE", label="Financial Triage Agent", category="MODEL", risk_level="SAFE", status="CONTAINED"),

            # Agentic Tools
            TopologyNode(id="TOOL_BASH", label="Shell Execution Tool", category="TOOL", risk_level="CRITICAL", status="VULNERABLE"),
            TopologyNode(id="TOOL_SQL", label="Postgres Connector Tool", category="TOOL", risk_level="CRITICAL", status="VULNERABLE"),
            TopologyNode(id="TOOL_EMAIL", label="SendGrid Mail Dispatcher", category="TOOL", risk_level="ELEVATED", status="MONITORED"),

            # Databases & Infrastructure
            TopologyNode(id="DB_PROD_SQL", label="Enterprise Production Postgres", category="DATABASE", risk_level="CRITICAL", status="MONITORED"),
            TopologyNode(id="DB_VEC_RAG", label="Milvus / Chroma Vector DB", category="DATABASE", risk_level="ELEVATED", status="MONITORED"),

            # Enterprise SOC Stack
            TopologyNode(id="SOC_WAZUH", label="Wazuh SIEM Indexer (OpenSearch)", category="SOC", risk_level="SAFE", status="CONTAINED"),
            TopologyNode(id="SOC_THEHIVE", label="TheHive 5.2 Case Management", category="SOC", risk_level="SAFE", status="CONTAINED"),
        ]

        edges = [
            TopologyEdge(source="USR_EXT", target="GW_AEGIS", protocol="HTTPS/REST", blast_radius_weight=1.0),
            TopologyEdge(source="GW_AEGIS", target="LLM_COPILOT", protocol="mTLS", blast_radius_weight=1.2),
            TopologyEdge(source="GW_AEGIS", target="LLM_SQL_AGENT", protocol="mTLS", blast_radius_weight=2.5),
            TopologyEdge(source="GW_AEGIS", target="LLM_FINANCE", protocol="mTLS", blast_radius_weight=1.8),

            # Model to Tools
            TopologyEdge(source="LLM_SQL_AGENT", target="TOOL_SQL", protocol="FunctionCall", is_compromised=True, blast_radius_weight=4.0),
            TopologyEdge(source="LLM_SQL_AGENT", target="TOOL_BASH", protocol="FunctionCall", is_compromised=True, blast_radius_weight=5.0),
            TopologyEdge(source="LLM_COPILOT", target="TOOL_EMAIL", protocol="FunctionCall", blast_radius_weight=2.0),

            # Tools to Data
            TopologyEdge(source="TOOL_SQL", target="DB_PROD_SQL", protocol="SQL", is_compromised=True, blast_radius_weight=5.0),
            TopologyEdge(source="LLM_COPILOT", target="DB_VEC_RAG", protocol="gRPC", blast_radius_weight=2.2),

            # Telemetry to SOC
            TopologyEdge(source="GW_AEGIS", target="SOC_WAZUH", protocol="IndexerAPI", blast_radius_weight=0.5),
            TopologyEdge(source="GW_AEGIS", target="SOC_THEHIVE", protocol="REST/JWT", blast_radius_weight=0.5),
        ]

        critical_paths = sum(1 for e in edges if e.is_compromised or e.blast_radius_weight >= 4.0)

        return AttackSurfaceTopology(
            nodes=nodes,
            edges=edges,
            total_assets=len(nodes),
            critical_blast_paths=critical_paths,
            overall_posture_score=87.5
        )

topology_engine = TopologyEngine()
