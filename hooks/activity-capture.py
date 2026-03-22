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
    - PostToolUse Read: fichero leido (ruta y rango, sin contenido).
    - PostToolUse Glob: busqueda de ficheros por patron.
    - PostToolUse Grep: busqueda de contenido en ficheros.
    - PostToolUse Agent: lanzamiento de subagente (prompt + resultado).
    - PostToolUse WebFetch: peticion HTTP a URL externa.
    - PostToolUse WebSearch: busqueda web.
    - PostToolUse NotebookEdit: edicion de notebook Jupyter.
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

# Comandos de Alfred que pueden prepararse de forma determinista antes de que
# el modelo intente resolver el prompt por si mismo.
_ALFRED_PREFETCH_COMMANDS = frozenset({
    "alfred",
    "map-codebase",
    "discuss",
    "quick",
})

# Prefijo para los mensajes de aviso en stderr.
_LOG_PREFIX = "[activity-capture]"


def _ensure_plugin_root_on_path() -> str:
    """Asegura que la raiz del plugin este disponible para imports.

    Los hooks se ejecutan como scripts sueltos desde Claude Code y no siempre
    reciben ``PYTHONPATH`` con la raiz del plugin. Sin este ajuste, imports
    como ``core.memory`` o ``core.memory_config`` pueden fallar incluso cuando
    el plugin esta bien instalado.

    Returns:
        Ruta absoluta a la raiz del plugin.
    """
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)
    return plugin_root


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
        "Read": _dispatch_read,
        "Glob": _dispatch_glob,
        "Grep": _dispatch_grep,
        "Agent": _dispatch_agent,
        "WebFetch": _dispatch_web_fetch,
        "WebSearch": _dispatch_web_search,
        "NotebookEdit": _dispatch_notebook,
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
    _ensure_plugin_root_on_path()
    try:
        from core.memory_config import is_memory_enabled
    except ImportError:
        return False

    return is_memory_enabled(os.getcwd())


def _memory_settings():
    """Carga la configuracion efectiva de memoria del proyecto."""
    _ensure_plugin_root_on_path()
    try:
        from core.memory_config import load_memory_config
    except ImportError:
        return {
            "enabled": False,
            "sync_to_native": True,
            "sync_commits_limit": 10,
            "capture_decisions": True,
            "capture_commits": True,
            "retention_days": 365,
        }
    return load_memory_config(os.getcwd())


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
    _ensure_plugin_root_on_path()

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


def _try_sync(db, action: str, **kwargs) -> None:
    """Ejecuta una sincronizacion incremental a ficheros .md nativos.

    Proyecta los cambios recientes a los ficheros de memoria nativa de
    Claude Code. Si falla por cualquier razon, continua silenciosamente
    (politica fail-open).

    Args:
        db: instancia de MemoryDB.
        action: tipo de sincronizacion (decision, iteration, commits).
        **kwargs: argumentos adicionales para el metodo de sync.
    """
    try:
        settings = _memory_settings()
        if not settings.get("sync_to_native", True):
            return

        from core.memory_sync import MemorySync, resolve_memory_dir

        memory_dir = resolve_memory_dir(os.getcwd())
        if memory_dir is None:
            return

        commits_limit = settings.get("sync_commits_limit", 10)
        if not isinstance(commits_limit, int) or commits_limit < 1:
            commits_limit = 10

        sync = MemorySync(db, memory_dir, commits_limit=commits_limit)

        if action == "decision":
            decision_id = kwargs.get("decision_id")
            if decision_id is not None:
                sync.sync_decision(decision_id)
        elif action == "iteration":
            sync.sync_iteration()
        elif action == "commits":
            sync.sync_commits()
        else:
            return  # Accion no reconocida: no sincronizar

        sync.sync_summary()
        sync.update_index()
    except Exception as e:
        print(
            f"{_LOG_PREFIX} Aviso: sync incremental fallida: {e}",
            file=sys.stderr,
        )


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


