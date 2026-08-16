from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import server as engine
from analysis_bundle import build_analysis_bundle
from editorial_intelligence import generate_candidates
from editorial_ranker import select_diverse
from targeted_retrieval import download_segment, fetch_recon_audio, fetch_youtube_captions


def _shift_transcript(transcript: dict[str, Any], offset: float) -> dict[str, Any]:
    result = {
        **transcript,
        "segments": [],
    }
    for segment in transcript.get("segments", []):
        item = dict(segment)
        item["start"] = max(0.0, float(segment.get("start", 0.0)) - offset)
        item["end"] = max(0.0, float(segment.get("end", 0.0)) - offset)
        words = []
        for word in segment.get("words", []) or []:
            word_item = dict(word)
            word_item["start"] = max(0.0, float(word.get("start", 0.0)) - offset)
            word_item["end"] = max(0.0, float(word.get("end", 0.0)) - offset)
            words.append(word_item)
        item["words"] = words
        result["segments"].append(item)
    result["duration"] = max(0.0, float(transcript.get("duration", 0.0)) - offset)
    result["source"] = f"{transcript.get('source', 'unknown')}:shifted"
    return result


def _shift_candidate(candidate: dict[str, Any], offset: float) -> dict[str, Any]:
    result = dict(candidate)
    result["start"] = max(0.0, float(candidate["start"]) - offset)
    result["end"] = max(result["start"], float(candidate["end"]) - offset)
    result["duration"] = result["end"] - result["start"]
    return result


def _segment_lookup(segments: list[dict[str, Any]]):
    def lookup(start: float, end: float):
        return [s for s in segments if float(s.get("end", 0.0)) >= start and float(s.get("start", 0.0)) <= end]

    return lookup


def _reconnaissance(job_dir: Path, url: str, language: str | None, job_id: str) -> tuple[dict[str, Any], str]:
    transcript = fetch_youtube_captions(url, job_dir)
    if transcript:
        if language:
            transcript["language"] = language
        return transcript, "youtube_vtt"
    audio = fetch_recon_audio(url, job_dir, job_id)
    return engine.transcribe_local(audio, language), "recon_audio_whisper"


def _max_candidates(req) -> int:
    return min(40, max(req.clip_count * 4, 12))


