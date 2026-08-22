# 🛰️ NexuX — README-NEXT: Upgrade/Update Handoff Document

> **Dokumen ini adalah briefing lengkap untuk agen (AI/human) yang akan melanjutkan pengembangan NexuX.**
> Berisi: kondisi terkini, semua yang sudah dibangun, keputusan arsitektur, jebakan yang harus dihindari,
> dan roadmap menuju "jauh di atas Opus Clip".
>
> **Baca AGENTS.md juga** — itu knowledge base operasional yang selalu diperbarui.

---

## 1. Visi Produk

**NexuX** = local-first AI video repurposing engine (bukan SaaS — jalan 100% di mesin pengguna, nol biaya cloud).

**Target:** melampaui Opus Clip di SEMUA dimensi. Opus Clip hanya punya: podcast clipping + subtitle + virality score.
NexuX sudah melampauinya dengan:
- **Dual-mode**: Podcast Mode (video panjang → klip viral) + **AI Creative Mode / Mode 2** (1 keyword → kompilasi multi-sumber, Opus tidak punya ini)
- **Mode 2 Universal**: 1 keyword bebas (mis. "one punch man", "berpikir kritis") → Shorts viral Bahasa Indonesia otomatis, dengan arketipe naratif: **Hook → Kenapa → Fakta → Sisi Gelap → Mindblowing**
- **Beyond-Opus engines** (V9.6.0): Smart Cut, Retention Heatmap, Hook Lab — detail di bagian 3
- **Multi-Job Compare** (V9.6.1): dashboard kualitas lintas-job — Opus hanya single-job view
- **Storyboard traceability**: setiap job menyimpan storyboard lengkap (auditability)

---

## 2. Kondisi Terkini (State of the Project)

### Versi & Branch
- **Versi terpasang: 9.6.1** — string versi hidup di 5 tempat yang HARUS sinkron:
  `backend/main.py` (`VERSION`), `backend/utils/config.py`, `backend/requirements.txt` (header),
  `frontend/package.json`, docstring header modul engine.
