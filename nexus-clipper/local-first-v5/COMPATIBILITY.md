# Canonical V5 compatibility contract

The React frontend talks to a small compatibility API so the UI does not need to know the internal V5 stages.

| Frontend action | Canonical endpoint | Result |
|---|---|---|
| Generate | `POST /api/generate` | persistent queued job |
| Poll | `GET /api/job/{job_id}` | queued/processing/completed/failed/cancelled |
| Cancel | `DELETE /api/job/{job_id}` | cooperative cancellation between pipeline stages |
| Output | `/output/<filename>` | locally rendered MP4 |
| Health | `GET /api/health` | canonical engine and media-tool state |
| Styles | `GET /api/styles` | actual V5 presets/aspect ratios |

B-roll is deliberately absent from this contract. The canonical V5 job records `broll: false` and never requests external B-roll sources.
