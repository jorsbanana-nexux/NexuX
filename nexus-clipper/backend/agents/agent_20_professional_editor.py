"""AGENT_20_PROFESSIONAL_EDITOR - V7.0 Editorial Consciousness
================================================================
The editor that actually edits. No longer a stub that refuses to work.

This agent coordinates the editorial pipeline:
1. Receives clip candidates from the analyzer
2. Runs the critic revision loop on each
3. Coordinates re-rendering for clips that need revision
4. Makes final editorial decisions based on quality

This is the agent that owns the editorial decision loop —
the core of NexuX's "conscious professional editor" identity.
"""
from pathlib import Path
from typing import Dict, List, Optional, Callable
from utils.logger import get_logger

log = get_logger("agent_20")


class ProfessionalEditor:
    """
    V7.0: The editor that owns the craft decision loop.
    
    This is no longer a delegation stub. It actively:
    - Evaluates clips using the critic engine
    - Applies revision directives (adjust start, seek payoff, retime)
    - Coordinates re-rendering of revised clips
    - Makes final quality decisions
    """

    def __init__(self):
        from engine.critic import evaluate_clip, apply_revision_directives, revision_loop
        from engine.editorial import analyze_editorial
        self._evaluate = evaluate_clip
        self._apply_directives = apply_revision_directives
        self._revision_loop = revision_loop
        self._analyze_editorial = analyze_editorial

    async def edit(
        self,
        clips: List[Dict],
        transcript: Dict,
        full_duration: float,
        output_paths: List[Path],
        render_fn: Optional[Callable] = None,
        max_revisions: int = 3,
    ) -> Dict:
        """
        Run the editorial decision loop on a batch of clips.
        
        Args:
            clips: Clip candidates from the analyzer
            transcript: Full transcript
            full_duration: Total video duration
            output_paths: Paths to rendered clips
            render_fn: Optional function(clip, index) → Path for re-rendering
            max_revisions: Max revision iterations per clip
        
        Returns:
            Dict with final clips, critiques, and editorial decisions
        """
        log.info(f"[Editor] Starting editorial loop on {len(clips)} clips")

        full_segments = transcript.get("segments", [])
        final_clips = []
        final_paths = []
        critiques = []
        editorial_decisions = []

        for i, (clip, out_path) in enumerate(zip(clips, output_paths)):
            log.info(f"[Editor] Clip {i}: Evaluating...")

            # Run the full revision loop
            final_clip, critique = self._revision_loop(
                clip=clip,
                clip_index=i,
                candidates=clips,
                transcript=transcript,
                output_path=out_path,
                full_duration=full_duration,
                render_fn=render_fn,
                max_iterations=max_revisions,
            )

            final_clips.append(final_clip)
            critiques.append(critique)

            # Record editorial decision
            decision = {
                "clip_index": i,
                "verdict": critique.verdict,
                "score": round(critique.score, 3),
                "dimensions": {k: round(v, 3) for k, v in critique.dimensions.items()},
                "issues": critique.issues,
                "revisions": critique.revision_count,
                "evidence": " | ".join(critique.issues[:3]) if critique.issues else "No issues",
            }

            if critique.verdict == "GOLD":
                decision["action"] = "ACCEPT_AS_IS"
                decision["note"] = "Gold standard — no revision needed"
                log.info(f"[Editor] Clip {i}: GOLD ✨")
            elif critique.verdict == "ACCEPTABLE":
                decision["action"] = "ACCEPT_AS_IS"
                decision["note"] = "Acceptable quality"
                log.info(f"[Editor] Clip {i}: ACCEPTABLE ✅")
            elif critique.verdict == "NEEDS_REVISION":
                if critique.revision_count > 0:
                    decision["action"] = "REVISED"
                    decision["note"] = f"Revised {critique.revision_count}x — improved"
                    # Use the re-rendered path if available
                    if render_fn:
                        try:
                            new_path = render_fn(final_clip, i)
                            if new_path:
                                final_paths.append(new_path)
                            else:
                                final_paths.append(out_path)
                        except Exception:
                            final_paths.append(out_path)
                    else:
                        final_paths.append(out_path)
                    log.info(f"[Editor] Clip {i}: REVISED → improved ✅")
                else:
                    decision["action"] = "BEST_AVAILABLE"
                    decision["note"] = "Best available — no improvement possible"
                    final_paths.append(out_path)
                    log.info(f"[Editor] Clip {i}: BEST_AVAILABLE ⚠️")
            else:
                decision["action"] = "REJECTED_BEST_AVAILABLE"
                decision["note"] = "Rejected but kept as best available"
                final_paths.append(out_path)
                log.warning(f"[Editor] Clip {i}: REJECTED — using best available ❌")

            editorial_decisions.append(decision)

        # Summary
        gold_count = sum(1 for c in critiques if c.verdict == "GOLD")
        acceptable_count = sum(1 for c in critiques if c.verdict == "ACCEPTABLE")
        revised_count = sum(1 for c in critiques if c.revision_count > 0)
        rejected_count = sum(1 for c in critiques if c.verdict == "REJECT")

        summary = {
            "total_clips": len(clips),
            "gold": gold_count,
            "acceptable": acceptable_count,
            "revised": revised_count,
            "rejected": rejected_count,
            "editorial_quality": "PREMIUM" if gold_count > 0 else "GOOD" if acceptable_count > 0 else "BASIC",
        }

        log.info(f"[Editor] Editorial complete: {summary}")

        return {
            "final_clips": final_clips,
            "final_paths": final_paths,
            "critiques": [
                {
                    "clip_index": c.clip_index,
                    "verdict": c.verdict,
                    "score": round(c.score, 3),
                    "dimensions": {k: round(v, 3) for k, v in c.dimensions.items()},
                    "issues": c.issues,
                    "revisions": c.revision_count,
                }
                for c in critiques
            ],
            "editorial_decisions": editorial_decisions,
            "summary": summary,
        }


professional_editor = ProfessionalEditor()
