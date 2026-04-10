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
import sys
from typing import Any, Dict, List, Optional


def build_compact_context(
    decisions: List[Dict[str, Any]],
) -> str:
    """Construye el texto de contexto protegido para la compactacion.

    Incluye las decisiones criticas de la sesion para garantizar
    continuidad entre compactaciones.

    Args:
        decisions: lista de diccionarios de decisiones.

    Returns:
        Texto formateado para inyectar.
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
        "\nContexto reinyectado por memory-compact para mantener coherencia."
    )
    return "\n".join(lines)


def _is_memory_enabled(project_dir: str) -> bool:
    """Consulta la configuración canónica de memoria del proyecto."""
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)

    try:
        from core.memory_config import is_memory_enabled
    except ImportError:
        return False

    return is_memory_enabled(project_dir)


def main():
    """Punto de entrada del hook PreCompact."""
    # Comprobar si la memoria esta habilitada
    project_dir = os.getcwd()
    if not _is_memory_enabled(project_dir):
        sys.exit(0)

    # Importar MemoryDB
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, plugin_root)

    try:
        from core.memory import MemoryDB
    except ImportError:
        sys.exit(0)

    db_path = os.path.join(project_dir, ".claude", "alfred-memory.db")
    if not os.path.isfile(db_path):
        sys.exit(0)

    try:
        db = MemoryDB(db_path)

        active = db.get_active_iteration()
        if active:
            decisions = db.get_decisions(iteration_id=active["id"], limit=10)
            if not decisions:
                decisions = db.get_decisions(limit=5)
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
