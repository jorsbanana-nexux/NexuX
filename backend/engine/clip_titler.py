"""
NexuX V9.5 — Clip Titler (Auto Viral Title Generator)
=======================================================
Auto-generates SEO-optimized viral titles for each clip.

Opus Clip generates generic titles. NexuX generates titles that are:
1. Keyword-rich (SEO optimized for YouTube/TikTok search)
2. Emotionally compelling (curiosity gap, pattern interrupt)
3. Platform-specific (different styles for TikTok, Reels, Shorts)
4. Language-aware (Indonesian + English)
5. A/B tested patterns (multiple variations per clip)

Title Archetypes:
- The Question: "Why Did [X] Do This?"
- The Revelation: "The Truth About [X] Nobody Tells You"
- The Number: "5 Things [X] Doesn't Want You To Know"
- The Contrarian: "Everyone Is Wrong About [X]"
- The Story: "How [X] Changed Everything"
- The Challenge: "This Is Why [X] Is Harder Than You Think"
- The Behind-the-Scenes: "What Really Happened When [X]"
- The Bold Claim: "[X] Is The Most Important Thing In [Y]"
"""
import re
import random
import logging
from typing import Dict, List, Optional

log = logging.getLogger("nexus.clip_titler")


# Title templates (with placeholders)
TITLE_TEMPLATES = {
    "question": [
        "Why Did {subject} {action}?",
        "What If {subject} Is Wrong About {topic}?",
        "Is {subject} Really The Best {topic}?",
        "Kenapa {subject} {action}?",
        "Apa Benar {subject} {topic}?",
    ],
    "revelation": [
        "The Truth About {topic} Nobody Tells You",
        "What {subject} Doesn't Want You To Know About {topic}",
        "The Real Reason {subject} {action}",
        "Kebenaran Tentang {topic} Yang Tidak Orang Bicarkan",
        "Alasan Sebenarnya {subject} {action}",
    ],
    "numbered": [
        "3 Things About {topic} That Will Shock You",
        "5 Reasons {subject} Is Wrong About {topic}",
        "The #1 Mistake Everyone Makes With {topic}",
        "3 Fakta {topic} Yang Bikin Kamu Nggak Nyangka",
        "5 Alasan Kenapa {subject} {action}",
    ],
    "contrarian": [
        "Everyone Is Wrong About {topic}",
        "{subject} Is Actually Right About {topic}",
        "The Unpopular Truth About {topic}",
        "Semua Orang Salah Soal {topic}",
        "Pendapat Ngga Populer: {topic}",
    ],
    "story": [
        "How {subject} Changed Everything",
        "The Moment {subject} Realized {topic}",
        "What Happened When {subject} {action}",
        "Begini Ceritanya {subject} {action}",
        "Kisah {subject} Dan {topic}",
    ],
    "bold_claim": [
        "{subject} Is The Most Important {topic} Ever",
        "This Changes Everything About {topic}",
        "{subject} Just Changed The Game For {topic}",
        "{topic} Adalah Hal Paling Penting Pernah",
        "Ini Mengubah Semua Tentang {topic}",
    ],
    "curiosity": [
        "Wait Until You See What {subject} Did",
        "You Won't Believe What {subject} Said About {topic}",
        "The Crazy Part About {topic} Is...",
        "Tunggu Sampai Kamu Lihat Apa Yang {subject} Lakukan",
        "Tak Akan Percaya Apa {subject} Bilang Soal {topic}",
    ],
}

# Platform-specific suffixes
PLATFORM_SUFFIXES = {
    "tiktok": [" #fyp", " #viral", " #foryou", ""],
    "reels": [" #reels", " #viral", " #explore", ""],
    "shorts": [" #shorts", " #viral", " #youtube", ""],
    "general": [""],
}


