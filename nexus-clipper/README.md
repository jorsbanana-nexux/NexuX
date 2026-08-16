# NexuX — Autonomous AI Video Repurposing Engine

> **V6.4 CANONICAL** — Local-first, zero cloud cost, no B-roll.

NexuX transforms long-form videos into high-virality vertical clips (9:16)
with auto-reframing, kinetic subtitles, and multimodal editorial intelligence.

## Architecture

```
NexuX/
├── backend/              # Canonical V6.4 Python pipeline
│   ├── main.py           # FastAPI entry point
│   ├── orchestrator.py   # Pipeline orchestrator
│   ├── engine/           # 14 engine modules (vision, render, editorial)
│   ├── agents/           # 25 AI agents + capability matrix
│   └── pipeline/         # Reconstruction, targeting, retrieval
├── frontend/             # TypeScript/React 19/Tailwind v4 (canonical)
│   ├── src/api/          # nexuxApi.ts — full API client with polling
│   ├── src/components/   # SpaceshipConsole, ProcessingLoadingState, etc
│   └── src/utils/        # Sound effects, subtitle store, scroll blur
├── local-first-v5/       # Vision quality module
├── frontend-contract/    # API type definitions
└── tests/                # Backend tests
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
