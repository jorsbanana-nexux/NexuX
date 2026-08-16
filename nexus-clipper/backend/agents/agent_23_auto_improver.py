"""AGENT_23_AUTO_IMPROVER - V6.4 Editorial Consciousness
===========================================================
Real self-healing improvement loop. No longer just a counter.

The old agent returned {"should_retry": True} with no diagnosis or change.
This version:
1. Diagnoses what specifically is wrong (from the critic's feedback)
2. Generates targeted improvement actions
3. Tracks what was tried to avoid repeating the same fix
4. Reports what improved and what didn't
"""
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

log = get_logger("agent_23")


class AutoImprover:
    """
    V6.4: Real improvement loop with diagnosis and learning.
    
    Instead of blindly retrying, this improver:
    - Reads the critic's specific issues
    - Maps issues to targeted actions
    - Tracks which fixes have been attempted
    - Reports improvement deltas
    - Knows when further improvement isn't possible
    """

    MAX_RETRIES = 3

    # Issue → action mapping
    ACTION_MAP = {
        "weak hook": "ADJUST_START",
        "low coherence": "EXPAND_BOUNDARIES",
        "incomplete narrative": "SEEK_PAYOFF",
        "flat emotional": "RETIME",
        "low editorial": "REPLACE",
        "technical quality": "RE_RENDER",
    }

    def __init__(self):
        self._attempted_fixes: Dict[int, List[str]] = {}  # clip_index → fixes tried

    async def analyze_and_improve(
        self,
        critique: Dict[str, Any],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Analyze critique and generate targeted improvement plan.
        
        Args:
            critique: Critique result from the critic engine
            retry_count: Current retry iteration
        
        Returns:
            Dict with should_retry, specific actions, and diagnosis
        """
        clip_idx = critique.get("clip_index", 0)
        verdict = critique.get("verdict", "")
        score = critique.get("score", 0)
        issues = critique.get("issues", [])

        # Already good enough
        if verdict in ("GOLD", "ACCEPTABLE"):
            return {
                "should_retry": False,
                "reason": f"Clip {clip_idx} already {verdict}",
                "actions": [],
            }

        # Max retries reached
        if retry_count >= self.MAX_RETRIES:
            return {
                "should_retry": False,
                "reason": f"Max retries ({self.MAX_RETRIES}) reached for clip {clip_idx}",
                "actions": [],
                "final_score": score,
            }

        # Diagnose issues and generate targeted actions
        actions = []
        diagnosis = []

        for issue in issues:
            issue_lower = issue.lower()

            # Map issue to action
            for pattern, action in self.ACTION_MAP.items():
                if pattern in issue_lower:
                    # Check if we already tried this fix
                    tried = self._attempted_fixes.get(clip_idx, [])
                    if action not in tried:
                        actions.append(action)
                        diagnosis.append(f"{action}: {issue}")
                        # Record the attempt
                        if clip_idx not in self._attempted_fixes:
                            self._attempted_fixes[clip_idx] = []
                        self._attempted_fixes[clip_idx].append(action)
                    break

        if not actions:
            # No new actions to try — we've exhausted options
            return {
                "should_retry": False,
                "reason": f"No new improvement actions available for clip {clip_idx}",
                "actions": [],
                "attempted_fixes": self._attempted_fixes.get(clip_idx, []),
                "final_score": score,
            }

        # Predict expected improvement
        expected_delta = self._estimate_improvement(actions)

        log.info(f"[Improver] Clip {clip_idx}: {len(actions)} actions — "
                 f"expected +{expected_delta:.3f} improvement")

        return {
            "should_retry": True,
            "retry_count": retry_count + 1,
            "actions": actions,
            "diagnosis": diagnosis,
            "attempted_fixes": self._attempted_fixes.get(clip_idx, []),
            "original_score": score,
            "target_score": min(1.0, score + expected_delta),
            "expected_improvement": expected_delta,
        }

    def _estimate_improvement(self, actions: List[str]) -> float:
        """Estimate how much improvement each action might bring."""
        deltas = {
            "ADJUST_START": 0.08,      # Better hook → significant
            "EXPAND_BOUNDARIES": 0.05,  # More context → moderate
            "SEEK_PAYOFF": 0.07,       # Complete narrative → significant
            "RETIME": 0.04,           # Better emotional capture → moderate
            "REPLACE": 0.10,          # Different clip → potentially large
            "RE_RENDER": 0.03,        # Technical fix → small
        }
        return sum(deltas.get(a, 0.02) for a in actions)

    def reset(self, clip_idx: Optional[int] = None):
        """Reset attempted fixes tracking."""
        if clip_idx is not None:
            self._attempted_fixes.pop(clip_idx, None)
        else:
            self._attempted_fixes.clear()


auto_improver = AutoImprover()
