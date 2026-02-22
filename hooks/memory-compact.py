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
from typing import Any, Dict, List, Optional


def build_compact_context(
    decisions: List[Dict[str, Any]],
    pinned_items: Optional[List[Dict[str, Any]]] = None,
    pending_actions: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Construye el texto de contexto protegido para la compactacion.

    Incluye decisiones criticas, elementos marcados por el usuario y
    acciones pendientes del dashboard GUI para garantizar continuidad
    completa entre sesiones.

    Args:
        decisions: lista de diccionarios de decisiones.
        pinned_items: elementos marcados (opcionales).
        pending_actions: acciones pendientes de la GUI (opcionales).

    Returns:
        Texto formateado para inyectar.
    """
    if not decisions and not pinned_items and not pending_actions:
        return ""

    lines = []

    if decisions:
        lines.append(
            "## Decisiones criticas de la sesion (protegidas contra compactacion)\n"
        )
        for d in decisions:
            titulo = d.get("title", "sin titulo")
            elegida = d.get("chosen", "")
            fecha = d.get("decided_at", "")[:10]
            lines.append(f"- [{fecha}] **{titulo}**: {elegida}")

    if pinned_items:
        lines.append("\n## Elementos marcados por el usuario\n")
        for item in pinned_items:
            tipo = item.get("item_type", "?")
            ref = item.get("item_ref") or f"id:{item.get('item_id', '?')}"
            nota = item.get("note", "")
            auto = " (auto)" if item.get("auto_pinned") else ""
            lines.append(f"- [{tipo}] {ref}: {nota}{auto}")

    if pending_actions:
        lines.append("\n## Acciones pendientes desde el dashboard\n")
        for action in pending_actions:
            tipo = action.get("action_type", "?")
            payload = action.get("payload", "{}")
            lines.append(f"- {tipo}: {payload}")

    lines.append(
        "\nContexto reinyectado por memory-compact para mantener coherencia."
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

        active = db.get_active_iteration()
        if active:
            decisions = db.get_decisions(iteration_id=active["id"], limit=10)
        else:
            decisions = db.get_decisions(limit=5)

        # Recopilar elementos marcados y acciones pendientes
        pinned_items = db.get_pinned_items()
        pending_actions = db.get_pending_actions()

        context = build_compact_context(decisions, pinned_items, pending_actions)
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
