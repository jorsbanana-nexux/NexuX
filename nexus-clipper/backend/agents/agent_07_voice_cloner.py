"""AGENT_07_VOICE_CLONER - optional network TTS compatibility agent."""

from pathlib import Path
from utils.logger import get_logger
from utils.config import get_settings

log = get_logger("agent_07")
settings = get_settings()

class VoiceCloner:
    """Optional edge-tts voice synthesis. Never reports success without an artifact."""

    def __init__(self):
        self.voice_profiles = {
            "male_deep": {"voice": "en-US-ChristopherNeural", "pitch": "-3Hz", "rate": "+5%"},
            "male_young": {"voice": "en-US-EricNeural", "pitch": "+0Hz", "rate": "+10%"},
            "male_narrator": {"voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+5%"},
            "gen_z_male": {"voice": "en-US-EricNeural", "pitch": "+1Hz", "rate": "+15%"},
            "mystery_male": {"voice": "en-US-GuyNeural", "pitch": "-2Hz", "rate": "+3%"},
            "horror": {"voice": "en-US-ChristopherNeural", "pitch": "-5Hz", "rate": "+2%"},
            "gaming": {"voice": "en-US-DavisNeural", "pitch": "+3Hz", "rate": "+12%"},
        }

    async def synthesize_speech(self, text, style="male_narrator", output_path=None, custom_pitch=None, custom_rate=None):
        if not text or not str(text).strip():
            return {"success": False, "error": "text_required"}
        profile = self.voice_profiles.get(style, self.voice_profiles["male_narrator"])
        pitch = custom_pitch or profile["pitch"]
        rate = custom_rate or profile["rate"]
        if not output_path:
            output_dir = Path(settings.OUTPUT_DIR) / "audio"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"tts_{style}_{abs(hash(text)) % 100000}.mp3")
        try:
            import edge_tts
        except ImportError:
            return {"success": False, "error": "optional_dependency_missing: edge-tts"}
        try:
            communicate = edge_tts.Communicate(text=text, voice=profile["voice"], pitch=pitch, rate=rate)
            await communicate.save(output_path)
            path = Path(output_path)
            if not path.exists() or path.stat().st_size == 0:
                return {"success": False, "error": "tts_artifact_missing", "audio_path": output_path}
            return {"success": True, "audio_path": output_path, "voice_used": profile["voice"], "pitch": pitch, "rate": rate}
        except Exception as exc:
            return {"success": False, "error": str(exc), "audio_path": output_path}

    async def synthesize_segments(self, segments, style="male_narrator"):
        output_dir = Path(settings.OUTPUT_DIR) / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for seg in segments:
            result = await self.synthesize_speech(
                text=seg.get("text", ""),
                style=style,
                output_path=str(output_dir / f"seg_{seg.get('segment', 'unknown')}.mp3"),
            )
            results.append({**result, "segment": seg.get("segment"), "start": seg.get("start", 0), "end": seg.get("end", 0), "text": seg.get("text", "")})
        ok = sum(1 for item in results if item.get("success"))
        return {"success": ok == len(results) and bool(results), "audio_segments": results, "total": len(results), "successful": ok}

    async def list_voices(self):
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            en = [v for v in voices if v.get("Locale", "").startswith("en-")]
            return {"success": True, "total": len(voices), "english": len(en), "voices": [{"name": v["ShortName"], "locale": v["Locale"]} for v in en[:30]]}
        except Exception as exc:
            return {"success": False, "error": str(exc), "profiles": list(self.voice_profiles.keys())}

voice_cloner = VoiceCloner()
