"""AGENT_20_PROFESSIONAL_EDITOR - safe compatibility wrapper.

The legacy evasion transform set has intentionally been removed. Canonical NexuX
renders source footage without fingerprint-evasion transforms.
"""

from pathlib import Path
from utils.logger import get_logger
from utils.config import get_settings

log = get_logger("agent_20")
settings = get_settings()


class ProfessionalEditor:
    def __init__(self):
        self.output_dir = Path(settings.OUTPUT_DIR) / "renders"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def render(self, render_config):
        pid = str(render_config.get("project_id", "unknown"))
        if render_config.get("evasion_params"):
            raise ValueError("Evasion transforms are not supported by NexuX")
        source = render_config.get("source") or render_config.get("source_path")
        if not source:
            return {
                "success": False,
                "project_id": pid,
                "output_path": str(self.output_dir / f"{pid}_final.mp4"),
                "error": "A source path is required; use the canonical Local-First V5 compositor for rendering.",
            }
        return {
            "success": False,
            "project_id": pid,
            "source": str(source),
            "output_path": str(self.output_dir / f"{pid}_final.mp4"),
            "evasion_applied": False,
            "note": "Legacy agent isolated. Canonical rendering is handled by Local-First V5.",
        }


professional_editor = ProfessionalEditor()
