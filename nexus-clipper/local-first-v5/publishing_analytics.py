from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any


@dataclass(frozen=True)
class PublishTarget:
    platform: str
    aspect_ratio: str
    title: str
    description: str
    hashtags: list[str]
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_publish_plan(project_id: str, clip: dict[str, Any], platforms: list[str] | None = None) -> dict[str, Any]:
    platforms = platforms or ["youtube_shorts", "tiktok", "instagram_reels"]
    text = str(clip.get("text", "")).strip()
    words = [w.strip(".,!?;:#") for w in text.split() if len(w.strip(".,!?;:#")) > 3]
    tags = []
    for word in words:
        tag = "#" + "".join(ch for ch in word if ch.isalnum())
        if len(tag) > 3 and tag.lower() not in {t.lower() for t in tags}:
            tags.append(tag)
        if len(tags) >= 8:
            break
    title = text[:85] or f"NexuX clip {project_id}"
    desc = text[:300]
    targets = []
    for platform in platforms:
        aspect = "16:9" if platform == "youtube_full" else "9:16"
        targets.append(PublishTarget(platform, aspect, title, desc, tags).to_dict())
    return {"project_id": project_id, "generated_at": datetime.now(timezone.utc).isoformat(), "targets": targets}


def record_analytics_event(root: Path, project_id: str, event: dict[str, Any]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{project_id}_analytics.jsonl"
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def aggregate_analytics(root: Path, project_id: str) -> dict[str, Any]:
    path = root / f"{project_id}_analytics.jsonl"
    events = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {"project_id": project_id, "event_count": len(events), "events": events[-200:]}
