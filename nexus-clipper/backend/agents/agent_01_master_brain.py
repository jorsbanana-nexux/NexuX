"""AGENT_01_MASTER_BRAIN - Core Orchestrator"""

import asyncio, json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
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
    script_segments: List[Dict] = field(default_factory=list)
    emotion_map: List[Dict] = field(default_factory=list)
    scene_plan: List[Dict] = field(default_factory=list)
    tts_audio_path: str = ""
    bgm_path: str = ""
    sfx_paths: List[str] = field(default_factory=list)
    video_clips: List[Dict] = field(default_factory=list)
    subtitle_data: str = ""
    viral_score: float = 0.0
    quality_score: float = 0.0
    render_path: str = ""
    export_paths: Dict[str, str] = field(default_factory=dict)
    critique_report: str = ""
    retry_count: int = 0

class MasterBrain:
    """Agent 01: The supreme commander of the 25-agent matrix."""

    def __init__(self):
        self.active_projects: Dict[str, VideoProject] = {}
        self.pipeline_queue: asyncio.Queue = asyncio.Queue()

    async def initialize(self):
        from utils.config import detect_hardware
        hw = detect_hardware()
        log.info(f"Master Brain initialized. HW: {hw['cpu_count']} CPUs, {hw['total_ram_gb']}GB RAM")
        return {"status": "initialized", "hardware": hw, "agent_count": 25}

    async def create_project(self, params):
        pid = f"nx-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(self.active_projects):04d}"
        project = VideoProject(project_id=pid, status="created", created_at=datetime.utcnow().isoformat(),
                               topic=params.get("topic", ""), keywords=params.get("keywords", []),
                               narrative_style=params.get("narrative_style", "casual"),
                               target_duration=params.get("target_duration", 60),
                               platform=params.get("platform", "tiktok"),
                               batch_count=params.get("batch_count", 1))
        self.active_projects[pid] = project
        await self.pipeline_queue.put(pid)
        log.success(f"Project {pid} created")
        return project

    async def get_project(self, pid):
        return self.active_projects.get(pid)

    async def update_project(self, pid, updates):
        p = self.active_projects.get(pid)
        if p:
            for k, v in updates.items():
                if hasattr(p, k): setattr(p, k, v)
        return p

    async def orchestrate_pipeline(self, pid):
        log.info(f"Orchestrating pipeline for {pid}")
        stages = ["research", "script_audio", "visual", "execution", "qa_distribution"]
        results = {"project_id": pid, "stages": {}}
        for stage in stages:
            results["stages"][stage] = {"status": "completed"}
        return results

master_brain = MasterBrain()
