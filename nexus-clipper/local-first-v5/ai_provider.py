from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ai_editorial import EditorialDecision, evaluate_with_provider
from ai_prompt import build_editorial_prompt


class HttpEditorialProvider:
    """Minimal provider adapter using a generic OpenAI-compatible HTTP API.

    Endpoint and credentials are environment-controlled. The adapter is kept
    deliberately small so a provider can be swapped without touching NexuX's
    editorial engine.
    """

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
    endpoint = os.getenv("NEXUX_AI_ENDPOINT", "").strip()
    api_key = os.getenv("NEXUX_AI_API_KEY", "").strip()
    model = os.getenv("NEXUX_AI_MODEL", "").strip()
    if not endpoint or not api_key or not model:
        return None
    return HttpEditorialProvider(endpoint, api_key, model)


def evaluate_ai(packet: dict[str, Any]) -> EditorialDecision:
    return evaluate_with_provider(build_env_provider(), packet)
