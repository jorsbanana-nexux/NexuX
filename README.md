# 🚀 NexuX V7.0 — Autonomous AI Video Repurposing Engine

> **Local-first, zero cloud cost, production-ready.** Transform long-form videos into viral clips that surpass Opus Clip — entirely on your own machine.

[![Version](https://img.shields.io/badge/version-7.0.0-cyan)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Python](https://img.shields.io/badge/Python-3.11+-yellow)]()
[![React](https://img.shields.io/badge/React-19-black)]()

---

## 📋 Table of Contents

1. [What is NexuX?](#-what-is-nexux)
2. [Features That Beat Opus Clip](#-features-that-beat-opus-clip)
3. [Architecture](#-architecture)
4. [Prerequisites](#-prerequisites)
5. [Quick Start (5 Minutes)](#-quick-start-5-minutes)
6. [Configuration](#-configuration)
7. [API Reference](#-api-reference)
8. [Frontend Guide](#-frontend-guide)
9. [Production Deployment](#-production-deployment)
10. [Troubleshooting](#-troubleshooting)
11. [Changelog](#-changelog)

---

## 🎯 What is NexuX?

NexuX is an **autonomous AI video repurposing engine** that takes long-form YouTube videos and automatically extracts, edits, and enhances the most viral moments into short-form clips (TikTok, Reels, Shorts).

Unlike Opus Clip and similar cloud-based tools:
- **100% Local Processing** — No API keys, no cloud costs, no per-minute charges
- **Whisper + OpenCV + FFmpeg** — Industry-grade open-source stack
- **Editorial Consciousness** — A built-in critic evaluates every clip and auto-revises weak ones
- **B-Roll Free Policy** — No stock footage overlay; the original content speaks for itself
- **SQLite Persistence** — Job history survives restarts

---

## 🏆 Features That Beat Opus Clip

| Feature | Opus Clip | NexuX V7.0 |
|---------|-----------|------------|
| Processing | Cloud (per-minute cost) | Local (zero cost) |
| Privacy | Video uploaded to cloud | Stays on your machine |
| AI Transcription | Cloud Whisper | Local faster-whisper |
| Face Tracking | Basic | OpenCV + MediaPipe |
| Editorial Critic | None | Multi-dimensional auto-revision loop |
| Audio Enhancement | Basic | Ducking + normalization + EQ chain |
| B-Roll | Stock footage overlay | B-roll-free (preserves authenticity) |
| Job Persistence | Cloud storage | SQLite (survives restarts) |
| API Auth | API key required | Optional API key (local dev = no auth) |
| Cost | $19–$39/month | **Free forever** |
| Customization | Limited | Full source code, modify anything |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     NexuX V7.0 Architecture                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     WebSocket      ┌──────────────────┐    │
│  │  React 19    │◄───── /ws ───────►│  FastAPI V7.0    │    │
│  │  Tailwind v4 │                   │  (main.py)        │    │
│  │  TypeScript  │     HTTP API      │                   │    │
│  │  Vite 6      │◄── 14 endpoints ─►│  ┌─────────────┐ │    │
│  └──────────────┘                   │  │ Pipeline.py │ │    │
│                                     │  │ (async +     │ │    │
│  Frontend (port 3000)               │  │  threaded)  │ │    │
│                                     │  └──────┬──────┘ │    │
│                                     │         │        │    │
│                                     │  ┌──────▼──────┐ │    │
│                                     │  │ Engine      │ │    │
│                                     │  │ ├ download  │ │    │
│                                     │  │ ├ vision    │ │    │
│                                     │  │ ├ transcribe│ │    │
│                                     │  │ ├ analyze   │ │    │
│                                     │  │ ├ render    │ │    │
│                                     │  │ ├ critic    │ │    │
│                                     │  │ └ audio FX │ │    │
│                                     │  └─────────────│ │    │
│                                     │                 │    │
│                                     │  ┌───────────┐  │    │
│                                     │  │ SQLite DB │  │    │
│                                     │  │ (jobs.db) │  │    │
│                                     │  └───────────┘  │    │
│                                     └──────────────────┘    │
│                                      Backend (port 8000)    │
│                                                              │
│  External Tools: yt-dlp · faster-whisper · OpenCV · FFmpeg   │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

```
1. Download (0-15%)     → yt-dlp fetches the video
2. Vision (15-25%)      → Face detection, scene changes, screen share
3. Transcription (25-55%) → faster-whisper (local, no cloud)
4. Editorial Analysis (55-70%) → Content scoring + editorial enrichment
5. Subtitle QA (68-70%) → Readability validation
6. Rendering (70-85%)   → FFmpeg with smart zoom, captions, effects
7. Critic Revision (85-95%) → Multi-dimensional critique + auto-revision
8. Final Assembly (95-100%) → Concatenate + audio enhancement
```

---

## ✅ Prerequisites

### System Requirements

- **OS:** Linux, macOS, or Windows (WSL2 recommended for Windows)
- **Python:** 3.11 or higher
- **Node.js:** 18 or higher (for frontend)
- **FFmpeg:** 6.0 or higher
- **RAM:** 8GB minimum (16GB recommended for Whisper medium/large models)
- **GPU:** Optional (CUDA for faster transcription, CPU works fine)
- **Disk:** 2GB for dependencies + space for video processing

### Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install -y ffmpeg
```

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Windows (scoop):**
```powershell
scoop install ffmpeg
```

**Verify:**
```bash
ffmpeg -version
```

### Install Python 3.11+

**Ubuntu/Debian:**
```bash
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS:**
```bash
brew install python@3.11
```

**Windows:**
Download from https://python.org/downloads/

### Install Node.js 18+

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

**macOS:**
```bash
brew install node
```

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/jorsbanana-nexux/NexuX.git
cd NexuX/nexus-clipper
```

### Step 2: Set Up the Backend

```bash
# Create Python virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example ../.env

# Start the backend
python main.py
```

The API will be available at `http://127.0.0.1:8000`

### Step 3: Set Up the Frontend (in a new terminal)

```bash
cd nexus-clipper/frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The UI will be available at `http://localhost:3000`

### Step 4: Generate Your First Clip

1. Open `http://localhost:3000` in your browser
2. Paste a YouTube URL (e.g., a podcast or interview)
3. Select your target duration (20-60 seconds)
4. Choose subtitle style and aspect ratio (9:16 for TikTok/Reels)
5. Click **Generate**
6. Watch real-time progress via WebSocket
7. Download your clips when complete

### Step 5: Verify Everything Works

```bash
# Check backend health
curl http://127.0.0.1:8000/api/health

# Expected response:
{
  "status": "healthy",
  "canonical_runtime": true,
  "canonical_engine": "local-first-v7.0.0",
  "broll": false,
  "auth_enabled": false,
  "db_connected": true
}
```

---

## ⚙ Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Backend bind address (use 127.0.0.1 for local) |
| `PORT` | `8000` | Backend port |
| `NEXUX_ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated CORS origins |
| `NEXUX_API_KEY` | (empty) | API key for auth (empty = no auth) |
| `NEXUX_DB_PATH` | `nexux_jobs.db` | SQLite database path |
| `NEXUX_JOB_TTL_HOURS` | `72` | Auto-cleanup jobs after N hours |
| `WHISPER_MODEL` | `small` | Whisper model: tiny/base/small/medium/large |
| `NEXUX_AI_ENABLED` | `0` | Optional cloud AI (disabled by default) |

### Enable API Authentication (Production)

```bash
# Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
NEXUX_API_KEY=your-generated-key-here
```

When enabled, all API endpoints (except `/` and `/api/health`) require:
```
X-API-Key: your-generated-key-here
```

---

## 📡 API Reference

### Base URL
```
http://127.0.0.1:8000
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Server info |
| GET | `/api/health` | Health check |
| GET | `/api/styles` | Available styles, ratios, codecs |
| POST | `/api/preview` | Get video info |
| POST | `/api/search` | Search YouTube |
| POST | `/api/generate` | Start clip generation |
| GET | `/api/job/{id}` | Get job status |
| GET | `/api/jobs` | List jobs (with pagination) |
| DELETE | `/api/job/{id}` | Cancel job |
| GET | `/api/vision/{id}` | Vision analysis data |
| GET | `/api/render-qa/{id}` | Render quality assurance |
| GET | `/api/critic/{id}` | Editorial critique report |
| GET | `/api/publish/{id}` | Publish plan |
| POST | `/api/publish/{id}/{platform}` | Prepare for platform |
| GET | `/api/analytics/{id}` | Job analytics |
| GET | `/api/download/{id}` | Download clips |
| WS | `/ws` | WebSocket for real-time progress |

### Example: Generate Clips

```bash
curl -X POST http://127.0.0.1:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=...",
    "target_duration": 45,
    "aspect_ratio": "9:16",
    "subtitle_style": "hormozi",
    "clip_count": 3,
    "auto_zoom": true,
    "face_tracking": true,
    "normalize_audio": true,
    "emoji_enabled": true
  }'
```

### Example: WebSocket Progress

```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'job_progress') {
    console.log(`${data.stage}: ${data.progress}%`);
  }
};
```

---

## 🎨 Frontend Guide

### Tech Stack
- React 19 + TypeScript
- Tailwind CSS v4
- Vite 6
- Framer Motion (animations)
- Lucide Icons

### Frontend Commands

```bash
cd nexus-clipper/frontend

npm install      # Install dependencies
npm run dev      # Dev server (port 3000)
npm run build    # Production build
npm run preview  # Preview production build
npx tsc --noEmit # Type check (zero errors expected)
```

### Frontend Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── nexuxApi.ts       # API client + types
│   ├── components/
│   │   ├── SpaceshipConsole.tsx    # Main UI
│   │   ├── ProcessingLoadingState.tsx
│   │   ├── ResultsMosaicGrid.tsx
│   │   ├── ShowcaseSection.tsx
│   │   └── ErrorBoundary.tsx
│   ├── utils/
│   │   └── soundEffects.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 🚀 Production Deployment

### Option 1: Local Server (Recommended for NexuX)

Since NexuX is local-first, "production" means running on your own machine:

```bash
# 1. Set production environment
echo 'NEXUX_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")' >> .env

# 2. Build frontend for production
cd nexus-clipper/frontend
npm run build
# Output: dist/ directory

# 3. Serve frontend via the backend (optional)
# Or use a static file server:
npx serve dist -p 3000

# 4. Start backend in production mode
cd ../backend
source venv/bin/activate
python main.py
```

### Option 2: Systemd Service (Linux)

```ini
# /etc/systemd/system/nexux.service
[Unit]
Description=NexuX Video Clipper API
After=network.target

[Service]
Type=simple
User=nexux
WorkingDirectory=/opt/nexux/nexus-clipper/backend
EnvironmentFile=/opt/nexux/.env
ExecStart=/opt/nexux/nexus-clipper/backend/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nexux
sudo systemctl start nexux
```

### Option 3: Docker

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "nexus-clipper/backend/main.py"]
```

```bash
docker build -t nexux .
docker run -p 8000:8000 nexux
```

---

## 🔧 Troubleshooting

### FFmpeg Not Found
```bash
# Verify installation
ffmpeg -version
# If missing, install: sudo apt install ffmpeg (Linux) / brew install ffmpeg (macOS)
```

### Whisper Model Download Slow
The first run downloads the Whisper model (~500MB for `small`). It's cached in `~/.cache/`. Use `WHISPER_MODEL=tiny` for faster startup (lower accuracy).

### Port Already in Use
```bash
# Change port in .env
PORT=8080
```

### GPU Not Detected
NexuX works on CPU. For GPU acceleration, install CUDA toolkit and PyTorch with CUDA support.

### CORS Errors
Make sure `NEXUX_ALLOWED_ORIGINS` in `.env` matches your frontend URL.

---

## 📝 Changelog

### V7.0.0 (2026-08-16)
- **SQLite persistent job storage** — Jobs survive server restarts
- **API key authentication** — Optional, env-based
- **Job history with pagination** — `/api/jobs?limit=50&offset=0`
- **Automatic TTL cleanup** — Old jobs auto-deleted after 72 hours
- **Interrupted job recovery** — In-progress jobs marked as "interrupted" on restart
- **V6.4 endpoints** — All 14 API endpoints matching frontend contract
- **Threaded pipeline** — All blocking operations via `asyncio.to_thread()`
- **Cleaned dependencies** — 120+ → ~20 direct packages, no cloud AI SDKs
- **Security hardening** — CORS locked, host bound to 127.0.0.1

### V6.4.0 (2026-08-16)
- Initial backend-frontend parity fix
- 7 missing API endpoints added
- Pipeline async/threaded execution

### V4.0.0 (Original)
- Initial release with V4 backend

---

## 📄 License

MIT — Free to use, modify, and distribute.

## 🤝 Contributing

This is a personal project. Feel free to fork and modify for your own use.

---

> **NexuX** — *Built to surpass Opus Clip. Local-first, zero cost, production-ready.*
