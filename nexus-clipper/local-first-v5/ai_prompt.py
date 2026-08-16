from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are NexuX's senior short-form editorial judge.
Evaluate candidates as an editor, not as a generic summarizer.
Prefer self-contained moments with a strong opening, understandable context,
rising tension or curiosity, a satisfying payoff, and minimal dead air.
Do not invent facts or evidence. Scores must reflect only supplied evidence.
Return JSON only matching the requested schema.
"""


def build_editorial_prompt(packet: dict[str, Any]) -> str:
    # Keep provider payload deterministic and bounded; the provider adapter owns
    # authentication and transport.
    body = json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
    return f"""{SYSTEM_PROMPT}

Candidate packet:
{body}

Return exactly this JSON shape:
{{
  \"verdict\": \"KEEP|REFINE|REJECT|REVIEW\",
  \"confidence\": 0.0,
  \"scores\": {{
    \"hook\": 0.0,
    \"context\": 0.0,
    \"tension\": 0.0,
    \"payoff\": 0.0,
    \"retention\": 0.0,
    \"novelty\": 0.0,
    \"shareability\": 0.0
  }},
  \"adjustments\": {{\"start\": 0.0, \"end\": 0.0}},
  \"evidence\": [\"brief evidence grounded in packet\"],
  \"summary\": \"brief editorial assessment\"
}}
"""
