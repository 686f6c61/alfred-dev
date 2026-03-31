#!/usr/bin/env python3
"""
Hook PreToolUse para evitar deriva tras consumir un prefetch helper-first.

Cuando un comando como `/alfred-dev:map-codebase` ya ha consumido el resultado
preparado por `UserPromptSubmit`, Claude ya tiene en contexto la respuesta final
lista. Este hook bloquea lecturas/escrituras/exploracion posteriores durante una
ventana corta para forzar que responda con ese resultado en lugar de rehacer el
trabajo manualmente.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


_MARKER_RELATIVE_PATH = os.path.join(".claude", "alfred-prefetch-consumed.json")
_PREFETCH_RELATIVE_PATH = os.path.join(".claude", "alfred-prefetch.json")
_PENDING_GUARD_COMMANDS = frozenset({"alfred", "map-codebase", "discuss", "memory-ui"})


def _discover_project_dir(data: dict) -> str:
    """Intenta resolver la raiz del proyecto a partir del tool input real."""
    candidates = []
    cwd = data.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        candidates.append(cwd)

    tool_input = data.get("tool_input", {}) or {}
    for key in ("file_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append(value)

    candidates.append(os.getcwd())

    for raw in candidates:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = Path(os.getcwd()) / candidate
        candidate = candidate.resolve()
        if candidate.is_file():
            candidate = candidate.parent

        for current in (candidate, *candidate.parents):
            if (current / ".claude").is_dir():
                return str(current)

    return os.getcwd()


def _load_active_marker(project_dir: str):
    marker_path = os.path.join(project_dir, _MARKER_RELATIVE_PATH)
    try:
        with open(marker_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        try:
            os.remove(marker_path)
        except OSError:
            pass
        return None

    if not isinstance(payload, dict):
        return None

    expires_at_raw = payload.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(expires_at_raw)
    except (TypeError, ValueError):
        expires_at = None

    if expires_at is None:
        try:
            os.remove(marker_path)
        except OSError:
            pass
        return None

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        try:
            os.remove(marker_path)
        except OSError:
            pass
        return None

    return payload


def _load_pending_prefetch(project_dir: str):
    prefetch_path = os.path.join(project_dir, _PREFETCH_RELATIVE_PATH)
    try:
        with open(prefetch_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    source_command = str(payload.get("source_command", "")).strip().lower()
    prefetched_command = str(payload.get("prefetched_command", "")).strip().lower()
    if not {source_command, prefetched_command} & _PENDING_GUARD_COMMANDS:
        return None

    expires_at_raw = payload.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(expires_at_raw)
    except (TypeError, ValueError):
        return None

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        return None

    return payload


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError):
        sys.exit(0)

    project_dir = _discover_project_dir(data)
    pending = _load_pending_prefetch(project_dir)
    if pending is not None:
        source_command = pending.get("source_command", "alfred")
        prefetched_command = pending.get("prefetched_command", source_command)
        tool_name = data.get("tool_name", "tool")
        print(
            f"[Alfred Dev] Bloqueado {tool_name}: hay un prefetch pendiente para "
            f"/alfred-dev:{source_command}. Consume primero el helper "
            f"({prefetched_command}) antes de leer o explorar el repo.",
            file=sys.stderr,
        )
        json.dump(
            {
                "decision": "block",
                "reason": (
                    "Hay un prefetch helper-first pendiente. "
                    "Ejecuta consume-prefetch antes de usar mas tools."
                ),
            },
            sys.stdout,
        )
        sys.exit(2)

    marker = _load_active_marker(project_dir)
    if marker is None:
        sys.exit(0)

    source_command = marker.get("source_command", "alfred")
    prefetched_command = marker.get("prefetched_command", source_command)
    tool_name = data.get("tool_name", "tool")

    print(
        f"[Alfred Dev] Bloqueado {tool_name}: el helper-first de "
        f"/alfred-dev:{source_command} ya devolvio una respuesta final lista. "
        f"Usa la salida del helper consumido ({prefetched_command}) y termina.",
        file=sys.stderr,
    )
    json.dump(
        {
            "decision": "block",
            "reason": (
                "El prefetch helper-first ya resolvio este comando. "
                "No uses mas tools; responde con la salida del helper."
            ),
        },
        sys.stdout,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
