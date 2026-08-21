# NexuX

**Local-first AI video repurposing engine.** Ubah satu video panjang (podcast, interview, webinar) menjadi klip short-form siap posting — berjalan sepenuhnya di mesin sendiri, tanpa biaya cloud, tanpa per-minute charge.

**Canonical engine: `backend/main.py` (FastAPI).** Ini satu-satunya sumber kebenaran API dan struktur.

---

## Daftar Isi

1. [Apa itu NexuX](#apa-itu-nexux)
2. [Fitur utama](#fitur-utama)
3. [Arsitektur](#arsitektur)
4. [Prasyarat](#prasyarat)
5. [Instalasi](#instalasi)
6. [Konfigurasi](#konfigurasi)
7. [Referensi API](#referensi-api)
8. [Frontend](#frontend)
9. [Deployment produksi](#deployment-produksi)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

---

## Apa itu NexuX

NexuX punya dua mode:

- **Mode 1 — Podcast:** Ambil video panjang (YouTube / upload) → transkripsi → analisis konten → skor viral → deteksi hook → reframe 9:16 + caption → render → klip siap.
- **Mode 2 — AI Creative:** Satu keyword → cari momen relevan di banyak video → susun narasi → kompilasi satu video dengan TTS + SFX.

Berbeda dari tools cloud:

- **100% pemrosesan lokal** — Whisper + OpenCV + FFmpeg. Tanpa API berbayar, tanpa upload ke cloud orang lain.
- **Skor transparan** — Opus Killer 8 dimensi, bukan black-box satu angka.
- **B-roll-free** — tidak menempelkan stock footage; konten asli yang bicara.
- **SQLite persistence** — riwayat job bertahan saat restart.

### Mode 1 — Podcast pipeline

```
URL/upload → caption/whisper → podcast analysis → opus killer score →
hook detection → partial download → render paralel → critic revision →
auto titles → final assembly
```

Kecerdasan khusus podcast: topic segmentation, punchline extraction, heat detection, story arc, Q&A pairing, filler word detection, speaker turn-taking.

### Mode 2 — Creative pipeline

```
keyword → expand (15+ terms) → search multi-source → analisis transkrip →
LLM narasi → partial download → compile (TTS+SFX+transisi) → auto metadata → score
```

---

## Fitur utama

| Fitur | Catatan |
|-------|---------|
| Skor viral 8 dimensi | hook, virality, editorial, conversation flow, retention, shareability, technical, competitor delta |
| Hook detection | 9 pola arketipe (EN + ID) |
| Auto viral titles | 8 arketipe, 5 variasi per klip, bilingual EN+ID |
| Keyword expansion | 1 keyword → 15+ istilah pencarian (Mode 2) |
| Local upload | `POST /api/upload` → token `local://` (tanpa cloud) |
| 4K export | `output_resolution=uhd` |
| Subtitle presets | puluhan preset creator, karaoke/kinetic |
| Reframe 9:16 / 1:1 / 16:9 | face tracking (OpenCV + MediaPipe) |
| Filler detection | tandai "um/uh/eh" untuk dipotong |
| Voice-over TTS | edge-tts (ID: Ardi, Gadis; EN: Guy, Girl) |
| Job persistence | SQLite, auto-cleanup via TTL |
| Auth opsional | API key; kosong = tanpa auth untuk dev lokal |

---

## Arsitektur

```
nexux/
├── backend/                  # FastAPI — canonical API + engine
│   ├── main.py               # entrypoint API
│   ├── api_v95_editor.py     # editor post-render (preview, rerender, overlay)
│   ├── api_v95_modes.py      # mode router (/api/v2/*)
│   ├── engine/               # pipeline inti
│   │   ├── transcribe.py     # faster-whisper
│   │   ├── podcast_analyzer.py
│   │   ├── opus_killer.py    # scoring 8 dimensi
│   │   ├── hook_detection.py
│   │   ├── reframe_engine.py
│   │   ├── render.py / render_pro.py
│   │   ├── clip_titler.py
│   │   ├── keyword_expander.py
│   │   └── ... (25 modul)
│   ├── utils/                # config, logger, rate_limiter
│   ├── tests/
│   └── requirements.txt
├── frontend/                 # React 19 + Vite 6 + Tailwind v4 + TypeScript
│   └── src/
│       ├── api/              # nexuxApi.ts, editorApi.ts
│       └── components/       # console, editor studio, subtitle studio, ...
├── Dockerfile                # multi-stage backend image
└── docker-compose.yml
```

**Alur request:** Frontend (port 3000) ↔ HTTP API + WebSocket `/ws` ↔ FastAPI (port 8000) → engine → SQLite.

---

## Prasyarat

| Kebutuhan | Minimum | Rekomendasi |
|-----------|---------|-------------|
| OS | Linux / macOS / Windows (WSL2) | Linux/macOS |
| Python | 3.11+ | 3.12 |
| Node.js | 18+ | 20+ |
| FFmpeg | 6.0+ | 7.0+ |
| RAM | 8 GB | 16 GB (Whisper medium/large) |
| GPU | opsional | CUDA (transkripsi lebih cepat) |
| Disk | 2 GB deps + ruang proses | 10 GB+ |

### System tools

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y ffmpeg python3.11 python3.11-venv python3-pip nodejs npm git

# macOS
brew install ffmpeg python@3.11 node git
```

Verifikasi: `ffmpeg -version`, `python3.11 --version`, `node --version`.

---

## Instalasi

### 1. Clone

```bash
git clone https://github.com/jorsbanana-nexux/NexuX.git
cd NexuX
```

### 2. Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate        # Windows native: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env       # opsional, untuk Mode 2 LLM
python main.py
```

Backend di `http://127.0.0.1:8000`. Swagger: `http://127.0.0.1:8000/docs`.

### 3. Frontend (terminal baru)

```bash
cd frontend
npm install
npm run dev
```

Frontend di `http://localhost:3000`.

### 4. Verifikasi

```bash
curl http://127.0.0.1:8000/api/health
# {"status":"healthy","canonical_runtime":true,...}

curl http://127.0.0.1:8000/api/v2/modes
# daftar mode podcast + creative
```

### 5. Klip pertama (Mode 1)

```bash
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"podcast","youtube_url":"https://www.youtube.com/watch?v=VIDEO_ID","target_duration":45,"clip_count":5}'
```

### 6. Video creative pertama (Mode 2)

```bash
# preview keyword expansion
curl "http://127.0.0.1:8000/api/v2/keyword/expand?keyword=motivasi+belajar"

curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"creative","keyword":"motivasi belajar","voice_enabled":true,"voice_name":"id-ID-ArdiNeural","target_duration":60}'
```

---

## Konfigurasi

Salin `.env.example` → `.env`.

| Variabel | Default | Deskripsi |
|----------|---------|-----------|
| `HOST` | `127.0.0.1` | bind address backend |
| `PORT` | `8000` | port backend |
| `NEXUX_ALLOWED_ORIGINS` | `http://localhost:3000,...` | CORS origins (koma) |
| `NEXUX_API_KEY` | (kosong) | API key auth; kosong = tanpa auth |
| `NEXUX_DB_PATH` | `nexux_jobs.db` | path SQLite |
| `NEXUX_JOB_TTL_HOURS` | `72` | auto-cleanup job setelah N jam |
| `WHISPER_MODEL` | `small` | tiny/base/small/medium/large |
| `NEXUX_AI_ENABLED` | `0` | cloud AI opsional (default lokal penuh) |

### Mode 2 — LLM (opsional)

Tanpa key, Mode 2 pakai fallback narrative berbasis template. Set salah satu untuk narasi lebih baik:

```bash
OPENAI_API_KEY=sk-...            # OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=sk-ant-...     # ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
GEMINI_API_KEY=...               # GEMINI_MODEL=gemini-1.5-flash
```

### Aktifkan auth (produksi)

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# masukkan ke .env sebagai NEXUX_API_KEY
```

---

## Referensi API

Base URL: `http://127.0.0.1:8000`. Referensi interaktif lengkap: `/docs`.

### Mode (V9.5)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/v2/modes` | daftar mode + fitur |
| POST | `/api/v2/generate` | mulai generasi (auto-detect mode) |
| GET | `/api/v2/keyword/expand` | preview keyword expansion |
| GET | `/api/v2/modes/{mode}/features` | detail mode |

### Editor (post-render)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/editor/templates` | template creator |
| GET | `/api/editor/styles` | preset subtitle |
| GET | `/api/editor/clip/{job_id}/{idx}` | detail klip |
| GET | `/api/editor/clip/{job_id}/{idx}/transcript` | transkrip word-level |
| POST | `/api/editor/preview/{job_id}/{idx}` | preview FFmpeg cepat |
| POST | `/api/editor/rerender/{job_id}/{idx}` | re-render dengan personalisasi |
| POST | `/api/editor/rerender/{job_id}/all` | batch re-render |

### Inti

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/` | info server |
| GET | `/api/health` | health check |
| GET | `/api/styles` | styles, rasio, codec |
| POST | `/api/preview` | info video |
| POST | `/api/search` | cari YouTube |
| POST | `/api/upload` | upload video lokal → token `local://` |
| POST | `/api/generate` | mulai generasi (Mode 1 legacy) |
| GET | `/api/job/{id}` | status job |
| GET | `/api/jobs` | daftar job (paginasi) |
| DELETE | `/api/job/{id}` | batalkan job |
| GET | `/api/download/{id}` | unduh hasil |
| WS | `/ws` | progress realtime |

---

## Frontend

React 19 + Vite 6 + Tailwind v4 + TypeScript.

### API clients (`src/api/`)

| File | Dipakai untuk |
|------|---------------|
| `nexuxApi.ts` | endpoint inti (generate, job, download, upload) |
| `editorApi.ts` | endpoint editor (templates, preview, re-render) |

### Komponen utama (`src/components/`)

| Komponen | Fungsi |
|----------|--------|
| `SpaceshipConsole.tsx` | input Mode 1 + progress |
| `Mode2Console.tsx` | input Mode 2 + settings |
| `ClipEditorStudio.tsx` | personalisasi klip + re-render |
| `TimelineEditorStudio.tsx` | timeline editor + overlay drag |
| `SubtitleEngineStudio.tsx` | preview style subtitle |

> Catatan: beberapa komponen dari versi lama (`ModeSelector`, `PostRenderFlow`, `v2Api.ts`) tidak diaktifkan di `App.tsx` dan sengaja dibuang saat konsolidasi. Jika ingin UI dual-mode terpadu, aktifkan kembali alur `/api/v2/*` lewat `nexuxApi`.

---

## Deployment produksi

### Docker

```bash
docker build -t nexux .
docker run -p 8000:8000 nexux
```

### Docker Compose

```bash
docker compose up --build
# backend di :8000; set NEXUX_API_KEY / WHISPER_MODEL via env
```

### Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## Testing

```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm test        # unit
cd frontend && npx tsc --noEmit  # typecheck
cd frontend && npm run build   # build produksi
```

CI (`.github/workflows/ci.yml`) menjalankan backend compile+tests dan frontend typecheck+build.

---

## Troubleshooting

**FFmpeg not found**
```bash
sudo apt install ffmpeg && ffmpeg -version
```

**Whisper model download gagal / RAM kurang**
```bash
WHISPER_MODEL=tiny python main.py
```

**yt-dlp terlalu lama**
```bash
pip install --upgrade yt-dlp
```

**Port sudah dipakai**
```bash
PORT=8001 python main.py
```

**Mode 2 narasi terlalu sederhana** — itu fallback template. Set satu LLM key (`OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY`).

---

## Lisensi

MIT