def generate_clip_titles(
    clip: Dict,
    transcript_segments: List[Dict],
    hook_text: str = "",
    mode: str = "podcast",
    count: int = 5,
    language: str = "en",
    platform: str = "general",
) -> List[Dict]:
    """
    Generate multiple viral title variations for a clip.
    
    Args:
        clip: Clip candidate with start, end, text
        transcript_segments: Segments within the clip
        hook_text: The hook text (first 3 seconds)
        mode: "podcast" or "creative"
        count: Number of title variations
        language: "en" or "id"
        platform: "tiktok", "reels", "shorts", or "general"
    
    Returns:
        List of {"title": str, "archetype": str, "score": float, "language": str}
    """
    clip_text = " ".join(s.get("text", "") for s in transcript_segments).strip()
    
    # Extract subject, topic, and action from the clip
    subject, topic, action = _extract_entities(clip_text, hook_text, language)
    
    # Generate titles from all archetypes
    all_titles = []
    
    for archetype, templates in TITLE_TEMPLATES.items():
        # Pick templates appropriate for language
        lang_templates = _filter_by_language(templates, language)
        
        for template in lang_templates:
            try:
                title = template.format(
                    subject=subject or "This",
                    topic=topic or "This Topic",
                    action=action or "Did This",
                )
                
                # Add platform suffix
                suffix = random.choice(PLATFORM_SUFFIXES.get(platform, [""]))
                full_title = title + suffix
                
                # Score the title
                title_score = _score_title(full_title, archetype, clip_text, hook_text, language)
                
                all_titles.append({
                    "title": full_title,
                    "archetype": archetype,
                    "score": round(title_score, 1),
                    "language": language,
                    "platform": platform,
                    "character_count": len(full_title),
                })
            except (KeyError, ValueError):
                continue
    
    # Sort by score and return top N
    all_titles.sort(key=lambda t: t["score"], reverse=True)
    
    # Ensure variety (don't return 5 of the same archetype)
    seen_archetypes = set()
    varied_titles = []
    for t in all_titles:
        if t["archetype"] not in seen_archetypes:
            varied_titles.append(t)
            seen_archetypes.add(t["archetype"])
        if len(varied_titles) >= count:
            break
    
    # Fill remaining slots with best non-varied titles
    for t in all_titles:
        if len(varied_titles) >= count:
            break
        if t not in varied_titles:
            varied_titles.append(t)
    
    log.info(f"[ClipTitler] Generated {len(varied_titles)} titles for clip [{clip.get('start', 0):.0f}-{clip.get('end', 0):.0f}s]")
    if varied_titles:
        log.info(f"[ClipTitler] Top title: \"{varied_titles[0]['title']}\" ({varied_titles[0]['score']:.0f})")
    
    return varied_titles[:count]


def generate_hashtags(
    clip_text: str,
    mode: str = "podcast",
    language: str = "en",
    count: int = 8,
) -> List[str]:
    """Generate SEO-optimized hashtags for a clip."""
    hashtags = set()
    
    # Extract key terms
    words = re.findall(r'\b[A-Za-z]{4,}\b', clip_text.lower())
    
    # Add common viral hashtags
    viral_tags = ["viral", "fyp", "foryou", "shorts"]
    if language == "id":
        viral_tags.extend(["viral", "fyp", "foryou"])
    
    for tag in viral_tags:
        hashtags.add(f"#{tag}")
    
    # Add mode-specific hashtags
    if mode == "podcast":
        hashtags.update(["#podcast", "#podcastclips", "#interview"])
    elif mode == "creative":
        hashtags.update(["#creative", "#compilation", "#shorts"])
    
    # Extract significant words from clip text
    stop_words = {"this", "that", "with", "from", "have", "they", "were", "been",
                  "yang", "dengan", "dari", "untuk", "pada", "dalam", "akan", "adalah",
                  "tidak", "akan", "sudah", "bisa", "harus", "lebih", "sangat"}
    
    word_freq = {}
    for w in words:
        if w not in stop_words and len(w) >= 4:
            word_freq[w] = word_freq.get(w, 0) + 1
    
    # Top words as hashtags
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    for word, freq in top_words:
        if len(hashtags) >= count:
            break
        if freq >= 2:
            hashtags.add(f"#{word}")
    
    return list(hashtags)[:count]


