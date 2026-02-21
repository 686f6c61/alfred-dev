#!/usr/bin/env python3
"""
Hook PreCompact: reinyecta decisiones criticas como contexto protegido.

Al compactar el contexto de la sesion, Claude puede perder las decisiones
inyectadas al inicio. Este hook reconstruye un bloque de contexto con las
decisiones de la iteracion activa (o las mas recientes) para que sobrevivan
a la compactacion.

Politica: fail-open. Si algo falla, sale con exit 0.
"""

import json
import os
import re
import sys
from typing import Any, Dict, List


def build_compact_context(decisions: List[Dict[str, Any]]) -> str:
    """Construye el texto de contexto protegido para la compactacion.

    Formatea las decisiones criticas en un bloque Markdown que se inyecta
    como contexto adicional durante la compactacion. Esto garantiza que
    las decisiones importantes sobrevivan al recorte del historial.

    Args:
        decisions: lista de diccionarios de decisiones de MemoryDB.

    Returns:
        Texto formateado para inyectar, o cadena vacia si no hay decisiones.
    """
    if not decisions:
        return ""

    lines = [
        "## Decisiones criticas de la sesion (protegidas contra compactacion)\n"
    ]
    for d in decisions:
        titulo = d.get("title", "sin titulo")
        elegida = d.get("chosen", "")
        fecha = d.get("decided_at", "")[:10]
        lines.append(f"- [{fecha}] **{titulo}**: {elegida}")

    lines.append(
        "\nEstas decisiones se reinyectan automaticamente por el hook "
        "memory-compact para mantener coherencia entre sesiones."
    )
    return "\n".join(lines)


def main():
    """Punto de entrada del hook PreCompact."""
    # Comprobar si la memoria esta habilitada
    config_path = os.path.join(os.getcwd(), ".claude", "alfred-dev.local.md")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = r"memoria:\s*\n(?:\s*#[^\n]*\n|\s*\w+:[^\n]*\n)*?\s*enabled:\s*true"
        if not re.search(pattern, content):
            sys.exit(0)
    except (OSError, FileNotFoundError):
        sys.exit(0)

    # Importar MemoryDB
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, plugin_root)

    try:
        from core.memory import MemoryDB
    except ImportError:
        sys.exit(0)

    db_path = os.path.join(os.getcwd(), ".claude", "alfred-memory.db")
    if not os.path.isfile(db_path):
        sys.exit(0)

    try:
        db = MemoryDB(db_path)

        # Obtener decisiones de la iteracion activa o las ultimas
        active = db.get_active_iteration()
        if active:
            decisions = db.get_decisions(iteration_id=active["id"], limit=10)
        else:
            decisions = db.get_decisions(limit=5)

        context = build_compact_context(decisions)
        db.close()

        if context:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreCompact",
                    "suppressOutput": False,
                    "additionalContext": context,
                }
            }
            print(json.dumps(output))
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
