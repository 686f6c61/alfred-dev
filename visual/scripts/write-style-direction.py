#!/usr/bin/env python3
"""Genera docs/style-direction.md a partir de la elección de Selina."""

from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.selina_style_direction import write_style_direction_artifact


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generar docs/style-direction.md desde la elección de Selina")
    parser.add_argument("--project-dir", required=True, help="Ruta raíz del proyecto")
    parser.add_argument("--visual-path", required=True, help="Ruta a session_dir o state_dir del servidor visual")
    parser.add_argument(
        "--proposals-file",
        help="Ruta opcional al sidecar JSON de propuestas. Si se omite, se autodetecta.",
    )
    parser.add_argument(
        "--choice",
        help="Sobrescribe la elección registrada y fuerza una opción concreta del sidecar.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = write_style_direction_artifact(
            os.path.abspath(args.project_dir),
            args.visual_path,
            proposals_file=args.proposals_file,
            choice_override=args.choice,
        )
    except ValueError as exc:
        payload = {
            "status": "pending",
            "message": str(exc),
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return 0

    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
