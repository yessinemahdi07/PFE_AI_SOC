# 🚀 Setup & Installation Guide

This guide explains how to deploy the AI-Native SOC Orchestrator locally.

## 📋 Prerequisites
- **Python 3.13+**
- **Ollama** (for local LLM inference)
- **Docker** (for TheHive and Cortex)
- **Wazuh** (OVA or installed via Docker)

## 🛠️ 1. Environment Setup

Clone the repository:
```bash
git clone https://github.com/yessinemahdi07/PFE_AI_SOC.git
cd PFE_AI_SOC
pip install -r requirements.txt
ollama pull llama3.2:3b