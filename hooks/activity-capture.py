#!/usr/bin/env python3
"""
Hook centralizado de captura de actividad para Alfred Dev.

Sustituye a ``memory-capture.py`` y ``commit-capture.py`` proporcionando un
unico punto de entrada que registra TODA la actividad relevante en la base
de datos de memoria persistente. Cada evento se almacena con tres niveles
de detalle:

- **summary**: texto legible en castellano para el dashboard.
- **payload**: JSON estructurado para filtrado programatico.
- **content**: texto completo sin truncar para consulta bajo demanda.

Eventos gestionados:
    - PostToolUse Write: fichero escrito (contenido completo).
    - PostToolUse Edit: fichero editado (diff old/new).
    - PostToolUse Bash: comando ejecutado (stdout+stderr completos).
    - UserPromptSubmit: prompt del usuario.
    - PreCompact: marcador de compactacion de contexto.
    - Stop: cierre de sesion.

Politica fail-open: el hook NUNCA bloquea el flujo de trabajo. Cualquier
error se imprime en stderr con prefijo ``[activity-capture]`` y se sale
con codigo 0.
"""

import json
import os
import re
import subprocess
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Directorios y patrones excluidos de la captura generica.
# Son ficheros internos cuya actividad genera ruido sin aportar contexto
# util al historial del proyecto.
_EXCLUDED_PREFIXES = (
    ".claude/",
    ".git/",
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    ".mypy_cache/",
    ".pytest_cache/",
)

# Patron que detecta 'git commit' como comando real, no como argumento
# de otro comando (grep, echo, etc.). Solo detecta git commit al inicio
# de la linea o despues de operadores de shell (&&, ||, ;).
_GIT_COMMIT_RE = re.compile(r"(?:^|&&|\|\||;)\s*git\s+commit\b")

# Comandos triviales que no aportan contexto util al historial.
# Son comandos de lectura, navegacion o diagnostico que no modifican
# el estado del proyecto.
_TRIVIAL_COMMANDS = frozenset({
    "ls", "pwd", "cd", "echo", "cat", "head", "tail", "less", "more",
    "wc", "whoami", "date", "which", "where", "type", "file", "true",
    "false", "clear", "history", "env", "printenv", "set", "export",
    "alias", "unalias", "source", ".", "test", "[",
})

# Prefijo para los mensajes de aviso en stderr.
_LOG_PREFIX = "[activity-capture]"


# ---------------------------------------------------------------------------
# Tabla de dispatchers
# ---------------------------------------------------------------------------

def _build_dispatcher_table():
    """Construye el mapa evento -> funcion de despacho.

    Se define como funcion para evitar referencias anticipadas a funciones
    que aun no se han declarado en el momento de la definicion del modulo.

    Returns:
        Diccionario con claves de evento y valores de funcion dispatcher.
    """
    return {
        "Write": _dispatch_write,
        "Edit": _dispatch_edit,
        "Bash": _dispatch_bash,
        "UserPromptSubmit": _dispatch_prompt,
        "PreCompact": _dispatch_compact,
        "Stop": _dispatch_stop,
    }


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def _is_memory_enabled() -> bool:
    """Comprueba si la memoria persistente esta habilitada en la configuracion.

    Busca el fichero ``alfred-dev.local.md`` en el directorio ``.claude``
    del proyecto actual y verifica que contenga la seccion ``memoria:`` con
    ``enabled: true``.

    Returns:
        True si la memoria esta habilitada, False en caso contrario.
    """
    project_dir = os.getcwd()
    config_path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, FileNotFoundError):
        return False

    pattern = r"memoria:\s*\n(?:\s*#[^\n]*\n|\s*\w+:[^\n]*\n)*?\s*enabled:\s*true"
    return bool(re.search(pattern, content))


def _is_excluded_path(file_path: str) -> bool:
    """Determina si un fichero debe excluirse de la captura generica.

    Se excluyen ficheros internos del plugin, del sistema de control de
    versiones y de caches de herramientas. La comparacion se hace sobre
    la ruta relativa al directorio del proyecto.

    Args:
        file_path: ruta absoluta o relativa del fichero.

    Returns:
        True si el fichero debe excluirse.
    """
    project_dir = os.getcwd()
    try:
        rel_path = os.path.relpath(file_path, project_dir)
    except ValueError:
        rel_path = file_path

    rel_path = rel_path.replace(os.sep, "/")

    for prefix in _EXCLUDED_PREFIXES:
        if rel_path.startswith(prefix) or f"/{prefix}" in rel_path:
            return True
    return False


