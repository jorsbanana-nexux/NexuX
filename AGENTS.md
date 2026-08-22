# NexuX — Agent Knowledge Base

## Project
Local-first AI video repurposing engine (V9.6.0). Dual-mode: Podcast Mode (long video → viral clips) + AI Creative Mode (keyword → multi-source compilation). FastAPI backend + React 19/TS frontend.

## Canonical structure
- `backend/main.py` — canonical FastAPI app. VERSION = "9.6.0". Job store = SQLite (`NEXUX_DB_PATH`) + in-memory hot cache (`jobs` dict).
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

## Progres Sesi Benchmark E2E (2026-08-21)

### Bug yang sudah diperbaiki & ter-push
1. `907ff78` — NameError render_clip/concatenate_clips → *_pro; path ASS pass2 harus absolut (libass resolve vs CWD, bukan output dir).
2. `bb7b2a9` — **Bug 261 byte**: section file dari yt-dlp --download-sections mulai dari t=0, tapi pipeline mengoper clip.start absolut sebagai ffmpeg -ss. Fix: parameter section_offset di render_clip_pro; guard output < 1KB.

### Cara menjalankan benchmark
cd backend && . .venv/bin/activate && python benchmark_e2e.py "<youtube_url>" 30 3
Log: /tmp/benchmark_e2e*.log. Output: engine/output/bench_e2e/.

### Catatan environment sandbox
- ffmpeg bisa HILANG setelah sandbox reset → reinstall: sudo apt-get update && sudo apt-get install -y ffmpeg
- Jika klip 261 byte dan ffmpeg hilang → FileNotFoundError, bukan bug kode.

### Yang masih tertunda
- Re-run benchmark E2E penuh setelah fix offset (verifikasi 3 klip valid + subtitle burn-in)
- Sambungkan auto-open editor ke Mode 2 (keyword/creative)
- Benchmark kualitas: bandingkan output vs target Opus Clip

## V9.6.0 — "Beyond Opus" engines (2026-08-22)
- `engine/smart_cut.py` — compute_keep_segments + remap_transcript. Word dicts may use "word" (whisper) OR "text" (json3) keys — always read via `w.get("word", w.get("text", ""))`.
- Smart cut render integration: `render_clip_pro(..., smart_cuts=dict)` runs Pass 0 (trim/concat filter_complex), remaps transcript AND the clip dict to the compressed [0, N] timeline — downstream passes read the clip dict, so forgetting `clip = {**clip, "start": 0, "end": new_dur}` desyncs karaoke subtitles.
- `engine/retention_heatmap.py` — per-second retention; `_speech_density` weights by overlap fraction so segment-level transcripts don't read as dense.
- `engine/hook_lab.py` — hook variants reuse hook_detection internals; CTR predictor is deterministic (7 factors).
- Endpoints live in api_v95_extras: `/api/clips/{job}/{idx}/retention` + `/hook-lab`.
- Test gotcha: extras router resolves NEXUX_DB_PATH per call, but main.py's db binds at import — seed test jobs via raw sqlite3 into env path, not main._save_job.

## V9.6.1 — Quality & Traceability (2026-08-22)
- **Duration filter** (`mode2_storyboard.py`): MIN_SOURCE_DURATION=30, MAX_SOURCE_DURATION=600. Overfetch 3x then filter. Storyboard returns `skipped_by_duration`.
- **Traceability** (`mode2_pipeline.py`): metadata["storyboard"] persisted to `OUTPUT_DIR/{job_id}/metadata.json`. `/api/mode2/jobs` reads it. Without this, jobs endpoint always empty.
- **Compare view**: `GET /api/jobs/compare` aggregates mode2 (metadata.json) + podcast (jobs DB). Frontend: `JobCompareView.tsx` + `nexuxApi.jobsCompare`.
- **yt-dlp 2026**: `-y` flag removed. Never use it — check `yt-dlp --version` before adding flags.
- **Sandbox YouTube 403**: Video download blocked; subtitle fetch works. E2E test with real keyword hits 403 — verify fix with mock, not real download.
- `run_mode2_pipeline` signature includes `storyboard: Optional[List[Dict]]` — when set, skips YouTube search. Don't remove it or TestMode2Traceability fails.

## V9.6.2 — yt-dlp resilience (2026-08-22)
- **`download._ytdlp_common_args()`** — single source of anti-block args, injected into EVERY yt-dlp call in download.py + mode2_search.py: `NEXUX_COOKIES_FILE` / `NEXUX_COOKIES_BROWSER` (file wins over browser), `NEXUX_PLAYER_CLIENTS` (→ `--extractor-args youtube:player_client=...`), `NEXUX_PROXY` (→ `--proxy`, covers metadata AND streams).
- **`engine/ytdlp_updater.py`** — self-heal: background thread at startup (`main.lifespan`, delayed `NEXUX_YTDLP_UPDATE_DELAY`=120s) + reactive: `download._run_ytdlp` upgrades yt-dlp once and retries once when stderr matches 403. Process-wide lock; failures never crash the app. Opt out: `NEXUX_YTDLP_AUTO_UPDATE=0`.
- Sandbox finding: metadata fetch works, but stream download 403s even with player_client — cookies + proxy are the durable fixes; on a hostile network only `NEXUX_PROXY` (or local upload) unblocks googlevideo.
- Tests: `tests/test_ytdlp_resilience.py` (13 tests). Never add yt-dlp subprocess calls without `_ytdlp_common_args()`.
