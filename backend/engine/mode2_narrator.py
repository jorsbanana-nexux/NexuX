"""
NexuX V9.5 — Mode 2: AI Narrative Engine
=========================================
Uses LLM API (OpenAI/Anthropic/Gemini) to write compelling commentary
that connects moments from multiple videos into one cohesive story.

The AI acts as a creative director:
- Analyzes all selected moments
- Writes a narrative script (hook → buildup → payoff)
- Decides pacing, SFX placement, transitions
- Generates title, hashtags, description
- Has HUMOR — understands sarcasm, irony, comedic timing
- Picks thumbnail frame description
"""
import json
import os
from typing import Dict, List, Optional
from logging import getLogger
from pathlib import Path

log = getLogger("nexus.mode2.narrator")


def _get_llm_config() -> Dict:
    """Get LLM configuration from environment or config file."""
    # Check for API keys in order of preference
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    
    if openai_key:
        return {
            "provider": "openai",
            "api_key": openai_key,
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
            "api_url": "https://api.openai.com/v1/chat/completions",
        }
    elif anthropic_key:
        return {
            "provider": "anthropic",
            "api_key": anthropic_key,
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            "api_url": "https://api.anthropic.com/v1/messages",
        }
    elif gemini_key:
        return {
            "provider": "gemini",
            "api_key": gemini_key,
            "model": os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
            "api_url": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
        }
    else:
        return {"provider": "none"}


def generate_narrative(
    keyword: str,
    moments: List[Dict],
    target_duration: int = 60,
) -> Dict:
    """Generate a complete narrative script for the compilation video.
    
    Uses LLM to:
    1. Analyze all moments
    2. Write commentary script (Indonesian)
    3. Structure story: hook (3s) → buildup → payoff
    4. Decide SFX, transitions, B-roll placement
    5. Generate title, hashtags, description
    6. Pick thumbnail moment
    
    Returns a complete production plan.
    """
    config = _get_llm_config()
    
    if config["provider"] == "none":
        log.warning("[Mode2] No LLM API key found — using fallback narrative")
        return _fallback_narrative(keyword, moments, target_duration)
    
    # Prepare context for the LLM
    moments_context = _format_moments_for_llm(moments, target_duration)
    
    prompt = f"""You are a professional video editor and creative director for viral YouTube Shorts content in Indonesian language.

KEYWORD: "{keyword}"
TARGET DURATION: {target_duration} seconds

You have {len(moments)} video moments from different YouTube videos. Here they are:

{moments_context}

Your job is to create a COMPLETE production plan for a viral YouTube Short. You must:

1. WRITE THE NARRATIVE SCRIPT (in Indonesian):
   - Hook (first 3 seconds): Something that stops people from scrolling. Use conflict, controversy, or curiosity.
   - Buildup: Connect moments with smooth transitions
   - Payoff: The most satisfying or shocking moment goes last
   - Be FUNNY when appropriate. Use sarcasm, irony, unexpected comparisons. Match the humor to the content.
   - Total narration should fit within {target_duration} seconds of speaking time

2. CHOOSE MOMENTS to include (you don't have to use all of them — pick the BEST ones)
   - Select 3-7 best moments that tell a story
   - Order them for maximum engagement
   - Each moment gets 5-15 seconds

3. FOR EACH SELECTED MOMENT, specify:
   - Which source video and time range to use
   - What the narrator says during this moment
   - Visual effects: zoom style, color grade, any transitions before/after
   - SFX: what sound effect and when (whoosh, impact, ding, riser, pop)
   - Text overlay: what text appears on screen (bold, punchy, 2-5 words)
   - B-roll: should we cut away to another moment? When and why?

4. GENERATE:
   - Title (catchy, Indonesian, with emoji if appropriate, max 100 chars)
   - 3-5 hashtags
   - Description (SEO-friendly, 200-300 chars)
   - Thumbnail suggestion: which moment and what text to overlay

Return as JSON with this structure:
{{
  "title": "...",
  "hashtags": ["...", "..."],
  "description": "...",
  "thumbnail": {{
    "moment_index": 0,
    "overlay_text": "...",
    "style": "dramatic|energetic|mysterious"
  }},
  "narration_script": "...",
  "segments": [
    {{
      "moment_index": 0,
      "narration": "...",
      "text_overlay": "...",
      "zoom_style": "slow_push|punch|subtle|ken_burns|oscillate|breath",
      "color_grade": "warm|cool|vibrant|cinematic|noir|vintage|hdr_pop|none",
      "transition_in": "hard_cut|fade|dissolve|zoom_in|slide_up|glitch|wipe_left",
      "sfx": [
        {{"type": "whoosh|impact|ding|pop|riser", "time_offset": 0.0, "reason": "..."}}
      ],
      "broll_from_moment": null,
      "duration_estimate": 10
    }}
  ],
  "total_estimated_duration": 60,
  "bgm_mood": "tense|upbeat|dramatic|quirky|melancholic|energetic|calm",
  "pacing_notes": "..."
}}

Be creative. Be funny when the content allows it. Be dramatic when needed. Think like a human editor, not a template machine."""

    # Call LLM API
    result = _call_llm(config, prompt)
    
    if result:
        try:
            # Parse the JSON from the response
            # The LLM might return markdown-wrapped JSON
            json_str = result
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            plan = json.loads(json_str)
            log.info(f"[Mode2] Narrative generated: {len(plan.get('segments', []))} segments")
            log.info(f"[Mode2] Title: {plan.get('title', 'N/A')}")
            return plan
        except json.JSONDecodeError as e:
            log.error(f"[Mode2] JSON parse failed: {e}")
            return _fallback_narrative(keyword, moments, target_duration)
    
    return _fallback_narrative(keyword, moments, target_duration)


