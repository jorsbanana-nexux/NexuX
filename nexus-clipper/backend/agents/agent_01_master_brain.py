"""AGENT_01_MASTER_BRAIN - compatibility orchestrator for the canonical V5 engine.

This agent owns project state but never fakes completion of media stages. The
canonical Local-First V5 pipeline remains the only render engine.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Any
from enum import Enum
from datetime import datetime, timezone
from utils.logger import get_logger

log = get_logger("agent_01")

class NarrativeStyle(str, Enum):
    GEN_Z = "gen_z_slang"
    MYSTERY = "mysterious_narrator"
    GAMING = "energetic_gaming"
    DOCUMENTARY = "documentary"
    HORROR = "horror"
    PROFESSIONAL = "professional"
    CASUAL = "casual"

class Platform(str, Enum):
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"

@dataclass
class VideoProject:
    project_id: str = ""
    status: str = "initializing"
    created_at: str = ""
    topic: str = ""
    keywords: List[str] = field(default_factory=list)
    narrative_style: str = "casual"
    target_duration: int = 60
    platform: str = "tiktok"
    batch_count: int = 1
    keyword_cloud: List[str] = field(default_factory=list)
    script: str = ""
    script_segments: List[Dict[str, Any]] = field(default_factory=list)
    emotion_map: List[Dict[str, Any]] = field(default_factory=list)
    scene_plan: List[Dict[str, Any]] = field(default_factory=list)
    tts_audio_path: str = ""
    bgm_path: str = ""
    sfx_paths: List[str] = field(default_factory=list)
    video_clips: List[Dict[str, Any]] = field(default_factory=list)
    subtitle_data: str = ""
    viral_score: float = 0.0
    quality_score: float = 0.0
    render_path: str = ""
    export_paths: Dict[str, str] = field(default_factory=dict)
    critique_report: str = ""
    retry_count: int = 0

class MasterBrain:
    """Project/state orchestrator; canonical V5 owns actual media processing."""

    def __init__(self):
        self.active_projects: Dict[str, VideoProject] = {}
        self.pipeline_queue: asyncio.Queue[str] = asyncio.Queue()

    async def initialize(self):
        from utils.config import detect_hardware
        hw = detect_hardware()
        return {"status": "initialized", "hardware": hw, "agent_count": 25, "role": "compatibility_orchestrator"}

    async def create_project(self, params):
        pid = f"nx-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{len(self.active_projects):04d}"
        project = VideoProject(
            project_id=pid,
            status="created",
            created_at=datetime.now(timezone.utc).isoformat(),
            topic=params.get("topic", ""),
            keywords=params.get("keywords", []),
            narrative_style=params.get("narrative_style", "casual"),
            target_duration=params.get("target_duration", 60),
            platform=params.get("platform", "tiktok"),
            batch_count=params.get("batch_count", 1),
        )
        self.active_projects[pid] = project
        await self.pipeline_queue.put(pid)
        return project

    async def get_project(self, pid):
        return self.active_projects.get(pid)

    async def update_project(self, pid, updates):
        project = self.active_projects.get(pid)
        if project:
            for key, value in updates.items():
                if hasattr(project, key):
                    setattr(project, key, value)
        return project

    async def orchestrate_pipeline(self, pid):
        project = self.active_projects.get(pid)
        if not project:
            return {"project_id": pid, "status": "error", "error": "project_not_found"}
        return {
            "project_id": pid,
            "status": "delegated",
            "canonical_engine": "local-first-v5",
            "public_entrypoint": "canonical_api.py",
            "stages": {
                "research": {"status": "delegated"},
                "script_audio": {"status": "delegated"},
                "visual": {"status": "delegated"},
                "execution": {"status": "delegated"},
                "qa_distribution": {"status": "delegated"},
            },
            "note": "No stage is reported completed by the compatibility orchestrator. Completion is owned by the canonical job pipeline and render QA.",
        }

master_brain = MasterBrain()