def generate_description(
    clip_text: str,
    title: str,
    mode: str = "podcast",
    language: str = "en",
    hashtags: List[str] = None,
) -> str:
    """Generate an SEO-optimized video description."""
    hashtags = hashtags or generate_hashtags(clip_text, mode, language)
    
    if language == "id":
        desc = f"{title}\n\n"
        desc += "Jangan lupa like, comment, dan subscribe untuk konten viral lainnya! 🔥\n\n"
        desc += " ".join(hashtags)
    else:
        desc = f"{title}\n\n"
        desc += "Don't forget to like, comment, and subscribe for more viral content! 🔥\n\n"
        desc += " ".join(hashtags)
    
    return desc


# ── Helpers ──

def _extract_entities(text: str, hook_text: str, language: str) -> tuple:
    """Extract subject, topic, and action from clip text."""
    text_lower = text.lower()
    
    # Try to find a person's name (capitalized words)
    names = re.findall(r'\b([A-Z][a-z]+)\b', text)
    subject = names[0] if names else None
    
    # Try to find the main topic (most frequent significant word)
    stop = {"the", "a", "an", "is", "was", "are", "were", "this", "that", "and", "or", "but",
            "yang", "dan", "atau", "tapi", "ini", "itu", "adalah", "tidak", "akan"}
    words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', text_lower) if w not in stop]
    
    if words:
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        topic = max(freq, key=freq.get) if freq else None
        topic = topic.capitalize() if topic else None
    else:
        topic = None
    
    # Try to find an action verb
    action_match = re.search(r'\b(said|did|made|went|told|explained|revealed|discovered|changed)\b', text_lower)
    if not action_match:
        action_match = re.search(r'\b(bilang|lakukan|buat|pergi|cerita|ungkap|temukan|ubah)\b', text_lower)
    action = action_match.group(0) if action_match else None
    
    return subject, topic, action


def _filter_by_language(templates: List[str], language: str) -> List[str]:
    """Filter templates by language (Indonesian templates contain Indonesian words)."""
    id_indicators = ["Kenapa", "Apa", "Kebenaran", "Alasan", "Semua", "Pendapat",
                     "Begini", "Kisah", "Tunggu", "Tak Akan", "Ini Mengubah", "3 Fakta",
                     "5 Alasan"]
    
    if language == "id":
        return [t for t in templates if any(ind in t for ind in id_indicators)]
    else:
        return [t for t in templates if not any(ind in t for ind in id_indicators)]


def _score_title(title: str, archetype: str, clip_text: str, hook_text: str, language: str) -> float:
    """Score a title's viral potential (0-100)."""
    score = 50.0
    
    # Length check (optimal: 30-70 chars for shorts)
    if 30 <= len(title) <= 70:
        score += 15.0
    elif len(title) > 100:
        score -= 10.0
    
    # Archetype scoring
    archetype_bonus = {
        "revelation": 12.0,   # Curiosity gap
        "contrarian": 10.0,   # Sparks debate
        "numbered": 10.0,     # Clickable format
        "question": 8.0,      # Engages viewer
        "curiosity": 11.0,    # Open loop
        "story": 7.0,         # Narrative hook
        "bold_claim": 9.0,    # Demands attention
    }
    score += archetype_bonus.get(archetype, 5.0)
    
    # Power words
    power_words = ["shocking", "truth", "secret", "nobody", "wrong", "crazy",
                   "gila", "kebenaran", "rahasia", "salah", "buset"]
    title_lower = title.lower()
    score += sum(3.0 for w in power_words if w in title_lower)
    
    # Emojis (slight bonus)
    if any(c in title for c in "🔥💯🤯😱"):
        score += 5.0
    
    # Relevance to clip content
    clip_lower = clip_text.lower()
    title_words = set(re.findall(r'\b[a-z]{4,}\b', title_lower))
    clip_words = set(re.findall(r'\b[a-z]{4,}\b', clip_lower))
    if title_words & clip_words:
        score += 10.0  # Title words appear in clip
    
    return min(100.0, score)
