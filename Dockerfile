# ╔══════════════════════════════════════════════════════════════════╗
# ║  AGENT DASHBOARD - Dockerfile                                  ║
# ║  Flask + Socket.IO + React                                     ║
# ╚══════════════════════════════════════════════════════════════════╝

# ─── Build Arguments ─────────────────────────────────────────────
ARG ENV_FILE=.env.docker

# ─── Stage 1: Build frontend ─────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python backend ─────────────────────────────────────
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=server.py
ENV PYTHONIOENCODING=utf-8
ENV ENV_FILE=${ENV_FILE}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browser (install deps manually to avoid missing font packages)
RUN apt-get update && apt-get install -y \
    fonts-unifont \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/* \
    && playwright install chromium

# Copy application files (exclude frontend/src, frontend/node_modules)
COPY api/ ./api/
COPY common/ ./common/
COPY extensions/ ./extensions/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY server.py .
COPY config.yml .
COPY system_prompt.md .

# Copy env file (defaults to .env.docker for Docker builds)
COPY ${ENV_FILE} .env

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/ || exit 1

# Run with eventlet (for Socket.IO)
CMD ["python", "-c", "from server import app, socketio; socketio.run(app, host='0.0.0.0', port=5050, debug=False)"]
