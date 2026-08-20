"""
NexuX V9.5 — Keyword Expander (Mode 2 Enhanced)
=================================================
Expands a single keyword into a rich set of related search terms
for much better YouTube search results in Mode 2.

Opus Clip doesn't have a keyword-based creative mode at all.
NexuX's Mode 2 is already unique — this makes it even better.

Expansion strategies:
1. Synonyms and related terms
2. Trending suffixes ("2026", "viral", "terbaru")
3. Question formats ("what is X", "why X")
4. Compound terms ("X explained", "X reaction")
5. Indonesian + English bilingual expansion
6. Niche-specific modifiers (gaming, tech, finance, etc.)
"""
import re
import logging
from typing import List, Dict, Tuple

log = logging.getLogger("nexus.keyword_expander")


# Bilingual synonym maps
SYNONYM_MAP = {
    "game": ["gaming", "gameplay", "game", "permainan"],
    "tech": ["technology", "teknologi", "gadget", "eletronik"],
    "money": ["finance", "uang", "keuangan", "investasi", "cuan"],
    "motivation": ["motivasi", "inspirasi", "inspiration", "self improvement"],
    "ai": ["artificial intelligence", "kecerdasan buatan", "chatgpt", "machine learning"],
    "music": ["lagu", "musik", "song", "cover"],
    "movie": ["film", "movie", "bioskop", "sinema"],
    "food": ["makanan", "kuliner", "cooking", "resep"],
    "travel": ["perjalanan", "traveling", "wisata", "liburan"],
    "fitness": ["olahraga", "workout", "gym", "fitnes"],
    "business": ["bisnis", "usaha", "entrepreneur", "startup"],
    "crypto": ["cryptocurrency", "bitcoin", "kripto", "btc", "web3"],
    "anime": ["anime", "manga", "otaku", "weeb"],
    "history": ["sejarah", "history", "historical", "fakta sejarah"],
    "science": ["sains", "ilmu", "scientific", "experiment"],
}

# Trending suffixes
TREND_SUFFIXES_EN = ["2026", "viral", "trending", "explained", "reaction", "best of",
                     "compilation", "moments", "highlights", "funny"]
TREND_SUFFIXES_ID = ["2026", "viral", "terbaru", "terbaik", "kocak", "lucu",
                     "keren", "beli", "review", "rekomendasi"]

# Question formats
QUESTION_FORMATS = [
    "what is {kw}",
    "why {kw}",
    "how {kw} works",
    "{kw} explained",
    "the truth about {kw}",
    "apa itu {kw}",
    "kenapa {kw}",
    "cara {kw}",
    "kebenaran tentang {kw}",
]

# Niche modifiers
NICHE_MODIFIERS = {
    "gaming": ["gameplay", "walkthrough", "speedrun", "boss fight", "easter egg"],
    "tech": ["review", "unboxing", "comparison", "vs", "specifications"],
    "finance": ["tips", "strategy", "for beginners", "mistakes to avoid", "passive income"],
    "motivation": ["speech", "advice", "habits", "discipline", "mindset"],
    "entertainment": ["best moments", "funny moments", "behind the scenes", "bloopers"],
    "education": ["tutorial", "for beginners", "step by step", "easy", "simple"],
}


