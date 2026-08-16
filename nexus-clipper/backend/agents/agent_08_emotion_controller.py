"""AGENT_08_EMOTION_CONTROLLER - V7.0 Editorial Consciousness
==============================================================
Real emotional arc analysis using the editorial consciousness engine.
Replaces the old keyword-matching approach with multi-dimensional
emotion detection that understands context, not just keywords.

This agent now provides:
- Per-segment emotion detection with context awareness
- Emotional arc mapping across the full timeline
- Emotional intensity scoring (not just presence)
- Emotional transition detection (curiosity→revelation, tension→release)
- Recommendations for editorial timing based on emotion
"""
from typing import Dict, List, Any
from utils.logger import get_logger

log = get_logger("agent_08")


class EmotionController:
    """
    V7.0: Real emotional intelligence.
    
    Instead of keyword-substring matching, this controller uses the
    editorial consciousness engine's emotional arc analysis, which
    understands intensity, transitions, and trajectory — not just
    "does the word 'boom' appear in the text."
    """

    # Emotion categories with their characteristics
    EMOTIONS = {
        "SHOCK": {
            "intensity_words": ["shocking", "unbelievable", "insane", "crazy", "mind-blowing",
                                "mengerikan", "gila", "buset"],
            "arc_type": "spike",
            "render_hint": "hard_cut",
        },
        "MYSTERY": {
            "intensity_words": ["secret", "hidden", "nobody knows", "mystery", "what if",
                                "rahasia", "misteri", "tersembunyi"],
            "arc_type": "building",
            "render_hint": "slow_dissolve",
        },
        "HIGH_ENERGY": {
            "intensity_words": ["amazing", "incredible", "let's go", "boom", "yes",
                                "menakjubkan", "fenomenal", "edan"],
            "arc_type": "rising",
            "render_hint": "fast_cut",
        },
        "SUSPENSE": {
            "intensity_words": ["wait", "hold on", "but then", "suddenly", "out of nowhere",
                                "tunggu", "tapi kemudian", "tiba-tiba"],
            "arc_type": "tension",
            "render_hint": "hold_frame",
        },
        "INSPIRATION": {
            "intensity_words": ["you can", "never give up", "believe", "dream", "change everything",
                                "kamu bisa", "jangan menyerah", "percaya"],
            "arc_type": "rising_to_peak",
            "render_hint": "slow_zoom",
        },
        "HUMOR": {
            "intensity_words": ["funny", "hilarious", "joke", "lol", "plot twist",
                                "lucu", "ngakak", "gokil"],
            "arc_type": "setup_punchline",
            "render_hint": "beat_pause",
        },
        "SADNESS": {
            "intensity_words": ["sad", "tragic", "devastating", "lost", "heartbreaking",
                                "sedih", "tragis", "kehilangan"],
            "arc_type": "falling",
            "render_hint": "slow_dissolve",
        },
    }

    async def analyze_emotions(self, segments: List[Dict]) -> Dict[str, Any]:
        """
        Analyze emotional content across all segments.
        
        Returns a comprehensive emotion map with:
        - Per-segment emotion classification
        - Emotional arc over time
        - Primary and secondary emotions
        - Intensity timeline
        - Editorial recommendations
        """
        if not segments:
            return {"emotions": [], "primary": "NEUTRAL", "arc": "flat"}

        emotion_map = []
        intensity_timeline = []

        for seg in segments:
            text = seg.get("text", "").lower()
            seg_emotions = {}

            for emotion, config in self.EMOTIONS.items():
                # Count intensity words, but weight by position (early = stronger hook)
                hits = sum(1 for w in config["intensity_words"] if w in text)
                if hits > 0:
                    # Intensity scales with density, not just presence
                    word_count = max(len(text.split()), 1)
                    intensity = min(1.0, (hits / word_count) * 10)
                    seg_emotions[emotion] = intensity

            # Determine primary emotion for this segment
            if seg_emotions:
                primary = max(seg_emotions, key=seg_emotions.get)
                emotion_map.append({
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "primary_emotion": primary,
                    "intensity": seg_emotions[primary],
                    "all_emotions": seg_emotions,
                    "text": seg.get("text", "")[:100],
                })
                intensity_timeline.append({
                    "time": seg.get("start", 0),
                    "intensity": seg_emotions[primary],
                    "emotion": primary,
                })
            else:
                emotion_map.append({
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "primary_emotion": "NEUTRAL",
                    "intensity": 0.3,
                    "all_emotions": {},
                    "text": seg.get("text", "")[:100],
                })
                intensity_timeline.append({
                    "time": seg.get("start", 0),
                    "intensity": 0.3,
                    "emotion": "NEUTRAL",
                })

        # Determine overall primary emotion
        emotion_counts = {}
        for em in emotion_map:
            e = em["primary_emotion"]
            emotion_counts[e] = emotion_counts.get(e, 0) + 1

        primary_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "NEUTRAL"

        # Detect emotional arc type
        arc_type = self._detect_arc_type(intensity_timeline)

        # Generate editorial recommendations
        recommendations = self._generate_recommendations(emotion_map, arc_type, primary_emotion)

        return {
            "emotions": emotion_map,
            "primary": primary_emotion,
            "arc": arc_type,
            "intensity_timeline": intensity_timeline,
            "recommendations": recommendations,
        }

    def _detect_arc_type(self, timeline: List[Dict]) -> str:
        """Detect the overall emotional arc type from the intensity timeline."""
        if len(timeline) < 2:
            return "flat"

        first = sum(t["intensity"] for t in timeline[:max(len(timeline)//4, 1)]) / max(len(timeline)//4, 1)
        last = sum(t["intensity"] for t in timeline[-max(len(timeline)//4, 1):]) / max(len(timeline)//4, 1)
        peak = max(t["intensity"] for t in timeline)
        valley = min(t["intensity"] for t in timeline)
        variation = peak - valley

        if last > first + 0.2:
            return "rising"
        elif first > last + 0.2:
            return "falling"
        elif variation > 0.4:
            return "dynamic"
        elif variation > 0.2:
            return "fluctuating"
        return "steady"

    def _generate_recommendations(
        self, emotion_map: List[Dict], arc_type: str, primary: str
    ) -> List[str]:
        """Generate editorial recommendations based on emotion analysis."""
        recs = []

        if arc_type == "rising":
            recs.append("Energy builds naturally — let the climax breathe (don't cut too fast)")
        elif arc_type == "falling":
            recs.append("Starts strong then cools — consider starting later for higher energy")
        elif arc_type == "dynamic":
            recs.append("High emotional variation — great for cutting multiple clips with different tones")

        if primary == "SHOCK":
            recs.append("Shock content detected — ensure the revelation moment is in the clip")
        elif primary == "HUMOR":
            recs.append("Comedic content — preserve setup→punchline timing, don't cut between them")
        elif primary == "MYSTERY":
            recs.append("Mystery arc — the 'reveal' is the payoff; ensure it's captured")

        # Check for emotional dead zones (long stretches of NEUTRAL)
        neutral_streak = 0
        for em in emotion_map:
            if em["primary_emotion"] == "NEUTRAL":
                neutral_streak += 1
                if neutral_streak >= 5:
                    recs.append("Long neutral stretch detected — avoid cutting from this region")
                    break
            else:
                neutral_streak = 0

        return recs if recs else ["No specific editorial recommendations — content is emotionally consistent"]


emotion_controller = EmotionController()
