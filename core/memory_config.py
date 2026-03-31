#!/usr/bin/env python3
"""
Lectura ligera de la configuracion de memoria de Alfred por proyecto.

El fichero ``.claude/alfred-dev.local.md`` usa frontmatter YAML simple.
Este modulo evita depender de PyYAML y expone una API pequeña para leer
la subseccion ``memoria`` con defaults consistentes.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

DEFAULT_MEMORY_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "sync_to_native": True,
    "sync_commits_limit": 10,
    "capture_decisions": True,
    "capture_commits": True,
    "retention_days": 365,
}


def _coerce_value(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""

    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def _extract_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    if lines[0].strip() != "---":
        return text

    collected = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        collected.append(line)
    return "\n".join(collected)


def load_memory_config(project_dir: str) -> Dict[str, Any]:
    """
    Devuelve la configuracion efectiva de ``memoria`` para un proyecto.

    Si el fichero no existe o la seccion no aparece, devuelve defaults.
    """
    config = dict(DEFAULT_MEMORY_CONFIG)
    config_path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")

    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            content = handle.read()
    except OSError:
        return config

    frontmatter = _extract_frontmatter(content)
    lines = frontmatter.splitlines()

    memoria_indent: Optional[int] = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped != "memoria:":
            continue

        memoria_indent = len(line) - len(line.lstrip(" "))
        for child in lines[index + 1:]:
            child_stripped = child.strip()
            if not child_stripped or child_stripped.startswith("#"):
                continue

            child_indent = len(child) - len(child.lstrip(" "))
            if child_indent <= memoria_indent:
                break
            if ":" not in child_stripped:
                continue

            key, raw_value = child_stripped.split(":", 1)
            key = key.strip()
            if key in config:
                config[key] = _coerce_value(raw_value)
        break

    return config


def is_memory_enabled(project_dir: str) -> bool:
    """Atajo para comprobar si la memoria persistente esta activa."""
    return bool(load_memory_config(project_dir).get("enabled", False))
