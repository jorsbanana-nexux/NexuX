# 🚀 NexuX V9.6 — Autonomous AI Video Repurposing Engine

> **Local-first, zero cloud cost, production-ready.** Transform long-form videos into viral clips — entirely on your own machine.
>
> **V9.5:** Dual-mode system — Podcast Mode (clip podcasts/interviews) + AI Creative Mode (keyword → multi-source compilation). Opus Killer scoring (8 dimensions), auto viral titles, keyword expansion, post-render editor.

[![Version](https://img.shields.io/badge/version-9.6.0-cyan)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Python](https://img.shields.io/badge/Python-3.11+-yellow)]()
[![React](https://img.shields.io/badge/React-19-black)]()

**Canonical engine: `backend/main.py` (FastAPI).** Satu-satunya sumber kebenaran API dan struktur.

---

## 📋 Daftar Isi

1. [Apa itu NexuX?](#-apa-itu-nexux)
2. [Dual-Mode System](#-dual-mode-system)
3. [Fitur yang Melampaui Opus Clip](#-fitur-yang-melampaui-opus-clip)
4. [Arsitektur](#-arsitektur)
5. [Prasyarat](#-prasyarat)
6. [Instalasi](#-instalasi)
7. [Konfigurasi](#-konfigurasi)
8. [Referensi API](#-referensi-api)
9. [Frontend](#-frontend)
10. [Deployment Produksi](#-deployment-produksi)
11. [Testing](#-testing)
12. [Troubleshooting](#-troubleshooting)
13. [Changelog](#-changelog)

---

## 🎯 Apa itu NexuX?

NexuX adalah **autonomous AI video repurposing engine** dengan dua mode:

- **Mode 1 — Podcast:** Ambil video panjang (YouTube / upload lokal) → transkripsi → analisis podcast → skor viral → deteksi hook → reframe 9:16 + caption → render → klip siap posting.
- **Mode 2 — AI Creative:** Satu keyword → cari momen relevan di banyak video → susun narasi → kompilasi satu video dengan TTS + SFX.

Berbeda dari tools cloud (Opus Clip, dsb.):

- **100% pemrosesan lokal** — Whisper + OpenCV + FFmpeg. Tanpa API berbayar, tanpa upload ke cloud orang lain.
- **Skor transparan** — Opus Killer 8 dimensi, bukan black-box satu angka.
- **Editorial Consciousness** — critic bawaan mengevaluasi setiap klip dan me-revisi yang lemah.
- **B-roll-free** — tidak menempelkan stock footage; konten asli yang bicara.
- **SQLite persistence** — riwayat job bertahan saat restart.
- **Auto Viral Titles** — 8 arketipe, 5 variasi per klip, bilingual EN+ID.
- **Keyword Expansion** — 1 keyword → 15+ istilah pencarian (Mode 2).

---

## 🔀 Dual-Mode System

### Mode 1 — Podcast Mode (🎙️)

**Input:** YouTube URL atau upload lokal (podcast, interview, talk show)
**Output:** Beberapa klip viral (20–90 detik)

```
URL/upload → auto-caption/Whisper → podcast analysis → Opus Killer scoring →
hook detection → partial download → render paralel → critic revision →
auto titles → final assembly
```

Kecerdasan khusus podcast: topic segmentation, punchline extraction, heat detection, story arc, Q&A pairing, filler word detection, speaker turn-taking.

Tahapan progress (via WebSocket `/ws`):

```
1. Smart Metadata (0-5%)     → yt-dlp fetch info (tanpa download)
2. Caption Fetch (5-10%)     → YouTube auto-captions ATAU faster-whisper
3. Podcast Analysis (10-20%) → segmentasi topik, punchline, heat
4. Opus Killer Score (20%)   → scoring 8 dimensi + hook detection
5. Partial Download (20-40%) → download HANYA segmen terpilih
6. Parallel Render (40-85%)  → semua klip dirender bersamaan
7. Critic Revision (85-95%)  → kritik multi-dimensi + auto-revisi
8. Auto Titles (95-97%)      → 5 judul viral + hashtag per klip
9. Final Assembly (97-100%)  → concat + audio enhancement
```

### Mode 2 — AI Creative Mode (✨)

**Input:** Satu keyword (misal "peter parker", "game terbaik 2026", "motivasi")
**Output:** Satu video kompilasi dengan narasi AI, SFX, dan teks overlay

```
keyword → expand (15+ terms) → search multi-source → analisis transkrip →
LLM narasi → partial download → compile (TTS+SFX+transisi) →
auto metadata → Opus Killer score
```

Tahapan progress:

```
1. Keyword Expansion (3%)    → 1 keyword → 15+ istilah pencarian
2. Multi-Source Search (8%)  → cari YouTube dengan istilah hasil expand
3. Transcript Analysis (18%) → temukan momen relevan di 10+ video
4. LLM Narrative (32%)       → AI menulis skrip hook → buildup → payoff
5. Partial Download (45%)    → download hanya momen relevan
6. Compile Video (65%)       → TTS + SFX + transisi + teks overlay
7. Auto Metadata (85%)       → judul viral + hashtag + deskripsi SEO
8. Opus Killer Score (90%)   → skor kompilasi final
9. Final Output (100%)       → video + thumbnail + metadata
```

---

## 🏆 Fitur yang Melampaui Opus Clip

| Fitur | Opus Clip | NexuX V9.6 |
|-------|-----------|------------|
| **Biaya** | $19–$39/bulan | **Gratis selamanya** |
| **Privasi** | Video diupload ke cloud | Tetap di mesin Anda |
| **Hook Detection** | ~3 pola | **9 arketipe (EN + ID)** |
| **Virality Scoring** | Black box, 1 angka | **8 dimensi, transparan** |
| **Upload lokal** | Cloud | ✅ `POST /api/upload` → token `local://` |
| **Subtitle Presets** | Template brand | ✅ 46+ preset creator |
| **Emoji Injection** | Template | ✅ Auto emoji + emphasis (Caption Engine v2) |
| **Filler Removal** | Berbayar, black box | ✅ **Smart Cut: jump-cut nyata di render**, tiap potongan dilaporkan (V9.6) |
| **Retention Heatmap** | 1 angka retensi | ✅ Kurva per detik + alasan drop-off (V9.6) |
| **Hook Variants** | 1 hook terpilih | ✅ Hook Lab: N varian ter-ranking + skor CTR judul transparan (V9.6) |
| **Voice-over (TTS)** | Limit harian | ✅ Unlimited edge-tts |
| **Conversation Flow** | ❌ | ✅ Analisis turn-taking pembicara |
| **Retention Curve** | ❌ | ✅ Prediksi titik drop-off |
| **Shareability** | ❌ | ✅ Quotability + meme potential |
| **Competitor Delta** | ❌ | ✅ "Beats Opus by X points" |
| **Podcast Mode** | Clipper generik | ✅ Segmentasi topik + punchline + heat |
| **Creative Mode** | ❌ | ✅ Kompilasi multi-sumber dari keyword |
| **Auto Titles** | Basic | ✅ 8 arketipe, 5 variasi, bilingual |
| **Keyword Expansion** | ❌ | ✅ 15+ istilah (sinonim, trending, Q&A) |
| **Face Tracking** | Basic | OpenCV + MediaPipe |
| **Editorial Critic** | ❌ | Auto-revision loop multi-dimensi |
| **B-Roll** | Stock footage | B-roll-free (orisinalitas terjaga) |
| **Job Persistence** | Cloud | SQLite (bertahan saat restart) |
| **API Auth** | Wajib | Opsional (dev lokal = tanpa auth) |
| **Kustomisasi** | Terbatas | Full source code |

---

## 🏗 Arsitektur

```
NexuX/
├── backend/                       # FastAPI — canonical API + engine
│   ├── main.py                    # entrypoint API + job store + workers
│   ├── api_v95_modes.py           # dual-mode router (/api/v2/*)
│   ├── api_v95_editor.py          # post-render editor router (/api/editor/*)
│   ├── api_v95_extras.py          # extras router (virality, hooks, repair, rerender legacy)
│   ├── engine/                    # pipeline inti (38 modul)
│   │   ├── pipeline.py            # orchestrator Mode 1
│   │   ├── transcribe.py          # faster-whisper (lazy)
│   │   ├── podcast_analyzer.py    # segmentasi topik, punchline, heat
│   │   ├── opus_killer.py         # scoring 8 dimensi
│   │   ├── hook_detection.py      # 9 arketipe hook (EN+ID)
│   │   ├── virality_score.py      # 8-dimension virality
│   │   ├── reframe_engine.py      # face tracking → crop FFmpeg
│   │   ├── render.py / render_pro.py  # render multi-pass, subtitle kinetik
│   │   ├── caption_engine_v2.py   # kinetic typography
│   │   ├── clip_titler.py         # judul viral bilingual
│   │   ├── keyword_expander.py    # Mode 2 keyword expansion
│   │   ├── mode2_*.py             # Mode 2: search, narrator, compiler, pipeline
│   │   ├── critic.py              # editorial critique
│   │   ├── self_healer.py         # pemulihan error 3 lapis
│   │   ├── repair_system.py       # diagnosa + fix
│   │   ├── preview_renderer.py    # preview FFmpeg realtime
│   │   ├── rerender_pipeline.py   # re-render personalisasi + overlay burn-in
│   │   └── ...
│   ├── utils/                     # config, logger, rate_limiter
│   ├── tests/                     # 55+ test (pytest)
│   └── requirements.txt
├── frontend/                      # React 19 + Vite 6 + Tailwind v4 + TypeScript
│   └── src/
│       ├── api/                   # nexuxApi.ts, v2Api.ts, editorApi.ts
│       └── components/            # PostRenderFlow, ModeSelector, consoles, studios...
├── Dockerfile                     # multi-stage (backend + frontend)
└── docker-compose.yml
```

**Alur request:** Frontend (port 3000) ↔ HTTP API + WebSocket `/ws` ↔ FastAPI (port 8000) → engine → SQLite.

**Job lifecycle (kedua mode):** `/api/v2/generate` mendaftarkan job ke store SQLite → worker background memproses → progress realtime via `/ws` + polling `/api/job/{id}` → hasil di `/api/download/{id}` → personalisasi ulang via `/api/editor/*`.

---

## ✅ Prasyarat

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

## 📝 Instalasi

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
# {"status":"healthy","canonical_runtime":true,"canonical_engine":"local-first-v9.5.2",...}

curl http://127.0.0.1:8000/api/v2/modes
# daftar mode podcast + creative
```

### 5. Klip pertama (Mode 1)

**Via UI:** buka `http://localhost:3000` → pilih **Podcast Mode** (🎙️) → tempel URL YouTube → atur durasi/jumlah klip → Generate → setelah render selesai, **editor personalisasi terbuka otomatis**.

**Via API:**

```bash
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"podcast","youtube_url":"https://www.youtube.com/watch?v=VIDEO_ID","target_duration":45,"clip_count":5}'

# poll progress (job TERDAFTAR di store — bisa dipoll, dibatalkan, bertahan saat restart)
curl http://127.0.0.1:8000/api/job/<job_id>
```

### 6. Video creative pertama (Mode 2)

**Via UI:** pilih **AI Creative Mode** (✨) → ketik keyword → atur voice/SFX/BGM → Generate.

**Via API:**

```bash
# preview keyword expansion
curl "http://127.0.0.1:8000/api/v2/keyword/expand?keyword=motivasi+belajar"

curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"creative","keyword":"motivasi belajar","voice_enabled":true,"voice_name":"id-ID-ArdiNeural","target_duration":60}'
```

---

## ⚙ Konfigurasi

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

## 📡 Referensi API

Base URL: `http://127.0.0.1:8000`. Referensi interaktif lengkap: `/docs`.

### Mode (V9.5)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/v2/modes` | daftar mode + fitur |
| POST | `/api/v2/generate` | mulai generasi (auto-detect mode) → **job terdaftar & bisa dipoll** |
| GET | `/api/v2/keyword/expand` | preview keyword expansion |
| GET | `/api/v2/modes/{mode}/features` | detail mode |

### Editor (post-render)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/editor/templates` | 12 template creator |
| GET | `/api/editor/styles` | 46+ preset subtitle |
| GET | `/api/editor/effects` | zoom, color grade, speed ramp, animasi |
| GET | `/api/editor/clip/{job_id}/{idx}` | detail klip |
| GET | `/api/editor/clip/{job_id}/{idx}/transcript` | transkrip word-level |
| POST | `/api/editor/preview/{job_id}/{idx}` | preview FFmpeg cepat (480p, 5s) |
| POST | `/api/editor/rerender/{job_id}/{idx}` | re-render dengan personalisasi + overlay burn-in |
| POST | `/api/editor/rerender/{job_id}/all` | batch re-render |

### Analisis & Utilitas (V9.5 Extras)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/virality/{job_id}` | skor virality 8 dimensi per klip |
| GET | `/api/hooks/{job_id}` | hasil hook detection per klip |
| GET | `/api/clips/{job_id}/{idx}/retention` | heatmap retensi per detik + titik drop-off (V9.6) |
| GET | `/api/clips/{job_id}/{idx}/hook-lab` | varian hook ter-ranking + lab CTR judul (V9.6) |
| GET | `/api/caption-quality/{job_id}` | laporan kualitas caption per klip |
| GET | `/api/reframe/{job_id}` | data auto-reframe per klip |
| GET | `/api/platforms` | platform publish yang didukung |
| GET | `/api/repair/diagnose` | diagnosa self-healing |
| POST | `/api/repair/fix-all` | auto-fix semua masalah terdeteksi |
| POST | `/api/preview-render/{job_id}/{idx}` | preview FFmpeg (legacy shape) |
| POST | `/api/rerender/{job_id}/{idx}` | re-render personalisasi (legacy shape) |
| POST | `/api/rerender/{job_id}/{idx}/overlays` | re-render + overlay burn-in (timeline editor) |

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
| GET | `/api/job/{id}` | status job (bekerja untuk job v1 DAN v2) |
| GET | `/api/jobs` | daftar job (paginasi) |
| DELETE | `/api/job/{id}` | batalkan job |
| GET | `/api/vision/{id}` | data analisis vision |
| GET | `/api/render-qa/{id}` | QA hasil render |
| GET | `/api/critic/{id}` | laporan kritik editorial |
| GET | `/api/publish/{id}` | rencana publish |
| POST | `/api/publish/{id}/{platform}` | persiapan platform |
| GET | `/api/analytics/{id}` | analitik job |
| GET | `/api/download/{id}` | unduh hasil |
| POST | `/api/mode2/generate` | Mode 2 sinkron (legacy, satu-shot) |
| GET | `/api/mode2/jobs` | daftar hasil Mode 2 dari disk |
| GET | `/api/mode2/voices` | daftar suara TTS |
| WS | `/ws` | progress realtime |

---

## 🎨 Frontend

React 19 + Vite 6 + Tailwind v4 + TypeScript.

### API clients (`src/api/`)

| File | Dipakai untuk |
|------|---------------|
| `nexuxApi.ts` | endpoint inti (generate, job, download, upload, rerender legacy, repair, platforms) |
| `v2Api.ts` | endpoint dual-mode V9.5 (modes, generate, keyword expand) |
| `editorApi.ts` | endpoint editor (templates, preview, re-render) |

### Komponen utama (`src/components/`)

| Komponen | Fungsi |
|----------|--------|
| `PostRenderFlow.tsx` | Orchestrator dual-mode: seleksi mode → konsol (aktif di `App.tsx`) |
| `ModeSelector.tsx` | UI seleksi mode (fetch `/api/v2/modes`, fallback offline) |
| `SpaceshipConsole.tsx` | Mode 1 — input + progress, auto-open editor setelah render |
| `Mode2Console.tsx` | Mode 2 — input keyword + settings |
| `ClipEditorStudio.tsx` | personalisasi klip + re-render (undo/redo, shortcut keyboard) |
| `TimelineEditorStudio.tsx` | timeline editor + overlay drag → burn-in via `/api/rerender/.../overlays` |
| `SubtitleEngineStudio.tsx` | preview style subtitle |

---

## 🚀 Deployment Produksi

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

## 🧪 Testing

```bash
cd backend && python -m pytest tests/ -v        # 55+ test
cd frontend && npm test                          # unit (vitest)
cd frontend && npx tsc --noEmit                  # typecheck
cd frontend && npm run build                     # build produksi
```

CI (`.github/workflows/ci.yml`) menjalankan backend compile+tests dan frontend typecheck+build.

---

## 🔧 Troubleshooting

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

**Endpoint mengembalikan 404** — pastikan server versi terbaru; seluruh router (`api_v95_modes`, `api_v95_editor`, `api_v95_extras`) ter-mount otomatis di `main.py`. Cek log startup.

---

## 📦 Changelog

### V9.6.0 (Agustus 2026) — "Beyond Opus": Smart Cut, Retention Heatmap, Hook Lab

**NEW — tiga engine yang melampaui Opus Clip:**
- **Smart Cut Engine** (`engine/smart_cut.py`) — `remove_fillers_pauses` kini BENAR-BENAR memotong video: jump-cut silence > 0.45s + filler words (EN+ID) langsung di render via Pass 0 `trim`/`concat` FFmpeg, dengan re-timing transkrip agar karaoke subtitle tetap sinkron. Setiap potongan dilaporkan dengan alasannya (`silence`/`filler`) — bukan black box. Safety valve menolak pemotongan > 50% (deteksi transkrip misaligned).
- **Retention Heatmap** (`engine/retention_heatmap.py` + `GET /api/clips/{job_id}/{idx}/retention`) — kurva retensi per detik dengan alasan drop-off (silence/low_density/natural_decay), strongest window, dan grade. Opus Clip hanya menampilkan satu angka; NexuX menampilkan seluruh kurva.
- **Hook Lab** (`engine/hook_lab.py` + `GET /api/clips/{job_id}/{idx}/hook-lab`) — N varian hook ter-ranking (arketipe + skor + start-shift) dan prediktor CTR judul transparan 7 faktor (`predict_title_ctr`) dengan saran rewrite konkret.

**Integrasi:**
- `render_clip_pro` menerima `smart_cuts=` (Pass 0) — pass 1–4 berjalan transparan di timeline terkompresi.
- `pipeline.py` menghitung smart cut per klip saat `remove_fillers_pauses=True`; statistik potongan masuk metadata klip.
- Frontend: `nexuxApi.retentionHeatmap()` + `nexuxApi.hookLab()` typed client.

**Tests:** 34 test baru di `tests/test_beyond_opus.py` (unit engine + endpoint via TestClient). Total backend: 83 passed.

### V9.5.3 (Agustus 2026) — Rombakan Total: Rancangan ↔ Realita

**Fixed (kritis):**
- **`/api/v2/generate` sekarang mendaftarkan job sungguhan** ke store SQLite — sebelumnya job berjalan "hantu" tanpa registrasi sehingga `/api/job/{id}` selalu 404. Kedua mode kini punya progress realtime, WebSocket update, pembatalan, dan persistence penuh.
- **Dead `_integrate_api.py` exec-loader dihapus** — fungsinya digantikan router proper `api_v95_extras.py` (virality, hooks, caption-quality, reframe, platforms, repair, rerender legacy + overlays) yang ter-mount di `main.py`.
- Versi diseragamkan ke **9.5.2** di `main.py`, `utils/config.py`, `requirements.txt`, `package.json`, dan seluruh header modul engine.
- `SyntaxWarning` invalid escape `\k` di docstring diperbaiki (raw docstrings).
- `Settings` pydantic dimigrasi ke `SettingsConfigDict` (tanpa deprecation warning).

**NEW:**
- `PostRenderFlow.tsx` — orchestrator dual-mode aktif di `App.tsx`: seleksi mode → konsol podcast/kreatif.
- `ModeSelector.tsx` — UI seleksi mode dengan fetch `/api/v2/modes` + fallback offline.
- `v2Api.ts` — client frontend typed untuk `/api/v2/*`.
- 20+ test baru: `tests/test_v95_extras.py` (backend) dan `src/test/v2Api.test.ts` (frontend).

### V9.5.2 (Agustus 2026) — Router Mount + Stabilitas

**Fixed:**
- `editor_router` dan `modes_router` ter-mount di `main.py` (sebelumnya V9.5 endpoints 404).
- Import relatif diperbaiki di `api_v95_editor.py` dan `api_v95_modes.py`.
- `TimelineEditorStudio.tsx` useEffect block-scoped variable fix (TS2448).

### V9.5.1 (Agustus 2026) — Post-Render Editor

- `api_v95_editor.py` — 8 endpoint editor dengan preview FFmpeg nyata.
- Auto-open editor setelah render selesai.
- Undo/Redo + shortcut keyboard di ClipEditorStudio.
- Overlay drag → burn-in via FFmpeg drawtext.
- 12 template creator + 46+ preset subtitle.

### V9.5 (Agustus 2026) — Opus Clip Killer Upgrade

- `opus_killer.py` — scoring 8 dimensi terpadu.
- `podcast_analyzer.py` — segmentasi topik, punchline, heat, Q&A, filler.
- `clip_titler.py` — 5 judul viral per klip (8 arketipe, bilingual).
- `keyword_expander.py` — 1 keyword → 15+ istilah.
- `mode_router.py` + `mode2_enhanced.py` + `api_v95_modes.py`.

### V9.0 / V8.0 (Sebelumnya)

- Timeline editor, undo/redo, preview FFmpeg realtime, self-repair.
- Mode 2 AI Creative, smart pipeline (auto-caption + partial download), render engine 4-pass, self-healer 32 tipe error.

---

## 📜 Lisensi

MIT
