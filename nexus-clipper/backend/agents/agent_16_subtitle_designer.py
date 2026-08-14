"""AGENT_16_SUBTITLE_DESIGNER - Cinematic Text Engine"""

from utils.logger import get_logger
log = get_logger("agent_16")

class SubtitleDesigner:
    async def generate_subtitles(self, script_segments, emotion_map, style="word_by_word_pop"):
        log.info(f"Generating subtitles for {len(script_segments)} segments")
        lines = []
        for i, seg in enumerate(script_segments):
            em = emotion_map[i].get("primary_emotion","HIGH_ENERGY") if i < len(emotion_map) else "HIGH_ENERGY"
            words = seg.get("text","").split()
            duration = seg.get("end",5) - seg.get("start",0)
            lines.append({"segment": seg.get("segment"), "start": seg.get("start",0), "end": seg.get("end",5),
                         "words": words, "word_duration": duration/max(len(words),1), "emotion": em, "full_text": seg.get("text","")})
        return {"style": style, "subtitle_lines": lines, "total_lines": len(lines)}

    async def generate_srt_file(self, subtitle_data):
        lines = subtitle_data.get("subtitle_lines",[])
        parts = []
        for i, line in enumerate(lines,1):
            s = int(line["start"]); e = int(line["end"])
            parts.append(f"{i}\n{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d},000 --> {e//3600:02d}:{(e%3600)//60:02d}:{e%60:02d},000\n{line['full_text']}\n")
        return {"format": "srt", "content": "\n".join(parts), "lines": len(lines)}

subtitle_designer = SubtitleDesigner()
