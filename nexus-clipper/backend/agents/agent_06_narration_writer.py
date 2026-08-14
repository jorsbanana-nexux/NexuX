"""AGENT_06_NARRATION_WRITER - NLP Hook Engine & Script Generator"""

import random
from utils.logger import get_logger

log = get_logger("agent_06")

class NarrationWriter:
    """Agent 06: Script generation with NLP psychological hooks."""

    async def write_script(self, topic, structure, style="casual", target_duration=60):
        log.info(f"Writing script: {topic[:50]} ({style})")
        segments = structure.get("segments", [])
        hook_templates = ["STOP scrolling. {topic} is absolutely insane...",
                          "You won't believe what happens with {topic}...",
                          "The truth about {topic} that nobody tells you..."]
        hook = random.choice(hook_templates).format(topic=topic)
        setup = f"So here is the deal with {topic}. Most people have no idea about this. I have been digging into this for a while and what I found is actually wild."
        buildup = f"But here is where it gets interesting. {topic} is not what it looks like. And then something happened that nobody expected. The deeper you go, the crazier it gets."
        climax = f"And then BOOM. {topic} just completely changed everything. This is the moment where it becomes absolutely unbelievable. Nobody predicted this."
        resolution = f"So yeah, that is the real story behind {topic}. After everything we have seen, one thing is clear."
        cta = "Follow for more insane content like this. You will not regret it."
        script_parts = {"hook": hook, "setup": setup, "buildup": buildup, "climax": climax, "resolution": resolution, "cta": cta}
        script_segments = []
        for seg in segments:
            name = seg["name"]
            text = script_parts.get(name, f"Content about {topic}")
            script_segments.append({"segment": name, "start": seg["start"], "end": seg["end"], "text": text, "word_count": len(text.split())})
        full_script = " ".join(s["text"] for s in script_segments)
        log.success(f"Script: {len(full_script.split())} words, {len(script_segments)} segments")
        return {"topic": topic, "style": style, "target_duration": target_duration, "full_script": full_script, "segments": script_segments, "total_words": len(full_script.split())}

narration_writer = NarrationWriter()
