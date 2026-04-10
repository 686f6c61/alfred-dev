#!/usr/bin/env python3
"""Genera style-options.html a partir del sidecar de propuestas de Selina."""

from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.selina_style_options import write_style_options_html


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generar style-options.html desde el sidecar de Selina")
    parser.add_argument("--visual-path", required=True, help="Ruta a session_dir o state_dir del servidor visual")
    parser.add_argument(
        "--proposals-file",
        help="Ruta opcional al sidecar JSON de propuestas. Si se omite, se autodetecta.",
    )
    parser.add_argument("--title", help="Titulo opcional para la pantalla de seleccion.")
    parser.add_argument("--subtitle", help="Subtitulo opcional para la pantalla de seleccion.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = write_style_options_html(
            args.visual_path,
            proposals_file=args.proposals_file,
            title=args.title,
            subtitle=args.subtitle,
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
