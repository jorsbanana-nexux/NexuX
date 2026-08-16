from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CacheRecord:
    key: str
    artifact: Any
    metadata: dict[str, Any]


def cache_key(*parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, default=str).encode("utf-8")
    return sha256(payload).hexdigest()


class JsonCache:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def get(self, key: str) -> CacheRecord | None:
        path = self.path_for(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return CacheRecord(key, payload.get("artifact"), dict(payload.get("metadata", {})))
        except (OSError, ValueError, TypeError):
            return None

    def put(self, key: str, artifact: Any, metadata: dict[str, Any] | None = None) -> CacheRecord:
        record = CacheRecord(key, artifact, dict(metadata or {}))
        target = self.path_for(key)
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps({"artifact": artifact, "metadata": record.metadata}, sort_keys=True, default=str), encoding="utf-8")
        temp.replace(target)
        return record
