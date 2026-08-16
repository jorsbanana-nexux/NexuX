"""AGENT_22_AUDIENCE_PREDICTOR - V7.0 Editorial Consciousness
==============================================================
Real virality prediction using editorial intelligence, not buzzword counting.

The old agent had ~72% of its score as hardcoded constants. This version
uses the editorial consciousness engine's multi-dimensional analysis
to predict audience engagement based on:
- Narrative completeness (does the clip tell a story?)
- Hook intelligence (does it grab attention?)
- Emotional arc (does it take viewers on a journey?)
- Coherence (can viewers follow it standalone?)
- Momentum (does it build energy?)
"""
from typing import Dict, List, Any
from utils.logger import get_logger

log = get_logger("agent_22")


class AudiencePredictor:
    """
    V7.0: Evidence-based audience prediction.
    
    Instead of counting buzzwords and adding fixed constants, this predictor
    uses the editorial consciousness scores to estimate how audiences will
    respond. Every score component has a clear, explainable basis.
    """

    async def predict(self, project_data: Dict) -> Dict[str, Any]:
        """
        Predict audience engagement based on editorial analysis.
        
        Uses editorial scores (if available) or falls back to content analysis.
        Returns a verdict with specific evidence for WHY.
        """
        # Check if editorial scores are available
        editorial = project_data.get("editorial", {})

        if not editorial:
            # Fall back to basic analysis if no editorial data
            return self._basic_predict(project_data)

        # ── Evidence-based scoring ──
        scores = {
            "narrative_completeness": editorial.get("narrative_completeness", 0),
            "emotional_arc": editorial.get("emotional_arc", 0),
            "hook_intelligence": editorial.get("hook_intelligence", 0),
            "coherence": editorial.get("coherence", 0),
            "momentum": editorial.get("momentum", 0),
            "comedic_timing": editorial.get("comedic_timing", 0),
            "contextual_significance": editorial.get("contextual_significance", 0),
            "uniqueness": editorial.get("uniqueness", 0),
        }

        # Weight by what actually drives audience retention
        weights = {
            "hook_intelligence": 0.25,        # Hook = first 3 seconds = make or break
            "narrative_completeness": 0.20,    # Complete stories retain better
            "emotional_arc": 0.15,             # Emotional journeys keep viewers
            "coherence": 0.15,                # Confusion = bounce
            "momentum": 0.10,                 # Energy keeps attention
            "uniqueness": 0.07,               # Generic = scroll past
            "contextual_significance": 0.05,  # Less critical for standalone
            "comedic_timing": 0.03,           # Bonus if present
        }

        viral_score = sum(scores[k] * weights[k] for k in weights)
        viral_score = round(viral_score * 100, 1)

        # ── Generate evidence-based verdict ──
        evidence = []

        if scores["hook_intelligence"] >= 0.6:
            evidence.append("Strong hook — high probability of first-3-second retention")
        elif scores["hook_intelligence"] < 0.3:
            evidence.append("Weak hook — viewers likely to scroll past in first 3 seconds")

        if scores["narrative_completeness"] >= 0.7:
            evidence.append("Complete narrative arc — viewers will watch to the end")
        elif scores["narrative_completeness"] < 0.4:
            evidence.append("Incomplete narrative — viewers may lose interest mid-clip")

        if scores["emotional_arc"] >= 0.6:
            evidence.append("Strong emotional journey — high engagement and sharing potential")
        elif scores["emotional_arc"] < 0.3:
            evidence.append("Flat emotional arc — low engagement trigger")

        if scores["coherence"] >= 0.7:
            evidence.append("Standalone coherent — works without context")
        elif scores["coherence"] < 0.4:
            evidence.append("Fragment-like — viewers may feel they're missing context")

        if scores["momentum"] >= 0.6:
            evidence.append("Good energy trajectory — maintains viewer attention")

        if scores["uniqueness"] < 0.3:
            evidence.append("Generic content — may struggle to stand out")

        # ── Verdict ──
        if viral_score >= 75:
            verdict = "VIRAL_READY"
            recommendation = "Publish with confidence — strong across multiple dimensions"
        elif viral_score >= 60:
            verdict = "STRONG"
            recommendation = "Good potential — consider minor adjustments to hook"
        elif viral_score >= 45:
            verdict = "MODERATE"
            recommendation = "Decent content — needs stronger hook or narrative payoff"
        elif viral_score >= 30:
            verdict = "WEAK"
            recommendation = "Significant issues — consider revising clip selection"
        else:
            verdict = "UNLIKELY"
            recommendation = "This clip is unlikely to perform well — consider replacing"

        return {
            "viral_score": min(viral_score, 100),
            "verdict": verdict,
            "recommendation": recommendation,
            "evidence": evidence,
            "dimension_scores": {k: round(v * 100, 1) for k, v in scores.items()},
            "method": "editorial_consciousness_v64",
        }

    def _basic_predict(self, project_data: Dict) -> Dict[str, Any]:
        """Fallback prediction when editorial data isn't available."""
        clip_score = project_data.get("score", 0)
        score_pct = round(clip_score * 100, 1)

        if score_pct >= 70:
            verdict = "STRONG"
        elif score_pct >= 50:
            verdict = "MODERATE"
        else:
            verdict = "WEAK"

        return {
            "viral_score": score_pct,
            "verdict": verdict,
            "evidence": ["Basic algorithmic score — no editorial analysis available"],
            "method": "basic_fallback",
        }


audience_predictor = AudiencePredictor()
