from __future__ import annotations

from typing import Any, Mapping


def evaluate_render_quality(report: Mapping[str, Any], *, threshold: float = 0.80) -> dict[str, Any]:
    quality = float(report.get("quality", report.get("score", 0.0)) or 0.0)
    quality = max(0.0, min(1.0, quality))
    technical = report.get("technical", {}) or {}
    editorial = report.get("editorial", {}) or {}
    issues = list(report.get("issues", []) or [])
    if bool(technical.get("invalid", False)):
        issues.append("technical output invalid")
    if bool(technical.get("av_sync_failed", False)):
        issues.append("audio/video synchronization failed")
    if bool(editorial.get("premature_cut", False)):
        issues.append("premature narrative cut")
    verdict = "PASS" if quality >= threshold and not issues else ("REFINE" if quality >= threshold * 0.65 else "REVIEW")
    return {
        "quality": quality,
        "threshold": threshold,
        "verdict": verdict,
        "issues": issues,
        "eligible_for_publish": verdict == "PASS",
    }
