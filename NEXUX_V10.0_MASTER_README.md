# 🚀 NexuX V10.0 — MASTER PRODUCT READMЕ & ARCHITECTURE BLUEPRINT

> **Status:** Master specification / consolidation document for the V10.0 target.
>
> **Repository:** `jorsbanana-nexux/NexuX`
>
> **Audited against:** current `main` at commit `58a993157e8a649c361b3b9bbd834a3195934125` (2026-08-21).
>
> **Purpose:** unify the product claims, canonical architecture, backend, frontend, editor, AI/editorial intelligence, verification rules, compatibility surfaces, deployment, testing, gaps, and V10.0 blueprint into one source of documentation truth.

---

## 0. EXECUTIVE VERDICT

NexuX is a local-first AI video repurposing platform whose repository currently contains **two layers that must not be conflated**:

1. **Canonical production clipping path:** the Local-First V5 architecture, exposed through the canonical backend runtime and governed by explicit contracts, deterministic editorial ranking, a single EditTimeline, FFmpeg rendering, and a render-quality gate.
2. **Expanded V9.x/V9.5 product layer:** advanced editor, virality, hook, reframe, publish/analytics, 4K, local upload, speaker isolation, dual-mode Podcast/Creative features, title generation, keyword expansion, and a large compatibility/agent surface.

V10.0 should therefore **not simply claim that every legacy agent or every README feature is already one production pipeline**. The correct V10 strategy is to preserve the V5 contract as the foundation and progressively integrate proven V9.5 capabilities through that contract.

This distinction is important because the repository's own audits explicitly state that planning-only agents are not production stages, the canonical V5 engine is the production source of truth, and commercial/superiority claims require reproducible real-world benchmarks.

---

# 1. PRODUCT IDENTITY

## 1.1 What NexuX is

NexuX is an autonomous/local-first AI video repurposing engine designed to turn long-form video into short-form, editorially selected clips. The core concept is:

`Source video → ingest → transcription → multimodal analysis → editorial ranking → deterministic timeline → camera/captions → FFmpeg → render QA → output`

The product emphasizes:

- local processing and privacy;
- minimal cloud dependency;
- explainable editorial decisions;
- targeted media retrieval rather than unnecessary full-video processing;
- multimodal intelligence combining semantic, audio, and vision signals;
- automatic reframing and captioning;
- editorial quality gates and revision loops;
- persistent jobs;
- a real React/TypeScript frontend connected to backend APIs;
- extensibility through API contracts and optional AI providers.

## 1.2 The two product modes described by V9.5

### Podcast Mode

Input: a YouTube URL for podcasts, interviews, talk shows, or similar long-form conversational content.

Target: multiple short clips, commonly around 20–90 seconds depending on the active runtime/contract.

Editorial intelligence described in V9.5 includes:

- topic segmentation;
- punchline extraction;
- heat/conflict detection;
- story-arc detection;
- Q&A pairing;
- filler-word detection;
- speaker turn-taking;
- hook detection;
- virality scoring;
- automatic titles and metadata;
- critic/revision loops;
- smart zoom and captions.

### AI Creative Mode

Input: one keyword.

Target: a multi-source compilation with generated narrative, TTS, SFX/BGM, overlays, transitions, and metadata.

The documented flow is:

`Keyword → keyword expansion → YouTube multi-source search → transcript analysis → relevant moments → narrative generation → partial download → compilation → TTS/SFX/transitions → metadata → quality scoring`

**V10.0 policy:** Creative Mode remains an expanded generation pipeline and must not silently be treated as identical to the canonical no-B-roll V5 clipper. Network-backed TTS or optional LLM calls must be explicitly surfaced as optional/non-local capabilities.

---

# 2. CANONICAL V10.0 ARCHITECTURE

The V10.0 architecture is based on the existing Architecture Contract:

```text
SOURCE
  ↓
INGEST / METADATA
  ↓
LOCAL TRANSCRIPTION
  ↓
ANALYSIS BUNDLE
  ├── semantic signals
  ├── audio signals
  ├── vision / scene signals
  ├── subject observations
  └── diarized transcript when available
  ↓
EDITORIAL RANKING
  ↓
EDIT TIMELINE / SMART EDL
  ↓
CAMERA + REFRAME + CAPTIONS + AUDIO PLAN
  ↓
FFMPEG COMPOSITOR
  ↓
RENDER QA
  ↓
PERSISTED OUTPUT ARTIFACT
  ↓
EDITOR / DOWNLOAD / PUBLISH / ANALYTICS
```

### Non-negotiable V10 invariants

