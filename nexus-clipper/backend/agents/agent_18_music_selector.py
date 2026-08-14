"""AGENT_18_MUSIC_SELECTOR - Background Music Engine"""

from utils.logger import get_logger
log = get_logger("agent_18")

class MusicSelector:
    async def select_music(self, topic, emotion_map, duration):
        em_to_genre = {"SHOCK":"gaming_funny","MYSTERY":"horror_mystery","HIGH_ENERGY":"gaming_funny","INSPIRATION":"motivational"}
        dominant = "HIGH_ENERGY"
        if emotion_map:
            counts = {}
            for e in emotion_map:
                em = e.get("primary_emotion","HIGH_ENERGY")
                counts[em] = counts.get(em,0)+1
            dominant = max(counts, key=counts.get)
        genre = em_to_genre.get(dominant, "casual_vlog")
        return {"genre": genre, "dominant_emotion": dominant, "duration": duration, "ducking_db": -22.0, "fade_in_s": 2.0, "fade_out_s": 3.0}

music_selector = MusicSelector()
