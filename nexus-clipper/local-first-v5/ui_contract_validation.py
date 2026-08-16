from __future__ import annotations

from fastapi import HTTPException

from ui_contract import ANIMATIONS, ASPECT_RATIOS, POSITIONS, SUBTITLE_STYLES, require_choice, require_color


def validate_generate_request(req) -> None:
    try:
        require_choice(req.aspect_ratio, ASPECT_RATIOS, "aspect_ratio")
        require_choice(req.subtitle_style, SUBTITLE_STYLES, "subtitle_style")
        require_choice(req.animation, ANIMATIONS, "animation")
        require_choice(req.position, POSITIONS, "position")
        require_color(req.primary_color, "primary_color")
        require_color(req.highlight_color, "highlight_color")
        require_color(req.stroke_color, "stroke_color")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
