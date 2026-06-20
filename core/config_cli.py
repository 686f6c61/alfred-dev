#!/usr/bin/env python3
"""CLI determinista para la superficie de `/alfred-dev:config`."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_loader import (
    build_config_section_menu,
    build_config_section_summaries,
    ensure_bootstrap_local_config,
    load_project_config,
)


def _config_path(project_dir: Path) -> Path:
    return project_dir / ".claude" / "alfred-dev.local.md"


def _build_summary(project_dir: Path, *, headless: bool) -> dict:
    config_path = _config_path(project_dir)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    changed = ensure_bootstrap_local_config(str(config_path))
    config = load_project_config(str(project_dir))
    return {
        "project_dir": str(project_dir),
        "config_path": str(config_path),
        "created_or_normalized": changed,
        "headless": headless,
        "sections": build_config_section_summaries(config, project_dir=str(project_dir)),
        "menu": build_config_section_menu(config, project_dir=str(project_dir)),
    }


def _render_markdown(summary: dict) -> str:
    lines: list[str] = [
        "# Configuracion de Alfred Dev",
        "",
        f"- Config: `{summary['config_path']}`",
        "- Estado del fichero: "
        + ("creado/normalizado" if summary["created_or_normalized"] else "ya estaba listo"),
        "",
        "## Secciones actuales",
        "",
        "| Seccion | Resumen |",
        "|---|---|",
    ]
    for section in summary["sections"]:
        lines.append(f"| {section['label']} | {section['summary']} |")

    if summary["headless"]:
        lines.extend(
            [
                "",
                "CONFIG_HEADLESS_MENU",
                "",
                "En modo no interactivo no se espera una seleccion humana. "
                "Este es el menu que debe mostrarse en una sesion interactiva:",
                "",
                "```json",
                json.dumps(summary["menu"], ensure_ascii=False, indent=2),
                "```",
                "",
                "Para modificar valores, ejecuta `/alfred-dev:config` en una sesion interactiva "
                "o indica la seccion y el cambio de forma explicita.",
            ]
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", help="Emite JSON estructurado.")
    parser.add_argument("--headless", action="store_true", help="Incluye salida fallback para claude -p.")
    args = parser.parse_args(argv)

    summary = _build_summary(Path(args.project_dir).resolve(), headless=args.headless)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(_render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
