# ── NexuX V8.0 Backend Dockerfile ──
FROM python:3.11-slim AS backend-base

# Install system dependencies (FFmpeg, OpenCV libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY nexus-clipper/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY nexus-clipper/backend/ ./backend/

WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "main.py"]

# ── Frontend Build Stage ──
FROM node:18-slim AS frontend-build

WORKDIR /app/frontend
COPY nexus-clipper/frontend/package.json nexus-clipper/frontend/package-lock.json ./
RUN npm ci
COPY nexus-clipper/frontend/ ./
RUN npm run build

# ── Frontend Serve Stage ──
FROM node:18-slim AS frontend
WORKDIR /app/frontend
COPY --from=frontend-build /app/frontend/dist ./dist
COPY nexus-clipper/frontend/package.json ./
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "dist", "-l", "3000"]
