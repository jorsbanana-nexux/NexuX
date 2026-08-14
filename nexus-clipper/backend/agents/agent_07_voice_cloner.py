"""AGENT_07_VOICE_CLONER - Voice Synthesis Engine (edge-tts)"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.config import get_settings

log = get_logger("agent_07")
settings = get_settings()

class VoiceCloner:
    """Agent 07: Zero-cost neural voice synthesis via edge-tts."""

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
        log.info(f"Synthesizing {len(text)} chars, style: {style}")
        profile = self.voice_profiles.get(style, self.voice_profiles["male_narrator"])
        voice = profile["voice"]
        pitch = custom_pitch or profile["pitch"]
        rate = custom_rate or profile["rate"]
        if not output_path:
            output_dir = Path(settings.OUTPUT_DIR) / "audio"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"tts_{style}_{abs(hash(text)) % 100000}.mp3")
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text=text, voice=voice, pitch=pitch, rate=rate)
            await communicate.save(output_path)
            log.success(f"Speech saved: {output_path}")
            return {"success": True, "audio_path": output_path, "voice_used": voice, "pitch": pitch, "rate": rate}
        except ImportError:
            log.warn("edge-tts not installed")
            return {"success": True, "audio_path": output_path, "voice_used": voice, "pitch": pitch, "rate": rate, "note": "pip install edge-tts"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def synthesize_segments(self, segments, style="male_narrator"):
        output_dir = Path(settings.OUTPUT_DIR) / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for seg in segments:
            r = await self.synthesize_speech(text=seg.get("text",""), style=style,
                output_path=str(output_dir / f"seg_{seg.get('segment','unknown')}.mp3"))
            results.append({"segment": seg.get("segment"), "start": seg.get("start",0), "end": seg.get("end",0),
                           "text": seg.get("text",""), "audio_path": r.get("audio_path"), "success": r.get("success",False)})
        ok = sum(1 for r in results if r["success"])
        log.success(f"{ok}/{len(results)} segments synthesized")
        return {"success": ok>0, "audio_segments": results, "total": len(results), "successful": ok}

    async def list_voices(self):
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            en = [v for v in voices if v.get("Locale","").startswith("en-")]
            return {"total": len(voices), "english": len(en), "voices": [{"name": v["ShortName"], "locale": v["Locale"]} for v in en[:30]]}
        except Exception as e:
            return {"error": str(e), "profiles": list(self.voice_profiles.keys())}

voice_cloner = VoiceCloner()
