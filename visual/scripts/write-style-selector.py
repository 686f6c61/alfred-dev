#!/usr/bin/env python3
"""Genera las pantallas guiadas de selección de Selina."""

from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.selina_style_selector import write_style_selector_html


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generar la pantalla de sistema base o la de tipografía/paleta de Selina"
    )
    parser.add_argument("--visual-path", required=True, help="Ruta a session_dir o state_dir del servidor visual")
    parser.add_argument(
        "--style-id",
        help="Si se indica, renderiza la segunda pantalla con combinaciones de tipografía y paleta para esa familia.",
    )
    parser.add_argument("--title", help="Título opcional para la pantalla.")
    parser.add_argument("--subtitle", help="Subtítulo opcional para la pantalla.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = write_style_selector_html(
        args.visual_path,
        style_id=args.style_id,
        title=args.title,
        subtitle=args.subtitle,
    )
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
