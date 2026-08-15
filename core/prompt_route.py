#!/usr/bin/env python3
"""Clasifica un prompt en castellano y sugiere la ruta Alfred sin slash."""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, Optional, Tuple


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower().strip()


def _has_slash_command(text: str) -> bool:
    stripped = (text or "").lstrip()
    if stripped.startswith("/"):
        return True
    return bool(re.search(r"(?m)^/alfred-dev:", text or ""))


# Orden: el primero que encaja gana.
_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    (
        "retomar",
        (
            r"\b(sigue|seguir|continua|continuar|retoma|retomar)\b",
            r"donde lo deje",
            r"por donde iba",
            r"\bresume\b",
        ),
    ),
    (
        "uat",
        (
            r"\buat\b",
            r"aceptacion (manual|humana)",
            r"aprobado por (el )?usuario",
            r"rechazado",
            r"verificar (el )?entregable",
        ),
    ),
    (
        "ship",
        (
            r"\b(despliega|desplegar|publica|publicar)\b",
            r"\ba produccion\b",
            r"\brelease\b",
            r"\bship\b",
        ),
    ),
    (
        "lucius",
        (r"\blucius\b", r"segunda opinion"),
    ),
    (
        "audit",
        (
            r"\baudi(t|ta|tar|toria)\b",
            r"\bowasp\b",
            r"seguridad del (repo|proyecto)",
        ),
    ),
    (
        "map-codebase",
        (
            r"\bmapea\b",
            r"mapa del (repo|codigo|codebase)",
            r"que hay en este repo",
            r"\bbrownfield\b",
        ),
    ),
    (
        "progress",
        (
            r"como va( el proyecto)?\b",
            r"que hay abierto",
            r"\bkanban\b",
            r"estado del (flujo|proyecto)",
        ),
    ),
    (
        "memory",
        (
            r"que decidimos",
            r"por que elegimos",
            r"ultima decision",
        ),
    ),
    (
        "fix",
        (
            r"\b(peta|falla|fallo|rompe|roto|bug|error|regresion)\b",
            r"no funciona",
            r"\b500\b",
            r"\bexception\b",
        ),
    ),
    (
        "discuss",
        (
            r"no se (si|que|como)",
            r"que te parece",
            r"\baterrizar\b",
            r"\buna idea\b",
        ),
    ),
    (
        "feature",
        (
            r"nueva funcionalidad",
            r"\bfeature\b",
            r"queremos que",
            r"implementar (un|una|el|la)",
        ),
    ),
    (
        "quick",
        (
            r"\b(cambia|cambiar|ajusta|ajustar|renombra|renombrar)\b",
            r"\btypo\b",
            r"\bcta\b",
            r"texto del",
        ),
    ),
)

_COMMAND_HINT = {
    "retomar": "/alfred-dev:retomar",
    "uat": "/alfred-dev:uat",
    "ship": "/alfred-dev:ship",
    "lucius": "/alfred-dev:lucius",
    "audit": "/alfred-dev:audit",
    "map-codebase": "/alfred-dev:map-codebase",
    "progress": "/alfred-dev:progress",
    "memory": "/alfred-dev:alfred",
    "fix": "/alfred-dev:fix",
    "discuss": "/alfred-dev:discuss",
    "feature": "/alfred-dev:feature",
    "quick": "/alfred-dev:quick",
}


def classify_prompt(text: str) -> Optional[Dict[str, str]]:
    """Devuelve la ruta sugerida o None si no hay señal o ya hay slash."""
    if not (text or "").strip() or _has_slash_command(text):
        return None
    folded = _fold(text)
    if len(folded) < 4:
        return None
    for route, patterns in _RULES:
        for pattern in patterns:
            if re.search(pattern, folded):
                return {
                    "route": route,
                    "command": _COMMAND_HINT[route],
                }
    return None


def render_route_hint(match: Dict[str, str]) -> str:
    command = match["command"]
    if match["route"] == "memory":
        return (
            f"Esta petición pregunta por una decisión. Consulta la memoria "
            f"o `docs/adr/` y actúa como `{command}`. No inventes historial."
        )
    return (
        f"Esta petición, sin slash, encaja con `{command}`. "
        f"Actúa como ese comando. No pidas que lo escriba."
    )
