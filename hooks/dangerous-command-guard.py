#!/usr/bin/env python3
"""
Hook PreToolUse para Bash: guardia de comandos peligrosos.

Intercepta las ejecuciones de Bash y analiza el comando en busca de patrones
potencialmente destructivos (borrado catastrofico, force push, destruccion de
datos, fork bombs, etc.). Si detecta un patron peligroso, bloquea la operacion
(exit 2) con un aviso explicativo.

Politica de seguridad: fail-closed. Si no se puede parsear la entrada del hook
o se produce cualquier error inesperado, se bloquea la operacion (exit 2).
Un hook de seguridad que permite la operacion cuando falla equivale a
desactivar la proteccion justo cuando mas se necesita. Esta politica es
coherente con secret-guard.sh, que tambien es fail-closed.

Patrones vigilados:
    - rm -rf / (o ~, o $HOME): borrado catastrofico del sistema o del home.
    - git push --force a main/master: perdida de historial en ramas protegidas.
    - DROP DATABASE / DROP TABLE: destruccion de datos en base de datos.
    - docker system prune -af: eliminacion de volumenes y datos de contenedores.
    - chmod -R 777: permisos inseguros en todo un arbol de directorios.
    - fork bombs: denegacion de servicio local.
    - mkfs / dd sobre dispositivos: destruccion de disco.
    - Escritura directa a dispositivos de bloque.
"""

import json
import re
import shlex
import sys


# --- Patrones peligrosos ---------------------------------------------------
# Cada tupla contiene (patron_compilado, descripcion_del_riesgo).
# Los patrones se evaluan en orden; la primera coincidencia bloquea.

_DANGEROUS_PATTERNS = [
    # Borrado catastrofico: rm -rf aplicado a raiz, home o rutas de sistema.
    # Cubre: flags juntas (-rf, -fr), separadas (-r -f), con sudo, y flags largas.
    (
        re.compile(
            r"(?:sudo\s+)?rm\s+"
            r"(?:-[a-zA-Z]*\s+)*"
            r"(?:--\w[\w-]*\s+)*"
            r"(?=-[a-zA-Z]*r)(?=.*-[a-zA-Z]*f)"
            r".*\s+(/\s|/\*|/$|~\s|~$|~\/|\$HOME|\$\{HOME\}|/usr|/etc|/var|/boot|/System)"
        ),
        "Borrado catastrofico: rm -rf sobre directorio raiz o de sistema",
    ),
    # Force push a ramas protegidas
    (
        re.compile(
            r"git\s+push\s+.*"
            r"(--force\b|-f\b)"
            r".*\b(main|master)\b"
        ),
        "Force push a rama protegida (main/master): riesgo de perdida de historial",
    ),
    # Variante: force push sin rama explicita (se asume rama actual)
    (
        re.compile(
            r"git\s+push\s+--force-with-lease\s*$"
            r"|git\s+push\s+-f\s*$"
            r"|git\s+push\s+--force\s*$"
        ),
        "Force push sin rama explicita: verifica que no estas en main/master",
    ),
    # Destruccion de base de datos
    (
        re.compile(r"DROP\s+(DATABASE|TABLE|SCHEMA)\s", re.IGNORECASE),
        "Destruccion de datos: DROP DATABASE/TABLE/SCHEMA",
    ),
    # Docker prune agresivo (cubre -af, -fa, -a -f, -f -a y combinaciones con otros flags)
    (
        re.compile(
            r"docker\s+system\s+prune\s+.*(-af|-fa)\b"
            r"|docker\s+system\s+prune\s+.*-a\b.*-f\b"
            r"|docker\s+system\s+prune\s+.*-f\b.*-a\b"
        ),
        "Docker system prune con -af: elimina todos los datos de contenedores",
    ),
    # Permisos inseguros
    (
        re.compile(r"chmod\s+(-R\s+)?777\s+/"),
        "Permisos inseguros: chmod 777 recursivo sobre directorio raiz",
    ),
    # Fork bomb (variantes comunes en bash)
    (
        re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;?\s*:"),
        "Fork bomb: denegacion de servicio local",
    ),
    # Formateo de disco
    (
        re.compile(r"mkfs\.\w+\s+/dev/"),
        "Formateo de disco: mkfs sobre dispositivo de bloque",
    ),
    # dd sobre dispositivo de bloque
    (
        re.compile(r"dd\s+.*of=/dev/(sd|hd|nvme|vd|xvd)"),
        "Escritura directa a dispositivo de bloque con dd",
    ),
    # Escritura a dispositivo via redireccion
    (
        re.compile(r">\s*/dev/(sd|hd|nvme|vd|xvd)"),
        "Redireccion de salida a dispositivo de bloque",
    ),
    # git reset --hard a remote (destructivo en combinacion con push)
    (
        re.compile(r"git\s+reset\s+--hard\s+origin/(main|master)"),
        "git reset --hard a origin/main: descarta todos los cambios locales",
    ),
]

