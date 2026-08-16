# NexuX — Autonomous AI Video Repurposing Engine

> **V7.0** — Local-first, zero cloud cost, no B-roll, SQLite persistent.

NexuX transforms long-form videos into high-virality vertical clips (9:16)
with auto-reframing, kinetic subtitles, and multimodal editorial intelligence.

## Architecture

```
NexuX/
├── backend/              # V7.0 Python pipeline (FastAPI + SQLite)
│   ├── main.py           # FastAPI entry — 14 endpoints, API key auth
│   ├── engine/           # 14 engine modules (vision, render, editorial)
│   ├── agents/           # 25 AI agents + capability matrix
│   ├── engine_bridge.py  # Legacy V5 → V7.0 vision bridge
│   └── utils/            # Config, logger, constants
├── frontend/             # TypeScript/React 19/Tailwind v4
│   ├── src/api/          # nexuxApi.ts — full API client with polling
│   ├── src/components/   # 20+ components (lazy-loaded, code-split)
│   └── src/utils/        # Sound effects, subtitle store, scroll blur
├── local-first-v5/       # Legacy vision quality module (bridge deps)
├── frontend-contract/    # API type definitions (synced)
└── .github/workflows/    # CI: Python compile + frontend build
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py  # API at http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # Dev server at http://localhost:3000
```

### Optional: API Key Authentication

```bash
export NEXUX_API_KEY="your-secret-key"  # Backend
# Frontend: enter key in SpaceshipConsole settings
```

## V7.0 Highlights

- **SQLite persistence** — Jobs survive restarts (`nexux_jobs.db`)
- **API key auth** — Optional `x-api-key` header with SHA-256 hashing
- **Threaded pipeline** — Blocking FFmpeg/Whisper tasks moved to threads
- **14 API endpoints** — Full CRUD + preview, search, cancel, styles
- **Code-split frontend** — 4 vendor chunks + 6 lazy-loaded components
- **V5 fully migrated** — Zero V5 references; all agents use V7.0 engine

## Pipeline Stages

1. **Recon** — Fetch source video metadata & captions
2. **Transcription** — Local Whisper (faster-whisper)
3. **Candidate Analysis** — 25-agent multimodal editorial intelligence
4. **Targeted Retrieval** — Download only needed segments
5. **Render** — FFmpeg compositor with dynamic layout
6. **Vision QA** — Scene detection & face verification
7. **Editorial Ranking** — Virality scoring with evidence
8. **Critic Revision** — Quality gate with revision loop
9. **Render QA** — FFmpeg output validation

## Key Differentiators vs Opus Clip

- **Local-first**: Whisper runs locally, no cloud API costs
- **No B-roll**: Pure clip extraction, no static image overlays
- **Explainable**: Editorial evidence for every clip decision
- **Targeted retrieval**: Downloads only needed segments
- **Critic revision**: Quality gate that can request re-renders
- **18+ subtitle presets**: Hormozi, MrBeast, Cyberpunk, Anime, more

## License

Proprietary — All rights reserved.
