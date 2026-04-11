#!/usr/bin/env python3
"""Genera la ronda final de tres variantes desde la selección guiada de Selina."""

from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.selina_style_variants import write_guided_style_options


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generar style-options.html/json desde la selección guiada de Selina"
    )
    parser.add_argument("--visual-path", required=True, help="Ruta a session_dir o state_dir del servidor visual")
    parser.add_argument("--style-id", help="Sobrescribe la familia visual seleccionada.")
    parser.add_argument("--font-pairing-id", help="Sobrescribe el pairing tipográfico seleccionado.")
    parser.add_argument("--palette-mode", help="Sobrescribe el modo de paleta seleccionado.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = write_guided_style_options(
            args.visual_path,
            style_id=args.style_id,
            font_pairing_id=args.font_pairing_id,
            palette_mode=args.palette_mode,
        )
    except ValueError as exc:
        sys.stdout.write(
            json.dumps({"status": "pending", "message": str(exc)}, ensure_ascii=False) + "\n"
        )
        return 0

    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
