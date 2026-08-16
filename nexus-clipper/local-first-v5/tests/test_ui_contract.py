from ui_contract import (
    ANIMATIONS,
    ASPECT_RATIOS,
    POSITIONS,
    SUBTITLE_STYLES,
    canonicalize_fronted_values,
    require_choice,
    require_color,
)


def test_supported_ui_contract_choices() -> None:
    assert require_choice("9:16", ASPECT_RATIOS, "aspect_ratio") == "9:16"
    assert require_choice("hormozi", SUBTITLE_STYLES, "subtitle_style") == "hormozi"
    assert require_choice("pop", ANIMATIONS, "animation") == "pop"
    assert require_choice("bottom", POSITIONS, "position") == "bottom"
    assert require_color("#ffffff", "primary_color") == "#FFFFFF"


def test_fronted_intents_map_to_real_renderer_presets() -> None:
    assert canonicalize_fronted_values("minimal-aesthetic", "word-by-word") == ("minimalist", "pop")
    assert canonicalize_fronted_values("gamer-comic", "bounce-zoom") == ("gaming", "bounce")
    assert canonicalize_fronted_values("neon-cyberpunk", "pulse-glow") == ("neon", "flicker")
    assert canonicalize_fronted_values("anime-impact", "fade-drift") == ("mrbeast", "fade_slow")


def test_invalid_ui_contract_choices_fail_loudly() -> None:
    for value, allowed, field in (
        ("3:4", ASPECT_RATIOS, "aspect_ratio"),
        ("unknown", SUBTITLE_STYLES, "subtitle_style"),
        ("spin", ANIMATIONS, "animation"),
        ("left", POSITIONS, "position"),
    ):
        try:
            require_choice(value, allowed, field)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{field} accepted unsupported value {value!r}")

    try:
        require_color("yellow", "primary_color")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid color was accepted")
