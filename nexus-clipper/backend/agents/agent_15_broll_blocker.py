"""AGENT_15_BROLL_BLOCKER - NO AUTO B-ROLL PROTOCOL"""

from utils.logger import get_logger
log = get_logger("agent_15")

class BrollBlocker:
    def __init__(self):
        self.blocked_sources = ["pixabay", "pexels", "mixkit", "storyblocks", "shutterstock", "istock", "getty"]
        self.allowed_sources = ["user_provided_url", "youtube_direct_url", "user_uploaded_footage"]

    async def validate_footage_source(self, source_url, source_type):
        if source_type in self.allowed_sources:
            return {"allowed": True}
        for blocked in self.blocked_sources:
            if blocked in source_url.lower():
                log.warn(f"BLOCKED: Auto B-roll from {blocked}")
                return {"allowed": False, "reason": f"Auto B-roll from {blocked} BLOCKED"}
        return {"allowed": True}

    async def get_protocol_status(self):
        return {"protocol": "NO_AUTO_BROLL", "active": True, "message": "ZERO auto B-roll. All footage must be user-provided."}

broll_blocker = BrollBlocker()
