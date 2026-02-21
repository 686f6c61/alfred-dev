#!/usr/bin/env python3
"""
Hook PostToolUse para Bash: captura automatica de commits en la memoria.

Intercepta comandos git commit ejecutados via Bash, extrae los metadatos
del commit (SHA, mensaje, autor, ficheros) y los registra en la base de
datos de memoria persistente del proyecto.

El hook actua como un observador pasivo: nunca bloquea la operacion.
Si algo falla, sale silenciosamente con exit 0 (politica fail-open).

Eventos capturados:
    - Cualquier git commit exitoso (exit code 0).
"""

import json
import os
import re
import subprocess
import sys


# Patron que detecta 'git commit' como comando real, no como argumento
# de otro comando (grep, echo, etc.). Solo detecta git commit al inicio
# de la linea o despues de operadores de shell (&&, ||, ;).
_GIT_COMMIT_RE = re.compile(
    r"(?:^|&&|\|\||;)\s*git\s+commit\b"
)


def is_git_commit_command(command: str) -> bool:
    """Determina si un comando contiene un git commit real.

    Args:
        command: comando de shell a analizar.

    Returns:
        True si contiene un git commit real.
    """
    return bool(_GIT_COMMIT_RE.search(command))


def main():
    """Punto de entrada del hook."""
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    command = tool_input.get("command", "")
    exit_code = tool_result.get("exit_code")

    # Solo actuar si es un git commit exitoso
    if not is_git_commit_command(command):
        sys.exit(0)
    if exit_code != 0:
        sys.exit(0)

    # Comprobar si la memoria esta habilitada
    if not _is_memory_enabled():
        sys.exit(0)

    # Extraer metadatos del ultimo commit
    try:
        result = subprocess.run(
            ["git", "log", "-1",
             "--format=%H|%s|%an|%aI",
             "--name-only"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            sys.exit(0)
    except Exception:
        sys.exit(0)

    lines = result.stdout.strip().split("\n")
    if not lines or "|" not in lines[0]:
        sys.exit(0)

    parts = lines[0].split("|", 3)
    sha = parts[0]
    message = parts[1] if len(parts) > 1 else ""
    author = parts[2] if len(parts) > 2 else ""
    files = [l.strip() for l in lines[1:] if l.strip()]

    # Registrar en la memoria
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
        db.log_commit(
            sha=sha, message=message, author=author,
            files=files, files_changed=len(files),
        )
        db.close()
    except Exception:
        sys.exit(0)


def _is_memory_enabled() -> bool:
    """Comprueba si la memoria esta habilitada en la configuracion local."""
    config_path = os.path.join(os.getcwd(), ".claude", "alfred-dev.local.md")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, FileNotFoundError):
        return False
    pattern = r"memoria:\s*\n(?:\s*#[^\n]*\n|\s*\w+:[^\n]*\n)*?\s*enabled:\s*true"
    return bool(re.search(pattern, content))


if __name__ == "__main__":
    main()
