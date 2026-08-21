# NexuX — Agent Knowledge Base

## Project
Local-first AI video repurposing engine (V9.5.2). Dual-mode: Podcast Mode (long video → viral clips) + AI Creative Mode (keyword → multi-source compilation). FastAPI backend + React 19/TS frontend.

## Canonical structure
- `backend/main.py` — canonical FastAPI app. VERSION = "9.5.2". Job store = SQLite (`NEXUX_DB_PATH`) + in-memory hot cache (`jobs` dict).
- Routers mounted in main.py: `api_v95_modes` (/api/v2/*), `api_v95_editor` (/api/editor/*), `api_v95_extras` (virality/hooks/repair/rerender legacy).
- `backend/engine/` — 38 pipeline modules. Heavy deps (torch, whisper, mediapipe) are LAZILY imported — never import them at module top level.
- Frontend: `frontend/src/api/{nexuxApi,v2Api,editorApi}.ts` mirror the three backend surfaces.

## Job lifecycle (critical)
- `/api/v2/generate` MUST register jobs via `main.start_pipeline_job` / `main.start_mode2_job` (BackgroundTasks) — never call pipelines directly, or jobs become un-pollable ghosts (404 on /api/job/{id}).
- Workers: `_process_job` (podcast, async progress callback) and `_process_mode2_job` (creative, sync `progress_callback(pct, msg)` bridged to ws).
- Cancel endpoint rejects completed/failed jobs with 400 — correct semantics.

## Verify
- Backend: `cd backend && . .venv/bin/activate && python -m pytest tests/ -q` (55 tests). venv at `backend/.venv` (Python 3.13).
- Frontend: `cd frontend && npx tsc --noEmit && npm test && npm run build` (18 vitest tests).
- Backend run: `cd backend && python main.py` (port 8000). Frontend dev: `npm run dev` (needs `allowedHosts` for *.prod-runtime.all-hands.dev in vite.config.ts).

## Conventions
- Version strings live in: main.py VERSION, utils/config.py, requirements.txt header, package.json, engine module docstring headers — keep them in sync.
- pydantic v2: use `SettingsConfigDict`, not class Config.
- Docstrings containing `\k` (e.g. karaoke) must be raw docstrings (r"""...""") to avoid SyntaxWarning.
- TestClient runs BackgroundTasks synchronously — stub `main._process_job`/`_process_mode2_job` in tests and decrement `main.active_count` in the stub's finally (module state persists across tests; reset `main.jobs`/`cancel_flags`/`active_count` per test).