| Invariant | V10 rule |
|---|---|
| Local-first | Canonical clipping must not require paid cloud AI |
| No B-roll | Canonical clipper never fetches, creates, synthesizes, or inserts B-roll |
| One job identity | Every artifact belongs to one persistent job ID |
| One timeline | Video/audio/camera/captions derive from the same EditTimeline |
| One renderer | FFmpeg is the canonical compositor |
| One QA gate | A render cannot become completed before media inspection passes |
| UI independence | UI may evolve without changing engine contracts |
| Deterministic core | Core clipping decisions remain reproducible from the same inputs/configuration |
| No synthetic success | Planning/placeholder modules cannot report completed media operations |
| Evidence-first claims | Product claims must distinguish implemented, verified, benchmarked, and aspirational behavior |

---

# 3. SYSTEM COMPONENT MAP

| Layer | Current repository surface | V10.0 role | Status |
|---|---|---|---|
| Canonical backend | `nexus-clipper/backend` | Main production API/runtime | **Canonical** |
| Local-First V5 | `nexus-clipper/local-first-v5` | Contract, quality gate, deterministic clipping foundation | **Canonical foundation** |
| Legacy agents | `backend/agents` | Compatibility/utility surface | **Not all production** |
| Frontend | `nexus-clipper/frontend` | React 19 application | **Canonical UI** |
| Frontend contract | `frontend-contract` | API/type contract | **Canonical contract surface** |
| V9.5 APIs | `api_v90_*`, `api_v95_*`, related modules | Advanced feature adapters | **Integrated where mounted/verified** |
| SQLite | job persistence | Persistent local jobs | **Implemented** |
| FFmpeg | media compositor | Single canonical renderer | **Implemented** |
| faster-whisper | transcription fallback | Local transcription | **Implemented** |
| OpenCV / MediaPipe | vision | face/subject/scene intelligence | **Implemented in canonical/adapter paths** |
| yt-dlp | source acquisition | YouTube metadata/download/search | **Implemented** |
| edge-tts | generated voice | Creative/optional voice-over | **Implemented but network-backed** |
| LLM providers | OpenAI/Anthropic/Gemini env options | Optional narrative intelligence | **Optional** |
| GitHub Actions | `.github/workflows/local-first-v5.yml` | CI quality gate | **Implemented** |
| Docker | Dockerfile / compose | Deployment packaging | **Implemented for V9.5 surface** |

---

# 4. BACKEND / ENGINE CAPABILITY MATRIX

The repository documents a broad engine surface. The following table separates capability from production status rather than treating every filename as proof of production behavior.

| Capability | Function | V10.0 position |
|---|---|---|
| Source acquisition | yt-dlp / local file support | Core |
| Metadata probing | ffprobe | Core |
| Section retrieval | targeted FFmpeg cuts | Core |
| Audio extraction | local FFmpeg extraction | Core |
| Transcription | faster-whisper / captions fast path | Core |
| Diarization | WhisperX-supported paths | Advanced |
| Semantic analysis | transcript/editorial signals | Core |
| Audio analysis | speech/audio profiles | Core, ranking integration still to harden everywhere |
| Scene detection | vision scanner | Core |
| Subject analysis | candidate-window subject observations | Core/adapter |
| Face tracking | OpenCV/MediaPipe | Core |
| Auto reframe | subject-aware framing | Core |
| Hook detection | multilingual hook archetypes | Advanced |
| Editorial ranking | deterministic multi-signal selection | Core |
| Virality scoring | transparent heuristic dimensions | Advanced |
| Retention prediction | drop-off heuristic | Advanced/benchmark required |
| Shareability | quotability/meme potential | Advanced/benchmark required |
| Competitor delta | score comparison language | Presentation only unless benchmarked |
| Critic | quality verdict/revision loop | Core/advanced |
| Render | FFmpeg compositor | Core |
| Render QA | media inspection | Core |
| Captions | kinetic/animated caption engine | Core |
| Subtitle QA | CPS/WPM/line checks | Advanced |
| Audio enhancement | ducking/EQ/loudness | Core/advanced |
| 4K export | UHD preset | Verified in V9.5 code/tests |
| Local upload | `POST /api/upload` + `local://` | Verified |
| Speaker isolation | mute/isolate via FFmpeg filters | Verified |
| Editor preview | FFmpeg preview renderer | Verified |
| Overlay burn-in | FFmpeg drawtext | Verified |
| Rerender | personalized rerender pipeline | Advanced |
| Repair system | diagnostics + auto-fix | Verified by repository comparison doc; benchmark still needed |
| Autopost | platform adapters | Advanced; scheduler/UI incomplete |
| Analytics | virality/analytics endpoints | Advanced; not equivalent to platform analytics |
| Thumbnail generation | module exists | UI incomplete |
| Creative narrative | LLM/fallback | Optional generation mode |
| TTS | edge-tts | Optional/network-backed |
| SFX/BGM planning | sound/music modules | Some surfaces are planning-only |
| Transition planning | transition labels | Not a canonical renderer feature until connected |

