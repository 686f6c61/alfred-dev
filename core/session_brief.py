#!/usr/bin/env python3
"""Briefing de sesión: qué hay abierto, qué se decidió y cómo hablarle a Alfred."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from core.continuity import (
    MEMORY_DB_RELATIVE_PATH,
    STATE_RELATIVE_PATH,
    get_pending_gate,
    load_handoff,
    load_state,
    load_uat,
    suggest_verify_action,
)
from core.memory_config import is_memory_enabled
from core.project_docs import ADR_DIR, list_adr_files


CONVERSATION_PROTOCOL = """## Cómo hablarle a Alfred

Si el usuario describe trabajo, un bug, retomar, entregar o preguntar qué toca **sin** un slash command, actúa como `/alfred-dev:alfred`: elige la ruta y ejecútala. No ofrezcas el catálogo.

Ruta principal: `/alfred-dev:alfred`. Flujos: `/alfred-dev:feature`, `/alfred-dev:quick`, `/alfred-dev:fix`, `/alfred-dev:spike`, `/alfred-dev:audit`, `/alfred-dev:ship`. Estado: `/alfred-dev:progress`. Continuar: `/alfred-dev:retomar`.

Criterio, no menú:
- cambio local y acotado → `quick`, no abras un PRD
- bug o regresión → `fix`
- decisión de stack, auth o persistencia → ADR, no un comentario
- UAT pendiente o rechazada → no despliegues

Si Agent Teams está activo en esta sesión, úsalo para fases en paralelo; si no, usa la herramienta Agent. No reescribas `.claude/settings.json`.
"""


def _read(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _last_decisions(project_dir: str, limit: int = 2) -> List[Dict[str, str]]:
    if not is_memory_enabled(project_dir):
        return []
    db_path = os.path.join(project_dir, MEMORY_DB_RELATIVE_PATH)
    if not os.path.isfile(db_path):
        return []
    try:
        from core.memory import MemoryDB

        db = MemoryDB(db_path)
        try:
            rows = db.get_decisions(limit=limit)
        finally:
            db.close()
    except Exception:
        return []
    out: List[Dict[str, str]] = []
    for row in rows:
        title = str(row.get("title") or "").strip()
        chosen = str(row.get("chosen") or row.get("choice") or "").strip()
        if title:
            out.append({"title": title, "chosen": chosen})
    return out


def list_accepted_adrs(project_dir: str) -> List[str]:
    titles: List[str] = []
    for name in list_adr_files(project_dir):
        text = _read(os.path.join(project_dir, ADR_DIR, name))
        if not re.search(r"(?im)^\*\*Estado:\*\*\s*aceptado\b", text):
            continue
        heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        titles.append(heading.group(1).strip() if heading else name)
    return titles


def build_session_brief(project_dir: str) -> Dict[str, Any]:
    """Datos reales para el primer mensaje de la sesión."""
    root = os.path.abspath(project_dir)
    state_path = os.path.join(root, STATE_RELATIVE_PATH)
    state = load_state(state_path) if os.path.isfile(state_path) else None
    if not isinstance(state, dict):
        state = None

    phase = str((state or {}).get("fase_actual") or "")
    command = str((state or {}).get("comando") or "")
    description = str((state or {}).get("descripcion") or "")
    active = bool(state and phase and phase != "completado")

    handoff = load_handoff(root)
    pending_handoff = bool(handoff and not handoff.get("resolved", False))
    uat = load_uat(root) or {}
    uat_status = str(uat.get("status") or "")
    verify = suggest_verify_action(root)
    decisions = _last_decisions(root)
    adrs = list_accepted_adrs(root)

    next_step = ""
    if active:
        next_step = "/alfred-dev:retomar"
    elif pending_handoff:
        next_step = "/alfred-dev:retomar"
    elif verify is not None or uat_status in {"pending", "rejected"}:
        next_step = "/alfred-dev:uat"
    else:
        next_step = ""

    return {
        "active": active,
        "command": command,
        "phase": phase,
        "description": description,
        "pending_gate": get_pending_gate(state) if active else None,
        "pending_handoff": pending_handoff,
        "uat_status": uat_status,
        "verify_pending": verify is not None,
        "decisions": decisions,
        "accepted_adrs": adrs,
        "next_step": next_step,
    }


def render_brief_lines(brief: Dict[str, Any]) -> str:
    lines: List[str] = ["## Briefing"]
    if brief.get("active"):
        desc = brief.get("description") or "sin descripción"
        gate = brief.get("pending_gate") or "sin gate"
        lines.append(
            f"Sesión activa: `{brief.get('command')}` / `{brief.get('phase')}`. "
            f"{desc}. Gate: {gate}."
        )
        lines.append("Siguiente: `/alfred-dev:retomar`.")
    elif brief.get("pending_handoff"):
        lines.append("Hay un handoff pendiente. Siguiente: `/alfred-dev:retomar`.")
    elif brief.get("uat_status") == "rejected":
        lines.append("UAT rechazada. No despliegues. Revisa `docs/project/uat.md`.")
    elif brief.get("verify_pending") or brief.get("uat_status") == "pending":
        lines.append("UAT pendiente del último entregable. Siguiente: `/alfred-dev:uat`.")
    else:
        lines.append(
            "No hay sesión abierta. Si el repo ya tiene código y no hay mapa, "
            "prioriza `/alfred-dev:map-codebase`. Si no, pregunta qué quiere hacer."
        )

    decisions = brief.get("decisions") or []
    if decisions:
        first = decisions[0]
        chosen = f" → {first['chosen']}" if first.get("chosen") else ""
        lines.append(f"Última decisión: {first['title']}{chosen}.")

    adrs = brief.get("accepted_adrs") or []
    if adrs:
        lines.append("ADRs aceptados: " + "; ".join(adrs[:3]) + ".")
        lines.append("Si el trabajo contradice un ADR aceptado, dilo antes de escribir código.")
    return "\n".join(lines)


def render_session_start_context(project_dir: str = ".") -> str:
    """Texto que SessionStart inyecta en Claude. Fail-open en el hook."""
    brief = build_session_brief(project_dir)
    return CONVERSATION_PROTOCOL + "\n" + render_brief_lines(brief) + "\n"
