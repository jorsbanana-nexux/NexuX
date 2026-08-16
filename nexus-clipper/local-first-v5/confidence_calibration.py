from __future__ import annotations

def calibrate(raw_confidence: float, *, reliability: float = 1.0, disagreement: float = 0.0) -> float:
    raw = max(0.0, min(1.0, float(raw_confidence)))
    rel = max(0.0, min(1.0, float(reliability)))
    dis = max(0.0, min(1.0, float(disagreement)))
    return max(0.0, min(1.0, raw * rel * (1.0 - 0.5 * dis)))
