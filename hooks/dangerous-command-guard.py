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
import os
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
    "blocked",
    "consume-prefetch",
    "discuss",
    "in-progress",
    "map-codebase",
    "memory-ui",
    "next",
    "pause",
    "progress",
    "quick",
    "resume",
    "search",
    "standup",
    "validate",
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
    "$(",
    "`",
)

_SAFE_CAPTURE_SUFFIXES = (
    "2>&1",
    "2>/dev/null",
    "2>/dev/null 2>&1",
)


_DROP_SQL_REGEX = re.compile(r"\bDROP\s+(DATABASE|TABLE|SCHEMA)\b", re.IGNORECASE)
_DEVICE_REDIRECT_REGEX = re.compile(r">\s*/dev/(sd|hd|nvme|vd|xvd)\w*", re.IGNORECASE)
_SHELL_WRAPPERS = frozenset({"sh", "bash", "zsh"})
_SQL_CLIENTS = frozenset({"psql", "mysql", "mariadb", "sqlite3", "duckdb"})


def _command_basename(token: str) -> str:
    return os.path.basename(token or "")


def _strip_leading_wrappers(tokens):
    """Elimina wrappers neutros al principio: sudo, env y variables inline."""
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        base = _command_basename(token)

        if base == "sudo":
            idx += 1
            while idx < len(tokens) and tokens[idx].startswith("-"):
                idx += 1
            continue

        if base == "env":
            idx += 1
            while idx < len(tokens) and "=" in tokens[idx] and not tokens[idx].startswith("-"):
                idx += 1
            continue

        if "=" in token and not token.startswith("-"):
            name, _value = token.split("=", 1)
            if name.replace("_", "").isalnum():
                idx += 1
                continue

        break

    return tokens[idx:]


def _strip_quoted_content(command: str) -> str:
    """Reemplaza el contenido entre comillas por espacios preservando operadores."""
    result = []
    in_single = False
    in_double = False
    escaped = False

    for char in command:
        if escaped:
            result.append(" " if (in_single or in_double) else char)
            escaped = False
            continue

        if char == "\\":
            escaped = True
            result.append(" " if (in_single or in_double) else char)
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            result.append(" ")
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            result.append(" ")
            continue

        result.append(" " if (in_single or in_double) else char)

    return "".join(result)


def _has_shell_controls_outside_quotes(command: str) -> bool:
    """Detecta operadores de shell reales ignorando texto dentro de comillas.

    Permitimos helpers con argumentos quoted como:
    `--raw "login | signup"` o `--raw "funnel A > B"`.
    Lo que seguimos bloqueando es el uso real de operadores fuera de quotes,
    como `;`, `&&`, `||`, pipes y redirecciones.
    """
    in_single = False
    in_double = False
    escaped = False
    idx = 0

    while idx < len(command):
        char = command[idx]

        if escaped:
            escaped = False
            idx += 1
            continue

        if char == "\\":
            escaped = True
            idx += 1
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            idx += 1
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            idx += 1
            continue

        if in_single or in_double:
            idx += 1
            continue

        next_two = command[idx : idx + 2]
        if next_two in {"&&", "||", ">>", "<<"}:
            return True
        if char in {";", "|", ">", "<"}:
            return True
        idx += 1

    return False


def _extract_shell_c_command(tokens):
    """Extrae el comando embebido en shell wrappers tipo sh -c / bash -lc."""
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens:
        return None

    base = _command_basename(core_tokens[0])
    if base not in _SHELL_WRAPPERS:
        return None

    idx = 1
    while idx < len(core_tokens):
        token = core_tokens[idx]
        if token == "-c" and idx + 1 < len(core_tokens):
            return core_tokens[idx + 1]
        if token.startswith("-") and "c" in token and idx + 1 < len(core_tokens):
            return core_tokens[idx + 1]
        idx += 1
    return None


def _is_recursive_force_rm(tokens):
    has_recursive = False
    has_force = False
    for token in tokens:
        if token == "--recursive":
            has_recursive = True
        elif token == "--force":
            has_force = True
        elif token.startswith("-") and token != "-":
            flags = token[1:]
            has_recursive = has_recursive or ("r" in flags)
            has_force = has_force or ("f" in flags)
    return has_recursive and has_force


def _is_sensitive_rm_target(target: str) -> bool:
    sensitive_roots = ("/", "/etc", "/usr", "/var", "/boot", "/System")
    home_markers = {"~", "~/", "$HOME", "${HOME}"}

    if target in home_markers or target.startswith("~/"):
        return True
    if target in {"/*", "~/*"}:
        return True
    if target in {"$HOME/*", "${HOME}/*"}:
        return True
    for root in sensitive_roots:
        if target == root or target == f"{root}/*":
            return True
        if root != "/" and target.startswith(root + "/"):
            return True
    return False


def _is_absolute_permission_target(target: str) -> bool:
    return target == "/" or target.startswith("/")


