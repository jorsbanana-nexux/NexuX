"""AGENT_14_LIP_SYNC - explicit capability declaration.

The legacy GPU lip-sync transform is not present in the canonical engine. This
agent only reports capability state and never pretends to modify media.
"""

from utils.logger import get_logger

log = get_logger("agent_14")

class LipSyncModifier:
    async def analyze_lip_sync_needs(self, original_audio_path, translated_text, target_language="id"):
        needs = target_language != "en"
        return {
            "supported": False,
            "needs_lip_sync": needs,
            "target_language": target_language,
            "status": "disabled",
            "note": "Full lip-sync transform is not implemented in the canonical engine; no media is modified by this agent.",
        }

lip_sync_modifier = LipSyncModifier()
