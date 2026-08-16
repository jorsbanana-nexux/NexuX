from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine_media import ffprobe
from youtube import download_youtube, probe_youtube, validate_youtube_url


@dataclass(frozen=True)
class IngestedMedia:
    source_type: str
    source_ref: str
    metadata: dict[str, Any]
    local_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "metadata": self.metadata,
            "local_path": str(self.local_path) if self.local_path else None,
        }


class MediaIngestService:
    """Canonical ownership of source validation, metadata probing and full retrieval."""

    def validate_youtube(self, url: str) -> str:
        return validate_youtube_url(url)

    def probe_youtube(self, url: str) -> IngestedMedia:
        normalized = self.validate_youtube(url)
        return IngestedMedia("youtube", normalized, probe_youtube(normalized))

    def download_youtube(
        self,
        url: str,
        job_dir: Path,
        max_height: int = 1080,
        job_id: str | None = None,
    ) -> IngestedMedia:
        normalized = self.validate_youtube(url)
        path, metadata = download_youtube(normalized, job_dir, max_height, job_id)
        return IngestedMedia("youtube", normalized, metadata, path)

    def inspect_local(self, path: Path) -> IngestedMedia:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Media artifact not found: {path}")
        return IngestedMedia("local", str(path), ffprobe(path), path)


media_ingest = MediaIngestService()