---

# 5. 25-AGENT MATRIX — TRUTH TABLE

The repository itself explicitly warns that an agent returning a dictionary is not automatically production-integrated. V10.0 keeps this distinction.

| # | Agent | Current documented truth | V10.0 classification |
|---:|---|---|---|
| 01 | Master Brain | Orchestration shell; does not execute V5 pipeline | Compatibility |
| 02 | URL Fetcher | Real yt-dlp downloader/validator | Useful adapter |
| 03 | Keyword Optimizer | Deterministic keyword expansion | Creative/metadata utility |
| 04 | Content Planner | Generated-script planning | Creative utility |
| 05 | Competitor Analyzer | Static heuristic; no competitor ingestion | Not production intelligence |
| 06 | Narration Writer | Generates synthetic narration text | Creative utility |
| 07 | Voice Cloner | edge-tts network synthesis | Optional/non-local |
| 08 | Emotion Controller | Keyword-based emotion mapping | Candidate enrichment |
| 09 | Spatial 8D Audio | Metadata-only placeholder | Disabled |
| 10 | Breath Injector | Returns injection points | Planning-only |
| 11 | Scene Segmenter | Real media-backed adapter | Compatibility over V5 vision |
| 12 | Subject Tracker | Real media-backed observations | Compatibility over V5 vision |
| 13 | Visual Quality Checker | Real media-backed inspection | Compatibility over V5 QA |
| 14 | Lip Sync | GPU placeholder | Disabled |
| 15 | B-roll Blocker | Real policy guard | Active guard |
| 16 | Subtitle Designer | SRT/text metadata builder | V5 renderer remains canonical |
| 17 | Sound Designer | SFX plan only | Disabled until real local assets/render connected |
| 18 | Music Selector | Genre/ducking plan only | Disabled until real local source |
| 19 | Transition AI | Transition labels only | Disabled until timeline transforms exist |
| 20 | Professional Editor | Legacy compatibility wrapper | Isolated from canonical rendering |
| 21 | Quality Inspector | Real post-render inspection adapter | Compatibility over V5 QA |
| 22 | Audience Predictor | Static heuristic | V5 scorer remains canonical |
| 23 | Auto Improver | Retry decision only | Disabled until concrete transform |
| 24 | Omni Exporter | Export plans only | V5 export path canonical |
| 25 | SEO Generator | Metadata template utility | Optional |

### V10.0 integration rule

No agent is promoted to **production stage** merely because its module imports successfully. Promotion requires:

1. a concrete artifact;
2. a declared input/output contract;
3. real media evidence where applicable;
4. deterministic or controlled behavior;
5. integration into the canonical timeline/pipeline;
6. regression tests;
7. quality-gate coverage.

---

# 6. EDITORIAL INTELLIGENCE

## 6.1 Canonical ranking signals

The canonical editorial ranker is local and deterministic. Documented signals include:

- hook strength;
- payoff strength;
- context completeness;
- standalone quality;
- specificity;
- novelty;
- topic coherence;
- pacing;
- scene-boundary alignment;
- diversity;
- repetition penalties.

## 6.2 V9.5 Opus Killer dimensions

The V9.5 documentation describes an eight-dimensional scoring concept covering:

1. hook power;
2. virality;
3. editorial quality;
4. conversation flow;
5. retention curve;
6. shareability;
7. technical quality;
8. competitor delta.

V10.0 treats these as **explainable scoring dimensions**, not proof of superiority over a commercial product. The repository's own benchmark protocol requires matched-source, human-rated evaluation before superiority claims.

## 6.3 Hook intelligence

The V9.5 documentation reports multilingual hook archetypes and automatic opening adjustment. The verified comparison describes nine archetypes and an automatic shift window of up to five seconds. Exact count may vary between older documentation revisions, so V10.0 should expose the actual runtime registry rather than hard-code a marketing number.

---

# 7. CAPTION / SUBTITLE SYSTEM

