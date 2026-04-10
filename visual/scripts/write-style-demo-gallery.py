#!/usr/bin/env python3
"""Genera una galeria de demos visuales del catalogo de Selina."""

from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.selina_style_demo import write_style_demo_gallery


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generar galería y landings simples del catálogo de sistemas de diseño de Selina"
    )
    parser.add_argument(
        "--visual-path",
        required=True,
        help="Ruta a session_dir o state_dir del servidor visual",
    )
    parser.add_argument("--title", help="Titulo opcional para la galeria.")
    parser.add_argument("--subtitle", help="Subtitulo opcional para la galeria.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = write_style_demo_gallery(
        args.visual_path,
        title=args.title,
        subtitle=args.subtitle,
    )
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
