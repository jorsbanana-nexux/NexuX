from __future__ import annotations

import json
import urllib.request
from typing import Any

from ai_brain_config import selected_brain
from ai_editorial import EditorialDecision, evaluate_with_provider
from ai_prompt import build_editorial_prompt


class HttpEditorialProvider:
    """Small OpenAI-compatible adapter behind the central AI-brain config."""

    def __init__(self, endpoint: str, api_key: str, model: str, timeout: float = 30.0):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def evaluate(self, packet: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are NexuX's senior short-form editorial judge."},
                {"role": "user", "content": build_editorial_prompt(packet)},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        return json.loads(content)


def build_env_provider() -> HttpEditorialProvider | None:
    brain = selected_brain()
    if brain is None:
        return None
    return HttpEditorialProvider(brain.endpoint, brain.api_key, brain.model)


def evaluate_ai(packet: dict[str, Any]) -> EditorialDecision:
    return evaluate_with_provider(build_env_provider(), packet)