def _is_trivial_command(command: str) -> bool:
    """Determina si un comando es trivial y no merece ser registrado.

    Extrae el primer token del comando (ignorando variables de entorno
    y redirecciones) y lo compara con la lista de comandos triviales.

    Args:
        command: comando de shell completo.

    Returns:
        True si el comando es trivial.
    """
    cleaned = re.sub(r"^\s*(?:\w+=\S*\s+)*", "", command.strip())
    first_token = cleaned.split()[0] if cleaned.split() else ""
    base_command = os.path.basename(first_token)
    return base_command in _TRIVIAL_COMMANDS


def is_git_commit_command(command: str) -> bool:
    """Determina si un comando contiene un git commit real.

    Se expone como funcion publica para facilitar su uso en tests.

    Args:
        command: comando de shell a analizar.

    Returns:
        True si contiene un git commit real.
    """
    return bool(_GIT_COMMIT_RE.search(command))


def _open_db():
    """Abre la base de datos de memoria del proyecto actual.

    Busca la DB en ``.claude/alfred-memory.db`` relativa al directorio
    de trabajo. Si no existe o no se puede abrir, devuelve None.

    Returns:
        Instancia de MemoryDB o None si no se pudo abrir.
    """
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)

    try:
        from core.memory import MemoryDB
    except ImportError as e:
        print(
            f"{_LOG_PREFIX} Aviso: no se pudo importar core.memory: {e}",
            file=sys.stderr,
        )
        return None

    db_path = os.path.join(os.getcwd(), ".claude", "alfred-memory.db")
    if not os.path.isfile(db_path):
        return None

    try:
        return MemoryDB(db_path)
    except Exception as e:
        print(
            f"{_LOG_PREFIX} Aviso: no se pudo abrir la DB de memoria: {e}",
            file=sys.stderr,
        )
        return None


def _relative_path(file_path: str, project_dir: str) -> str:
    """Convierte una ruta absoluta a ruta relativa respecto al proyecto.

    Args:
        file_path: ruta absoluta del fichero.
        project_dir: directorio raiz del proyecto.

    Returns:
        Ruta relativa. Si la conversion falla, devuelve la ruta original.
    """
    try:
        return os.path.relpath(file_path, project_dir)
    except ValueError:
        return file_path


def _read_file_safe(file_path: str) -> Optional[str]:
    """Lee el contenido de un fichero de forma segura.

    Args:
        file_path: ruta absoluta del fichero.

    Returns:
        Contenido del fichero como texto, o None si falla la lectura.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _first_meaningful_line(text: str) -> str:
    """Extrae la primera linea no vacia de un texto.

    Args:
        text: texto de entrada.

    Returns:
        Primera linea no vacia, truncada a 120 caracteres. Cadena vacia
        si no se encuentra ninguna linea con contenido.
    """
    if not text:
        return ""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return ""


def _load_state_file(file_path: str) -> Optional[dict]:
    """Lee y parsea el fichero de estado de sesion.

    Valida que el JSON tenga la estructura minima requerida: debe ser
    un diccionario con las claves ``comando`` y ``fase_actual``.

    Args:
        file_path: ruta absoluta al fichero alfred-dev-state.json.

    Returns:
        Diccionario con el estado, o None si no se puede leer o parsear.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError, FileNotFoundError):
        return None

    if not isinstance(state, dict):
        return None
    if "comando" not in state or "fase_actual" not in state:
        return None

    return state


# ---------------------------------------------------------------------------
# Logica de estado (iteraciones y fases)
# ---------------------------------------------------------------------------