| Capability | V10.0 target |
|---|---|
| Kinetic typography | Supported |
| Word-by-word emphasis | Supported |
| Active-word glow/progress | Supported |
| Speaker colors | Supported where diarization exists |
| Emoji injection | Supported in V9.5 surface |
| Creator presets | 32 presets explicitly verified in V9.5 comparison |
| Subtitle QA | CPS/WPM/line validation |
| Inline transcript correction | Editor-supported |
| Cut-boundary remapping | Canonical boundary-safe preparation |
| No fake transcript data | Mandatory |

The frontend integration contract explicitly bans mock production data, fake progress timers, fabricated metrics, and hardcoded output paths.

---

# 8. VIDEO / VISION SYSTEM

NexuX combines:

- scene-change detection;
- face/subject observations;
- MediaPipe/OpenCV tracking;
- auto-reframing;
- multiple aspect ratios;
- screen-share/gameplay detection;
- candidate-window analysis;
- render-time visual QA.

Documented aspect-ratio support includes 9:16, 1:1, 16:9, 4:5, 2:3, 21:9, and 3:4 in the V9.5 comparison surface.

V10.0 must preserve the integrity rule that subject coordinates, scene timestamps, and quality scores cannot be fabricated or hard-coded.

---

# 9. AUDIO SYSTEM

Documented audio capabilities include:

- EBU R128 loudness normalization;
- ducking;
- EQ;
- bass enhancement in rerender surfaces;
- speaker mute/isolation;
- filler-word detection/marking;
- local audio extraction;
- optional TTS narration;
- optional SFX/BGM planning.

Important limitation: the forensic audit states that `normalize_audio` remains a compatibility request field and does not yet control a fully explicit normalization stage in every runtime surface. V10.0 should close that contract gap instead of claiming universal audio normalization.

---

# 10. FRONTEND ARCHITECTURE

The canonical frontend is the React 19 + TypeScript + Tailwind v4 application under `nexus-clipper/frontend`.

The frontend integration audit records the removal of the previous React 18/JSX/Tailwind v3 frontend and consolidation into the React 19 codebase.

### Main UI concepts

- `SpaceshipConsole` — generation and job control;
- `ProcessingLoadingState` — real backend progress;
- `ResultsMosaicGrid` — dynamic result presentation;
- `ClipEditorStudio` — post-render personalization/editor;
- `TimelineEditorStudio` — timeline/filmstrip/waveform/speaker editing;
- error boundary / crash protection;
- API client via `nexuxApi.ts`;
- V9.5 mode selector and V2 API client;
- editor helpers/tests.

### Frontend package baseline

| Package | Current repository declaration |
|---|---|
| React | `^19.0.1` |
| React DOM | `^19.0.1` |
| Vite | `^6.2.3` |
| TypeScript | `~5.8.2` |
| Tailwind | `^4.1.14` |
| Motion | `^12.23.24` |
| GSAP | `^3.15.0` |
| Lenis | `^1.3.26` |
| Lucide React | `^0.546.0` |
| Vitest | `^4.1.11` |

---

# 11. FRONTEND ↔ BACKEND CONTRACT

The integration contract documents these endpoints as core frontend surfaces:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/styles` | Styles/aspect ratios |
| POST | `/api/generate` | Start generation |
| GET | `/api/job/{job_id}` | Job polling |
| GET | `/api/jobs` | Job listing |
| DELETE | `/api/job/{job_id}` | Cancellation |
| GET | `/api/vision/{job_id}` | Vision bundle |
| GET | `/api/render-qa/{job_id}` | Render QA |
| GET | `/api/critic/{job_id}` | Critic/revision state |
| GET | `/api/publish/{job_id}` | Publish plan |
| POST | `/api/publish/{job_id}/{platform}` | Platform publish |
| GET | `/api/analytics/{job_id}` | Analytics |
| GET | `/api/download/{job_id}` | Download outputs |

V9.x/V9.5 adds advanced endpoint families for virality, hooks, reframe, analytics v2, rerender, repair, previews, caption quality, modes, keyword expansion, editor operations, upload, and related capabilities.

The repository's historical commits report **42 total routes** at one V9.0 integration checkpoint and later documentation reports **39+ / 50** depending on the revision/surface being counted. V10.0 must expose the actual OpenAPI/runtime route inventory at build time instead of maintaining a manually copied marketing count.

---

# 12. V9.5 DUAL-MODE API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v2/modes` | Enumerate modes/features |
| POST | `/api/v2/generate` | Start mode-aware generation |
| GET | `/api/v2/keyword/expand` | Preview keyword expansion |
| GET | `/api/v2/modes/{mode}/features` | Mode capabilities |

### Podcast request concept