def _detect_rm(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens or _command_basename(core_tokens[0]) != "rm":
        return None
    if not _is_recursive_force_rm(core_tokens[1:]):
        return None
    targets = [token for token in core_tokens[1:] if not token.startswith("-")]
    if any(_is_sensitive_rm_target(target) for target in targets):
        return "Borrado catastrofico: rm -rf sobre directorio raiz o de sistema"
    return None


def _detect_git_push(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 2:
        return None
    if _command_basename(core_tokens[0]) != "git" or core_tokens[1] != "push":
        return None

    force = any(
        token in {"--force", "--force-with-lease", "-f"}
        or (token.startswith("-") and "f" in token[1:])
        for token in core_tokens[2:]
    )
    if not force:
        return None

    protected_refs = {"main", "master", "origin/main", "origin/master", "refs/heads/main", "refs/heads/master"}
    if any(token in protected_refs for token in core_tokens[2:] if not token.startswith("-")):
        return "Force push a rama protegida (main/master): riesgo de perdida de historial"
    return "Force push sin rama explicita: verifica que no estas en main/master"


def _detect_sql_drop(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens:
        return None
    first = _command_basename(core_tokens[0]).lower()
    if first == "drop":
        if len(core_tokens) > 1 and core_tokens[1].upper() in {"DATABASE", "TABLE", "SCHEMA"}:
            return "Destruccion de datos: DROP DATABASE/TABLE/SCHEMA"
        return None
    if _command_basename(core_tokens[0]) not in _SQL_CLIENTS:
        return None
    if any(_DROP_SQL_REGEX.search(token) for token in core_tokens[1:]):
        return "Destruccion de datos: DROP DATABASE/TABLE/SCHEMA"
    return None


def _detect_docker_prune(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 3:
        return None
    if (
        _command_basename(core_tokens[0]) != "docker"
        or core_tokens[1] != "system"
        or core_tokens[2] != "prune"
    ):
        return None

    has_all = any(
        token in {"-a", "--all"} or (token.startswith("-") and "a" in token[1:])
        for token in core_tokens[3:]
    )
    has_force = any(
        token in {"-f", "--force"} or (token.startswith("-") and "f" in token[1:])
        for token in core_tokens[3:]
    )
    if has_all and has_force:
        return "Docker system prune con -af: elimina todos los datos de contenedores"
    return None


def _detect_chmod(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 3 or _command_basename(core_tokens[0]) != "chmod":
        return None

    mode_tokens = [token for token in core_tokens[1:] if not token.startswith("-")]
    if not mode_tokens or mode_tokens[0] != "777":
        return None
    targets = mode_tokens[1:]
    if any(_is_absolute_permission_target(target) for target in targets):
        return "Permisos inseguros: chmod 777 recursivo sobre directorio raiz"
    return None


def _detect_fork_bomb(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if core_tokens[:3] == [":(){", ":|:&", "};:"]:
        return "Fork bomb: denegacion de servicio local"
    return None


def _detect_mkfs(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 2:
        return None
    if not _command_basename(core_tokens[0]).startswith("mkfs."):
        return None
    if any(token.startswith("/dev/") for token in core_tokens[1:]):
        return "Formateo de disco: mkfs sobre dispositivo de bloque"
    return None


def _detect_dd(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens or _command_basename(core_tokens[0]) != "dd":
        return None
    if any(re.match(r"of=/dev/(sd|hd|nvme|vd|xvd)\w*", token) for token in core_tokens[1:]):
        return "Escritura directa a dispositivo de bloque con dd"
    return None


def _detect_redirection_to_device(command: str):
    stripped = _strip_quoted_content(command)
    if _DEVICE_REDIRECT_REGEX.search(stripped):
        return "Redireccion de salida a dispositivo de bloque"
    return None


def _detect_git_reset(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 4:
        return None
    if _command_basename(core_tokens[0]) != "git" or core_tokens[1] != "reset":
        return None
    if "--hard" in core_tokens[2:] and any(
        token in {"origin/main", "origin/master"} for token in core_tokens[2:]
    ):
        return "git reset --hard a origin/main: descarta todos los cambios locales"
    return None


def _find_dangerous_reason(command: str):
    """Devuelve la razon de bloqueo si el comando es realmente peligroso."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = []

    embedded = _extract_shell_c_command(tokens) if tokens else None
    if embedded:
        return _find_dangerous_reason(embedded)

    detectors = (
        _detect_rm,
        _detect_git_push,
        _detect_sql_drop,
        _detect_docker_prune,
        _detect_chmod,
        _detect_fork_bomb,
        _detect_mkfs,
        _detect_dd,
        _detect_git_reset,
    )
    for detector in detectors:
        reason = detector(tokens)
        if reason:
            return reason

    return _detect_redirection_to_device(command)


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

    if _has_shell_controls_outside_quotes(normalized):
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

    description = _find_dangerous_reason(command)
    if description:
        # Bloquear con aviso explicativo
        print(
            f"\n[Alfred Dev] COMANDO PELIGROSO BLOQUEADO\n\n"
            f"  Comando:  {command[:200]}\n"
            f"  Riesgo:   {description}\n\n"
            f"  Si realmente necesitas ejecutar este comando, pidele\n"
            f"  al usuario que lo ejecute manualmente en su terminal.\n",
            file=sys.stderr,
        )
        sys.exit(2)

    # Comando seguro, permitir
    sys.exit(0)


if __name__ == "__main__":
    main()
