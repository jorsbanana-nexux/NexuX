from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    youtube_url: str = Field(..., min_length=10, max_length=2000)
    target_duration: int = Field(45, ge=20, le=60)
    aspect_ratio: str = Field("9:16")
    subtitle_style: str = Field("hormozi")
    font: str = Field("Arial", max_length=160)
    font_size: int = Field(48, ge=20, le=96)
    primary_color: str = Field("#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str = Field("#FFD700", pattern=r"^#[0-9A-Fa-f]{6}$")
    stroke_color: str = Field("#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    stroke_width: int = Field(3, ge=1, le=12)
    position: str = Field("center", pattern=r"^(top|center|bottom)$")
    animation: str = Field("pop", max_length=32)
    auto_zoom: bool = True
    face_tracking: bool = True
    clip_count: int = Field(3, ge=1, le=10)
    language: str | None = Field(None, max_length=20)
    normalize_audio: bool = True
    emoji_enabled: bool = False
    clip_prompt: str | None = Field(default=None, max_length=500)
    genre: str = Field(default="auto", max_length=40)
    remove_fillers_pauses: bool = True
    pause_threshold: float = Field(default=0.42, ge=0.20, le=2.0)
    voice_over: bool = False
    voice_over_text: str | None = Field(default=None, max_length=1200)
    voice_style: str = Field(default="male_narrator", max_length=40)
    publish_platforms: list[str] | None = None


class CompatJob(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    stage: str = "queued"
    output_path: str | None = None
    error: str | None = None
    clips: list[str] = Field(default_factory=list)
    broll: bool = False
    render_meta: list[dict[str, Any]] = Field(default_factory=list)
    analysis_bundle: dict[str, Any] | None = None
