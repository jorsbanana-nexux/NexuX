from __future__ import annotations

from pathlib import Path
import asyncio

VOICES = {
    "male_deep": "en-US-ChristopherNeural",
    "male_narrator": "en-US-GuyNeural",
    "male_young": "en-US-EricNeural",
    "gaming": "en-US-DavisNeural",
    "horror": "en-US-ChristopherNeural",
}


async def synthesize(text: str, output: Path, style: str = "male_narrator") -> Path:
    if not text.strip():
        raise ValueError("voiceover text is required")
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("optional_dependency_missing: edge-tts") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=VOICES.get(style, VOICES["male_narrator"]))
    await communicate.save(str(output))
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("voiceover artifact missing")
    return output


def synthesize_sync(text: str, output: Path, style: str = "male_narrator") -> Path:
    return asyncio.run(synthesize(text, output, style))
