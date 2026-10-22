"""
AEGIS AI - Enterprise Configuration Engine
Centralized, secure configuration management with environment variable priority
and local JSON fallback for development environments.
"""
import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
API_KEYS_FILE = CONFIG_DIR / "api_keys.json"

def _load_json_keys() -> dict:
    if API_KEYS_FILE.exists():
        try:
            with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

_json_keys = _load_json_keys()

class Settings(BaseSettings):
    # System Info
    PROJECT_NAME: str = "AEGIS AI - Cognitive Cyber Defense"
    VERSION: str = "5.0.0-enterprise"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # LLM & AI Target Settings
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_GENERATE_ENDPOINT: str = f"{os.getenv('OLLAMA_URL', 'http://localhost:11434')}/api/generate"
    OLLAMA_OPENAI_ENDPOINT: str = f"{os.getenv('OLLAMA_URL', 'http://localhost:11434')}/v1"
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "ollama")
    DEFAULT_TARGET_MODEL: str = os.getenv("TARGET_MODEL", "llama3.2:3b")
    DEFAULT_ANALYST_MODEL: str = os.getenv("ANALYST_MODEL", "llama3.2:3b")
    
    # Threat Intelligence Keys
    ABUSEIPDB_API_KEY: str = os.getenv("ABUSEIPDB_API_KEY", _json_keys.get("abuseipdb", ""))
    VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", _json_keys.get("virustotal", ""))
    ALIENVAULT_OTX_KEY: str = os.getenv("ALIENVAULT_OTX_KEY", _json_keys.get("alienvault_otx", ""))
    
    # Wazuh SIEM
    WAZUH_INDEXER_URL: str = os.getenv("WAZUH_INDEXER_URL", "https://localhost:9200")
    WAZUH_INDEXER_USER: str = os.getenv("WAZUH_INDEXER_USER", "admin")
    WAZUH_INDEXER_PASS: str = os.getenv("WAZUH_INDEXER_PASS", "admin")
    
    # TheHive
    THEHIVE_URL: str = os.getenv("THEHIVE_URL", "http://192.168.218.130:9000")
    THEHIVE_ADMIN_KEY: str = os.getenv("THEHIVE_ADMIN_KEY", "GgHSm7Eb4hlb5ogCjty5y3OgvaguvTnX")
    THEHIVE_ORG: str = os.getenv("THEHIVE_ORG", "soc-org")
    
    # Storage Paths
    LOG_DIR: Path = PROJECT_ROOT / "logs"
    REPORT_DIR: Path = PROJECT_ROOT / "reports"
    DATA_DIR: Path = PROJECT_ROOT / "database"

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure directories exist
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORT_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