_SAFE_ALFRED_HELPER_SUBCOMMANDS = frozenset({
    "allow-stop-once",
    "consume-prefetch",
    "discuss",
    "map-codebase",
    "next",
    "pause",
    "progress",
    "quick",
    "resume",
    "verify",
})

_SHELL_CONTROL_TOKENS = frozenset({
    ";",
    "&&",
    "||",
    "|",
    ">",
    ">>",
    "<",
    "<<",
    "2>",
    "&>",
    "&>>",
})

_SHELL_CONTROL_SUBSTRINGS = (
    ";",
    "&&",
    "||",
    "|",
    ">",
    "<",
    "$(",
    "`",
)

_SAFE_CAPTURE_SUFFIXES = (
    "2>&1",
    "2>/dev/null",
    "2>/dev/null 2>&1",
)


def _is_safe_alfred_helper_command(command: str) -> bool:
    """Reconoce helpers deterministas locales que Alfred puede autoaprobar.

    El objetivo es destrabar la primera ejecución headless de Claude Code para
    los comandos operativos helper-first. La allowlist es estrecha:
    - `python3`
    - wrapper local `.claude/alfred-continuity.py`
    - solo subcomandos deterministas y operativos
    - sin operadores de control de shell
    """
    normalized = command.strip()
    for suffix in _SAFE_CAPTURE_SUFFIXES:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)].rstrip()
            break

    if any(marker in normalized for marker in _SHELL_CONTROL_SUBSTRINGS):
        return False

    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return False

    if len(tokens) < 3:
        return False
    if tokens[0] != "python3":
        return False
    if tokens[1] != ".claude/alfred-continuity.py":
        return False
    if tokens[2] not in _SAFE_ALFRED_HELPER_SUBCOMMANDS:
        return False
    if any(token in _SHELL_CONTROL_TOKENS for token in tokens):
        return False
    return True


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin proporcionado por PreToolUse, extrae el comando
    de ``tool_input.command`` y lo compara contra la lista de patrones
    peligrosos. Si alguno coincide, bloquea la operacion con exit 2.
    """
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as e:
        # Fail-closed: si no podemos parsear, bloquear por precaucion.
        # Un guard de seguridad que falla en abierto equivale a no tenerlo.
        print(
            f"[Alfred Dev] BLOQUEADO: no se pudo parsear la entrada del hook: {e}. "
            f"La guardia de comandos peligrosos bloquea por precaucion.",
            file=sys.stderr,
        )
        json.dump(
            {
                "decision": "block",
                "reason": f"No se pudo analizar el comando: {e}",
            },
            sys.stdout,
        )
        sys.exit(2)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    if _is_safe_alfred_helper_command(command):
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            },
            sys.stdout,
        )
        sys.exit(0)

    # Comprobar cada patron contra el comando
    for pattern, description in _DANGEROUS_PATTERNS:
        if pattern.search(command):
            # Bloquear con aviso explicativo
            print(
                f"\n[Alfred Dev] COMANDO PELIGROSO BLOQUEADO\n\n"
                f"  Comando:  {command[:200]}\n"
                f"  Riesgo:   {description}\n\n"
                f"  Si realmente necesitas ejecutar este comando, pidele\n"
                f"  al usuario que lo ejecute manualmente en su terminal.\n",
                file=sys.stderr,
            )
            # Emitir JSON de bloqueo por stdout para Claude Code
            json.dump(
                {
                    "decision": "block",
                    "reason": f"Comando potencialmente destructivo: {description}",
                },
                sys.stdout,
            )
            sys.exit(2)

    # Comando seguro, permitir
    sys.exit(0)


if __name__ == "__main__":
    main()
