from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
from editorial_memory import EditorialMemoryEvent, EditorialPreferenceProfile, build_profile

class EditorialMemoryStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, event: EditorialMemoryEvent) -> None:
        item = event.normalized().to_dict()
        path = self.root / f"{event.user_id}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    def events(self, user_id: str) -> list[EditorialMemoryEvent]:
        path = self.root / f"{user_id}.jsonl"
        if not path.exists():
            return []
        result: list[EditorialMemoryEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            result.append(EditorialMemoryEvent(item["event_id"], item["user_id"], item["signal"], item["value"], item.get("context", {}), item.get("created_at", ""), item.get("source", "human")))
        return result

    def profile(self, user_id: str, prior: EditorialPreferenceProfile | None = None) -> EditorialPreferenceProfile:
        return build_profile(self.events(user_id), prior=prior)

    def export(self, user_id: str) -> list[dict]:
        return [event.normalized().to_dict() for event in self.events(user_id)]
