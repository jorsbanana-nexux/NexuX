# NexuX Local-First V5

Zero-cost, local-first automatic short-form clipping engine. **No B-roll.**

## Canonical runtime

The public runtime is `local-first-v5/canonical_api.py`.

Windows:
```bat
run_nexus_canonical.bat
```

Unix/macOS:
```bash
./run_nexus_canonical.sh
```

The API listens on `127.0.0.1:8000` by default.

## Canonical pipeline

```text
source
  -> yt-dlp / local upload
  -> local Whisper transcription
  -> semantic + audio + vision analysis
  -> editorial ranking
  -> Smart EDL
  -> subject-aware camera
  -> captions
  -> FFmpeg compositor
  -> render QA
  -> output artifact
```

## Product invariants

- No paid cloud AI is required for canonical clipping.
- B-roll is disabled by policy and is not part of the product.
- The same timeline drives video, audio, captions, and camera remapping.
- A render must pass media QA before a job can become `completed`.
- Future UI work is decoupled from the canonical runtime contract.

## Legacy surfaces

`backend/`, `build_nexus.py`, and `server.py` remain only for compatibility/migration while the repository converges. They are not the canonical launch path.

See `ARCHITECTURE_CONTRACT.md` for the source-of-truth rules.
