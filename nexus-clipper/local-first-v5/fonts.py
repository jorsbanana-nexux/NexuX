from __future__ import annotations

import hashlib
import re
from pathlib import Path

ALLOWED = {".ttf", ".otf", ".woff", ".woff2"}


def safe_font_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", name).strip()
    return cleaned[:120] or "font"


def validate_font(path: Path) -> None:
    if path.suffix.lower() not in ALLOWED:
        raise ValueError(f"Unsupported font type: {path.suffix}")
    if path.stat().st_size < 256:
        raise ValueError("Font file is too small to be valid")
    data = path.read_bytes()[:16]
    valid = (
        data[:4] in {b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"}
        or data[:4] == b"wOFF"
        or data[:4] == b"wOF2"
    )
    if not valid:
        raise ValueError("Font signature is not recognized")


def install_font(source: Path, fonts_dir: Path) -> dict[str, str]:
    validate_font(source)
    fonts_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    name = safe_font_name(source.stem)
    target = fonts_dir / f"{name}-{digest}{source.suffix.lower()}"
    target.write_bytes(source.read_bytes())
    return {"name": name, "path": str(target), "sha256_12": digest}


def list_fonts(fonts_dir: Path) -> list[dict[str, str]]:
    fonts_dir.mkdir(parents=True, exist_ok=True)
    return [
        {"name": p.stem, "path": str(p), "extension": p.suffix.lower()}
        for p in sorted(fonts_dir.iterdir())
        if p.suffix.lower() in ALLOWED and p.is_file()
    ]