```json
{
  "mode": "podcast",
  "youtube_url": "https://youtube.com/watch?v=...",
  "target_duration": 45,
  "clip_count": 5
}
```

### Creative request concept

```json
{
  "mode": "creative",
  "keyword": "peter parker",
  "voice_enabled": true,
  "voice_name": "id-ID-ArdiNeural",
  "target_duration": 60
}
```

V10.0 should preserve these concepts while routing every generated artifact through explicit contracts and QA.

---

# 13. VERIFIED V9.5 CAPABILITIES

The latest repository commit specifically records automated tests and verification around:

| Feature | Verification state in latest V9.5 work |
|---|---|
| Local upload | Tested via TestClient and local token flow |
| 4K/UHD math | Tested |
| Local pipeline helpers | Tested: metadata, section cut, audio extraction |
| Speaker filter strings | Tested |
| Critic robustness | Tested |
| Frontend upload client | Tested |
| Editor speaker helpers | Tested |
| Editor transcript helpers | Tested |
| TypeScript | Clean in reported V9.5 verification |
| Backend tests | 41/41 pass in the latest V9.5 commit message |
| Frontend tests | 13/13 pass in the latest V9.5 commit message |
| Earlier broader suite | 73/73 pass in an earlier quality-gate repair checkpoint |

These are repository-reported test results at the relevant commits, not a claim that every real-world video format has been exhaustively tested.

---

# 14. OPUS CLIP COMPARISON — HONEST VERSION

The repository contains a detailed V9.5 comparison. V10.0 keeps the useful engineering comparison but rejects unsupported equivalence language.

| Dimension | NexuX documented capability | V10.0 evidence policy |
|---|---|---|
| Cost | Local/free software architecture | Hardware/runtime cost still exists |
| Privacy | Local-first canonical processing | Must remain true for canonical mode |
| Transcription | Local faster-whisper | Code/dependency verified |
| Targeted retrieval | Relevant sections only | Core |
| Virality score | Multi-dimensional heuristic | Must not be presented as platform truth |
| Critic loop | Automatic revision capability | Must pass render QA |
| Captions | Kinetic + presets | Implemented surfaces |
| Reframe | OpenCV/MediaPipe | Implemented |
| 4K | UHD rendering path | Verified |
| Local upload | `POST /api/upload` | Verified |
| Speaker isolation | Mute/isolate | Verified |
| Editor | Timeline/clip editor | Implemented surface |
| Autopost | Adapters | Scheduler/profile completeness still incomplete |
| Analytics | Prediction/collection | Not equivalent to native platform analytics |
| XML export | Not implemented | V10 target gap |
| Share links | Not implemented | V10 target gap |
| MCP/Zapier | Not implemented | V10 target gap |
| Enterprise SSO | Not implemented | V10 target gap |
| AI speech cleanup | Incomplete | V10 target gap |

### Critical wording rule

Do not state "NexuX beats Opus Clip" as a measured universal fact. The repository's own benchmark protocol says superiority requires a published corpus, matched source inputs, predeclared metrics, and statistically meaningful human preference results.

The strongest defensible current statement is:

> **NexuX is a feature-rich, local-first AI video repurposing system with an unusually broad editable, explainable, and privacy-oriented architecture; comparative superiority remains a benchmark question.**

---

# 15. PRIVACY / LOCAL-FIRST MODEL

## Canonical clipper

The canonical V5 architecture is designed to operate without paid cloud AI. Core processing uses local media/ML tools such as FFmpeg, faster-whisper, OpenCV, MediaPipe and deterministic editorial logic.

## Network boundaries

Network access may still be required for source acquisition through yt-dlp. Optional V9.5 Creative functionality can also use network-backed edge-TTS and optional LLM providers.

Therefore V10.0 uses three explicit modes of dependency labeling:

| Label | Meaning |
|---|---|
| LOCAL | Runs locally with no paid cloud AI requirement |
| NETWORK | Requires external network access but not necessarily paid AI |
| OPTIONAL-CLOUD | Uses an optional external AI provider |

No UI may imply that a network-backed capability is offline.

---

# 16. PERSISTENCE / RELIABILITY

NexuX uses SQLite for persistent job state in the local-first architecture. The audits also report hard cancellation, persistent jobs, worker isolation, analysis-bundle contracts, and render QA as implemented areas that require target-machine evidence for launch confidence.

The forensic audit records fixes for:

1. queued cancellation race;
2. local API accidentally binding to `0.0.0.0` instead of loopback;
3. frontend/backend duration mismatch;
4. language parameter not reaching Whisper;
5. incomplete quality-gate dependency/module coverage;
6. frontend missing from CI;
7. missing automatic main-branch V5 validation.

