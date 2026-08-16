# FRONTEND INTEGRATION CONTRACT — NexuX V7.0

## Status: CANONICAL — Fronted Integrated

The frontend has been consolidated. The `frontend/` directory now contains the
TypeScript/React 19/Tailwind v4 codebase (formerly the "Fronted" repo).

### What Changed (2026-08-16)

- **Old frontend** (React 18, JSX, Tailwind v3) → **removed entirely**
- **New frontend** (React 19, TypeScript, Tailwind v4, Motion v12) → **canonical**
- `SpaceshipConsole` → **real API** (`nexuxApi.generate` + `startJobPolling`), no mock data
- `ProcessingLoadingState` → **real progress** from API, no fake timers
- `ResultsMosaicGrid` → **dynamic clips** from API response, no hardcoded counts
- `ShowcaseSection` → **honest metrics**, no fabricated accuracy claims
- `ErrorBoundary` → crash protection added
- `nexuxApi.ts` → all canonical endpoints + V6 advanced fields

### API Endpoints (all in `frontend/src/api/nexuxApi.ts`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/styles` | Available subtitle styles & aspect ratios |
| POST | `/api/generate` | Start clip generation job |
| GET | `/api/job/{job_id}` | Poll job status |
| GET | `/api/jobs` | List all jobs (optional status filter) |
| DELETE | `/api/job/{job_id}` | Cancel a job |
| GET | `/api/vision/{job_id}` | Vision analysis bundle |
| GET | `/api/render-qa/{job_id}` | Render quality assurance |
| GET | `/api/critic/{job_id}` | Editorial critique & revision |
| GET | `/api/publish/{job_id}` | Publish plan |
| POST | `/api/publish/{job_id}/{platform}` | Publish to platform |
| GET | `/api/analytics/{job_id}` | Analytics data |
| GET | `/api/download/{job_id}` | Download clip(s) |

### Contract Rules (STILL ENFORCED)

1. **No mock data in production** — `SAMPLE_GENERATED_CLIPS` is banned
2. **No fake timers** — all progress comes from real API polling
3. **No fabricated metrics** — no "99.4% accuracy" unless backend verifies
4. **No unsupported platform claims** — only YouTube ingestion is supported
5. **All video URLs must use `buildOutputUrl()`** — no hardcoded `/output/` paths
6. **API base URL from `VITE_NEXUX_API_URL`** — no hardcoded `127.0.0.1:8000`

### Environment

```bash
# frontend/.env (create from .env.example)
VITE_NEXUX_API_URL=http://127.0.0.1:8000
```

### Build

```bash
cd frontend
npm install
npm run dev    # dev server at :3000
npm run build  # production build
npm run lint   # type check
```