async def run_generation(job_id: str, req: engine.GenerateRequest) -> None:
    job = engine._read(job_id)
    try:
        engine.CANCEL_FLAGS.setdefault(job_id, False)
        if job.get("status") == "cancelled" or engine.CANCEL_FLAGS.get(job_id):
            return

        job_dir = engine.DATA / "uploads" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        source = {
            "type": "youtube",
            "url": req.youtube_url,
            "max_height": 1080,
        }
        engine._set(job, status="processing", stage="reconnaissance", progress=5, source=source, job_dir=str(job_dir), retrieval={"strategy": "caption-first-targeted"})

        transcript, recon_source = await asyncio.to_thread(
            _reconnaissance, job_dir, req.youtube_url, req.language, job_id
        )
        engine._set(job, stage="candidate_generation", progress=30, transcript=transcript, retrieval={"strategy": "caption-first-targeted", "recon_source": recon_source})
        if engine.CANCEL_FLAGS.get(job_id):
            engine._set(job, status="cancelled", stage="cancelled")
            return

        candidates = generate_candidates(transcript.get("segments", []), max_candidates=1200)
        if not candidates:
            raise RuntimeError("No viable editorial candidates found")

        # Reuse the canonical deterministic ranker on V6.1 candidate hypotheses.
        ranked = select_diverse(
            candidates,
            limit=_max_candidates(req),
            target_duration=float(req.target_duration),
            scene_boundaries=None,
            audio_profiles={},
        )
        if not ranked:
            raise RuntimeError("Editorial ranking produced no candidates")

        # Keep retrieval bounded: only materialize the candidates that may actually render.
        render_candidates = ranked[: req.clip_count]
        render_meta: list[dict[str, Any]] = []
        rendered: list[str] = []
        all_subject_samples: list[dict[str, Any]] = []

        for idx, candidate in enumerate(render_candidates):
            if engine.CANCEL_FLAGS.get(job_id):
                engine._set(job, status="cancelled", stage="cancelled")
                return

            engine._set(job, stage=f"retrieving clip {idx + 1}/{len(render_candidates)}", progress=45 + int(10 * idx / max(1, len(render_candidates))))
            video, retrieval = await asyncio.to_thread(
                download_segment,
                req.youtube_url,
                job_dir,
                candidate["id"],
                float(candidate["start"]),
                float(candidate["end"]),
                6.0,
                8.0,
                1080,
            )
            media = await asyncio.to_thread(engine.ffprobe, video)
            offset = float(retrieval["retrieved_start"])
            local_candidate = _shift_candidate(candidate, offset)
            local_transcript = _shift_transcript(transcript, offset)

            duration = float(media.get("format", {}).get("duration") or local_transcript.get("duration") or 0.0)
            scenes = await asyncio.to_thread(engine.detect_scene_changes, video, 0.0, duration or None)
            local_candidate = await asyncio.to_thread(
                _rerank_single_candidate,
                local_candidate,
                local_transcript,
                scenes,
                req.target_duration,
            )
            timeline = await asyncio.to_thread(engine.build_timeline, video, local_transcript, local_candidate)
            subject_samples = await asyncio.to_thread(
                engine.detect_face_subjects,
                video,
                float(local_candidate["start"]),
                float(local_candidate["end"]),
            )
            all_subject_samples.append({"candidate_id": local_candidate["id"], "observations": subject_samples})

            output = engine.OUTPUTS / f"{job_id}_clip_{idx + 1:02d}.mp4"
            info = await asyncio.to_thread(
                engine._render_with_spec,
                video,
                {**job, "job_id": job_id, "transcript": local_transcript, "meta": media},
                local_candidate,
                output,
                timeline,
                req,
            )
            rendered.append(f"/output/{output.name}")
            render_meta.append({
                "candidate_id": local_candidate["id"],
                "timeline": timeline.to_dict(),
                "render": info,
                "editorial_rank": local_candidate.get("editorial_rank"),
                "editorial_signals": local_candidate.get("editorial_signals"),
                "editorial_evidence": local_candidate.get("editorial_evidence"),
                "narrative": local_candidate.get("narrative"),
                "retrieval": retrieval,
            })

            engine._set(
                job,
                progress=55 + int(40 * (idx + 1) / len(render_candidates)),
                stage=f"rendering {idx + 1}/{len(render_candidates)}",
                render_meta=render_meta,
            )

        bundle = build_analysis_bundle(transcript, render_candidates, [], all_subject_samples)
        engine._set(
            job,
            status="completed",
            stage="completed",
            progress=100,
            output_path=rendered[0] if rendered else None,
            clips=rendered,
            candidates=render_candidates,
            selected_candidate_id=render_candidates[0]["id"] if render_candidates else None,
            analysis_bundle=bundle.to_dict(),
            render_meta=render_meta,
            broll=False,
            retrieval={
                "strategy": "caption-first-targeted",
                "recon_source": recon_source,
                "full_video_downloaded": False,
                "targeted_segments": len(rendered),
            },
        )
    except Exception as exc:
        if engine.CANCEL_FLAGS.get(job_id):
            engine._set(job, status="cancelled", stage="cancelled", error="Job cancelled")
        else:
            engine._set(job, status="failed", stage="failed", error=str(exc))
    finally:
        engine.CANCEL_FLAGS.pop(job_id, None)


def _rerank_single_candidate(
    candidate: dict[str, Any],
    transcript: dict[str, Any],
    scenes: list[dict[str, Any]],
    target_duration: int,
) -> dict[str, Any]:
    ranked = engine.rerank_candidates(
        [candidate],
        scene_boundaries=scenes,
        target_duration=float(target_duration),
        limit=1,
        video=None,
        transcript=transcript,
    )
    return ranked[0] if ranked else candidate
