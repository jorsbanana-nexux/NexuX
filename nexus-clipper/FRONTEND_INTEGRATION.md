# NexuX frontend integration contract

## Canonical relationship

`Fronted` is the interactive UI. `nexus-clipper/local-first-v5/canonical_api.py` is the single backend API surface.

The browser must not call `server.py`, `app.py`, legacy `/youtube/*`, or legacy `/render/*` routes directly.

## Browser base URL

Set the frontend variable:

```text
VITE_NEXUX_API_URL=http://127.0.0.1:8000
```

In production, set it to the deployed canonical API origin.

The backend allows explicit browser origins through:

```text
NEXUX_ALLOWED_ORIGINS=https://your-frontend.example,http://localhost:3000
```

## 1:1 UI mapping

| UI operation | Canonical API | Notes |
|---|---|---|
| Generate | `POST /api/generate` | Creates persistent job and starts V6.1 pipeline |
| Progress | `GET /api/job/{job_id}` | Poll `status`, `progress`, `stage`, `error` |
| Cancel | `DELETE /api/job/{job_id}` | Stops active retrieval/transcription/render subprocesses |
| Health | `GET /api/health` | Runtime/tool availability |
| Subtitle presets | `GET /api/styles` | Backend source of truth |
| Output download | `GET /api/download/{job_id}` | Downloads the canonical primary MP4 |
| Vision | `GET /api/vision/{job_id}` | Persisted analysis bundle after completion |
| Render QA | `GET /api/render-qa/{job_id}` | Canonical media QA report |

## Generate payload rules

The frontend must enforce the same ranges as the backend:

- `target_duration`: 20–60 seconds
- `clip_count`: 1–10
- aspect ratio: backend-supported values, preferably `9:16` for the main workflow
- `subtitle_style`: values returned by `/api/styles`
- `position`: `top`, `center`, or `bottom`
- `font_size`: 20–96
- `stroke_width`: 1–12

## Result mapping

The backend job returns `clips` as `/output/<filename>` paths. The frontend should build a preview URL from the API origin and use the job's `render_meta` for editorial score, narrative evidence, camera information, and QA.

Do not invent a viral score in the UI. Display backend editorial evidence or a clearly labeled heuristic score instead.

## State machine

```text
idle
  -> submitting
  -> queued
  -> processing
  -> completed
  -> failed
  -> cancelled
```

The UI must render `stage` and `progress` from the backend rather than using a fixed timeout.

## Prohibited frontend shortcuts

- No `setTimeout` pretending analysis completed.
- No `SAMPLE_GENERATED_CLIPS` in the production workflow.
- No direct Gemini/API credentials in browser code.
- No hard-coded `/99` viral score unless the backend supplies a verified metric with that name.
- No promise that unsupported ingestion providers work.
