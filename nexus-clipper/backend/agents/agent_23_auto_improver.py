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

    # ------------------------------------------------------------------ #
    # Core feedback loop: quality results → improvement suggestions.
    # ------------------------------------------------------------------ #
    async def process(
        self,
        quality_results: Dict[str, Any],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Feedback loop: take quality/critique results and generate concrete
        improvement suggestions.

        Args:
            quality_results: dict from the quality checker / critic, e.g. with
                ``score`` (0..1), ``verdict``, ``issues`` (list[str]), and
                optional ``clip_index``.
            retry_count: current retry iteration (used to bound the loop).

        Returns:
            Dict with ``status`` and ``improvement_actions`` (list of dicts,
            each describing a targeted action, the triggering issue, and the
            expected score delta).
        """
        clip_idx = quality_results.get("clip_index", 0)
        verdict = str(quality_results.get("verdict", "")).upper()
        score = float(quality_results.get("score", 0) or 0)
        issues = quality_results.get("issues", []) or []

        # Already acceptable — no improvement needed.
        if verdict in ("GOLD", "ACCEPTABLE") or score >= 1.0:
            return {
                "status": "completed",
                "agent": "agent_23_auto_improver",
                "clip_index": clip_idx,
                "improvement_actions": [],
                "note": f"Quality already acceptable (verdict={verdict}, score={score:.3f}).",
            }

        # Exhausted retries — stop the loop honestly.
        if retry_count >= self.MAX_RETRIES:
            return {
                "status": "exhausted",
                "agent": "agent_23_auto_improver",
                "clip_index": clip_idx,
                "improvement_actions": [],
                "retry_count": retry_count,
                "note": f"Max retries ({self.MAX_RETRIES}) reached; no further actions generated.",
            }

        # If the quality results include a score below threshold but no issues
        # were reported, synthesise a generic "low score" issue so the loop can
        # still propose something.
        if not issues and score < 0.6:
            issues = [f"low score ({score:.2f})"]

        tried = self._attempted_fixes.get(clip_idx, [])
        improvement_actions: List[Dict[str, Any]] = []

        for issue in issues:
            issue_lower = str(issue).lower()
            for pattern, action in self.ACTION_MAP.items():
                if pattern in issue_lower:
                    if action not in tried:
                        delta = self._action_delta(action)
                        improvement_actions.append({
                            "action": action,
                            "trigger_issue": issue,
                            "expected_delta": delta,
                            "target_score": round(min(1.0, score + delta), 4),
                        })
                        if clip_idx not in self._attempted_fixes:
                            self._attempted_fixes[clip_idx] = []
                        self._attempted_fixes[clip_idx].append(action)
                    break

        # Fallback: nothing matched but quality is low — propose a re-render as
        # a last-resort technical action.
        if not improvement_actions and "RE_RENDER" not in tried:
            delta = self._action_delta("RE_RENDER")
            improvement_actions.append({
                "action": "RE_RENDER",
                "trigger_issue": "unclassified quality degradation",
                "expected_delta": delta,
                "target_score": round(min(1.0, score + delta), 4),
            })
            self._attempted_fixes.setdefault(clip_idx, []).append("RE_RENDER")

        if not improvement_actions:
            return {
                "status": "completed",
                "agent": "agent_23_auto_improver",
                "clip_index": clip_idx,
                "improvement_actions": [],
                "attempted_fixes": tried,
                "note": "All known fixes already attempted; no new actions available.",
            }

        total_delta = sum(a["expected_delta"] for a in improvement_actions)

        log.info(
            "[Improver] process(): clip %s → %d action(s), expected +%.3f",
            clip_idx, len(improvement_actions), total_delta,
        )

        return {
            "status": "completed",
            "agent": "agent_23_auto_improver",
            "clip_index": clip_idx,
            "retry_count": retry_count + 1,
            "current_score": round(score, 4),
            "target_score": round(min(1.0, score + total_delta), 4),
            "expected_improvement": round(total_delta, 4),
            "improvement_actions": improvement_actions,
        }

    def _action_delta(self, action: str) -> float:
        """Expected score delta for a single action."""
        return self._estimate_improvement([action])

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