def _process_state(db, file_path: str) -> None:
    """Procesa el fichero de estado y registra eventos de iteracion/fases.

    La logica de comparacion sigue tres ejes:

    1. Si no hay iteracion activa en la DB, se inicia una nueva.
    2. Si hay fases completadas en el estado nuevo que no estan registradas
       como eventos en la DB, se registra un ``phase_completed`` por cada una.
    3. Si la fase actual es "completado", se cierra la iteracion activa.

    Ademas, las fases completadas se marcan automaticamente (auto-pin) para
    que sobrevivan entre sesiones.

    Args:
        db: instancia de MemoryDB ya abierta.
        file_path: ruta al fichero alfred-dev-state.json.
    """
    new_state = _load_state_file(file_path)
    if new_state is None:
        return

    comando = new_state.get("comando", "desconocido")
    descripcion = new_state.get("descripcion", "")
    fase_actual = new_state.get("fase_actual", "")
    fases_completadas = new_state.get("fases_completadas", [])

    # --- Comprobar si hay una iteracion activa ---
    active = db.get_active_iteration()

    if active is None:
        iteration_id = db.start_iteration(
            command=comando,
            description=descripcion,
        )
        db.log_event(
            event_type="iteration_started",
            payload={"comando": comando, "descripcion": descripcion},
            iteration_id=iteration_id,
        )
        active = db.get_active_iteration()

    if active is None:
        return

    iteration_id = active["id"]

    # --- Detectar fases nuevas completadas ---
    existing_events = db.get_timeline(iteration_id)
    existing_phases = set()
    for event in existing_events:
        if event.get("event_type") == "phase_completed":
            payload_raw = event.get("payload")
            if payload_raw:
                try:
                    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                    phase_name = payload.get("fase", "")
                    if phase_name:
                        existing_phases.add(phase_name)
                except (json.JSONDecodeError, AttributeError):
                    pass

    for fase in fases_completadas:
        nombre_fase = fase.get("nombre", "") if isinstance(fase, dict) else str(fase)
        if not nombre_fase:
            continue
        if nombre_fase in existing_phases:
            continue

        payload = {"fase": nombre_fase}
        if isinstance(fase, dict):
            if "resultado" in fase:
                payload["resultado"] = fase["resultado"]
            if "completada_en" in fase:
                payload["completada_en"] = fase["completada_en"]
            if "artefactos" in fase:
                payload["artefactos"] = fase["artefactos"]

        db.log_event(
            event_type="phase_completed",
            phase=nombre_fase,
            payload=payload,
            iteration_id=iteration_id,
        )

    # --- Detectar iteracion completada ---
    if fase_actual == "completado":
        db.complete_iteration(iteration_id)
        db.log_event(
            event_type="iteration_completed",
            payload={
                "comando": comando,
                "total_fases": len(fases_completadas),
            },
            iteration_id=iteration_id,
        )

    # --- Auto-pinning de fases completadas ---
    if fases_completadas and len(fases_completadas) > len(existing_phases):
        ultima_fase = fases_completadas[-1]
        nombre = ultima_fase.get("nombre", "") if isinstance(ultima_fase, dict) else str(ultima_fase)
        if nombre:
            try:
                db.pin_item(
                    item_type="phase",
                    item_ref=f"phase:{nombre}",
                    note=f"Fase completada: {nombre}",
                    auto=True,
                    priority=5,
                )
            except Exception:
                pass  # Fail-open: no bloquear si el pinning falla


# ---------------------------------------------------------------------------
# Captura de git commit
# ---------------------------------------------------------------------------

def _capture_git_commit(db) -> None:
    """Extrae metadatos del ultimo commit y los registra con log_commit().

    Complementa el evento generico con informacion estructurada del commit
    (SHA, mensaje, autor, ficheros) para la vista de commits del dashboard.

    Args:
        db: instancia de MemoryDB ya abierta.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1",
             "--format=%H|%s|%an|%aI",
             "--name-only"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return
    except Exception:
        return

    lines = result.stdout.strip().split("\n")
    if not lines or "|" not in lines[0]:
        return

    parts = lines[0].split("|", 3)
    sha = parts[0]
    message = parts[1] if len(parts) > 1 else ""
    author = parts[2] if len(parts) > 2 else ""
    files = [line.strip() for line in lines[1:] if line.strip()]

    db.log_commit(
        sha=sha, message=message, author=author,
        files=files, files_changed=len(files),
    )


# ---------------------------------------------------------------------------
# Dispatchers
# ---------------------------------------------------------------------------

def _dispatch_write(db, data: dict) -> None:
    """Captura la escritura completa de un fichero.

    Registra el contenido integro del fichero, su extension, numero de
    lineas y ruta relativa. Si el fichero es ``alfred-dev-state.json``,
    dispara ademas la logica de seguimiento de iteraciones/fases.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path or _is_excluded_path(file_path):
        return

    project_dir = os.getcwd()
    rel_path = _relative_path(file_path, project_dir)
    _, ext = os.path.splitext(file_path)
    ext_clean = ext.lstrip(".") if ext else ""

    # Leer el contenido completo del fichero
    file_content = _read_file_safe(file_path)
    line_count = file_content.count("\n") if file_content else 0

    summary = f"Escrito {rel_path} ({line_count} lineas, {ext_clean or 'sin extension'})"

    db.log_event(
        event_type="file_written",
        summary=summary,
        payload={"file": rel_path, "extension": ext_clean, "lines": line_count},
        content=file_content,
    )

    # Logica especifica de state.json
    if file_path.endswith("alfred-dev-state.json"):
        _process_state(db, file_path)