These fixes should be treated as part of the V10 reliability baseline.

---

# 17. CI / QUALITY GATE

The repository currently contains a GitHub Actions workflow that runs on relevant pushes to `main`, pull requests, and manual dispatch.

The workflow includes:

- Python 3.11 setup;
- FFmpeg installation;
- local-first and backend dependency installation;
- canonical backend import/compile verification;
- legacy shim import verification;
- V5 module compilation;
- legacy backend/root-builder compilation;
- frontend contract presence check;
- deterministic V5 pytest suite;
- local V5 quality gate;
- frontend `npm ci`;
- frontend production build.

### V10 CI expansion blueprint

```text
CI
├── Backend syntax/type/import gate
├── Canonical contract gate
├── Deterministic unit tests
├── Integration/API tests
├── Frontend typecheck
├── Frontend unit tests
├── Production build
├── OpenAPI route inventory check
├── No-B-roll invariant check
├── Artifact schema regression
├── Render QA fixtures
├── Security / secret scanning
└── Release evidence manifest
```

---

# 18. INSTALLATION BASELINE

## Backend

```bash
cd nexus-clipper/backend
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
# venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

Backend is intended for `http://127.0.0.1:8000` in local-first operation.

## Frontend

```bash
cd nexus-clipper/frontend
npm install
npm run dev
```

Development frontend is intended for port 3000.

## Environment

The frontend contract uses:

```env
VITE_NEXUX_API_URL=http://127.0.0.1:8000
```

Optional AI provider variables described in the V9.5 documentation include OpenAI, Anthropic, and Gemini keys for Creative narrative generation. These are optional and are not required by the canonical local-first clipping core.

---

# 19. DEPENDENCY BASELINE

| Dependency | Role | Classification |
|---|---|---|
| FastAPI | Backend API | Core |
| Uvicorn | ASGI server | Core |
| Pydantic | Validation | Core |
| pydantic-settings | Configuration | Core |
| yt-dlp | Source acquisition | Core |
| faster-whisper | Local transcription | Core fallback |
| CTranslate2 | Whisper runtime | Core transcription support |
| OpenCV | Vision | Core |
| MediaPipe | Face/subject tracking | Core/vision |
| NumPy | Numerical processing | Core |
| Torch | ML backend | Core for Whisper stack |
| edge-tts | TTS | Optional generation |
| httpx | HTTP client | Core/utility |
| psutil | System monitoring | Utility |
| pytest | Testing | Dev/CI |
| React 19 | UI | Core frontend |
| Vite | Build | Core frontend |
| Tailwind 4 | Styling | Core frontend |
| Motion | Animation | UI |
| GSAP | Animation | UI |
| Lenis | Smooth scrolling | UI |
| Lucide | Icons | UI |
| Vitest | Frontend testing | Dev/CI |

---

# 20. V10.0 BLUEPRINT — TARGET STATE

## Phase A — Contract consolidation

- Make canonical API the sole public runtime surface.
- Generate route inventory from the running FastAPI app.
- Define one versioned job schema.
- Define one Analysis Bundle schema.
- Define one EditTimeline schema.
- Define one Render Artifact schema.
- Remove ambiguity between legacy and canonical launch paths.

## Phase B — Intelligence fusion

Integrate proven V9.5 capabilities into the canonical Analysis Bundle:

```text
Analysis Bundle
├── transcript
├── diarization
├── scene boundaries
├── subject observations
├── audio profile
├── hook candidates
├── editorial candidates
├── retention signals
├── shareability signals
├── technical quality
└── evidence/provenance
```

## Phase C — Editorial intelligence

Build one scoring layer that can expose both:

- deterministic editorial rank;
- optional V9.5 virality dimensions;
- evidence for every score;
- penalties and reasons;
- diversity constraints;
- benchmark telemetry.

## Phase D — Autonomous editing

```text
Candidate set
  ↓
Editorial judge
  ↓
Best candidate set
  ↓
EditTimeline
  ↓
Camera/reframe
  ↓
Caption layout
  ↓
Audio plan
  ↓
Render
  ↓
QA
  ↓
If failed → bounded revision
  ↓
If passed → artifact
```

## Phase E — Professional editor

V10.0 target:

- timeline editing;
- waveform;
- speaker lanes;
- transcript correction;
- drag/resize/rotate text;
- layer management;
- undo/redo;
- version history;
- preview render;
- speaker mute/isolation;
- snap/grid;
- render queue;
- safe rerender.

## Phase F — Creative Mode isolation

