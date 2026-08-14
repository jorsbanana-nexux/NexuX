"""AGENT_10_BREATH_INJECTOR"""

from utils.logger import get_logger
log = get_logger("agent_10")

class BreathInjector:
    async def analyze_injection_points(self, script_segments, emotion_map):
        log.info(f"Analyzing breath points for {len(script_segments)} segments")
        points = []
        for i, seg in enumerate(script_segments):
            em = emotion_map[i].get("primary_emotion","neutral") if i < len(emotion_map) else "neutral"
            if len(seg.get("text","").split()) >= 3:
                points.append({"timestamp": seg.get("start",0), "breath_type": "short_inhale", "reason": "natural_start"})
            if em in ("SHOCK","SUSPENSE","INSPIRATION"):
                points.append({"timestamp": (seg.get("start",0)+seg.get("end",0))/2, "breath_type": "long_inhale"})
        return {"total_injection_points": len(points), "injection_points": points}

breath_injector = BreathInjector()