def expand_keyword(
    keyword: str,
    max_terms: int = 15,
    language: str = "both",
    niche: str = None,
) -> List[str]:
    """
    Expand a single keyword into multiple related search terms.
    
    Args:
        keyword: The user's input keyword
        max_terms: Maximum number of expanded terms
        language: "en", "id", or "both"
        niche: Optional niche for more targeted expansion
    
    Returns:
        List of search terms (original keyword always first)
    """
    kw_lower = keyword.lower().strip()
    expanded = [keyword]  # Always include original
    
    # 1. Synonyms
    for key, synonyms in SYNONYM_MAP.items():
        if key in kw_lower or any(s in kw_lower for s in synonyms):
            for syn in synonyms:
                if syn.lower() not in kw_lower and syn not in expanded:
                    expanded.append(syn)
    
    # 2. Trending suffixes
    if language in ("en", "both"):
        for suffix in TREND_SUFFIXES_EN:
            term = f"{keyword} {suffix}"
            if term not in expanded:
                expanded.append(term)
    
    if language in ("id", "both"):
        for suffix in TREND_SUFFIXES_ID:
            term = f"{keyword} {suffix}"
            if term not in expanded:
                expanded.append(term)
    
    # 3. Question formats
    for fmt in QUESTION_FORMATS:
        term = fmt.format(kw=keyword)
        if term not in expanded:
            expanded.append(term)
    
    # 4. Niche-specific modifiers
    if niche and niche.lower() in NICHE_MODIFIERS:
        for mod in NICHE_MODIFIERS[niche.lower()]:
            term = f"{keyword} {mod}"
            if term not in expanded:
                expanded.append(term)
    
    # 5. Auto-detect niche from keyword
    if not niche:
        detected_niche = _detect_niche(kw_lower)
        if detected_niche:
            for mod in NICHE_MODIFIERS.get(detected_niche, [])[:3]:
                term = f"{keyword} {mod}"
                if term not in expanded:
                    expanded.append(term)
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for term in expanded:
        t_lower = term.lower()
        if t_lower not in seen:
            seen.add(t_lower)
            unique.append(term)
    
    log.info(f"[KeywordExpander] '{keyword}' → {len(unique[:max_terms])} expanded terms")
    
    return unique[:max_terms]


def _detect_niche(keyword: str) -> str:
    """Auto-detect the niche from the keyword."""
    niche_keywords = {
        "gaming": ["game", "gaming", "valorant", "minecraft", "fortnite", "mobile legends",
                   "genshin", "pubg", "dota", "lol", "gameplay"],
        "tech": ["tech", "technology", "iphone", "samsung", "laptop", "gadget", "ai",
                 "chatgpt", "tesla", "spacex"],
        "finance": ["money", "investasi", "saham", "crypto", "bitcoin", "trading",
                    "passive income", "bisnis", "usaha", "startup"],
        "motivation": ["motivasi", "motivation", "inspirasi", "sukses", "success",
                       "discipline", "habits", "mindset"],
        "entertainment": ["movie", "film", "anime", "music", "lagu", "drakor",
                          "netflix", "celebrity", "artis"],
        "education": ["belajar", "tutorial", "learn", "course", "education",
                      "sekolah", "kuliah", "tips belajar"],
    }
    
    for niche, keywords in niche_keywords.items():
        if any(k in keyword for k in keywords):
            return niche
    
    return None


def get_search_strategy(keyword: str, max_sources: int = 10) -> Dict:
    """
    Get a complete search strategy for Mode 2.
    
    Returns a plan for how to search YouTube:
    - Primary terms (search first)
    - Secondary terms (search if primary doesn't return enough)
    - Filter criteria (min duration, max duration, min views)
    """
    expanded = expand_keyword(keyword, max_terms=max_sources)
    
    # Primary: original + top 3 expanded
    primary = expanded[:4]
    
    # Secondary: remaining expanded terms
    secondary = expanded[4:]
    
    strategy = {
        "original_keyword": keyword,
        "primary_terms": primary,
        "secondary_terms": secondary,
        "filter": {
            "min_duration": 60,      # At least 1 minute (no shorts)
            "max_duration": 7200,    # Max 2 hours
            "prefer_captions": True, # Prefer videos with auto-captions
            "deduplicate_channels": True,  # Don't take 3 videos from same channel
        },
        "niche": _detect_niche(keyword.lower()),
    }
    
    log.info(f"[KeywordExpander] Strategy for '{keyword}': {len(primary)} primary + {len(secondary)} secondary terms")
    
    return strategy
