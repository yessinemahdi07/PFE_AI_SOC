# 🏗️ System Architecture

The AI-Native SOC Orchestrator is a modular, pipeline-based architecture that integrates AI agents, enterprise security tools, and a cloud dashboard.

```mermaid
graph TD
    %% Entities
    User([SOC Analyst / CISO])
    API[FastAPI Orchestrator]
    
    subgraph AI_Agents [AI Security Agents]
        Red[Red Team Agent<br/>Microsoft PyRIT]
        Blue[Blue Team Agent<br/>Llama 3.2 via Ollama]
        TI[Threat Intel Engine<br/>OTX / VirusTotal / AbuseIPDB]
    end
    
    subgraph Enterprise_Stack [Enterprise Security Stack]
        Wazuh[Wazuh SIEM<br/>Indexer API]
        TheHive[TheHive Case Management<br/>REST API]
    end
    
    Dashboard[Streamlit Command Center<br/>Cloud Hosted]

    %% Flow
    User -->|Triggers POST /campaign/run| API
    API -->|1. Execute Attacks| Red
    Red -->|Attack Logs| Blue
    Blue -->|Analyze & Recommend| TI
    TI -->|Enriched Data| API
    API -->|2. Ingest Telemetry| Wazuh
    API -->|3. Create Incident Tickets| TheHive
    API -->|4. Generate JSON/TXT| Dashboard
    Dashboard -->|Visualize MITRE ATLAS/NIST| User

    classDef red fill:#FF003C,stroke:#fff,stroke-width:2px,color:#fff;
    classDef blue fill:#00F0FF,stroke:#fff,stroke-width:2px,color:#000;
    classDef green fill:#00FF85,stroke:#fff,stroke-width:2px,color:#000;
    classDef gray fill:#1E2530,stroke:#fff,stroke-width:2px,color:#fff;
    
    class Red red;
    class Blue blue;
    class Wazuh,TheHive green;
    class API,Dashboard,TI gray;
    