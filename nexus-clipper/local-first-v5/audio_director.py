from __future__ import annotations
from typing import Any, Mapping

def _n(value: Any, default: float = 50.0) -> float:
    try: return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError): return default

def plan_audio_direction(profile: Mapping[str, Any] | None = None, *, speech_protection: bool = True, music_enabled: bool = False) -> dict[str, Any]:
    p = dict(profile or {})
    clarity, density, rhythm, energy = (_n(p.get(k)) for k in ("clarity", "speech_density", "rhythm", "energy"))
    return {"director":"audio","speech_protection":speech_protection,"music_enabled":music_enabled,"ducking_db":-8.0 if speech_protection else -4.0,"processing":{"normalize_loudness":True,"protect_transients":True,"reduce_silence_artifacts":True,"preserve_natural_dynamics":True},"signals":{"clarity":clarity,"speech_density":density,"rhythm":rhythm,"energy":energy},"confidence":round(min(1.0,0.35+(clarity+density+rhythm)/300.0),3)}
