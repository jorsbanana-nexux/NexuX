from __future__ import annotations

import argparse
import json
from pathlib import Path

from transcription import transcribe


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--language", default=None)
    args = parser.parse_args()
    result = transcribe(Path(args.input), language=args.language or None)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
