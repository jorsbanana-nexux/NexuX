"""AGENT_08_EMOTION_CONTROLLER - Emotional Mapping Engine"""

from typing import Dict, List, Any
from utils.logger import get_logger

log = get_logger("agent_08")

class EmotionController:
    """Agent 08: Maps emotional states to timestamps."""

    def __init__(self):
        self.emotion_keywords = {
            "SHOCK": ["boom", "insane", "crazy", "unbelievable", "shocking", "wild", "mind-blowing"],
            "MYSTERY": ["secret", "hidden", "unknown", "mysterious", "dark", "truth"],
            "HIGH_ENERGY": ["fast", "quick", "rush", "speed", "intense", "extreme", "hype"],
            "LAUGHTER": ["funny", "lol", "ridiculous", "hilarious", "wtf"],
            "SUSPENSE": ["wait", "but then", "however", "suddenly", "plot twist"],
            "SADNESS": ["sad", "tragic", "lost", "gone", "never"],
            "INSPIRATION": ["achieve", "success", "believe", "dream", "possible", "overcome"],
        }
        self.emotion_triggers = {
            "SHOCK": {"audio_cues":["bass_drop","record_scratch"],"visual_cues":["zoom_in_rapid","shake"],"subtitle_style":"LARGE_BOLD_RED","color_grade":"high_contrast","transition":"glitch_cut"},
            "MYSTERY": {"audio_cues":["low_drone","reverb"],"visual_cues":["slow_zoom","vignette"],"subtitle_style":"slow_reveal","color_grade":"desaturated","transition":"slow_crossfade"},
            "HIGH_ENERGY": {"audio_cues":["upbeat","riser","whoosh"],"visual_cues":["fast_cuts","motion_blur"],"subtitle_style":"fast_pop","color_grade":"vibrant","transition":"whip_pan"},
            "LAUGHTER": {"audio_cues":["comedy_sting","rimshot"],"visual_cues":["zoom_punch","freeze"],"subtitle_style":"bouncy_emoji","color_grade":"bright_warm","transition":"bounce_cut"},
            "SUSPENSE": {"audio_cues":["heartbeat","bass_rumble"],"visual_cues":["slow_push","letterbox"],"subtitle_style":"delayed_reveal","color_grade":"contrast_buildup","transition":"slow_dissolve"},
        }

    async def analyze_script_emotions(self, script_segments):
        log.info(f"Analyzing emotions for {len(script_segments)} segments")
        emotion_map = []
        for seg in script_segments:
            text = seg.get("text","").lower()
            scores = {}
            for em, kws in self.emotion_keywords.items():
                s = sum(1 for kw in kws if kw in text) * 20
                if s > 0: scores[em] = min(s, 100)
            primary = max(scores, key=scores.get) if scores else "HIGH_ENERGY"
            if not scores: scores = {"HIGH_ENERGY": 50}
            triggers = self.emotion_triggers.get(primary, self.emotion_triggers["HIGH_ENERGY"])
            emotion_map.append({"segment": seg.get("segment"), "start": seg.get("start",0), "end": seg.get("end",0),
                               "primary_emotion": primary, "emotion_scores": scores, **triggers})
        log.success(f"Emotions mapped: {len(emotion_map)} segments")
        return {"emotion_map": emotion_map}

emotion_controller = EmotionController()