Creative Mode becomes a clearly separated orchestration graph:

```text
Keyword
 → expansion
 → source search
 → candidate extraction
 → narrative plan
 → optional TTS
 → optional SFX/BGM
 → compilation timeline
 → render QA
```

It must never weaken the canonical no-B-roll clipping invariant.

## Phase G — Release engineering

Add:

- reproducible release manifest;
- benchmark report;
- route manifest;
- dependency lock verification;
- security checks;
- real-media corpus tests;
- platform matrix;
- performance baseline;
- upgrade/migration notes.

---

# 21. V10.0 FEATURE PRIORITY TABLE

| Priority | Feature | Reason |
|---|---|---|
| P0 | Canonical runtime consolidation | Prevent architectural ambiguity |
| P0 | Real-media E2E corpus | Prove actual reliability |
| P0 | Unified job/timeline/artifact contracts | Prevent cross-surface drift |
| P0 | Render QA hardening | Protect output correctness |
| P0 | OpenAPI route inventory | Eliminate endpoint-count drift |
| P0 | Security/secret boundary audit | Protect local deployments |
| P1 | Full V9.5 intelligence fusion | Bring advanced features into canonical flow |
| P1 | Audio-profile ranking integration | Close known forensic gap |
| P1 | Speech cleanup | Improve professional output |
| P1 | Scheduler UI | Complete publishing workflow |
| P1 | Thumbnail UI | Complete packaging workflow |
| P1 | Asset upload library | Enable controlled creative editing |
| P1 | XML export | Professional NLE interoperability |
| P2 | Dubbing | Multi-language expansion |
| P2 | Team collaboration | Multi-user workflows |
| P2 | Share links | Review workflows |
| P2 | MCP integration | Agent/tool interoperability |
| P2 | Zapier integration | Automation ecosystem |
| P2 | Enterprise SSO | Enterprise deployment |
| P2 | SOC 2 program | Enterprise trust/compliance |

---

# 22. KNOWN GAPS — DO NOT HIDE

The repository's own V9.5 comparison identifies these real gaps:

1. AI speech enhancement / cleanup;
2. scheduler UI;
3. team collaboration;
4. XML export for Premiere/DaVinci workflows;
5. thumbnail UI;
6. AI voice-over dubbing;
7. enterprise SSO/SOC II-level compliance;
8. full transition editor rather than gallery/planning-only surfaces;
9. uploadable media-asset library.

The forensic audit additionally identifies:

- duplicated `app.py` / `server.py` concerns;
- legacy placeholder/compatibility agents;
- incomplete explicit audio-normalization control;
- audio-profile signals not fully incorporated into every ranking surface;
- need for real target-machine E2E testing;
- inability of deterministic tests alone to prove editorial superiority.

These are V10 roadmap items, not reasons to discard the product.

---

# 23. VERIFICATION POLICY

NexuX V10.0 uses four evidence levels:

| Level | Meaning |
|---|---|
| L0 — Documented | Mentioned in README/spec |
| L1 — Implemented | Concrete code path exists |
| L2 — Automated | Tests/CI exercise it |
| L3 — Real-world validated | Real media / target environment evidence |

A feature should only be called **production-ready** when it reaches the required level for its risk class. Editorial superiority claims require L3 benchmark evidence.

### Benchmark protocol

The repository defines a strong benchmark model using:

- stratified real-video corpus;
- podcasts/interviews/lectures/tutorials/commentary/gaming/vlogs/news/multi-speaker/difficult audio;
- 3–10 human-selected clip intervals per source;
- at least three independent editors per source;
- Top-1 IoU;
- Recall@K;
- mean best IoU;
- duration compliance;
- diversity;
- blinded human preference;
- editorial failure rate.

Required comparisons:

1. deterministic baseline;
2. human-selected reference set;
3. commercial product only under matched-source/blinded conditions.

---

# 24. RELEASE GATE FOR NEXUX V10.0

V10.0 should not be declared complete until the following are green:

- [ ] canonical API is the single documented public runtime;
- [ ] backend/frontend contracts are generated or cross-validated;
- [ ] all advertised routes exist and are tested;
- [ ] all advertised core features have implementation evidence;
- [ ] no production path relies on mock data;
- [ ] no fake progress timers exist;
- [ ] no fabricated metrics exist;
- [ ] no B-roll is inserted in canonical mode;
- [ ] every output has a persistent job identity;
- [ ] every render passes render QA;
- [ ] cancellation is safe across download/transcription/render stages;
- [ ] restart/crash recovery is tested;
- [ ] local API binds safely;
- [ ] target duration contracts are consistent end-to-end;
- [ ] language settings reach transcription;
- [ ] frontend typecheck passes;
- [ ] frontend tests pass;
- [ ] backend tests pass;
- [ ] CI validates main branch;
- [ ] real-media E2E corpus passes agreed thresholds;
- [ ] benchmark report exists before superiority claims;
- [ ] licensing statement is consistent across repository documentation.