def _call_llm(config: Dict, prompt: str) -> Optional[str]:
    """Call the configured LLM API."""
    import urllib.request
    import urllib.error
    
    try:
        if config["provider"] == "openai":
            payload = json.dumps({
                "model": config["model"],
                "messages": [
                    {"role": "system", "content": "You are a creative video editor AI that produces viral YouTube Shorts. You respond in JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
                "max_tokens": 4000,
            })
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['api_key']}",
            }
        elif config["provider"] == "anthropic":
            payload = json.dumps({
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000,
                "temperature": 0.8,
            })
            headers = {
                "Content-Type": "application/json",
                "x-api-key": config["api_key"],
                "anthropic-version": "2023-06-01",
            }
        elif config["provider"] == "gemini":
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 4000},
            })
            headers = {"Content-Type": "application/json"}
        else:
            return None
        
        req = urllib.request.Request(
            config["api_url"],
            data=payload.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        if config["provider"] == "openai":
            return data["choices"][0]["message"]["content"]
        elif config["provider"] == "anthropic":
            return data["content"][0]["text"]
        elif config["provider"] == "gemini":
            return data["candidates"][0]["content"]["parts"][0]["text"]
        
    except Exception as e:
        log.error(f"[Mode2] LLM call failed ({config['provider']}): {e}")
        return None


def _format_moments_for_llm(moments: List[Dict], target_duration: int) -> str:
    """Format moments into a readable context for the LLM."""
    lines = []
    for i, m in enumerate(moments):
        lines.append(f"--- Moment {i} ---")
        lines.append(f"Source: {m.get('video_title', 'Unknown')}")
        lines.append(f"URL: {m.get('video_url', '')}")
        lines.append(f"Time: {m['start']:.1f}s - {m['end']:.1f}s ({m['end']-m['start']:.1f}s)")
        lines.append(f"Text: {m.get('text', 'No text')}")
        lines.append("")
    return "\n".join(lines)


def _fallback_narrative(keyword: str, moments: List[Dict], target_duration: int) -> Dict:
    """Fallback narrative when no LLM is available."""
    # Pick best moments (first 5)
    selected = moments[:5]
    
    segments = []
    for i, m in enumerate(selected):
        narration = m.get("text", f"Momen {keyword} yang menarik ini.")
        segments.append({
            "moment_index": i,
            "narration": narration[:200],
            "text_overlay": keyword.upper()[:30],
            "zoom_style": "subtle" if i == 0 else "punch",
            "color_grade": "vibrant" if i % 2 == 0 else "cinematic",
            "transition_in": "hard_cut" if i == 0 else "fade",
            "sfx": [{"type": "whoosh", "time_offset": 0, "reason": "transition"}] if i > 0 else [],
            "broll_from_moment": None,
            "duration_estimate": min(15, m["end"] - m["start"]),
        })
    
    return {
        "title": f"YANG TERJADI KETIKA {keyword.upper()} 🔥",
        "hashtags": [f"#{keyword.replace(' ', '')}", "#shorts", "#viral"],
        "description": f"Kumpulan momen {keyword} terbaik!",
        "thumbnail": {
            "moment_index": 0,
            "overlay_text": keyword.upper(),
            "style": "energetic",
        },
        "narration_script": " | ".join(s["narration"] for s in segments),
        "segments": segments,
        "total_estimated_duration": sum(s["duration_estimate"] for s in segments),
        "bgm_mood": "energetic",
        "pacing_notes": "Fallback — no LLM available. Basic pacing.",
    }


def generate_tts_narration(
    script: str,
    output_path: Path,
    voice: str = "id-ID-ArdiNeural",
) -> Optional[Path]:
    """Generate TTS narration using edge-tts.
    
    Default voice: Indonesian male (Ardi).
    Other options: id-ID-GadisPratiwi (female), en-US-GuyNeural (English male)
    """
    try:
        import edge_tts
    except ImportError:
        log.warning("[Mode2] edge-tts not installed — cannot generate TTS")
        return None
    
    try:
        # Clean script for TTS
        clean = script.replace("|", " ").replace("  ", " ").strip()
        
        communicate = edge_tts.Communicate(clean, voice)
        
        # Save as MP3
        mp3_path = output_path.with_suffix(".mp3")
        communicate.save(str(mp3_path))
        
        # Convert to WAV for easier FFmpeg mixing
        import subprocess
        wav_path = output_path.with_suffix(".wav")
        cmd = ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", "44100", "-ac", "2", str(wav_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if r.returncode == 0 and wav_path.exists():
            mp3_path.unlink(missing_ok=True)
            return wav_path
        elif mp3_path.exists():
            return mp3_path
        
        return None
    except Exception as e:
        log.error(f"[Mode2] TTS generation failed: {e}")
        return None
