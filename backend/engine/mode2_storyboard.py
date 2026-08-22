"""
NexuX V9.6 — Mode 2 Storyboard Planner
=======================================
Transforms ONE free-form keyword into an editable multi-clip storyboard
(viral Indonesian Shorts format): hook → context beats → payoff.

Pure async metadata functions + subprocess, no heavy deps at import.
"""
import asyncio
import re
from typing import Dict, List, Optional

from .mode2_search import search_youtube

# ── Universal Shorts narrative archetypes (EN + ID) ──
# Format: label, query template
ARCHETYPES = [
    ("Hook & Overview", "{kw}"),
    ("Kenapa / Why", "kenapa {kw}"),
    ("Fakta / Facts", "fakta {kw}"),
    ("Sisi Gelap / Dark Side", "sisi gelap {kw}"),
    ("Mindblowing", "mindblowing {kw}"),
]

# Additional query templates for broader semantic coverage
EXTRA_QUERIES = [
    "{kw} terbaru",
    "{kw} viral",
    "{kw} trending",
    "{kw} reaction",
    "{kw} analysis",
]


async def plan_storyboard(
    keyword: str,
    max_clips: int = 5,
    clips_per_archetype: int = 1,
    extra_queries: int = 3,
) -> Dict:
    """Build a storyboard from ONE keyword.

    Strategy:
    1. Expand keyword into archetype queries (kenapa X, fakta X, sisi gelap X…)
    2. Search YouTube for each archetype
    3. Deduplicate by URL
    4. Score & select the best clips across archetypes
    5. Return ordered storyboard (Hook → … → Payoff)

    Returns:
        {
          "keyword": str,
          "archetypes": [...],
          "storyboard": [ {clip_idx, video_title, video_url, duration,
                            reason, source_query, archetype} ... ],
          "clips_per_archetype": int,
          "total_clips": int,
        }
    """
    keyword = keyword.strip()
    if not keyword:
        return {
            "keyword": keyword,
            "archetypes": [],
            "storyboard": [],
            "clips_per_archetype": clips_per_archetype,
            "total_clips": 0,
        }

    # Build query list
    queries = []
    for label, tpl in ARCHETYPES:
        queries.append({"label": label, "query": tpl.format(kw=keyword)})
    for tpl in EXTRA_QUERIES[:extra_queries]:
        queries.append({"label": "Extra", "query": tpl.format(kw=keyword)})

    # Parallel search for all queries
    search_tasks = [
        asyncio.to_thread(search_youtube, q["query"], max_results=clips_per_archetype)
        for q in queries
    ]
    search_results = await asyncio.gather(*search_tasks)

    # Collect & dedupe clips
    seen_urls = set()
    storyboard = []
    for q_info, results in zip(queries, search_results):
        for r in results:
            url = r.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            storyboard.append({
                "archetype": q_info["label"],
                "source_query": q_info["query"],
                "video_title": r.get("title", "")[:120],
                "video_url": url,
                "duration": r.get("duration", 0),
                "view_count": r.get("view_count", 0),
                "channel": r.get("channel", ""),
                "reason": f"Query '{q_info['query']}' found this clip",
            })

    # Simple scoring: view count + title keyword relevance
    kw_words = set(keyword.lower().split())
    def _score(clip):
        title = clip["video_title"].lower()
        hits = sum(1 for w in kw_words if w in title)
        views = clip.get("view_count") or 0
        return hits * 10 + min(views // 10000, 20)  # cap view boost at 20

    storyboard.sort(key=_score, reverse=True)

    # Ensure we have clips from at least 2 archetypes if possible
    archetypes_present = {c["archetype"] for c in storyboard}
    if len(archetypes_present) < 2 and len(storyboard) > 2:
        # Reorder to diversify archetypes
        diverse = []
        used = set()
        for arch in archetypes_present:
            for c in storyboard:
                if c["archetype"] == arch and c["video_url"] not in used:
                    diverse.append(c)
                    used.add(c["video_url"])
                    break
        # Fill rest by score
        for c in storyboard:
            if c["video_url"] not in used:
                diverse.append(c)
                used.add(c["video_url"])
        storyboard = diverse

    # Truncate to max_clips
    storyboard = storyboard[:max_clips]

    # Label order positions
    for idx, clip in enumerate(storyboard, 1):
        clip["clip_idx"] = idx
        if idx == 1:
            clip["role"] = "hook"
        elif idx == len(storyboard):
            clip["role"] = "payoff"
        else:
            clip["role"] = "beat"

    return {
        "keyword": keyword,
        "archetypes": [a[0] for a in ARCHETYPES],
        "storyboard": storyboard,
        "clips_per_archetype": clips_per_archetype,
        "total_clips": len(storyboard),
    }
