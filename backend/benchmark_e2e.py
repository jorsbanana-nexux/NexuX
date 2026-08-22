"""
NexuX V9.5 — End-to-End Benchmark (Mode 1, Podcast)
====================================================
Runs the REAL pipeline on a short YouTube video and reports:
- wall time per stage
- peak RAM (via psutil polling thread)
- clips produced + their durations
- partial-vs-full download behaviour

Run: python benchmark_e2e.py "<youtube_url>" [target_duration] [clip_count]
"""
import asyncio
import os
import sys
import threading
import time

import psutil


class RamWatchdog:
    """Peak-RSS sampler on a background thread."""

    def __init__(self, interval=0.25):
        self.interval = interval
        self.peak = 0
        self.proc = psutil.Process(os.getpid())
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop.set()
        self.thread.join()

    def _run(self):
        while not self._stop.is_set():
            try:
                rss = self.proc.memory_info().rss
                if rss > self.peak:
                    self.peak = rss
            except psutil.NoSuchProcess:
                break
            self._stop.wait(self.interval)


def _fmt_mb(nbytes):
    return f"{nbytes / (1024 * 1024):.1f} MB"


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    clip_count = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    smart_cut = "--smart-cut" in sys.argv

    os.environ.setdefault("WHISPER_MODEL", "tiny")

    from engine.pipeline import run_pipeline

    dog = RamWatchdog()
    dog.start()
    t0 = time.monotonic()

    stage_log = []

    async def progress(stage: str, pct: float, **data):
        stage_log.append((time.monotonic() - t0, stage, pct))
        print(f"  [+{time.monotonic() - t0:6.1f}s] {stage:20s} {pct:5.1f}%")

    print(f"=== NexuX E2E Benchmark ===")
    print(f"url={url}")
    print(f"target_duration={target} clip_count={clip_count} whisper={os.environ['WHISPER_MODEL']} smart_cut={smart_cut}")
    print()

    try:
        result = await run_pipeline(
            url,
            job_id="bench_e2e",
            progress_callback=progress,
            target_duration=target,
            clip_count=clip_count,
            aspect_ratio="9:16",
            subtitle_style="hormozi",
            remove_fillers_pauses=smart_cut,
        )
    except Exception as e:
        print(f"\nPIPELINE RAISED: {type(e).__name__}: {e}")
        return 2
    finally:
        dog.stop()

    total = time.monotonic() - t0
    clips = result.get("clips", [])
    error = result.get("error")

    print()
    print("=== RESULT ===")
    print(f"status        : {'OK' if not error else 'ERROR'}")
    if error:
        print(f"error         : {error}")
    print(f"clips         : {len(clips)}")
    for c in clips:
        exists = os.path.exists(c) if c else False
        size = os.path.getsize(c) if exists else 0
        print(f"  - {c}  [exists={exists} size={_fmt_mb(size)}]")
    for c in result.get("clip_candidates", []):
        sc = c.get("smart_cut")
        if sc:
            print(f"  smart_cut   : {c.get('path')}: removed {sc['removed_seconds']:.1f}s "
                  f"({sc['removed_pct']:.1f}%) — {sc['filler_count']} fillers, {sc['silence_count']} silences")
    print(f"total time    : {total:.1f}s")
    print(f"peak RAM      : {_fmt_mb(dog.peak)}")
    print(f"stages seen   : {len(stage_log)}")

    if stage_log:
        # per-stage durations (between consecutive progress ticks)
        print()
        print("=== STAGE TIMELINE ===")
        prev_t, prev_stage = stage_log[0][0], stage_log[0][1]
        for t, stage, _ in stage_log[1:]:
            print(f"  {prev_stage:20s} {t - prev_t:6.1f}s")
            prev_t, prev_stage = t, stage

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