- Branch kerja terakhir: `v961-quality-compare` (PR #39). Main: `73c9ece` (V9.6.0, PR #38).
- Stack: **FastAPI + Python 3.13** (backend), **React 19 + TypeScript + Vite + Motion** (frontend).

### Status Verifikasi (terakhir dicek: 2026-08-22)
| Suite | Status |
|---|---|
| Backend pytest | ✅ **93 passed** (`cd backend && . .venv/bin/activate && python -m pytest tests/ -q`) |
| Frontend vitest | ✅ **26 passed** (`cd frontend && npm test`) |
| TypeScript | ✅ `npx tsc --noEmit` bersih |
| Build | ✅ `npm run build` OK |
| E2E analisis nyata | ✅ keyword "berpikir kritis"/"elon musk": storyboard→transkrip→narasi 4.5s/2 sumber |
| E2E render video riil | ⚠️ **belum terverifikasi** — sandbox kena YouTube 403 (lihat bagian 6) |

### Job lifecycle (KRITIS — jangan dilanggar)
- `/api/v2/generate` dan `/api/mode2/generate` **HARUS** mendaftarkan job via `main.start_pipeline_job` / `main.start_mode2_job` (BackgroundTasks). Jangan panggil pipeline langsung — job jadi "hantu" (404 di `/api/job/{id}`).
- Workers: `_process_job` (podcast, async progress callback), `_process_mode2_job` (creative, sync `progress_callback(pct, msg)` di-bridge ke websocket).
- Job store: SQLite (`NEXUX_DB_PATH`) + hot cache in-memory (`jobs` dict). **Reset `main.jobs` / `cancel_flags` / `active_count` per test** — state modul persist antar-test.
- TestClient menjalankan BackgroundTasks secara sinkron — stub `main._process_job`/`_process_mode2_job` di test, dan decrement `main.active_count` di `finally` stub.
- Cancel endpoint menolak job completed/failed dengan 400 — itu semantik yang benar, jangan "diperbaiki".

---

## 3. Peta Arsitektur & Semua yang Sudah Dibangun

### Backend (`backend/`)
- **`main.py`** — canonical FastAPI app, satu-satunya sumber kebenaran API. Router yang dimount:
  `api_v95_modes` (`/api/v2/*`), `api_v95_editor` (`/api/editor/*`), `api_v95_extras` (retention/hook-lab/repair/rerender).
- **`engine/` — 48 modul pipeline.** Aturan keras: heavy deps (torch, whisper, mediapipe) **LAZY import** — jangan pernah import di top-level modul.

#### Modul kunci dan perannya
| Modul | Fungsi |
|---|---|
| `pipeline.py` / `download.py` / `transcribe.py` | Mode 1 core: unduh → transkripsi → klip |
| `render_pro.py` | Renderer utama. **Path ASS pass-2 harus ABSOLUT** (libass resolve vs CWD, bukan output dir) |
| `opus_killer.py` | Scoring 8 dimensi (`OpusKillerScore`, `score_with_opus_killer`) — lebih dalam dari skor Opus |
| `smart_cut.py` (V9.6.0) | `compute_keep_segments` + `remap_transcript`. Potong jeda/senyap otomatis |
| `retention_heatmap.py` (V9.6.0) | `predict_retention_curve` — retensi per-detik; `_speech_density` pakai overlap fraction |
| `hook_lab.py` (V9.6.0) | `generate_hook_variants` + `predict_title_ctr` (deterministik, 7 faktor) |
| `mode2_search.py` | `search_youtube` (ytsearch, no API key), `get_auto_captions`, `analyze_videos_for_keyword`, `download_video_moments` (--download-sections) |
| `mode2_storyboard.py` | `plan_storyboard` — planner arketipe; **filter durasi sumber 30–600s** (overfetch 3x, return `skipped_by_duration`) |
| `mode2_narrator.py` | Narasi viral; fallback deterministik jika tak ada LLM key |
| `mode2_pipeline.py` | `run_mode2_pipeline(keyword, ..., job_id, progress_callback, storyboard=None)` — persist `metadata.json` (storyboard + processing_time) ke `OUTPUT_DIR/{job_id}/` |
| `mode2_compiler.py` / `mode2_enhanced.py` | Kompilasi akhir Mode 2 |
| `caption_engine_v2.py` | Subtitle karaoke/Hormozi/dll. **Docstring dengan `\k` harus raw (`r"""`)** |
| `hook_detection.py`, `editorial.py`, `critic.py`, `virality_score.py`, `clip_titler.py`, `keyword_expander.py` | Analisis kualitas klip |
| `preview_renderer.py`, `reframe_engine.py`, `thumbnail.py` | Editor & reframe 9:16 |
| `self_healer.py`, `repair_system.py`, `rerender_pipeline.py` | QA & re-render |
| `analytics_engine.py`, `social.py`, `autopost_engine.py`, `broll.py` | Distribusi & insights |

#### Endpoint penting (main.py)
`/api/generate`, `/api/v2/generate` (podcast), `/api/mode2/generate` + `/api/mode2/storyboard` + `/api/mode2/jobs` + `/api/mode2/voices` (creative), `/api/jobs`, **`/api/jobs/compare`** (V9.6.1), `/api/job/{id}`, `/api/download/{job_id}`, `/api/preview`, `/api/critic/{job_id}`, `/api/vision/{job_id}`, `/api/analytics/{job_id}`, `/api/render-qa/{job_id}`, `/api/publish/{job_id}[/{platform}]`, `/api/clips/{job}/{idx}/retention` + `/hook-lab` (di extras), `/api/upload`, `/api/search`, `/api/styles`, `/api/health`.

### Frontend (`frontend/src/`)
- API mirrors: `api/nexuxApi.ts` (+`jobsCompare`, `JobCompareRow`), `api/v2Api.ts`, `api/editorApi.ts` — cermin 3 surface backend.
- Komponen kunci: `SpaceshipConsole` (podcast), `Mode2Console` (creative), `ClipEditorStudio` + `TimelineEditorStudio` (editor pasca-render), `InsightsPanel` (tab Insights di editor), `ResultsMosaicGrid`, `SubtitleEngineStudio`, **`JobCompareView.tsx`** (V9.6.1 — dashboard compare, dimount di `App.tsx` sebagai section 6.5).
- Vite dev **wajib** `allowedHosts` untuk `*.prod-runtime.all-hands.dev` di `vite.config.ts`.

---

## 4. Sejarah Bug Penting (Jangan Ulangi)

1. **`907ff78`** — NameError `render_clip`/`concatenate_clips` → `*_pro`; path ASS pass-2 absolut.
2. **`bb7b2a9`** — **Bug 261 byte**: file section dari `yt-dlp --download-sections` mulai dari t=0, tapi pipeline mengoper `clip.start` absolut sebagai `ffmpeg -ss`. Fix: parameter `section_offset` di `render_clip_pro` + guard output < 1KB.
3. **V9.6.1** — **yt-dlp 2026 menghapus flag `-y`**. SEMUA download gagal ("no such option"). Fix: hapus dari semua cmd di `mode2_search.py`. **Sebelum menambah flag yt-dlp apapun, cek `yt-dlp --version`.**
4. **V9.6.1** — signature `run_mode2_pipeline` kehilangan param `storyboard` saat edit → restore. Monkeypatch test storyboard harus target `mode2_storyboard.search_youtube`, BUKAN `mode2_search`.
5. **Smart cut** — setelah Pass 0 remap, WAJIB `clip = {**clip, "start": 0, "end": new_dur}`; kalau lupa, subtitle karaoke desync. Word dict bisa pakai key `"word"` (whisper) ATAU `"text"` (json3) — selalu `w.get("word", w.get("text", ""))`.

---

## 5. Konvensi Kode (Wajib)

- **Pydantic v2**: `SettingsConfigDict`, bukan `class Config`.
- Docstring yang mengandung `\k` (karaoke) → raw docstring `r"""..."""` (menghindari SyntaxWarning).
- Test backend: 93 test di `backend/tests/`, termasuk `TestMode2Traceability`, `TestJobsCompare`, `test_beyond_opus.py`.
- Test frontend: 26 vitest di `frontend/src/test/`.
- Tidak ada dependensi eksternal baru tanpa alasan kuat — filosofi local-first, minimal deps.

---

## 6. Batasan Lingkungan Sandbox (Penting!)

- **YouTube 403**: IP datacenter sandbox diblokir YouTube untuk download video (403 Forbidden). **Bukan bug kode.** Fetch subtitle/auto-caption TETAP JALAN. Di mesin residential user, download hampir pasti normal. Jika user tetap kena 403: `pip install -U yt-dlp`, atau tambahkan `--cookies-from-browser chrome` di cmd yt-dlp.
- **ffmpeg bisa HILANG setelah sandbox reset** → reinstall: `sudo apt-get update && sudo apt-get install -y ffmpeg`. Klip 261 byte + ffmpeg hilang = FileNotFoundError, bukan bug kode.
- **429 Too Many Requests** kadang muncul saat fetch subtitle berulang — retry/backoff.

---

## 7. Yang Masih Tertunda (Debt dari Sesi Sebelumnya)

1. **Re-run benchmark E2E penuh** (`backend/benchmark_e2e.py "<url>" 30 3`) setelah fix `section_offset` — verifikasi 3 klip valid + subtitle burn-in. Terblokir 403 di sandbox; jalankan di mesin user.
2. **E2E Mode 2 render video riil** — analisis sudah terbukti, render final belum (403).
3. **Auto-open editor dari Mode 2** — handoff Mode2Console → ClipEditorStudio sudah sebagian (PR #38), perlu verifikasi UX penuh.
4. **Benchmark kualitas vs Opus Clip** — perbandingan output side-by-side belum dilakukan.

---

## 8. ROADMAP "Jauh di Atas Opus Clip" (Prioritas Berurutan)

### Fase A — Fondasi Kualitas (kerjakan dulu)
- [ ] **A1. E2E render nyata terverifikasi** di mesin non-sandbox (Mode 1 + Mode 2). Kriteria: 3 klip ≥1KB, subtitle burn-in benar, karaoke sync.
- [ ] **A2. Retention Heatmap masuk UI klip** (bukan hanya editor) — overlay kurva retensi di `ResultsMosaicGrid`.
- [ ] **A3. Hook Lab auto-apply**: varian hook terbaik otomatis jadi default judul, bukan manual pilih.
- [ ] **A4. Smart Cut toggle per-klip di UI** + indikator "X detik dead-air dihapus".

### Fase B — Mode 2 Universal (diferensiasi utama vs Opus)
- [ ] **B1. Voiceover TTS Bahasa Indonesia** full pipeline (`voiceover.py` + `mode2_narrator`) — narasi Hook→Kenapa→Fakta→Sisi Gelap→Mindblowing dengan suara lokal.
- [ ] **B2. B-roll lokal/stock** (`broll.py`) untuk mengisi gap visual antar-momen.
- [ ] **B3. Retry + backoff transkrip** untuk 429; fallback whisper lokal saat auto-caption absen.
- [ ] **B4. Template arketipe yang bisa dikustom user** (preset "Sisi Gelap", "Fakta", custom JSON).

### Fase C — Intelijen Distribusi
- [ ] **C1. Autopost TikTok/YT Shorts/IG** (`autopost_engine.py` + `social.py`) dengan jadwal.
- [ ] **C2. CTR feedback loop**: user input performa nyata → `predict_title_ctr` dikalibrasi (learning lokal, tetap local-first).
- [ ] **C3. Thumbnail A/B generator** (`thumbnail.py`) + skor CTR per varian.
- [ ] **C4. Trend radar**: `keyword_expander` + pencarian trending → saran keyword Mode 2 harian.

### Fase D — Skala & UX
- [ ] **D1. Job queue antrean** (saat ini konkurensi terbatas `active_count`).
- [ ] **D2. Compare view v2**: grafik retensi/CTR lintas-job (data sudah ada di `/api/jobs/compare`).
- [ ] **D3. Docker one-command install** untuk user non-teknis.
- [ ] **D4. GPU opsional** (whisper/torch CUDA) dengan deteksi otomatis, tetap graceful di CPU.

### Prinsip yang TIDAK boleh dikorbankan
- Local-first, nol biaya cloud AI wajib. LLM opsional saja (fallback deterministik harus selalu ada).
- Heavy deps lazy-import.
- Semua test harus tetap hijau setelah setiap perubahan; tambahkan test untuk setiap fitur baru.
- Versi string di 5 lokasi selalu sinkron saat bump.

---

## 9. Quick Start untuk Agen Baru

```bash
# Verifikasi cepat (2 menit)
cd backend && . .venv/bin/activate && python -m pytest tests/ -q     # harus 93+ passed
cd ../frontend && npx tsc --noEmit && npm test                        # harus 26 passed
yt-dlp --version && ffmpeg -version                                   # pastikan ada

# Jalankan
cd backend && python main.py          # :8000
cd frontend && npm run dev            # dev server

# E2E Mode 2 (di mesin residential, BUKAN sandbox):
curl -X POST localhost:8000/api/mode2/generate -H "Content-Type: application/json" \
  -d '{"keyword":"fakta menarik","voice_enabled":true,"target_duration":45,"max_sources":3}'
```

**Aturan emas:** baca `AGENTS.md` dulu, jangan sentuh job lifecycle tanpa memahami bagian 2,
jalankan kedua test suite sebelum commit, dan catat temuan baru kembali ke `AGENTS.md`.

---
*Dokumen ini dibuat 2026-08-22 berdasarkan kondisi repo V9.6.1 (branch v961-quality-compare, PR #39).*
*Perbarui dokumen ini setiap fase selesai.*