def _parse_alfred_prefetch_prompt(prompt_text: str) -> Optional[dict]:
    """Extrae el slash command de Alfred si admite preparación helper-first."""
    normalized = (prompt_text or "").strip()
    if not normalized.startswith("/alfred-dev:"):
        return None

    first_line = normalized.splitlines()[0].strip()
    match = re.match(
        r"^/alfred-dev:(?P<command>[a-z0-9-]+)\b(?P<rest>.*)$",
        first_line,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    command = match.group("command").lower()
    if command not in _ALFRED_PREFETCH_COMMANDS:
        return None

    raw_request = " ".join(match.group("rest").split()).strip()
    return {
        "source_command": command,
        "raw_request": raw_request,
    }


def _prefetch_alfred_continuity(prompt_text: str) -> Optional[dict]:
    """Prepara artefactos de continuidad antes del primer razonamiento."""
    parsed = _parse_alfred_prefetch_prompt(prompt_text)
    if parsed is None:
        return None

    _ensure_plugin_root_on_path()
    try:
        from core.continuity import (
            needs_codebase_map,
            save_prefetch_result,
            start_quick_session,
            write_codebase_map_files,
            write_discovery_files,
        )
    except ImportError as exc:
        print(
            f"{_LOG_PREFIX} Aviso: no se pudo importar core.continuity: {exc}",
            file=sys.stderr,
        )
        return None

    project_dir = os.getcwd()
    source_command = parsed["source_command"]
    raw_request = parsed["raw_request"]

    target_command = source_command
    action = None

    if source_command == "alfred":
        if not needs_codebase_map(project_dir):
            return None
        target_command = "map-codebase"
        action = write_codebase_map_files
    elif source_command == "map-codebase":
        action = write_codebase_map_files
    elif source_command == "discuss":
        action = write_discovery_files
    elif source_command == "quick":
        action = start_quick_session

    if action is None:
        return None

    try:
        result = action(project_dir, raw_request)
    except RuntimeError as exc:
        print(
            f"{_LOG_PREFIX} Aviso: prefetch /alfred-dev:{source_command} omitido: {exc}",
            file=sys.stderr,
        )
        return None
    except Exception as exc:
        print(
            f"{_LOG_PREFIX} Aviso: fallo en prefetch /alfred-dev:{source_command}: {exc}",
            file=sys.stderr,
        )
        return None

    payload = result.copy() if isinstance(result, dict) else {}
    payload["source_command"] = source_command
    payload["prefetched_command"] = target_command
    save_prefetch_result(project_dir, payload)
    return payload


def _log_prefetch_event(db, project_dir: str, payload: dict) -> None:
    """Registra en memoria que Alfred dejó listo un helper-first command."""
    command = payload.get("prefetched_command", "desconocido")
    source_command = payload.get("source_command", command)
    artifacts = []

    for key, value in payload.items():
        if not key.endswith("_path"):
            continue
        if not isinstance(value, str) or not value:
            continue
        artifacts.append(_relative_path(value, project_dir))

    summary = f"Prefetch Alfred: /alfred-dev:{source_command}"
    if source_command != command:
        summary += f" preparó /alfred-dev:{command}"
    else:
        summary += " preparado antes del flujo principal"

    event_payload = {
        "source_command": source_command,
        "prefetched_command": command,
        "artifacts": artifacts,
    }
    next_command = payload.get("recommended_command") or payload.get("next_command")
    if isinstance(next_command, str) and next_command.strip():
        event_payload["next_command"] = next_command.strip()

    db.log_event(
        event_type="alfred_prefetched",
        summary=summary,
        payload=event_payload,
    )


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
        _try_sync(db, "iteration")
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
        _try_sync(db, "iteration")



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
    if not _memory_settings().get("capture_commits", True):
        return

    try:
        result = subprocess.run(
            ["git", "log", "-1",
             "--format=%H%x1f%s%x1f%an%x1f%aI",
             "--name-only"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return
    except Exception:
        return

    lines = result.stdout.strip().split("\n")
    if not lines or "\x1f" not in lines[0]:
        return

    parts = lines[0].split("\x1f", 3)
    sha = parts[0]
    message = parts[1] if len(parts) > 1 else ""
    author = parts[2] if len(parts) > 2 else ""
    files = [line.strip() for line in lines[1:] if line.strip()]

    db.log_commit(
        sha=sha, message=message, author=author,
        files=files, files_changed=len(files),
    )
    _try_sync(db, "commits")


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


def _dispatch_read(db, data: dict) -> None:
    """Captura la lectura de un fichero.

    Registra la ruta del fichero leido y el rango de lineas solicitado.
    No almacena el contenido (ya existe en el fichero) para evitar
    duplicacion innecesaria.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path or _is_excluded_path(file_path):
        return

    rel_path = _relative_path(file_path, os.getcwd())
    offset = tool_input.get("offset")
    limit = tool_input.get("limit")

    range_str = ""
    if offset and limit:
        range_str = f" (lineas {offset}-{offset + limit})"
    elif offset:
        range_str = f" (desde linea {offset})"
    elif limit:
        range_str = f" (primeras {limit} lineas)"

    summary = f"Leido {rel_path}{range_str}"

    payload = {"file": rel_path}
    if offset:
        payload["offset"] = offset
    if limit:
        payload["limit"] = limit

    db.log_event(
        event_type="file_read",
        summary=summary,
        payload=payload,
    )


def _dispatch_glob(db, data: dict) -> None:
    """Captura una busqueda de ficheros por patron glob.

    Registra el patron usado y el numero de resultados encontrados.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    pattern = tool_input.get("pattern", "")
    if not pattern:
        return

    search_path = tool_input.get("path", ".")

    # Contar resultados: tool_result puede ser string con rutas o un dict
    result_text = ""
    if isinstance(tool_result, str):
        result_text = tool_result
    elif isinstance(tool_result, dict):
        result_text = tool_result.get("output", "") or tool_result.get("stdout", "")

    match_count = len([l for l in result_text.strip().split("\n") if l.strip()]) if result_text.strip() else 0

    summary = f"Glob: {pattern} en {search_path} ({match_count} resultados)"

    db.log_event(
        event_type="glob_search",
        summary=summary,
        payload={"pattern": pattern, "path": search_path, "results": match_count},
        content=result_text if result_text else None,
    )


def _dispatch_grep(db, data: dict) -> None:
    """Captura una busqueda de contenido en ficheros.

    Registra el patron regex, el directorio y el numero de coincidencias.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    pattern = tool_input.get("pattern", "")
    if not pattern:
        return

    search_path = tool_input.get("path", ".")
    output_mode = tool_input.get("output_mode", "files_with_matches")
    file_type = tool_input.get("type", "")
    glob_filter = tool_input.get("glob", "")

    result_text = ""
    if isinstance(tool_result, str):
        result_text = tool_result
    elif isinstance(tool_result, dict):
        result_text = tool_result.get("output", "") or tool_result.get("stdout", "")

    match_count = len([l for l in result_text.strip().split("\n") if l.strip()]) if result_text.strip() else 0

    filter_str = ""
    if file_type:
        filter_str = f" tipo={file_type}"
    elif glob_filter:
        filter_str = f" filtro={glob_filter}"

    summary = f"Grep: '{pattern}' en {search_path}{filter_str} ({match_count} coincidencias)"

    payload = {"pattern": pattern, "path": search_path, "mode": output_mode, "results": match_count}
    if file_type:
        payload["type"] = file_type
    if glob_filter:
        payload["glob"] = glob_filter

    db.log_event(
        event_type="grep_search",
        summary=summary,
        payload=payload,
        content=result_text if result_text else None,
    )


def _dispatch_agent(db, data: dict) -> None:
    """Captura el lanzamiento de un subagente.

    Registra el tipo de subagente, la descripcion de la tarea y el
    prompt enviado. El resultado completo se almacena en content.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    description = tool_input.get("description", "")
    subagent_type = tool_input.get("subagent_type", "general-purpose")
    prompt = tool_input.get("prompt", "")

    summary = f"Subagente ({subagent_type}): {description}" if description else f"Subagente ({subagent_type}) lanzado"

    result_text = ""
    if isinstance(tool_result, str):
        result_text = tool_result
    elif isinstance(tool_result, dict):
        result_text = tool_result.get("output", "") or tool_result.get("stdout", "")

    content_parts = []
    if prompt:
        content_parts.append(f"--- prompt ---\n{prompt}")
    if result_text:
        content_parts.append(f"--- resultado ---\n{result_text}")

    db.log_event(
        event_type="agent_launched",
        summary=summary,
        payload={"subagent_type": subagent_type, "description": description},
        content="\n".join(content_parts) if content_parts else None,
    )


def _dispatch_web_fetch(db, data: dict) -> None:
    """Captura una peticion HTTP a una URL externa.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    url = tool_input.get("url", "")
    if not url:
        return

    result_text = ""
    if isinstance(tool_result, str):
        result_text = tool_result
    elif isinstance(tool_result, dict):
        result_text = tool_result.get("output", "") or tool_result.get("content", "")

    summary = f"Web fetch: {url[:100]}"

    db.log_event(
        event_type="web_fetched",
        summary=summary,
        payload={"url": url},
        content=result_text if result_text else None,
    )


def _dispatch_web_search(db, data: dict) -> None:
    """Captura una busqueda web.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    query = tool_input.get("query", "")
    if not query:
        return

    result_text = ""
    if isinstance(tool_result, str):
        result_text = tool_result
    elif isinstance(tool_result, dict):
        result_text = tool_result.get("output", "") or tool_result.get("content", "")

    summary = f"Web search: {query[:100]}"

    db.log_event(
        event_type="web_searched",
        summary=summary,
        payload={"query": query},
        content=result_text if result_text else None,
    )


def _dispatch_notebook(db, data: dict) -> None:
    """Captura la edicion de un notebook Jupyter.

    Args:
        db: instancia de MemoryDB ya abierta.
        data: datos del hook PostToolUse.
    """
    tool_input = data.get("tool_input", {})

    notebook_path = tool_input.get("notebook_path", "") or tool_input.get("path", "")
    if not notebook_path or _is_excluded_path(notebook_path):
        return

    rel_path = _relative_path(notebook_path, os.getcwd())
    command = tool_input.get("command", "edit")

    summary = f"Notebook {command}: {rel_path}"

    db.log_event(
        event_type="notebook_edited",
        summary=summary,
        payload={"file": rel_path, "command": command},
    )


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

    _ensure_plugin_root_on_path()
    try:
        from core.continuity import clear_prefetch_consumed_marker
    except ImportError:
        clear_prefetch_consumed_marker = None

    if clear_prefetch_consumed_marker is not None:
        clear_prefetch_consumed_marker(os.getcwd())

    prefetched = _prefetch_alfred_continuity(prompt_text)
    if prefetched:
        _log_prefetch_event(db, os.getcwd(), prefetched)

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

    _ensure_plugin_root_on_path()
    try:
        from core.continuity import clear_prefetch_consumed_marker
    except ImportError:
        clear_prefetch_consumed_marker = None

    if clear_prefetch_consumed_marker is not None:
        clear_prefetch_consumed_marker(os.getcwd())

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
