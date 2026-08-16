from __future__ import annotations
from typing import Any, Mapping, Sequence

def _clamp(value: float) -> float: return max(0.0, min(1.0, float(value)))
def plan_adaptive_reframe(observations: Sequence[Mapping[str, Any]] | None = None, *, aspect_ratio: str = "9:16", max_zoom: float = 1.12) -> dict[str, Any]:
    obs=[dict(x) for x in (observations or [])]; tracks=[]
    for i,item in enumerate(obs):
        box=item.get("bbox") or item.get("face") or item.get("subject")
        if box: tracks.append({"index":i,"bbox":dict(box) if isinstance(box,Mapping) else {}})
    return {"mode":"adaptive_subject_follow" if tracks else "safe_center","aspect_ratio":aspect_ratio,"max_zoom":float(max_zoom),"safe_margins":{"top":.08,"bottom":.10,"left":.06,"right":.06},"tracks":tracks,"stability":"smoothed","confidence":_clamp(.45+min(.5,len(tracks)*.1))}
