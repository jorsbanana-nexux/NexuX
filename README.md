# 🚀 NexuX V9.5 — Autonomous AI Video Repurposing Engine

> **Local-first, zero cloud cost, production-ready.** Transform long-form videos into viral clips that surpass Opus Clip — entirely on your own machine.
>
> **V9.5:** Dual-mode system — Podcast Mode (clip podcasts/interviews) + AI Creative Mode (keyword → multi-source compilation). Opus Killer scoring (8 dimensions), auto viral titles, keyword expansion.

[![Version](https://img.shields.io/badge/version-9.5.0-cyan)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Python](https://img.shields.io/badge/Python-3.11+-yellow)]()
[![React](https://img.shields.io/badge/React-19-black)]()

---

## 📋 Table of Contents

1. [What is NexuX?](#-what-is-nexux)
2. [Dual-Mode System](#-dual-mode-system)
3. [Features That Beat Opus Clip](#-features-that-beat-opus-clip)
4. [Architecture](#-architecture)
5. [Prerequisites & Materials](#-prerequisites--materials)
6. [Step-by-Step Installation](#-step-by-step-installation)
7. [Configuration](#-configuration)
8. [API Reference (V8 + V9.5)](#-api-reference-v8--v95)
9. [Frontend Guide](#-frontend-guide)
10. [Production Deployment](#-production-deployment)
11. [Troubleshooting](#-troubleshooting)
12. [Changelog](#-changelog)

---

## 🎯 What is NexuX?

NexuX is an **autonomous AI video repurposing engine** with **two modes**:

- **Mode 1 — Podcast:** Takes long-form YouTube videos (podcasts, interviews, talk shows) and automatically extracts, edits, and enhances the most viral moments into short-form clips (TikTok, Reels, Shorts).
- **Mode 2 — AI Creative:** Takes a single keyword, searches YouTube for 10+ related videos, finds the best moments, generates AI narration, and compiles everything into one viral video.

Unlike Opus Clip and similar cloud-based tools:
- **100% Local Processing** — No API keys, no cloud costs, no per-minute charges
- **Whisper + OpenCV + FFmpeg** — Industry-grade open-source stack
- **Opus Killer Scoring** — 8-dimension transparent scoring with "beats Opus by X points"
- **Editorial Consciousness** — A built-in critic evaluates every clip and auto-revises weak ones
- **B-Roll Free Policy** — No stock footage overlay; the original content speaks for itself
- **SQLite Persistence** — Job history survives restarts
- **Auto Viral Titles** — 8 archetype templates, 5 variations per clip, bilingual EN+ID
- **Keyword Expansion** — 1 keyword → 15+ search terms for Mode 2

---

## 🔀 Dual-Mode System

### Mode 1 — Podcast Mode (🎙️)

**Input:** YouTube URL (podcast, interview, talk show, long-form video)
**Output:** Multiple viral clips (20-90 seconds each)

**Flow:**
```
YouTube URL → Auto-captions/Whisper → Podcast Analysis → Opus Killer Scoring →
Hook Detection → Smart Zoom + Captions → Render → Critic Revision → Auto Titles
```

**Podcast-specific intelligence (NEW in V9.5):**
- **Topic segmentation** — Detects topic changes in the conversation
- **Punchline extraction** — Finds the "money quote" in each topic segment
- **Heat detection** — Identifies moments of conflict, excitement, or disagreement
- **Story arc detection** — Finds narrative anecdotes worth clipping
- **Q&A pairing** — Identifies engaging question-answer exchanges
- **Filler word detection** — Marks "um", "uh", "eh" for potential removal
- **Speaker turn-taking** — Scores conversation flow quality

### Mode 2 — AI Creative Mode (✨)

**Input:** One keyword (e.g., "peter parker", "game terbaik 2026", "motivasi")
**Output:** One compiled viral video with AI narration, SFX, and text overlays

**Flow:**
```
Keyword → Expand to 15+ terms → Search YouTube (10+ videos) → Analyze transcripts →
Find relevant moments → LLM generates narrative → Download only relevant moments →
Compile with TTS + SFX + transitions → Auto titles + hashtags → Opus Killer score
```

**Creative-specific intelligence (NEW in V9.5):**
- **Keyword expansion** — 1 keyword → 15+ search terms (synonyms, trending suffixes, question formats, niche modifiers, bilingual EN+ID)
- **Multi-source search** — Searches using expanded terms, deduplicates channels for diversity
- **LLM narrative** — AI writes hook → buildup → payoff script (Indonesian or English)
- **TTS narration** — Edge-TTS voice-over (Indonesian: Ardi, Gadis; English: Guy, Girl)
- **SFX + BGM** — Auto sound effects and background music
- **Auto metadata** — Viral titles, hashtags, SEO description auto-generated

---

## 🏆 Features That Beat Opus Clip

| Feature | Opus Clip | NexuX V9.5 |
|---------|-----------|------------|
| **Cost** | $19–$39/month | **Free forever** |
| **Privacy** | Video uploaded to cloud | Stays on your machine |
| **Processing** | Cloud (per-minute cost) | Local (zero cost) |
| **Hook Detection** | ~3 patterns | **8 archetype patterns** |
| **Virality Scoring** | Black box, 1 number | **8 dimensions, fully transparent** |
| **Conversation Flow** | ❌ | ✅ Speaker turn-taking analysis |
| **Retention Curve** | ❌ | ✅ Dropoff point prediction |
| **Shareability** | ❌ | ✅ Quotability + meme potential |
| **Competitor Delta** | ❌ | ✅ "Beats Opus by X points" |
| **Podcast Mode** | Generic clipper | ✅ Topic segmentation + punchlines + heat |
| **Creative Mode** | ❌ No keyword mode | ✅ Multi-source AI compilation |
| **Auto Titles** | Basic | ✅ 8 archetypes, 5 variations, bilingual |
| **Keyword Expansion** | ❌ | ✅ 15+ terms (synonyms, trending, Q&A) |
| **AI Transcription** | Cloud Whisper | Local faster-whisper |
| **Face Tracking** | Basic | OpenCV + MediaPipe |
| **Editorial Critic** | None | Multi-dimensional auto-revision loop |
| **Audio Enhancement** | Basic | Ducking + normalization + EQ chain |
| **B-Roll** | Stock footage overlay | B-roll-free (preserves authenticity) |
| **Job Persistence** | Cloud storage | SQLite (survives restarts) |
| **API Auth** | API key required | Optional API key (local dev = no auth) |
| **Customization** | Limited | Full source code, modify anything |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     NexuX V9.5 Architecture                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐     WebSocket      ┌──────────────────────┐     │
│  │  React 19    │◄───── /ws ───────►│  FastAPI V9.5         │     │
│  │  Tailwind v4 │                   │  (main.py)            │     │
│  │  TypeScript  │     HTTP API      │                       │     │
│  │  Vite 6      │◄── 20 endpoints ─►│  ┌─────────────────┐  │     │
│  │              │                   │  │ Mode Router      │  │     │
│  │  ModeSelect  │                   │  │  ├ Podcast Mode  │  │     │
│  │  Spaceship   │                   │  │  └ Creative Mode │  │     │
│  │  Mode2Consle │                   │  └────────┬─────────┘  │     │
│  └──────────────┘                   │           │            │     │
│                                     │  ┌────────▼─────────┐  │     │
│  Frontend (port 3000)               │  │ Engine          │  │     │
│                                     │  │ ├ download     │  │     │
│                                     │  │ ├ vision       │  │     │
│                                     │  │ ├ transcribe   │  │     │
│                                     │  │ ├ analyze       │  │     │
│                                     │  │ ├ podcast_anlz  │ NEW   │
│                                     │  │ ├ opus_killer   │ NEW   │
│                                     │  │ ├ clip_titler   │ NEW   │
│                                     │  │ ├ keyword_expand│ NEW   │
│                                     │  │ ├ render        │  │     │
│                                     │  │ ├ critic        │  │     │
│                                     │  │ └ audio FX     │  │     │
│                                     │  └─────────────────┘  │     │
│                                     │                       │     │
│                                     │  ┌───────────┐        │     │
│                                     │  │ SQLite DB │        │     │
│                                     │  │ (jobs.db) │        │     │
│                                     │  └───────────┘        │     │
│                                     └──────────────────────┘      │
│                                      Backend (port 8000)           │
│                                                                   │
│  External: yt-dlp · faster-whisper · OpenCV · MediaPipe · FFmpeg │
│             edge-tts · (optional) OpenAI/Anthropic/Gemini API     │
└──────────────────────────────────────────────────────────────────┘
```

### Mode 1 — Podcast Pipeline

```
1. Smart Metadata (0-5%)     → yt-dlp fetches video info (no download)
2. Caption Fetch (5-10%)     → YouTube auto-captions OR faster-whisper
3. Podcast Analysis (10-20%) → Topic segmentation, punchlines, heat, stories
4. Opus Killer Score (20%)   → 8-dimension scoring + hook detection
5. Partial Download (20-40%) → Download ONLY selected sections
6. Parallel Render (40-85%)  → All clips rendered simultaneously
7. Critic Revision (85-95%) → Multi-dimensional critique + auto-revision
8. Auto Titles (95-97%)      → Generate 5 viral titles + hashtags per clip
9. Final Assembly (97-100%)  → Concatenate + audio enhancement
```

### Mode 2 — Creative Pipeline

```
1. Keyword Expansion (3%)   → 1 keyword → 15+ search terms
2. Multi-Source Search (8%) → Search YouTube with expanded terms
3. Transcript Analysis (18%) → Find relevant moments in 10+ videos
4. LLM Narrative (32%)      → AI writes hook → buildup → payoff script
5. Partial Download (45%)   → Download only relevant moment clips
6. Compile Video (65%)      → TTS + SFX + transitions + text overlays
7. Auto Metadata (85%)      → Viral titles + hashtags + SEO description
8. Opus Killer Score (90%)  → Score the final compilation
9. Final Output (100%)      → Video + thumbnail + metadata
```

---

## ✅ Prerequisites & Materials

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Linux, macOS, Windows (WSL2) | Linux/macOS |
| **Python** | 3.11+ | 3.12 |
| **Node.js** | 18+ | 20+ |
| **FFmpeg** | 6.0+ | 7.0+ |
| **RAM** | 8GB | 16GB (for Whisper medium/large) |
| **GPU** | Optional | CUDA (faster transcription) |
| **Disk** | 2GB deps + processing space | 10GB+ |

### Bahan-Bahan (Dependencies)

#### System Tools

| Tool | Purpose | Install |
|------|---------|---------|
| **FFmpeg 6.0+** | Video processing, rendering, encoding | `sudo apt install ffmpeg` / `brew install ffmpeg` |
| **Python 3.11+** | Backend runtime | `sudo apt install python3.11` / `brew install python@3.11` |
| **Node.js 18+** | Frontend dev server | `curl -fsSL https://deb.nodesource.com/setup_18.x \| sudo -E bash -` |
| **Git** | Clone repository | `sudo apt install git` |

#### Python Packages (otomatis via `pip install -r requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.115 | API framework |
| `uvicorn` | ≥0.32 | ASGI server |
| `pydantic` | ≥2.10 | Data validation |
| `yt-dlp` | ≥2026.1 | YouTube download + search |
| `faster-whisper` | ≥1.1 | Local transcription (fallback) |
| `opencv-python-headless` | ≥4.10 | Face detection, scene analysis |
| `mediapipe` | ≥1.0 | Face tracking |
| `numpy` | ≥1.26 | Numerical operations |
| `torch` | ≥2.2 | ML backend (for whisper) |
| `edge-tts` | ≥6.1 | TTS voice-over (Mode 2) |
| `psutil` | ≥5.9 | System monitoring |
| `httpx` | ≥0.28 | HTTP client |

#### Node.js Packages (otomatis via `npm install`)

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^19.0 | UI framework |
| `vite` | ^6.2 | Build tool |
| `tailwindcss` | ^4.1 | Styling |
| `motion` | ^12.23 | Animations |
| `lucide-react` | ^0.546 | Icons |
| `gsap` | ^3.15 | Scroll animations |
| `lenis` | ^1.3 | Smooth scrolling |

#### Optional (untuk Mode 2 LLM Narrative)

Mode 2 bisa pakai LLM API buat generate narasi yang lebih bagus. Tanpa LLM, pakai fallback narrative. Set salah satu:

| Provider | Env Var | Model Default |
|----------|---------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| Gemini | `GEMINI_API_KEY` | `gemini-1.5-flash` |

---

## 📝 Step-by-Step Installation

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install FFmpeg 6.0+
sudo apt install -y ffmpeg

# Install Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Git (if not already)
sudo apt install -y git

# Verify installations
ffmpeg -version
python3.11 --version
node --version
git --version
```

**macOS (Homebrew):**
```bash
# Install Homebrew (if not already)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install all dependencies
brew install ffmpeg python@3.11 node git

# Verify
ffmpeg -version
python3.11 --version
node --version
```

**Windows (WSL2 recommended):**
```powershell
# Install WSL2
wsl --install

# Inside WSL2 (Ubuntu), follow the Ubuntu steps above

# Alternatively, install natively:
# - FFmpeg: scoop install ffmpeg
# - Python: Download from https://python.org/downloads/
# - Node.js: Download from https://nodejs.org/
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/jorsbanana-nexux/NexuX.git
cd NexuX/nexus-clipper
```

### Step 3: Set Up the Backend

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate
# Windows (WSL2): source venv/bin/activate
# Windows (native): venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment configuration
cp ../.env.example ../.env

# (Optional) Edit .env for Mode 2 LLM support
# nano ../.env
# Add: OPENAI_API_KEY=sk-... or ANTHROPIC_API_KEY=sk-... or GEMINI_API_KEY=...

# Start the backend
python main.py
```

✅ Backend berjalan di `http://127.0.0.1:8000`

### Step 4: Set Up the Frontend (in a new terminal)

```bash
# Navigate to frontend directory
cd NexuX/nexus-clipper/frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

✅ Frontend berjalan di `http://localhost:3000`

### Step 5: Verify Everything Works

```bash
# Check backend health
curl http://127.0.0.1:8000/api/health

# Expected response:
{
  "status": "healthy",
  "canonical_runtime": true,
  "canonical_engine": "local-first-v9.5.0",
  "broll": false,
  "auth_enabled": false,
  "db_connected": true
}

# Check V9.5 modes
curl http://127.0.0.1:8000/api/v2/modes

# Expected response:
[
  {
    "mode": "podcast",
    "name": "Podcast Mode",
    "icon": "🎙️",
    "requires_url": true,
    "features": [...]
  },
  {
    "mode": "creative",
    "name": "AI Creative Mode",
    "icon": "✨",
    "requires_keyword": true,
    "features": [...]
  }
]
```

### Step 6: Generate Your First Clip (Mode 1 — Podcast)

**Via UI:**
1. Open `http://localhost:3000` in your browser
2. Select **Podcast Mode** (🎙️)
3. Paste a YouTube URL (podcast, interview, or talk show)
4. Set target duration (20-90 seconds)
5. Choose subtitle style and aspect ratio (9:16 for TikTok/Reels)
6. Click **Generate**
7. Watch real-time progress via WebSocket
8. Download your clips — each with 5 auto-generated viral titles!

**Via API:**
```bash
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "podcast",
    "youtube_url": "https://www.youtube.com/watch?v=YOUR_VIDEO_ID",
    "target_duration": 45,
    "clip_count": 5
  }'
```

### Step 7: Generate Your First Creative Video (Mode 2 — AI Creative)

**Via UI:**
1. Open `http://localhost:3000`
2. Select **AI Creative Mode** (✨)
3. Type a keyword (e.g., "peter parker", "motivasi belajar", "game terbaik")
4. Toggle voice-over, SFX, BGM as desired
5. Select voice (Indonesian: Ardi, Gadis; English: Guy, Girl)
6. Click **Generate**
7. AI will search YouTube, find moments, generate narration, and compile

**Via API:**
```bash
# Preview keyword expansion first
curl "http://127.0.0.1:8000/api/v2/keyword/expand?keyword=motivasi+belajar"

# Generate
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "creative",
    "keyword": "motivasi belajar",
    "voice_enabled": true,
    "voice_name": "id-ID-ArdiNeural",
    "target_duration": 60,
    "max_sources": 10
  }'
```

---

## ⚙ Configuration

All configuration via environment variables. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Backend bind address |
| `PORT` | `8000` | Backend port |
| `NEXUX_ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated CORS origins |
| `NEXUX_API_KEY` | (empty) | API key for auth (empty = no auth) |
| `NEXUX_DB_PATH` | `nexux_jobs.db` | SQLite database path |
| `NEXUX_JOB_TTL_HOURS` | `72` | Auto-cleanup jobs after N hours |
| `WHISPER_MODEL` | `small` | Whisper model: tiny/base/small/medium/large |
| `NEXUX_AI_ENABLED` | `0` | Optional cloud AI (disabled by default) |

### Mode 2 — LLM Configuration (Optional)

Mode 2 dapat generate narasi lebih bagus dengan LLM API. Set salah satu:

```bash
# Option A: OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Option B: Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Option C: Gemini (free tier available)
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-1.5-flash
```

> Tanpa LLM API key, Mode 2 menggunakan **fallback narrative** (template-based, masih berfungsi tapi narasi lebih sederhana).

### Enable API Authentication (Production)

```bash
# Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
NEXUX_API_KEY=your-generated-key-here
```

---

## 📡 API Reference (V8 + V9.5)

### Base URL
```
http://127.0.0.1:8000
```

### V9.5 New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/modes` | List all modes + features |
| POST | `/api/v2/generate` | Start generation (auto-detect mode) |
| GET | `/api/v2/keyword/expand` | Preview keyword expansion |
| GET | `/api/v2/modes/{mode}/features` | Get mode details |

### V8.0 Existing Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Server info |
| GET | `/api/health` | Health check |
| GET | `/api/styles` | Available styles, ratios, codecs |
| POST | `/api/preview` | Get video info |
| POST | `/api/search` | Search YouTube |
| POST | `/api/generate` | Start clip generation (Mode 1 legacy) |
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
| POST | `/api/rerender/{job_id}/{clip_index}` | Re-render clip |
| POST | `/api/rerender/{job_id}/all` | Batch re-render all clips |

### V9.5 API Examples

**List modes:**
```bash
curl http://127.0.0.1:8000/api/v2/modes
```

**Mode 1 — Podcast:**
```bash
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "podcast",
    "youtube_url": "https://youtube.com/watch?v=...",
    "target_duration": 45,
    "clip_count": 5
  }'
```

**Mode 2 — Creative:**
```bash
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "creative",
    "keyword": "peter parker",
    "voice_enabled": true,
    "voice_name": "id-ID-ArdiNeural",
    "target_duration": 60,
    "max_sources": 10
  }'
```

**Keyword Expansion Preview:**
```bash
curl "http://127.0.0.1:8000/api/v2/keyword/expand?keyword=game+terbaik&max_terms=15"
```

---

## 🎨 Frontend Guide

### Components

| Component | Purpose |
|-----------|---------|
| `ModeSelector.tsx` | Dual-mode selection UI (NEW V9.5) |
| `SpaceshipConsole.tsx` | Mode 1 — Podcast input + progress |
| `Mode2Console.tsx` | Mode 2 — Creative keyword input + settings |
| `TimelineEditorStudio.tsx` | Timeline editor with drag-and-drop overlays |
| `SubtitleEngineStudio.tsx` | Subtitle style preview |
| `ClipEditorStudio.tsx` | Clip personalization + re-render |
| `ShowcaseSection.tsx` | Architecture telemetry display |

### Frontend API Clients

| File | Purpose |
|------|---------|
| `nexuxApi.ts` | V8.0 API client (existing endpoints) |
| `v2Api.ts` | V9.5 API client (mode-aware endpoints) |

---

## 🚀 Production Deployment

### Docker

```bash
# Build and run with Docker
cd nexus-clipper
docker build -t nexux-v95 .
docker run -p 8000:8000 nexux-v95
```

### Enable API Auth

```bash
# Generate secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env or environment
NEXUX_API_KEY=your-secure-key
```

### Run with Gunicorn (Production)

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## 🔧 Troubleshooting

### Common Issues

**FFmpeg not found:**
```bash
sudo apt install ffmpeg
# Verify: ffmpeg -version
```

**Whisper model download fails:**
```bash
# Use smaller model
WHISPER_MODEL=tiny python main.py
```

**yt-dlp too old:**
```bash
pip install --upgrade yt-dlp
```

**Port already in use:**
```bash
# Change port in .env
PORT=8001 python main.py
```

**Mode 2 LLM narrative fallback:**
If no LLM API key is set, Mode 2 uses a template-based fallback narrative. For better quality, set one of:
```bash
OPENAI_API_KEY=sk-...
# or
GEMINI_API_KEY=...
```

### V9.5 Integration to main.py

To activate V9.5 endpoints in `main.py`, add:

```python
from api_v95_modes import router as v2_router
app.include_router(v2_router)
```

---

## 📦 Changelog

### V9.5 (August 2026) — Opus Clip Killer Upgrade

**NEW:**
- `opus_killer.py` — 8-dimension unified scoring (hook, virality, editorial, conversation flow, retention curve, shareability, technical, competitor delta)
- `podcast_analyzer.py` — Podcast-specific: topic segmentation, punchline extraction, heat detection, story arc, Q&A pairing, filler word detection
- `clip_titler.py` — Auto-generate 5 viral titles per clip (8 archetype templates, bilingual EN+ID) + hashtags + SEO description
- `keyword_expander.py` — Expand 1 keyword → 15+ search terms (synonyms, trending suffixes, question formats, niche modifiers)
- `mode_router.py` — Clean mode selection and validation
- `mode2_enhanced.py` — Enhanced Mode 2 with keyword expansion + auto-titling + Opus Killer scoring
- `api_v95_modes.py` — 4 new API endpoints (`/api/v2/*`)
- `ModeSelector.tsx` — Dual-mode selection UI component
- `v2Api.ts` — V2 API client (frontend)

**Updated:**
- `engine/__init__.py` — Export all V9.5 modules
- `README.md` — Full rewrite with dual-mode docs, step-by-step, and material list

### V9.0 (Previous)
- Timeline editor with drag-and-drop overlays
- Undo/redo + keyboard shortcuts
- Real-time FFmpeg preview
- Self-repair system

### V8.0 (Previous)
- Mode 2 — AI Creative Compilation Engine
- Smart pipeline with auto-captions + partial download
- 4-pass render engine with kinetic subtitles
- Self-healer with 32 error types
