# GNSS-AGG Dockerfile
# Base image pinned by digest for deterministic builds
# Digest resolved: 2026-06-10
FROM python:3.11-slim-bookworm@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438

# Install ffmpeg at system level
# Version will be captured in build logs via RUN ffmpeg -version below
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Capture ffmpeg version in build log (A1)
RUN ffmpeg -version

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
# cache-bust: 2026-06-11
COPY pipeline/ ./pipeline/
COPY api/ ./api/
COPY tests/ ./tests/

# Default command (placeholder - services override in compose)
CMD ["python", "-c", "print('gnss-aggregator image')"]