---

# 25. DOCUMENTATION TRUTH RULES

The repository currently contains historical documentation from V5 through V9.5. V10.0 documentation must stop version drift by labeling each statement:

- **CANONICAL** — part of the current production contract;
- **VERIFIED** — proven by automated tests or direct code verification;
- **OPTIONAL** — available but not required for core operation;
- **COMPATIBILITY** — retained for migration/legacy support;
- **ROADMAP** — planned but not yet production;
- **BENCHMARK-REQUIRED** — implemented heuristic whose quality claim needs real-world evidence.

No marketing copy may promote a roadmap/placeholder module as a completed production feature.

---

# 26. REPOSITORY STRUCTURE — MASTER VIEW

```text
NexuX/
├── README.md                         # Existing V9.5 public README
├── NEXUX_V10.0_MASTER_README.md      # This unified V10.0 master document
├── V95_UPGRADE.md                    # V9.5 feature history
├── COMPARISON_OPUS_CLIP.md           # Verified comparison / gap analysis
├── build_nexus.py                    # Legacy/build tooling
├── install_nexus.bat                 # Windows installer tooling
├── .env.example
├── .github/
│   └── workflows/
│       └── local-first-v5.yml        # CI quality gate
└── nexus-clipper/
    ├── backend/                      # Canonical current backend surface
    │   ├── main.py
    │   ├── engine/
    │   ├── agents/                   # Compatibility/utility agent matrix
    │   ├── tests/
    │   └── requirements.txt
    ├── frontend/                     # React 19 + TypeScript + Tailwind 4
    │   ├── src/api/
    │   ├── src/components/
    │   ├── src/test/
    │   └── package.json
    ├── frontend-contract/            # API contract
    ├── local-first-v5/               # Canonical architecture + quality gate
    │   ├── canonical_api.py
    │   ├── server.py
    │   ├── app.py
    │   ├── quality_gate.py
    │   ├── requirements-local.txt
    │   ├── tests/
    │   └── architecture/benchmark docs
    ├── Dockerfile
    └── docker-compose.yml
```

---

# 27. FINAL V10.0 POSITION

NexuX already has the ingredients of a serious local-first video intelligence platform:

- a canonical deterministic clipping architecture;
- local transcription;
- multimodal analysis;
- editorial ranking;
- subject-aware framing;
- kinetic captions;
- FFmpeg rendering;
- render QA;
- persistence;
- cancellation/reliability work;
- real React 19 frontend integration;
- advanced editor surfaces;
- 4K output;
- local uploads;
- speaker isolation;
- virality/hook/reframe/analytics/repair capabilities;
- Podcast and Creative concepts;
- a large compatibility-agent ecosystem;
- automated CI and tests.

The correct V10.0 move is **not to add more disconnected features**. It is to turn the current breadth into one coherent, evidence-backed system:

> **One API. One job model. One analysis bundle. One editorial brain. One EditTimeline. One renderer. One QA gate. One frontend contract. One evidence system.**

That is the V10.0 architecture that can turn the current collection of V5/V8/V9/V9.5 capabilities into a unified product rather than a collection of historical layers.

---

## SOURCE / VERIFICATION BASIS

This master document was consolidated from the repository's current `main` state and the repository's own documentation/audit artifacts, including:

- root `README.md`;
- `V95_UPGRADE.md`;
- `COMPARISON_OPUS_CLIP.md`;
- `nexus-clipper/README.md`;
- `AGENT_MATRIX_AUDIT.md`;
- `ARCHITECTURE_CONTRACT.md`;
- `FORENSIC_AUDIT_2026-08-15.md`;
- `FRONTEND_INTEGRATION.md`;
- `GOD_TIER_READINESS.md`;
- `BENCHMARK_PROTOCOL.md`;
- `EDITORIAL_RANKING.md`;
- current GitHub Actions workflow;
- current frontend `package.json`;
- current backend `requirements.txt`;
- latest V9.5 commit/test evidence.

**Audit timestamp:** 2026-08-21.

**Important:** this document is a V10.0 master specification and verification-aware consolidation. It does not retroactively make an unimplemented feature implemented, and it does not convert a heuristic benchmark into proof of commercial superiority.
