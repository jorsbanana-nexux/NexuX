"""AGENT_14_LIP_SYNC - sync quality checker.

Checks whether speech segments (audio timing) align with the corresponding
video timestamps (on-screen lip movement frames). This is an analysis-only
agent — it scores alignment and reports misaligned segments but never modifies
media.
"""

from typing import Any, Dict, List, Optional

from utils.logger import get_logger

log = get_logger("agent_14")


class LipSyncModifier:
    """Speech-vs-video alignment checker (analysis only)."""

    async def analyze_lip_sync_needs(self, original_audio_path, translated_text, target_language="id"):
        needs = target_language != "en"
        return {
            "supported": False,
            "needs_lip_sync": needs,
            "target_language": target_language,
            "status": "disabled",
            "note": "Full lip-sync transform is not implemented; use process() for sync analysis.",
        }

    # ------------------------------------------------------------------ #
    # Core analysis: check speech/video alignment.
    # ------------------------------------------------------------------ #
    async def process(
        self,
        speech_segments: List[Dict[str, Any]],
        video_timestamps: Optional[List[Dict[str, Any]]] = None,
        tolerance_ms: int = 200,
    ) -> Dict[str, Any]:
        """
        Check whether speech segments align with video timestamps.

        Args:
            speech_segments: list of dicts with ``start`` and ``end`` (seconds,
                float) describing the audio/speech timing. ``text`` is optional.
            video_timestamps: list of dicts with ``start`` and ``end`` (seconds)
                describing the video/lip-movement timing. If omitted, the speech
                segments are paired index-by-index with themselves (i.e. the
                speech timing is treated as the reference).
            tolerance_ms: maximum acceptable offset, in milliseconds, before a
                segment is flagged as misaligned.

        Returns:
            Dict with ``status``, ``sync_score`` (0.0–1.0 fraction of aligned
            segments), and ``misaligned_segments`` (list of dicts describing
            each misalignment with offsets).
        """
        tolerance_s = max(0.0, float(tolerance_ms) / 1000.0)

        if not speech_segments:
            return {
                "status": "completed",
                "sync_score": 1.0,
                "misaligned_segments": [],
                "note": "No speech segments supplied; nothing to check.",
            }

        # If no video timeline given, compare each speech segment against the
        # same-index reference segment derived from the speech list itself.
        if video_timestamps is None:
            video_timestamps = list(speech_segments)

        total = 0
        aligned = 0
        misaligned: List[Dict[str, Any]] = []

        for idx, seg in enumerate(speech_segments):
            s_start = self._to_float(seg.get("start"))
            s_end = self._to_float(seg.get("end"))
            if s_start is None or s_end is None:
                continue

            total += 1

            ref = video_timestamps[idx] if idx < len(video_timestamps) else None
            if ref is None:
                misaligned.append({
                    "index": idx,
                    "speech_start": s_start,
                    "speech_end": s_end,
                    "issue": "no matching video timestamp",
                    "offset_start_ms": None,
                    "offset_end_ms": None,
                })
                continue

            v_start = self._to_float(ref.get("start"))
            v_end = self._to_float(ref.get("end"))

            start_offset = (v_start - s_start) if v_start is not None else None
            end_offset = (v_end - s_end) if v_end is not None else None

            start_bad = start_offset is not None and abs(start_offset) > tolerance_s
            end_bad = end_offset is not None and abs(end_offset) > tolerance_s

            if start_bad or end_bad:
                misaligned.append({
                    "index": idx,
                    "speech_start": s_start,
                    "speech_end": s_end,
                    "video_start": v_start,
                    "video_end": v_end,
                    "offset_start_ms": round(start_offset * 1000.0, 2) if start_offset is not None else None,
                    "offset_end_ms": round(end_offset * 1000.0, 2) if end_offset is not None else None,
                    "tolerance_ms": tolerance_ms,
                })
            else:
                aligned += 1

        sync_score = (aligned / total) if total else 1.0

        log.info(
            "Lip-sync check: %d/%d aligned (score=%.3f), %d misaligned",
            aligned, total, sync_score, len(misaligned),
        )

        return {
            "status": "completed",
            "agent": "agent_14_lip_sync",
            "sync_score": round(sync_score, 4),
            "aligned_segments": aligned,
            "total_segments": total,
            "tolerance_ms": tolerance_ms,
            "misaligned_segments": misaligned,
        }

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


lip_sync_modifier = LipSyncModifier()
