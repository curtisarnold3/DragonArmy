# GNSS-AGG Dockerfile
# Base image pinned by digest for deterministic builds
# Digest resolved: 2026-06-10
FROM python:3.11-slim-bookworm@sha256:8c9fb0c6e5cf15e9e18a85e75d3e05e45087b8b20e42a2d9f0c77a4fcdd0fde4

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
COPY pipeline/ ./pipeline/
COPY api/ ./api/
COPY tests/ ./tests/

# Default command (placeholder - services override in compose)
CMD ["python", "-c", "print('gnss-aggregator image')"]