def _dispatch_edit(db, data: dict) -> None:
    """Captura la edicion parcial de un fichero.

    Registra el diff (old_string -> new_string) junto con el conteo de
    lineas reemplazadas y nuevas.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path or _is_excluded_path(file_path):
        return

    rel_path = _relative_path(file_path, os.getcwd())
    _, ext = os.path.splitext(file_path)
    ext_clean = ext.lstrip(".") if ext else ""

    old_string = tool_input.get("old_string", "")
    new_string = tool_input.get("new_string", "")
    old_lines = old_string.count("\n") + 1 if old_string else 0
    new_lines = new_string.count("\n") + 1 if new_string else 0

    summary = f"Editado {rel_path}: {old_lines} lineas reemplazadas por {new_lines}"
    content = f"--- old ---\n{old_string}\n--- new ---\n{new_string}"

    db.log_event(
        event_type="file_edited",
        summary=summary,
        payload={"file": rel_path, "extension": ext_clean, "old_lines": old_lines, "new_lines": new_lines},
        content=content,
    )


def _dispatch_bash(db, data: dict) -> None:
    """Captura la ejecucion de un comando Bash.

    Registra el comando completo, codigo de salida, stdout y stderr sin
    truncar. Si el comando es un ``git commit`` exitoso, dispara ademas
    la captura enriquecida de metadatos del commit.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    command = tool_input.get("command", "")
    if not command or _is_trivial_command(command):
        return

    exit_code = tool_result.get("exit_code")
    stdout = tool_result.get("stdout", "") or tool_result.get("output", "")
    stderr = tool_result.get("stderr", "")

    cmd_short = command[:80] + "..." if len(command) > 80 else command
    exit_str = f"exit {exit_code}" if exit_code is not None else "sin exit code"
    first_line = _first_meaningful_line(stdout)
    summary_parts = [f"Ejecutado: {cmd_short} -- {exit_str}"]
    if first_line:
        summary_parts.append(first_line)
    summary = ", ".join(summary_parts)

    content_parts = []
    if stdout:
        content_parts.append(f"--- stdout ---\n{stdout}")
    if stderr:
        content_parts.append(f"--- stderr ---\n{stderr}")
    content = "\n".join(content_parts) if content_parts else None

    db.log_event(
        event_type="command_executed",
        summary=summary,
        payload={"command": command, "exit_code": exit_code},
        content=content,
    )

    # Captura enriquecida de git commit
    if _GIT_COMMIT_RE.search(command) and exit_code == 0:
        _capture_git_commit(db)


def _dispatch_prompt(db, data: dict) -> None:
    """Captura el prompt enviado por el usuario.

    Registra el texto completo del prompt y genera un resumen con la
    primera linea truncada a 100 caracteres.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook UserPromptSubmit.
    """
    prompt_text = data.get("prompt", "") or data.get("content", "")
    if not prompt_text:
        return

    first_line = prompt_text.split("\n")[0][:100]
    summary = f"Prompt: {first_line}"
    if len(prompt_text) > len(first_line):
        summary += "..."

    db.log_event(
        event_type="user_prompt",
        summary=summary,
        payload={"length": len(prompt_text)},
        content=prompt_text,
    )


def _dispatch_compact(db, data: dict) -> None:
    """Marca un evento de compactacion de contexto.

    Indica que los mensajes anteriores se han resumido por el motor de
    Claude Code.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PreCompact.
    """
    summary = "Contexto compactado -- los mensajes anteriores se han resumido"
    db.log_event(
        event_type="context_compacted",
        summary=summary,
        payload={"source": "PreCompact"},
    )


def _dispatch_stop(db, data: dict) -> None:
    """Marca el cierre de sesion.

    Registra un evento de finalizacion y cierra la iteracion activa si
    existe alguna.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook Stop.
    """
    summary = "Sesion finalizada"
    db.log_event(
        event_type="session_ended",
        summary=summary,
        payload={"source": "Stop"},
    )
    active = db.get_active_iteration()
    if active:
        db.complete_iteration(active["id"])


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin proporcionado por Claude Code, determina el tipo
    de evento y lo despacha al handler correspondiente. Nunca bloquea el
    flujo de trabajo: cualquier error sale con exit 0.
    """
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as e:
        print(
            f"{_LOG_PREFIX} Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La captura de actividad esta desactivada para esta operacion.",
            file=sys.stderr,
        )
        sys.exit(0)

    # Determinar la clave de despacho: primero tool_name, luego hook_event_name
    dispatch_key = data.get("tool_name") or data.get("hook_event_name", "")
    if not dispatch_key:
        sys.exit(0)

    dispatchers = _build_dispatcher_table()
    handler = dispatchers.get(dispatch_key)
    if handler is None:
        sys.exit(0)

    # Comprobar si la memoria esta habilitada
    if not _is_memory_enabled():
        sys.exit(0)

    # Abrir la base de datos
    db = _open_db()
    if db is None:
        sys.exit(0)

    try:
        handler(db, data)
    except Exception as e:
        print(
            f"{_LOG_PREFIX} Aviso: error al procesar evento '{dispatch_key}': {e}",
            file=sys.stderr,
        )
    finally:
        db.close()

    sys.exit(0)


if __name__ == "__main__":
    main()
