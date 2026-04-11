#!/usr/bin/env python3
"""Lee la última elección válida registrada por el servidor visual de Selina."""

from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.selina_style_selector import parse_guided_choice
from core.selina_visual import read_latest_style_choice, resolve_state_dir


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Leer la última elección visual de Selina")
    parser.add_argument("path", help="Ruta a session_dir o state_dir del servidor visual")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    state_dir = resolve_state_dir(args.path)
    choice = read_latest_style_choice(args.path)

    if choice is None:
        payload = {
            "status": "pending",
            "state_dir": state_dir,
            "message": "No hay ninguna elección válida registrada todavía.",
        }
    else:
        parsed_choice = parse_guided_choice(choice.get("choice"))
        payload = {
            "status": "ok",
            "state_dir": state_dir,
            **choice,
        }
        if parsed_choice:
            payload["parsed_choice"] = parsed_choice

    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
