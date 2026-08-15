"""AGENT_21_QUALITY_INSPECTOR - compatibility adapter over Local-First V5 render QA."""

from utils.logger import get_logger

log = get_logger("agent_21")


class QualityInspector:
    async def inspect(self, render_result):
        output_path = None
        if isinstance(render_result, str):
            output_path = render_result
        elif isinstance(render_result, dict):
            output_path = render_result.get("output_path") or render_result.get("output")
            nested = render_result.get("render")
            if not output_path and isinstance(nested, dict):
                output_path = nested.get("output_path") or nested.get("output")

        if not output_path:
            return {
                "checks": {},
                "passed": 0,
                "total": 0,
                "score": 0,
                "verdict": "NEEDS_FIX",
                "error": "No rendered output path was provided",
            }

        try:
            from local_first_v5.vision_quality import inspect_render
        except ImportError:
            try:
                from vision_quality import inspect_render
            except ImportError as exc:
                return {"checks": {}, "passed": 0, "total": 0, "score": 0, "verdict": "NEEDS_FIX", "error": str(exc)}

        try:
            result = inspect_render(output_path)
            return result
        except Exception as exc:
            log.exception("Post-render inspection failed")
            return {"checks": {}, "passed": 0, "total": 0, "score": 0, "verdict": "NEEDS_FIX", "error": str(exc)}


quality_inspector = QualityInspector()
