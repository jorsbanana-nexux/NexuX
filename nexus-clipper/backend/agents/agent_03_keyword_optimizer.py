"""AGENT_03_KEYWORD_OPTIMIZER - Semantic Keyword Expansion"""

from typing import Dict, List, Any, Set
from utils.logger import get_logger

log = get_logger("agent_03")

class KeywordOptimizer:
    """Agent 03: Expands keywords into rich semantic keyword clouds."""

    async def expand_keywords(self, keywords, platform="tiktok", count=25):
        log.info(f"Expanding {len(keywords)} keywords for {platform}")
        all_expanded = set()
        modifiers = ["how to", "why does", "what is", "the truth about", "secret of",
                     "explained", "revealed", "nobody talks about", "rare", "hidden", "ultimate"]
        suffixes = ["explained in 60 seconds", "that will shock you", "you need to know",
                    "gone wrong", "in real life", "caught on camera", "viral moment"]
        for kw in keywords:
            kwl = kw.lower().strip()
            all_expanded.update([kwl, f"{kwl} video", f"{kwl} compilation", f"best {kwl}",
                                 f"what is {kwl}", f"how {kwl} works"])
            for adj in ["insane", "rare", "crazy", "shocking"]:
                all_expanded.add(f"{adj} {kwl}")
            for prefix in modifiers:
                all_expanded.add(f"{prefix} {kwl}")
            for suffix in suffixes:
                all_expanded.add(f"{kwl} {suffix}")
        final = list(dict.fromkeys(all_expanded))[:count]
        log.success(f"Generated {len(final)} keyword variants")
        return {"original_keywords": keywords, "expanded_count": len(final), "keywords": final,
                "keyword_groups": {"core": final[:5], "semantic": final[5:15], "long_tail": final[15:]}}

    async def analyze_trend_potential(self, keywords):
        results = []
        for kw in keywords:
            score = 50.0
            if 3 <= len(kw) <= 20: score += 15
            if any(kw.lower().startswith(w) for w in ["what","how","why"]): score += 20
            if any(w in kw.lower() for w in ["insane","secret","hidden","rare","shocking"]): score += 20
            results.append({"keyword": kw, "trend_score": min(round(score, 1), 100),
                           "recommendation": "strong" if score > 60 else "moderate"})
        results.sort(key=lambda x: x["trend_score"], reverse=True)
        return {"results": results, "average_score": round(sum(r["trend_score"] for r in results)/len(results), 1)}

keyword_optimizer = KeywordOptimizer()
