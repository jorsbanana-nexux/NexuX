# NexuX Capability Matrix

Legend: `[+]` working/implemented evidence exists, `[~]` partial/adapter/heuristic, `[P]` planning or placeholder, `[-]` not yet present in canonical runtime.

| Domain | Capability | Current truth | Target maturity | Next proof |
|---|---|---:|---:|---|
| Ingest | YouTube acquisition | [+] | Production | multi-format failure corpus |
| Ingest | Local upload | [+] | Production | large-file/codec tests |
| Speech | Local Whisper | [+] | Production | long-duration memory benchmark |
| Speech | Word timestamps | [+] | Production | boundary corpus |
| Speech | Speaker diarization | [-] | Advanced | real multi-speaker benchmark |
| Vision | Scene detection | [+] | Advanced | 1h/6h/10h benchmark |
| Vision | Face/subject detection | [+] | Advanced | representative-face benchmark |
| Vision | Object/motion understanding | [~] | Advanced | category benchmark |
| Vision | OCR/text understanding | [-] | Advanced | screen/text corpus |
| Audio | Audio profile | [+] | Advanced | real-media benchmark |
| Audio | Filler/pause detection | [+] | Advanced | human edit comparison |
| Audio | Loudness/cleanup | [~] | Production | objective audio QA |
| Semantics | Topic/coherence | [+] | Advanced | annotated corpus |
| Semantics | Narrative signals | [+] | Advanced | human preference study |
| Editorial | Candidate generation | [+] | Advanced | Recall@K benchmark |
| Editorial | Deterministic ranking | [+] | Advanced | benchmark calibration |
| Editorial | AI rejudge | [+] | Advanced | blind A/B |
| Editorial | User intent matching | [~] | Advanced | prompt retrieval benchmark |
| Editorial | Evidence/confidence | [~] | Production | calibration test |
| Editorial | Duplicate/diversity control | [+] | Production | diversity benchmark |
| Camera | Subject-aware framing | [+] | Advanced | tracking/framing corpus |
| Camera | Multi-speaker directing | [-] | Frontier | speaker-camera benchmark |
| Camera | Motion-aware reframing | [~] | Advanced | moving-subject corpus |
| Timeline | Deterministic EDL | [+] | Production | AV drift corpus |
| Captions | Word-level captions | [+] | Production | caption accuracy benchmark |
| Captions | Smart line breaking | [+] | Advanced | readability benchmark |
| Captions | Style/animation presets | [+] | Production | visual regression |
| Editing | Filler/pause cleanup | [+] | Advanced | human preference |
| Editing | Dynamic layouts | [+] | Advanced | genre benchmark |
| Editing | Music selection/rendering | [~] | Advanced | licensed/local asset corpus |
| Editing | SFX selection/rendering | [~] | Advanced | event timing benchmark |
| Editing | B-roll | [P] policy-disabled | Optional | policy + asset pipeline |
| Voice | Voice-over | [+] optional | Advanced | naturalness/latency tests |
| Critic | Post-render critic | [+] | Advanced | known-defect corpus |
| Revision | Automatic revision execution | [~] | Advanced | defect-to-fix benchmark |
| QA | Media inspection gate | [+] | Production | corrupt-output injection |
| Jobs | Persistent job state | [+] | Production | crash/restart injection |
| Reliability | Hard cancellation | [+] | Production | interruption corpus |
| AI | External AI brain adapter | [+] optional | Advanced | provider contract tests |
| AI | Local AI brain | [-] | Advanced | local model adapter |
| Publishing | Publish plan | [+] | Production | schema contract |
| Publishing | Live platform upload | [~] | Advanced | OAuth sandbox tests |
| Analytics | Event recording | [+] | Production | event integrity tests |
| Personalization | User editorial profile | [-] | Advanced | preference acceptance study |
| Benchmark | Human reference protocol | [+] | Production | first labeled corpus |
| Benchmark | Automated leaderboard | [-] | Advanced | release benchmark runner |
| Performance | Targeted retrieval | [+] | Production | network/storage benchmark |
| Performance | Analysis reuse/cache | [~] | Advanced | call-count + timing regression |
| Hardware | CPU/GPU adaptation | [-] | Advanced | matrix across hardware |
| Security | Local API loopback | [+] | Production | bind/port regression |
| Architecture | Canonical single service boundary | [~] | Production | compatibility removal audit |
| Architecture | Legacy isolation | [+] | Production | launch-path verification |

## Highest-priority gaps

1. Canonical runtime convergence.
2. Speaker intelligence and multimodal evidence graph depth.
3. Editorial intent modeling.
4. Critic -> executable revision loop.
5. Objective benchmark runner and labeled corpus.
6. Personal editorial memory.
7. Performance/cache/hardware adaptation.
8. Real implementations for planning-only media capabilities.

## Evidence rule

No row may be promoted to `Production`, `Advanced`, or `Frontier` based only on code presence. The proof must be appropriate to the capability: deterministic tests, real-media tests, benchmark results, or blinded human evaluation.
