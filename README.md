# NexuX

Local-first AI video repurposing engine. Ubah satu video panjang (podcast, interview, webinar) menjadi klip short-form yang siap posting — berjalan sepenuhnya di mesin sendiri, tanpa biaya cloud.

**Canonical engine: `backend/main.py` (FastAPI).** Ini satu-satunya sumber kebenaran API.

## Apa yang dilakukan

- **Mode 1 — Podcast:** YouTube URL / upload → transkripsi (faster-whisper) → analisis konten → skor viral (Opus Killer, 8 dimensi) → deteksi hook → reframe 9:16 + caption → render → klip siap.
- **Mode 2 — AI Creative:** satu keyword → cari momen relevan → susun narasi → kompilasi satu video.

Prinsip: 100% pemrosesan lokal (Whisper + OpenCV + FFmpeg), tanpa B-roll otomatis, tanpa API berbayar.

## Struktur

```
nexux/
├── backend/            # FastAPI — canonical API + engine
│   ├── main.py         # entrypoint API (V9.5)
│   ├── api_v95_editor.py
│   ├── api_v95_modes.py
│   ├── engine/         # pipeline inti (transcribe, render, scoring, dsb)
│   ├── utils/          # config, logger, rate_limiter
│   ├── tests/
│   └── requirements.txt
└── frontend/           # React + Vite + Tailwind
    └── src/
```

## Menjalankan

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

## Konfigurasi

Salin `.env.example` ke `.env`. Kunci penting:

- `NEXUX_API_KEY` — kosong = tanpa auth (dev lokal). Isi untuk produksi.
- `WHISPER_MODEL` — `tiny/base/small/medium/large`.
- `NEXUX_AI_ENABLED` — `0` default (lokal penuh). Set endpoint untuk LLM opsional.

## Testing

```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm test
```

## API utama

- `POST /api/generate` → mulai job
- `GET /api/job/{job_id}` → status
- `GET /api/download/{job_id}` → hasil
- `POST /api/upload` → upload file lokal
- `WS /ws` → progress realtime

Lihat `/docs` untuk referensi lengkap.

## Lisensi

MIT
