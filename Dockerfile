# NexuX V9.5 Multi-Stage Dockerfile
# Backend (FastAPI) + Frontend (React/Vite)

# Stage 1: Backend Base
FROM python:3.11-slim AS backend-base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0

WORKDIR /app

# Copy requirements first for layer caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

WORKDIR /app/backend

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["python", "main.py"]

# Stage 2: Frontend Build
FROM node:18-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Stage 3: Frontend Serve (production)
FROM node:18-slim AS frontend

WORKDIR /app/frontend
COPY --from=frontend-build /app/frontend/dist ./dist
RUN npm install -g serve@14

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1

CMD ["serve", "dist", "-l", "3000", "--spa"]
