from __future__ import annotations

"""Central AI-brain configuration for NexuX.

Put real secrets in environment variables or a local untracked .env file.
This module is the single configuration surface used by the engine's AI
providers; the frontend must never receive provider API keys.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AIBrain:
    name: str
    endpoint_env: str
    api_key_env: str
    model_env: str
    default_endpoint: str = ""
    default_model: str = ""

    @property
    def endpoint(self) -> str:
        return os.getenv(self.endpoint_env, self.default_endpoint).strip()

    @property
    def api_key(self) -> str:
        return os.getenv(self.api_key_env, "").strip()

    @property
    def model(self) -> str:
        return os.getenv(self.model_env, self.default_model).strip()

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key and self.model)


# Add/remove brains here without changing the editorial engine.
# All credentials stay in environment variables.
AI_BRAINS: tuple[AIBrain, ...] = (
    AIBrain(
        name="primary",
        endpoint_env="NEXUX_AI_PRIMARY_ENDPOINT",
        api_key_env="NEXUX_AI_PRIMARY_API_KEY",
        model_env="NEXUX_AI_PRIMARY_MODEL",
    ),
    AIBrain(
        name="secondary",
        endpoint_env="NEXUX_AI_SECONDARY_ENDPOINT",
        api_key_env="NEXUX_AI_SECONDARY_API_KEY",
        model_env="NEXUX_AI_SECONDARY_MODEL",
    ),
    AIBrain(
        name="vision",
        endpoint_env="NEXUX_AI_VISION_ENDPOINT",
        api_key_env="NEXUX_AI_VISION_API_KEY",
        model_env="NEXUX_AI_VISION_MODEL",
    ),
)


def configured_brains() -> list[AIBrain]:
    return [brain for brain in AI_BRAINS if brain.configured]


def selected_brain() -> AIBrain | None:
    wanted = os.getenv("NEXUX_AI_BRAIN", "primary").strip().lower()
    for brain in AI_BRAINS:
        if brain.name == wanted and brain.configured:
            return brain
    return next(iter(configured_brains()), None)
