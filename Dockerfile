# ==============================================================================
# AEGIS AI - Autonomous Cognitive Cyber Defense Cloud
# Production Multi-Stage Container Image
# ==============================================================================
FROM python:3.13-slim as base

# Set system environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose API and Dashboard ports
EXPOSE 8000 8501

# Default healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command: Start API Orchestrator (can be overridden with docker-compose)
CMD ["uvicorn", "api.orchestrator:app", "--host", "0.0.0.0", "--port", "8000"]
