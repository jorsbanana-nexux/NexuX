# NexuX V9.5 — Opus Clip Killer Upgrade

## Apa Yang Baru?

NexuX V9.5 menambahkan 6 modul baru yang membuat NexuX mengalahkan Opus Clip dengan 2 mode: **Podcast** dan **AI Creative**.

## 2 Mode

### Mode 1 — Podcast (🎙️)
- Input: YouTube URL (podcast, wawancara, talk show)
- Output: Multiple viral clips (20-90 detik)
- **Podcast Analyzer** baru: topic segmentation, punchline extraction, heat/conflict detection, story arc detection, Q&A pairing, filler word detection
- **Opus Killer scoring**: 8-dimension analysis (hook power, virality, editorial, conversation flow, retention curve, shareability, technical quality, competitor delta)
- **Clip Titler**: auto-generate 5 judul viral per clip (8 archetype templates, bilingual EN+ID)
- Hook detection (8 archetypes) dengan auto-shift untuk dapat opening terbaik
- Editorial critic dengan revision loop (GOLD/ACCEPTABLE/NEEDS_REVISION/REJECT)
- Face tracking, auto-reframe, smart zoom, animated captions

### Mode 2 — AI Creative (✨)
- Input: Satu keyword (contoh: "peter parker", "game terbaik 2026")
- Output: Satu video kompilasi viral dengan narasi TTS
- **Keyword Expander** baru: expand 1 keyword → 15+ search terms (synonyms, trending suffixes, question formats, niche modifiers, bilingual EN+ID)
- Multi-source YouTube search (10+ videos, deduplicate channels for diversity)
- Partial download (hanya momen relevan, bukan full video)
- LLM narrative generation (hook → buildup → payoff, Indonesian)
- TTS narration (edge-tts, Indonesian + English voices)
- SFX + background music + text overlays + transitions
- Auto thumbnail, viral titles, hashtags, SEO description
- Opus Killer scoring untuk quality assessment

## File Baru (6 modul)

| File | Fungsi |
|------|--------|
| `engine/opus_killer.py` | Unified 8-dimension scoring engine |
| `engine/podcast_analyzer.py` | Podcast-specific clip detection |
| `engine/clip_titler.py` | Auto viral title + hashtag + description generator |
| `engine/keyword_expander.py` | Keyword → 15+ search terms expansion |
| `engine/mode_router.py` | Clean mode selection & validation |
| `engine/mode2_enhanced.py` | Enhanced Mode 2 with keyword expansion + auto-titling |
| `api_v95_modes.py` | New API endpoints (/api/v2/*) |

## File Frontend Baru

| File | Fungsi |
|------|--------|
| `src/components/ModeSelector.tsx` | Dual-mode selection UI |
| `src/api/v2Api.ts` | V2 API client (mode-aware) |

## File Updated

| File | Perubahan |
|------|----------|
| `engine/__init__.py` | Export modul-modul baru V9.5 |

## API Endpoints Baru

```
GET  /api/v2/modes           → List semua mode + features
POST /api/v2/generate        → Start generation (auto-detect mode)
GET  /api/v2/keyword/expand  → Preview keyword expansion
GET  /api/v2/modes/{mode}/features → Detail mode
```

## Cara Pakai

### Mode 1 (Podcast)
```bash
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "podcast",
    "youtube_url": "https://youtube.com/watch?v=...",
    "target_duration": 45,
    "clip_count": 5
  }'
```

### Mode 2 (Creative)
```bash
curl -X POST http://127.0.0.1:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "creative",
    "keyword": "peter parker",
    "voice_enabled": true,
    "voice_name": "id-ID-ArdiNeural",
    "target_duration": 60
  }'
```

### Preview Keyword Expansion
```bash
curl "http://127.0.0.1:8000/api/v2/keyword/expand?keyword=game+terbaik"
```

## Kenapa NexuX V9.5 > Opus Clip

| Feature | Opus Clip | NexuX V9.5 |
|---------|-----------|------------|
| Biaya | $19-39/bln | Free forever |
| Privacy | Cloud upload | 100% lokal |
| Hook Detection | ~3 pattern | 8 archetype |
| Virality Scoring | Black box 1 angka | 8 dimensi transparent |
| Conversation Flow | ❌ | ✅ Speaker turn-taking |
| Retention Curve | ❌ | ✅ Dropoff prediction |
| Shareability | ❌ | ✅ Quotability + meme potential |
| Competitor Delta | ❌ | ✅ "Beats Opus by X pts" |
| Podcast Mode | Generic | Topic segmentation + punchlines |
| Creative Mode | ❌ (no keyword mode) | ✅ Multi-source compilation |
| Auto Titles | Basic | 8 archetype, 5 variations, bilingual |
| Keyword Expansion | ❌ | ✅ 15+ terms (synonyms, trending, Q&A) |
| B-Roll | Stock footage | B-roll free (authenticity) |
| Job Persistence | Cloud storage | SQLite (survives restarts) |
| Customization | Limited | Full source code |

## Setup

Untuk menjalankan NexuX V9.5:

```bash
# 1. Clone & setup backend
cd nexus-clipper/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env

# 2. Start backend
python main.py

# 3. Setup frontend (terminal baru)
cd nexus-clipper/frontend
npm install
npm run dev

# 4. Buka http://localhost:3000
```

## Integrasi ke main.py

Untuk mengaktifkan endpoint V2 di main.py, tambahkan:

```python
from api_v95_modes import router as v2_router
app.include_router(v2_router)
```

## Dependencies

Tidak ada dependency baru — semua modul V9.5 menggunakan library yang sudah ada di requirements.txt:
- FastAPI (API endpoints)
- FFmpeg/ffprobe (technical quality check)
- Standard library (re, dataclasses, logging, typing)
