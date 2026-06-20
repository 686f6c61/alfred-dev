#!/usr/bin/env python3
"""
Herramientas de continuidad de trabajo para Alfred Dev.

Este módulo adapta a Alfred parte del modelo operativo de GSD: poder saber
qué toca hacer ahora, pausar una sesión con un handoff explícito y retomar
sin releer todo el proyecto.

Las funciones están diseñadas para ser deterministas y fáciles de probar.
Los comandos Markdown pueden apoyarse en esta lógica para no improvisar la
prioridad entre sesión activa, handoff pendiente y mapeo brownfield.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_loader import detect_stack
from core.optional_agents import order_optional_agent_names
from core.orchestrator import (
    FLOWS,
    OPTIONAL_INTEGRATIONS,
    create_session,
    get_effective_agents,
    load_state,
    run_flow,
    save_state,
)


STATE_RELATIVE_PATH = os.path.join(".claude", "alfred-dev-state.json")
HANDOFF_JSON_RELATIVE_PATH = os.path.join(".claude", "alfred-handoff.json")
STOP_BYPASS_RELATIVE_PATH = os.path.join(".claude", "alfred-stop-hook-bypass.json")
PREFETCH_RELATIVE_PATH = os.path.join(".claude", "alfred-prefetch.json")
PREFETCH_CONSUMED_RELATIVE_PATH = os.path.join(".claude", "alfred-prefetch-consumed.json")
UAT_JSON_RELATIVE_PATH = os.path.join(".claude", "alfred-uat.json")
CODEBASE_MAP_RELATIVE_PATH = os.path.join("docs", "project", "codebase-map.md")
CURRENT_RELATIVE_PATH = os.path.join("docs", "project", "current.md")
DISCOVERY_MD_RELATIVE_PATH = os.path.join("docs", "project", "discovery.md")
HANDOFF_MD_RELATIVE_PATH = os.path.join("docs", "project", "handoff.md")
UAT_MD_RELATIVE_PATH = os.path.join("docs", "project", "uat.md")
PROGRESS_MD_RELATIVE_PATH = os.path.join("docs", "project", "progress.md")
TRACEABILITY_MD_RELATIVE_PATH = os.path.join("docs", "project", "traceability.md")
STYLE_DIRECTION_RELATIVE_PATH = os.path.join("docs", "style-direction.md")
KANBAN_BACKLOG_RELATIVE_PATH = os.path.join("docs", "project", "kanban", "backlog.md")
KANBAN_IN_PROGRESS_RELATIVE_PATH = os.path.join("docs", "project", "kanban", "in-progress.md")
KANBAN_DONE_RELATIVE_PATH = os.path.join("docs", "project", "kanban", "done.md")
KANBAN_BLOCKED_RELATIVE_PATH = os.path.join("docs", "project", "kanban", "blocked.md")
GITHUB_SYNC_JSON_RELATIVE_PATH = os.path.join(".claude", "alfred-github-sync.json")
GITHUB_SYNC_MD_RELATIVE_PATH = os.path.join("docs", "project", "github-sync.md")
GUI_PORT_RELATIVE_PATH = os.path.join(".claude", "alfred-gui-port")
GUI_LOG_RELATIVE_PATH = os.path.join(".claude", "alfred-gui.log")
MEMORY_UI_JSON_RELATIVE_PATH = os.path.join(".claude", "alfred-memory-ui.json")
MEMORY_DB_RELATIVE_PATH = os.path.join(".claude", "alfred-memory.db")
VISUAL_SESSION_ROOT_RELATIVE_PATH = os.path.join(".alfred-dev", "visual")

_CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".scala",
    ".html",
    ".astro",
    ".vue",
    ".svelte",
}
_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    ".next",
    "dist",
    "build",
    "coverage",
    ".scannerwork",
}
_GREENFIELD_COMMAND = "alfred"
_SELF_ROUTING_COMMANDS = frozenset({"alfred"})
_NEXT_ACTION_SOURCE_LABELS = {
    "state": "sesión activa",
    "handoff": "handoff pendiente",
    "verify": "verificación/UAT",
    "brownfield": "mapa brownfield",
    "discovery": "discovery",
    "current": "estado operativo actual",
    "project": "contexto del proyecto",
    "default": "contexto mínimo",
}
_KANBAN_RELATIVE_BY_STATUS = {
    "backlog": KANBAN_BACKLOG_RELATIVE_PATH,
    "in-progress": KANBAN_IN_PROGRESS_RELATIVE_PATH,
    "done": KANBAN_DONE_RELATIVE_PATH,
    "blocked": KANBAN_BLOCKED_RELATIVE_PATH,
}
_KANBAN_STATUS_LABELS = {
    "backlog": "backlog",
    "in-progress": "in progress",
    "done": "done",
    "blocked": "blocked",
}
_KANBAN_TITLES = {
    "backlog": "Backlog",
    "in-progress": "In Progress",
    "done": "Done",
    "blocked": "Blocked",
}
_KNOWN_KANBAN_TASK_TYPES = frozenset({"generic", "main", "phase", "verify"})


def _session_optional_agent_flags(session: Dict[str, Any]) -> Dict[str, bool]:
    """Extrae los flags de agentes opcionales activos de una sesión."""
    equipo = session.get("equipo_sesion")
    if not isinstance(equipo, dict):
        return {}
    raw_flags = equipo.get("opcionales_activos")
    if not isinstance(raw_flags, dict):
        return {}
    return {
        str(agent_name).strip(): bool(is_active)
        for agent_name, is_active in raw_flags.items()
        if str(agent_name).strip()
    }


def _session_team_source_label(session: Dict[str, Any]) -> str:
    """Devuelve una etiqueta humana para la fuente del equipo runtime."""
    equipo = session.get("equipo_sesion")
    if not isinstance(equipo, dict):
        return ""

    source = str(equipo.get("fuente", "")).strip()
    if source == "config_persistida":
        return "configuración persistida"
    if source == "composicion_dinamica":
        return "composición dinámica"
    return ""


def _format_optional_agent_summary(
    parallel_optionals: List[str],
    sequential_optionals: List[str],
) -> str:
    """Construye una frase breve con los opcionales activos en una fase."""
    segments: List[str] = []
    ordered_parallel = order_optional_agent_names(parallel_optionals)
    ordered_sequential = order_optional_agent_names(sequential_optionals)
    if ordered_parallel:
        segments.append(
            "paralelo: " + ", ".join(f"`{agent}`" for agent in ordered_parallel)
        )
    if ordered_sequential:
        segments.append(
            "secuencial: " + ", ".join(f"`{agent}`" for agent in ordered_sequential)
        )
    return "; ".join(segments)


def _session_on_demand_optionals_for_flow(session: Dict[str, Any]) -> List[str]:
    """Devuelve opcionales activos que no se integran en ninguna fase del flujo."""
    command = str(session.get("comando", "")).strip()
    flow = FLOWS.get(command, {})
    flow_phases = {
        str(phase_def.get("nombre", "")).strip()
        for phase_def in (flow.get("fases") or [])
        if str(phase_def.get("nombre", "")).strip()
    }
    active_flags = _session_optional_agent_flags(session)
    active_names = [
        agent_name
        for agent_name, is_active in active_flags.items()
        if is_active
    ]

    on_demand: List[str] = []
    for agent_name in order_optional_agent_names(active_names):
        integration = OPTIONAL_INTEGRATIONS.get(agent_name, {})
        integrated_phases = {
            str(phase_name).strip()
            for phase_name in integration.get("fases", [])
            if str(phase_name).strip()
        }
        if not flow_phases.intersection(integrated_phases):
            on_demand.append(agent_name)
    return on_demand
_VISIBLE_KANBAN_TASK_TYPES = frozenset({"generic", "main"})
_SYNCABLE_KANBAN_TASK_TYPES = frozenset({"generic", "main"})
_KANBAN_RELATIVE_PATHS = frozenset(_KANBAN_RELATIVE_BY_STATUS.values())
_GH_STATUS_LABELS = {
    "backlog": "alfred:backlog",
    "in-progress": "alfred:in-progress",
    "done": "alfred:done",
    "blocked": "alfred:blocked",
}
_GH_SYNC_LABEL = "alfred:sync"
_GH_LEGACY_BOARD_LABEL = "alfred:board"
_KNOWN_ALFRED_COMMANDS = frozenset({
    "alfred",
    "feature",
    "quick",
    "fix",
    "spike",
    "ship",
    "audit",
    "map-codebase",
    "discuss",
    "next",
    "pause",
    "resume",
    "progress",
    "standup",
    "blocked",
    "in-progress",
    "verify",
    "validate",
    "search",
    "sync-github",
    "config",
    "status",
    "update",
    "help",
    "memory-ui",
    "lucius",
})


def _project_path(project_dir: str, relative_path: str) -> str:
    return os.path.join(project_dir, relative_path)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load_active_session_state(project_dir: str) -> Optional[Dict[str, Any]]:
    """Carga el estado activo si la sesión no está completada."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    if not isinstance(state, dict):
        return None
    if state.get("fase_actual") == "completado":
        return None
    return state


def _load_memory_runtime_config(project_dir: str) -> Dict[str, Any]:
    """Carga la configuración efectiva de memoria sin romper continuidad."""
    try:
        from core.memory_config import load_memory_config
    except Exception:
        return {
            "enabled": False,
            "capture_decisions": True,
        }
    return load_memory_config(project_dir)


def _open_memory_db(project_dir: str):
    """Abre la memoria del proyecto si está habilitada o ya existe."""
    db_path = _project_path(project_dir, MEMORY_DB_RELATIVE_PATH)
    settings = _load_memory_runtime_config(project_dir)
    if not settings.get("enabled", False) and not os.path.isfile(db_path):
        return None

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    try:
        from core.memory import MemoryDB
    except Exception:
        return None

    try:
        return MemoryDB(db_path)
    except Exception:
        return None


def _capture_helper_memory(
    project_dir: str,
    *,
    helper_name: str,
    event_summary: str,
    event_content: str,
    phase: Optional[str] = None,
    decision_title: Optional[str] = None,
    decision_choice: Optional[str] = None,
    decision_context: Optional[str] = None,
    decision_rationale: Optional[str] = None,
    impact: str = "low",
    tags: Optional[List[str]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Registra memoria ligera y útil para flujos helper-first."""
    db = _open_memory_db(project_dir)
    if db is None:
        return {"logged": False}

    settings = _load_memory_runtime_config(project_dir)
    decision_id = None
    event_id = None
    created_iteration_id = None
    helper_tags = ["helper-first", helper_name]
    if tags:
        helper_tags.extend(tags)

    try:
        active_iteration = db.get_active_iteration()
        iteration_id = int(active_iteration["id"]) if active_iteration else None
        if iteration_id is None:
            created_iteration_id = db.start_iteration(
                helper_name,
                decision_title or event_summary,
            )
            iteration_id = created_iteration_id

        if settings.get("capture_decisions", True) and decision_title and decision_choice:
            decision_id = db.log_decision(
                title=decision_title,
                chosen=decision_choice,
                context=decision_context,
                rationale=decision_rationale,
                impact=impact,
                phase=phase,
                iteration_id=iteration_id,
                tags=helper_tags,
            )

        event_payload = {
            "helper": helper_name,
            **(payload or {}),
        }
        if decision_id is not None:
            event_payload["decision_id"] = decision_id

        event_id = db.log_event(
            event_type="helper_seeded",
            phase=phase,
            payload=event_payload,
            summary=event_summary,
            content=event_content,
            iteration_id=iteration_id,
        )
        if created_iteration_id is not None:
            db.complete_iteration(created_iteration_id)
        return {"logged": True, "decision_id": decision_id, "event_id": event_id}
    finally:
        db.close()


def load_handoff(project_dir: str) -> Optional[Dict[str, Any]]:
    """Carga el handoff si existe y tiene estructura mínima válida."""
    handoff_path = _project_path(project_dir, HANDOFF_JSON_RELATIVE_PATH)
    try:
        with open(handoff_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    required = {"command", "phase", "resume_command"}
    if not required.issubset(data.keys()):
        return None

    return data


def load_uat(project_dir: str) -> Optional[Dict[str, Any]]:
    """Carga el estado de verificación manual si existe."""
    uat_path = _project_path(project_dir, UAT_JSON_RELATIVE_PATH)
    try:
        with open(uat_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    required = {"target_id", "status", "updated_at"}
    if not required.issubset(data.keys()):
        return None

    return data


def save_handoff(project_dir: str, handoff: Dict[str, Any]) -> str:
    """Guarda el handoff JSON en la ruta canónica y devuelve la ruta."""
    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    handoff_json_path = _project_path(project_dir, HANDOFF_JSON_RELATIVE_PATH)
    with open(handoff_json_path, "w", encoding="utf-8") as fh:
        json.dump(handoff, fh, indent=2, ensure_ascii=False)
    return handoff_json_path


def _iter_code_files(project_dir: str, max_depth: int = 2):
    root_depth = project_dir.rstrip(os.sep).count(os.sep)
    for current_root, dirs, files in os.walk(project_dir):
        current_depth = current_root.rstrip(os.sep).count(os.sep) - root_depth
        dirs[:] = [name for name in dirs if name not in _SKIP_DIRS]
        if current_depth > max_depth:
            dirs[:] = []
            continue

        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext.lower() in _CODE_EXTENSIONS:
                yield os.path.join(current_root, filename)


def project_has_codebase(project_dir: str) -> bool:
    """Determina si el directorio parece un repo brownfield con código."""
    stack = detect_stack(project_dir)
    if stack.get("runtime") != "desconocido":
        return True

    for marker in ("src", "app", "lib", "packages", "services", ".git"):
        if os.path.exists(os.path.join(project_dir, marker)):
            return True

    return next(_iter_code_files(project_dir), None) is not None


def needs_codebase_map(project_dir: str) -> bool:
    """Indica si conviene arrancar por map-codebase."""
    if not project_has_codebase(project_dir):
        return False

    codebase_map = _project_path(project_dir, CODEBASE_MAP_RELATIVE_PATH)
    return not os.path.isfile(codebase_map)


def _normalize_request_description(raw_request: str, fallback: str) -> str:
    """Normaliza descripciones libres para guardarlas en el estado."""
    compact = " ".join((raw_request or "").split()).strip()
    return compact if compact else fallback


def _read_text_if_exists(project_dir: str, relative_path: str) -> str:
    try:
        with open(_project_path(project_dir, relative_path), "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""
    except OSError:
        return ""


def _extract_markdown_list_items(markdown: str) -> List[str]:
    items: List[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        content = line[2:].strip()
        if not content:
            continue
        normalized = _normalize_free_text(content)
        if normalized in {"ninguna", "ninguno", "none", "sin bloqueos", "sin tareas"}:
            continue
        items.append(content)
    return items


def _extract_signal_lines(markdown: str, max_items: int = 3) -> List[str]:
    lines: List[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if not line:
            continue
        lines.append(line)
        if len(lines) >= max_items:
            break
    return lines


def _clean_inline_markdown(text: str) -> str:
    cleaned = (text or "").replace("**", "").replace("`", "").strip()
    return re.sub(r"\s+", " ", cleaned)


def _extract_criteria_ids(text: str) -> List[str]:
    found = {
        match.upper()
        for match in re.findall(r"\bCA-\d+\b", text or "", flags=re.IGNORECASE)
    }
    return sorted(found)


def _task_sort_key(task: Dict[str, Any]) -> Tuple[int, Any, str]:
    task_id = task.get("id") or ""
    match = re.search(r"(\d+)$", task_id)
    if match:
        return (0, int(match.group(1)), task.get("title", ""))
    return (1, task.get("title", "").lower(), task_id.lower())


def _task_reference(task: Dict[str, Any]) -> str:
    task_id = task.get("id")
    title = task.get("title", "sin titulo")
    if task_id:
        if isinstance(title, str) and title.startswith(f"[{task_id}]"):
            return title
        return f"[{task_id}] {title}"
    return title


def _parse_kanban_metadata_line(raw_line: str) -> Optional[Tuple[str, str]]:
    stripped = raw_line.strip()
    patterns = (
        r"^-\s+\*\*(?P<key>.+?):\*\*\s*(?P<value>.+?)\s*$",
        r"^-\s+\*\*(?P<key>.+?)\*\*:\s*(?P<value>.+?)\s*$",
        r"^-\s+(?P<key>[A-Za-zÀ-ÿ0-9 _/\-]+):\s*(?P<value>.+?)\s*$",
    )
    for pattern in patterns:
        match = re.match(pattern, stripped)
        if not match:
            continue
        key = _normalize_free_text(match.group("key")).replace(" ", "_")
        value = _clean_inline_markdown(match.group("value"))
        if key and value:
            return key, value
    return None


def _parse_kanban_tasks(markdown: str, status: str, relative_path: str) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    def flush() -> None:
        nonlocal current
        if current is None:
            return

        body_lines = current.get("body_lines", [])
        body = "\n".join(body_lines).strip()
        metadata = current.get("metadata", {})
        criteria = _extract_criteria_ids(" ".join([body] + list(metadata.values())))
        dependencies = metadata.get("dependencias") or metadata.get("dependencies") or ""
        evidence = metadata.get("evidencia") or metadata.get("evidence") or ""
        agent = metadata.get("agente") or metadata.get("agent") or ""
        notes = metadata.get("notas") or metadata.get("notes") or ""
        task_type = _normalize_task_type(metadata.get("tipo") or metadata.get("type") or "")

        current.update(
            {
                "body": body,
                "criteria": criteria,
                "dependencies": dependencies,
                "evidence": evidence,
                "agent": agent,
                "notes": notes,
                "task_type": task_type,
                "status": status,
                "path": relative_path,
            }
        )
        current.pop("body_lines", None)
        tasks.append(current)
        current = None

    heading_re = re.compile(r"^#{3,6}\s+(?:\[(?P<id>[^\]]+)\]\s+)?(?P<title>.+?)\s*$")
    checkbox_task_re = re.compile(
        r"^\s*-\s+\[(?: |x|X)\]\s+(?:\[(?P<id>[^\]]+)\]\s+)?(?P<title>.+?)\s*$"
    )
    bullet_id_task_re = re.compile(
        r"^\s*-\s+(?:\[(?P<id>[^\]]+)\]\s+)(?P<title>.+?)\s*$"
    )

    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        heading = heading_re.match(stripped)
        if heading:
            flush()
            current = {
                "id": (heading.group("id") or "").strip(),
                "title": heading.group("title").strip(),
                "metadata": {},
                "body_lines": [],
            }
            continue

        checkbox_task = checkbox_task_re.match(raw_line)
        if checkbox_task:
            flush()
            current = {
                "id": (checkbox_task.group("id") or "").strip(),
                "title": checkbox_task.group("title").strip(),
                "metadata": {},
                "body_lines": [],
            }
            continue

        bullet_id_task = bullet_id_task_re.match(raw_line)
        if bullet_id_task:
            flush()
            current = {
                "id": (bullet_id_task.group("id") or "").strip(),
                "title": bullet_id_task.group("title").strip(),
                "metadata": {},
                "body_lines": [],
            }
            continue

        if stripped.startswith("#"):
            flush()
            continue

        if current is None:
            continue

        metadata = _parse_kanban_metadata_line(raw_line)
        if metadata:
            key, value = metadata
            current["metadata"][key] = value
            continue

        current["body_lines"].append(raw_line.rstrip())

    flush()

    if tasks:
        return sorted(tasks, key=_task_sort_key)

    fallback_tasks: List[Dict[str, Any]] = []
    for index, item in enumerate(_extract_markdown_list_items(markdown), start=1):
        fallback_tasks.append(
            {
                "id": "",
                "title": item,
                "metadata": {},
                "body": item,
                "criteria": _extract_criteria_ids(item),
                "dependencies": "",
                "evidence": "",
                "agent": "",
                "notes": "",
                "task_type": "generic",
                "status": status,
                "path": relative_path,
                "fallback_index": index,
            }
        )
    return fallback_tasks


def load_kanban_board(project_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    board: Dict[str, List[Dict[str, Any]]] = {}
    for status, relative_path in _KANBAN_RELATIVE_BY_STATUS.items():
        markdown = _read_text_if_exists(project_dir, relative_path)
        board[status] = _parse_kanban_tasks(markdown, status=status, relative_path=relative_path)
    return board


def _normalize_task_id(task_id: str) -> str:
    cleaned = (task_id or "").strip().upper()
    if not cleaned:
        return ""
    match = re.fullmatch(r"T[- ]?(\d+)", cleaned)
    if match:
        return f"T-{int(match.group(1)):03d}"
    return cleaned


def _normalize_task_type(task_type: str) -> str:
    cleaned = _normalize_free_text(task_type).replace("_", "-")
    if cleaned in {"", "generica", "generico"}:
        return "generic"
    aliases = {
        "principal": "main",
        "flujo": "main",
        "fase": "phase",
        "verificacion": "verify",
        "validacion": "verify",
    }
    normalized = aliases.get(cleaned, cleaned)
    if normalized in _KNOWN_KANBAN_TASK_TYPES:
        return normalized
    return "generic"


def _infer_legacy_task_type(task: Dict[str, Any]) -> str:
    title = " ".join((task.get("title", "") or "").split()).strip()
    title_normalized = _normalize_free_text(title)
    notes_normalized = _normalize_free_text(task.get("notes", ""))
    agent = " ".join((task.get("agent", "") or "").split()).strip()
    agent_normalized = _normalize_free_text(agent)

    if (
        "con /alfred-dev:verify" in title_normalized
        or "validacion manual pendiente del flujo" in notes_normalized
        or agent_normalized == "alfred:verify"
    ):
        return "verify"

    match = re.match(r"^(?P<command>[a-z0-9-]+):(?P<phase>[a-z_]+)\s+[—-]", title)
    if match:
        command = match.group("command")
        phase_name = match.group("phase")
        flow = FLOWS.get(command)
        if flow and any(phase.get("nombre") == phase_name for phase in flow.get("fases", [])):
            return "phase"

    if agent_normalized.startswith("alfred:"):
        command = agent_normalized.split(":", 1)[1]
        if command in FLOWS:
            return "main"

    if any(
        signal in notes_normalized
        for signal in (
            "fase actual:",
            "flujo completado",
            "trabajo activo visible para sonia y la memory ui",
            "fases completadas:",
        )
    ):
        return "main"

    return "generic"


def _task_type(task: Dict[str, Any]) -> str:
    return _normalize_task_type(str(task.get("task_type", "")))


def _effective_task_type(task: Dict[str, Any]) -> str:
    stored = _task_type(task)
    if stored != "generic":
        return stored
    return _infer_legacy_task_type(task)


def _is_internal_kanban_task(task: Dict[str, Any]) -> bool:
    return _effective_task_type(task) not in _VISIBLE_KANBAN_TASK_TYPES


def _is_visible_kanban_task(task: Dict[str, Any]) -> bool:
    return _effective_task_type(task) in _VISIBLE_KANBAN_TASK_TYPES


def _is_syncable_kanban_task(task: Dict[str, Any]) -> bool:
    return _effective_task_type(task) in _SYNCABLE_KANBAN_TASK_TYPES


def _normalize_task_criteria(criteria: Optional[List[str]], *fallback_texts: str) -> List[str]:
    if criteria is not None:
        collected = " ".join(item for item in criteria if isinstance(item, str))
    else:
        collected = " ".join(item for item in fallback_texts if isinstance(item, str))
    return _extract_criteria_ids(collected)


def _next_kanban_task_id(board: Dict[str, List[Dict[str, Any]]]) -> str:
    highest = 0
    for lane_tasks in board.values():
        for task in lane_tasks:
            normalized = _normalize_task_id(task.get("id", ""))
            match = re.fullmatch(r"T-(\d+)", normalized)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"T-{highest + 1:03d}"


def _build_kanban_task(
    status: str,
    *,
    title: str,
    task_id: str,
    agent: str = "",
    notes: str = "",
    dependencies: str = "",
    evidence: str = "",
    criteria: Optional[List[str]] = None,
    body: str = "",
    task_type: str = "generic",
) -> Dict[str, Any]:
    cleaned_title = " ".join((title or "").split()).strip()
    if not cleaned_title:
        raise RuntimeError("La tarea SonIA necesita un título no vacío.")

    cleaned_body = (body or "").strip()
    cleaned_notes = " ".join((notes or "").split()).strip()
    cleaned_dependencies = " ".join((dependencies or "").split()).strip()
    cleaned_evidence = " ".join((evidence or "").split()).strip()
    cleaned_agent = " ".join((agent or "").split()).strip()

    return {
        "id": _normalize_task_id(task_id),
        "title": cleaned_title,
        "metadata": {},
        "body": cleaned_body,
        "criteria": _normalize_task_criteria(
            criteria,
            cleaned_title,
            cleaned_body,
            cleaned_notes,
            cleaned_dependencies,
            cleaned_evidence,
        ),
        "dependencies": cleaned_dependencies,
        "evidence": cleaned_evidence,
        "agent": cleaned_agent,
        "notes": cleaned_notes,
        "task_type": _normalize_task_type(task_type),
        "status": status,
        "path": _KANBAN_RELATIVE_BY_STATUS[status],
    }


def _render_kanban_task(task: Dict[str, Any]) -> str:
    lines = [f"### {_task_reference(task)}", ""]
    task_type = _effective_task_type(task)
    if task_type != "generic":
        lines.append(f"- **Tipo:** {task_type}")
    if task.get("agent"):
        lines.append(f"- **Agente:** {task['agent']}")
    if task.get("criteria"):
        lines.append(f"- **Criterios:** {', '.join(task['criteria'])}")
    if task.get("dependencies"):
        lines.append(f"- **Dependencias:** {task['dependencies']}")
    if task.get("notes"):
        lines.append(f"- **Notas:** {task['notes']}")
    if task.get("evidence"):
        lines.append(f"- **Evidencia:** {task['evidence']}")
    body = (task.get("body") or "").strip()
    if body:
        lines.extend(["", body])
    return "\n".join(lines).rstrip()


def _render_kanban_lane(status: str, tasks: List[Dict[str, Any]]) -> str:
    title = _KANBAN_TITLES[status]
    blocks = [_render_kanban_task(task) for task in sorted(tasks, key=_task_sort_key)]
    if not blocks:
        return f"# {title}\n"
    return f"# {title}\n\n" + "\n\n".join(blocks).rstrip() + "\n"


def _save_kanban_lane(project_dir: str, status: str, tasks: List[Dict[str, Any]]) -> str:
    relative_path = _KANBAN_RELATIVE_BY_STATUS[status]
    path = _project_path(project_dir, relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_render_kanban_lane(status, tasks))
    return path


def normalize_kanban_task_types(project_dir: str) -> Dict[str, Any]:
    board = load_kanban_board(project_dir)
    changed: List[Dict[str, str]] = []

    for status in _KANBAN_RELATIVE_BY_STATUS:
        lane_tasks = list(board.get(status, []))
        lane_changed = False
        normalized_lane: List[Dict[str, Any]] = []
        for task in lane_tasks:
            normalized_task = dict(task)
            effective_type = _effective_task_type(task)
            if _task_type(task) != effective_type:
                normalized_task["task_type"] = effective_type
                changed.append(
                    {
                        "id": normalized_task.get("id", ""),
                        "title": normalized_task.get("title", ""),
                        "task_type": effective_type,
                        "status": status,
                    }
                )
                lane_changed = True
            normalized_lane.append(normalized_task)
        if lane_changed:
            _save_kanban_lane(project_dir, status, normalized_lane)

    return {"count": len(changed), "changed": changed}


def _find_kanban_task(
    board: Dict[str, List[Dict[str, Any]]],
    task_ref: str,
) -> Tuple[str, int, Dict[str, Any]]:
    normalized_ref = _normalize_free_text(task_ref)
    normalized_id = _normalize_task_id(task_ref)
    for status, lane_tasks in board.items():
        for index, task in enumerate(lane_tasks):
            task_id = _normalize_task_id(task.get("id", ""))
            title = _normalize_free_text(task.get("title", ""))
            reference = _normalize_free_text(_task_reference(task))
            if normalized_id and task_id == normalized_id:
                return status, index, task
            if normalized_ref and normalized_ref in {title, reference}:
                return status, index, task
    raise RuntimeError(f"No se ha encontrado la tarea '{task_ref}' en el kanban.")


def create_kanban_task(
    project_dir: str,
    status: str,
    *,
    title: str,
    agent: str = "",
    notes: str = "",
    dependencies: str = "",
    evidence: str = "",
    criteria: Optional[List[str]] = None,
    body: str = "",
    task_id: str = "",
    task_type: str = "generic",
) -> Dict[str, Any]:
    if status not in _KANBAN_RELATIVE_BY_STATUS:
        raise RuntimeError(f"Columna kanban desconocida: {status}")

    board = load_kanban_board(project_dir)
    normalized_title = _normalize_free_text(title)
    for existing in board.get(status, []):
        if _normalize_free_text(existing.get("title", "")) != normalized_title:
            continue
        changed = False
        updated = dict(existing)
        if agent and not updated.get("agent"):
            updated["agent"] = " ".join(agent.split())
            changed = True
        if notes and not updated.get("notes"):
            updated["notes"] = " ".join(notes.split())
            changed = True
        if dependencies and not updated.get("dependencies"):
            updated["dependencies"] = " ".join(dependencies.split())
            changed = True
        if evidence and not updated.get("evidence"):
            updated["evidence"] = " ".join(evidence.split())
            changed = True
        if criteria is not None and not updated.get("criteria"):
            updated["criteria"] = _normalize_task_criteria(criteria)
            changed = True
        if body and not updated.get("body"):
            updated["body"] = body.strip()
            changed = True
        normalized_task_type = _normalize_task_type(task_type)
        if normalized_task_type != "generic" and _task_type(updated) == "generic":
            updated["task_type"] = normalized_task_type
            changed = True
        if changed:
            lane_tasks = [
                updated if task is existing else task
                for task in board.get(status, [])
            ]
            _save_kanban_lane(project_dir, status, lane_tasks)
            return updated
        return existing

    created = _build_kanban_task(
        status,
        title=title,
        task_id=task_id or _next_kanban_task_id(board),
        agent=agent,
        notes=notes,
        dependencies=dependencies,
        evidence=evidence,
        criteria=criteria,
        body=body,
        task_type=task_type,
    )
    lane_tasks = [*board.get(status, []), created]
    _save_kanban_lane(project_dir, status, lane_tasks)
    return created


def update_kanban_task(
    project_dir: str,
    task_ref: str,
    *,
    status: Optional[str] = None,
    title: Optional[str] = None,
    agent: Optional[str] = None,
    notes: Optional[str] = None,
    dependencies: Optional[str] = None,
    evidence: Optional[str] = None,
    criteria: Optional[List[str]] = None,
    body: Optional[str] = None,
    task_type: Optional[str] = None,
) -> Dict[str, Any]:
    board = load_kanban_board(project_dir)
    current_status, index, existing = _find_kanban_task(board, task_ref)
    target_status = status or current_status
    if target_status not in _KANBAN_RELATIVE_BY_STATUS:
        raise RuntimeError(f"Columna kanban desconocida: {target_status}")

    updated = dict(existing)
    if title is not None:
        cleaned_title = " ".join(title.split()).strip()
        if not cleaned_title:
            raise RuntimeError("La tarea SonIA necesita un título no vacío.")
        updated["title"] = cleaned_title
    if agent is not None:
        updated["agent"] = " ".join(agent.split()).strip()
    if notes is not None:
        updated["notes"] = " ".join(notes.split()).strip()
    if dependencies is not None:
        updated["dependencies"] = " ".join(dependencies.split()).strip()
    if evidence is not None:
        updated["evidence"] = " ".join(evidence.split()).strip()
    if body is not None:
        updated["body"] = body.strip()
    if criteria is not None:
        updated["criteria"] = _normalize_task_criteria(criteria)
    if task_type is not None:
        updated["task_type"] = _normalize_task_type(task_type)

    updated["status"] = target_status
    updated["path"] = _KANBAN_RELATIVE_BY_STATUS[target_status]
    if criteria is None:
        updated["criteria"] = _normalize_task_criteria(
            None,
            updated.get("title", ""),
            updated.get("body", ""),
            updated.get("notes", ""),
            updated.get("dependencies", ""),
            updated.get("evidence", ""),
        )

    current_lane = list(board.get(current_status, []))
    current_lane.pop(index)
    board[current_status] = current_lane
    board[target_status] = [*board.get(target_status, []), updated]

    for lane_status in {current_status, target_status}:
        _save_kanban_lane(project_dir, lane_status, board.get(lane_status, []))
    return updated


def move_kanban_task(
    project_dir: str,
    task_ref: str,
    target_status: str,
    *,
    agent: Optional[str] = None,
    notes: Optional[str] = None,
    dependencies: Optional[str] = None,
    evidence: Optional[str] = None,
    criteria: Optional[List[str]] = None,
    body: Optional[str] = None,
    task_type: Optional[str] = None,
) -> Dict[str, Any]:
    return update_kanban_task(
        project_dir,
        task_ref,
        status=target_status,
        agent=agent,
        notes=notes,
        dependencies=dependencies,
        evidence=evidence,
        criteria=criteria,
        body=body,
        task_type=task_type,
    )


def delete_kanban_task(project_dir: str, task_ref: str) -> Dict[str, Any]:
    board = load_kanban_board(project_dir)
    current_status, index, existing = _find_kanban_task(board, task_ref)
    lane_tasks = list(board.get(current_status, []))
    lane_tasks.pop(index)
    _save_kanban_lane(project_dir, current_status, lane_tasks)
    return existing


def _task_matches_candidate(task: Dict[str, Any], candidate: str) -> bool:
    normalized_candidate = _normalize_free_text(candidate)
    normalized_candidate_id = _normalize_task_id(candidate)
    task_id = _normalize_task_id(task.get("id", ""))
    if normalized_candidate_id and task_id == normalized_candidate_id:
        return True
    if not normalized_candidate:
        return False
    return normalized_candidate in {
        _normalize_free_text(task.get("title", "")),
        _normalize_free_text(_task_reference(task)),
    }


def _find_kanban_task_in_statuses(
    board: Dict[str, List[Dict[str, Any]]],
    candidates: List[str],
    statuses: Tuple[str, ...],
) -> Optional[Tuple[str, int, Dict[str, Any]]]:
    cleaned_candidates = [
        candidate for candidate in candidates
        if isinstance(candidate, str) and candidate.strip()
    ]
    if not cleaned_candidates:
        return None

    for status in statuses:
        for index, task in enumerate(board.get(status, [])):
            if any(_task_matches_candidate(task, candidate) for candidate in cleaned_candidates):
                return status, index, task
    return None


def _merge_task_notes(existing_notes: str, extra_note: str) -> str:
    existing = " ".join((existing_notes or "").split()).strip()
    extra = " ".join((extra_note or "").split()).strip()
    if not existing:
        return extra
    if not extra:
        return existing
    if _normalize_free_text(extra) in _normalize_free_text(existing):
        return existing
    return f"{existing} {extra}"


def _verification_task_title(description: str) -> str:
    cleaned = " ".join((description or "").split()).strip()
    if not cleaned:
        return "Validar último flujo completado con /alfred-dev:verify."
    return f"Validar '{cleaned}' con /alfred-dev:verify."


def _ensure_verification_task(
    project_dir: str,
    *,
    description: str,
    command: str,
) -> Dict[str, Any]:
    return create_kanban_task(
        project_dir,
        "backlog",
        title=_verification_task_title(description),
        agent="alfred:verify",
        notes=(
            f"Validación manual pendiente del flujo '{command}'. "
            "Cerrar con /alfred-dev:verify."
        ),
        task_type="verify",
    )


def _ensure_session_execution_task(
    project_dir: str,
    session: Dict[str, Any],
) -> Dict[str, Any]:
    description = " ".join((session.get("descripcion", "") or "").split()).strip()
    command = str(session.get("comando", "alfred")).strip() or "alfred"
    agent_label = f"alfred:{command}"

    board = load_kanban_board(project_dir)
    match = _find_kanban_task_in_statuses(
        board,
        [session.get("kanban_task_id", ""), description],
        ("in-progress", "backlog"),
    )
    if match is not None:
        current_status, _, task = match
        task_ref = task.get("id") or task.get("title", "")
        desired_agent = task.get("agent") or agent_label
        if current_status == "backlog":
            return move_kanban_task(
                project_dir,
                task_ref,
                "in-progress",
                agent=desired_agent,
                notes=task.get("notes", ""),
                dependencies=task.get("dependencies", ""),
                evidence=task.get("evidence", ""),
                criteria=task.get("criteria"),
                body=task.get("body", ""),
                task_type="main",
            )
        return update_kanban_task(
            project_dir,
            task_ref,
            agent=desired_agent,
            notes=task.get("notes", ""),
            dependencies=task.get("dependencies", ""),
            evidence=task.get("evidence", ""),
            criteria=task.get("criteria"),
            body=task.get("body", ""),
            task_type="main",
        )

    return create_kanban_task(
        project_dir,
        "in-progress",
        title=description or "Trabajo activo sin descripción",
        agent=agent_label,
        notes="Trabajo activo visible para SonIA y la Memory UI.",
        task_type="main",
    )


def _delete_first_matching_kanban_task(
    project_dir: str,
    candidates: List[str],
    *,
    statuses: Tuple[str, ...] = ("backlog", "in-progress", "blocked", "done"),
) -> Optional[Dict[str, Any]]:
    board = load_kanban_board(project_dir)
    match = _find_kanban_task_in_statuses(board, candidates, statuses)
    if match is None:
        return None
    _, _, task = match
    task_ref = task.get("id") or task.get("title", "")
    return delete_kanban_task(project_dir, task_ref)


def _sync_kanban_after_verify(
    project_dir: str,
    target: Dict[str, Any],
    record: Dict[str, Any],
) -> Dict[str, str]:
    if target.get("source") != "completed-session":
        return {}

    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH)) or {}
    description = " ".join((target.get("target_description", "") or "").split()).strip()
    command = str(target.get("target_command", "alfred")).strip() or "alfred"
    agent_label = f"alfred:{command}"
    main_candidates = [state.get("kanban_task_id", ""), description]
    verify_candidates = [
        state.get("kanban_verify_task_id", ""),
        _verification_task_title(description),
    ]

    if record.get("status") == "pending":
        verify_task = _ensure_verification_task(
            project_dir,
            description=description,
            command=command,
        )
        return {"verify_task_id": verify_task.get("id", "")}

    board = load_kanban_board(project_dir)
    match = _find_kanban_task_in_statuses(
        board,
        main_candidates,
        ("in-progress", "backlog", "blocked", "done"),
    )

    if record.get("status") == "approved":
        evidence = f"UAT aprobada el {record.get('updated_at', _now_utc().isoformat())}"
        if record.get("notes"):
            evidence = f"{evidence} — {record['notes']}"

        if match is not None:
            _, _, task = match
            task_ref = task.get("id") or task.get("title", "")
            synced = move_kanban_task(
                project_dir,
                task_ref,
                "done",
                agent=task.get("agent") or agent_label,
                notes=task.get("notes", ""),
                dependencies=task.get("dependencies", ""),
                evidence=evidence,
                criteria=task.get("criteria"),
                body=task.get("body", ""),
                task_type="main",
            )
        else:
            synced = create_kanban_task(
                project_dir,
                "done",
                title=description or f"Cierre de {command}",
                agent=agent_label,
                notes="Cerrado tras verificación manual/UAT aprobada.",
                evidence=evidence,
                task_type="main",
            )

        _delete_first_matching_kanban_task(project_dir, verify_candidates)
        return {"task_id": synced.get("id", ""), "task_status": "done"}

    if record.get("status") == "rejected":
        reject_note = (
            f"UAT rechazada: {record['notes']}"
            if record.get("notes")
            else "UAT rechazada; revisar el cambio y repetir /alfred-dev:verify."
        )

        if match is not None:
            _, _, task = match
            task_ref = task.get("id") or task.get("title", "")
            synced = move_kanban_task(
                project_dir,
                task_ref,
                "blocked",
                agent=task.get("agent") or agent_label,
                notes=_merge_task_notes(task.get("notes", ""), reject_note),
                dependencies=task.get("dependencies", ""),
                evidence="",
                criteria=task.get("criteria"),
                body=task.get("body", ""),
                task_type="main",
            )
        else:
            synced = create_kanban_task(
                project_dir,
                "blocked",
                title=description or f"Revisar {command}",
                agent=agent_label,
                notes=reject_note,
                task_type="main",
            )

        _delete_first_matching_kanban_task(project_dir, verify_candidates)
        return {"task_id": synced.get("id", ""), "task_status": "blocked"}

    return {}


def _project_dir_from_state_path(state_path: str) -> str:
    absolute = os.path.abspath(state_path)
    parent = os.path.dirname(absolute)
    if os.path.basename(absolute) == "alfred-dev-state.json" and os.path.basename(parent) == ".claude":
        return os.path.dirname(parent)
    return parent


def _load_matching_session_uat(project_dir: str, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if session.get("fase_actual") != "completado":
        return None

    command = str(session.get("comando", "desconocido")).strip() or "desconocido"
    target_id = f"session:{command}:{_last_completed_at(session)}"
    uat = load_uat(project_dir)
    if isinstance(uat, dict) and uat.get("target_id") == target_id:
        return uat
    return None


def _session_phase_summary(session: Dict[str, Any]) -> str:
    completed = [
        phase.get("nombre", "")
        for phase in (session.get("fases_completadas") or [])
        if isinstance(phase, dict) and phase.get("nombre")
    ]
    if not completed:
        return "Sin fases completadas todavía."
    return "Fases completadas: " + ", ".join(completed) + "."


def _completed_style_visual_phase(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for phase in (session.get("fases_completadas") or []):
        if not isinstance(phase, dict):
            continue
        if phase.get("nombre") != "estilo_visual":
            continue
        if str(phase.get("resultado", "")).strip() == "saltada":
            return None
        return phase
    return None


def _load_latest_selina_choice(project_dir: str) -> Optional[Dict[str, Any]]:
    visual_root = _project_path(project_dir, VISUAL_SESSION_ROOT_RELATIVE_PATH)
    if not os.path.isdir(visual_root):
        return None

    try:
        from core.selina_visual import read_latest_style_choice  # noqa: PLC0415
    except Exception:
        return None

    latest_choice: Optional[Dict[str, Any]] = None
    latest_key: Tuple[str, float] = ("", 0.0)

    for entry in os.scandir(visual_root):
        if not entry.is_dir():
            continue
        state_dir = os.path.join(entry.path, "state")
        events_path = os.path.join(state_dir, "events")
        if not os.path.isfile(events_path):
            continue

        choice = read_latest_style_choice(state_dir)
        if not isinstance(choice, dict):
            continue

        timestamp = str(choice.get("timestamp", "")).strip()
        try:
            mtime = os.path.getmtime(events_path)
        except OSError:
            mtime = 0.0

        candidate_key = (timestamp, mtime)
        if candidate_key >= latest_key:
            latest_key = candidate_key
            latest_choice = choice

    return latest_choice


def _enrich_style_visual_phase_result(project_dir: str, phase_result: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(phase_result)
    artifacts = [
        str(item).strip()
        for item in (enriched.get("artefactos") or [])
        if str(item).strip()
    ]
    style_direction_path = _project_path(project_dir, STYLE_DIRECTION_RELATIVE_PATH)
    if os.path.isfile(style_direction_path) and STYLE_DIRECTION_RELATIVE_PATH not in artifacts:
        artifacts.append(STYLE_DIRECTION_RELATIVE_PATH)
    enriched["artefactos"] = artifacts

    choice = _load_latest_selina_choice(project_dir)
    if isinstance(choice, dict):
        enriched["selina_choice"] = choice.get("choice")
        enriched["selina_label"] = choice.get("label")
        enriched["selina_timestamp"] = choice.get("timestamp")

    return enriched


def _enrich_session_style_visual(project_dir: str, session: Dict[str, Any]) -> Dict[str, Any]:
    phase_result = _completed_style_visual_phase(session)
    if phase_result is None:
        return session

    enriched = dict(session)
    phase_entries: List[Dict[str, Any]] = []
    for phase in (session.get("fases_completadas") or []):
        if not isinstance(phase, dict):
            phase_entries.append(phase)
            continue
        if phase.get("nombre") == "estilo_visual" and str(phase.get("resultado", "")).strip() != "saltada":
            phase_entries.append(_enrich_style_visual_phase_result(project_dir, phase))
        else:
            phase_entries.append(phase)

    enriched["fases_completadas"] = phase_entries
    global_artifacts = [
        str(item).strip()
        for item in (session.get("artefactos") or [])
        if str(item).strip()
    ]
    if os.path.isfile(_project_path(project_dir, STYLE_DIRECTION_RELATIVE_PATH)):
        if STYLE_DIRECTION_RELATIVE_PATH not in global_artifacts:
            global_artifacts.append(STYLE_DIRECTION_RELATIVE_PATH)
    enriched["artefactos"] = global_artifacts
    return enriched


def _phase_task_title(command: str, phase_name: str, description: str) -> str:
    cleaned_description = " ".join((description or "").split()).strip() or "sin descripcion"
    return f"{command}:{phase_name} — {cleaned_description}"


def _phase_task_notes(
    command: str,
    phase_def: Dict[str, Any],
    *,
    phase_result: Optional[Dict[str, Any]] = None,
    current_phase: bool = False,
) -> str:
    phase_name = phase_def.get("nombre", "desconocida")
    agents = ", ".join(phase_def.get("agentes") or [])
    base = f"Fase '{phase_name}' del flujo '{command}'."
    if agents:
        base += f" Agentes base: {agents}."

    if phase_result is not None:
        result = str(phase_result.get("resultado", "aprobado")).strip() or "aprobado"
        if result == "saltada":
            return f"{base} Fase saltada por condición del flujo."

        iterations = phase_result.get("iteraciones", 0)
        artifacts = phase_result.get("artefactos") or []
        note = f"{base} Fase completada con resultado '{result}'."
        if isinstance(iterations, int) and iterations > 0:
            note += f" Iteraciones internas: {iterations}."
        if artifacts:
            note += f" Artefactos registrados: {len(artifacts)}."
        if phase_result.get("selina_choice"):
            label = phase_result.get("selina_label") or phase_result.get("selina_choice")
            note += f" Elección visual: {label}."
        return note

    if current_phase:
        gate_type = phase_def.get("gate_tipo", "sin gate")
        return f"{base} Fase activa. Gate: {gate_type}."

    return f"{base} Pendiente de ejecución."


def _phase_task_evidence(phase_result: Optional[Dict[str, Any]]) -> str:
    if not isinstance(phase_result, dict):
        return ""
    completed_at = str(phase_result.get("completada_en", "")).strip()
    result = str(phase_result.get("resultado", "")).strip()
    if result == "saltada":
        return ""
    if phase_result.get("selina_choice"):
        label = str(phase_result.get("selina_label") or phase_result.get("selina_choice")).strip()
        timestamp = str(phase_result.get("selina_timestamp", "")).strip() or completed_at
        evidence = f"Elección visual '{label}' registrada"
        if timestamp:
            evidence += f" en {timestamp}"
        artifacts = phase_result.get("artefactos") or []
        if STYLE_DIRECTION_RELATIVE_PATH in artifacts:
            evidence += f" y artefacto {STYLE_DIRECTION_RELATIVE_PATH} generado"
        return evidence
    if completed_at:
        return f"Fase completada en {completed_at}"
    return ""


def _phase_task_body(
    phase_def: Dict[str, Any],
    *,
    phase_result: Optional[Dict[str, Any]] = None,
    current_phase: bool = False,
) -> str:
    phase_name = phase_def.get("nombre", "desconocida")
    gate_type = phase_def.get("gate_tipo", "sin gate")
    mode = "paralelo" if phase_def.get("paralelo") else "secuencial"
    description = " ".join((phase_def.get("descripcion", "") or "").split()).strip()
    artifacts = phase_result.get("artefactos") if isinstance(phase_result, dict) else []
    if not isinstance(artifacts, list):
        artifacts = []

    result_label = "pendiente"
    if phase_result is not None:
        result_label = str(phase_result.get("resultado", "aprobado")).strip() or "aprobado"
    elif current_phase:
        result_label = "en curso"

    lines = [
        f"Nombre de fase: {phase_name}",
        f"Gate: {gate_type}",
        f"Ejecución: {mode}",
        f"Estado de fase: {result_label}",
    ]
    if description:
        lines.append(f"Objetivo: {description}")

    if isinstance(phase_result, dict):
        iterations = phase_result.get("iteraciones", 0)
        if isinstance(iterations, int):
            lines.append(f"Iteraciones internas: {iterations}")
        completed_at = str(phase_result.get("completada_en", "")).strip()
        if completed_at:
            lines.append(f"Completada en: {completed_at}")
        if phase_result.get("selina_choice"):
            choice_label = str(phase_result.get("selina_label") or phase_result.get("selina_choice")).strip()
            lines.append(f"Elección visual: {choice_label}")
            choice_timestamp = str(phase_result.get("selina_timestamp", "")).strip()
            if choice_timestamp:
                lines.append(f"Elección registrada en: {choice_timestamp}")

    if artifacts:
        lines.append("Artefactos:")
        lines.extend(f"* {item}" for item in artifacts if str(item).strip())
    elif phase_result is not None and result_label != "saltada":
        lines.append("Artefactos: sin artefactos explícitos")

    return "\n".join(lines)


def _sync_session_phase_tasks(project_dir: str, session: Dict[str, Any]) -> Dict[str, str]:
    command = str(session.get("comando", "alfred")).strip() or "alfred"
    flow = FLOWS.get(command)
    if not flow:
        return {}

    description = " ".join((session.get("descripcion", "") or "").split()).strip()
    completed_entries = {
        phase.get("nombre", ""): phase
        for phase in (session.get("fases_completadas") or [])
        if isinstance(phase, dict) and phase.get("nombre")
    }
    current_phase = str(session.get("fase_actual", "")).strip()
    stored_ids = session.get("kanban_phase_task_ids")
    if not isinstance(stored_ids, dict):
        stored_ids = {}

    phase_task_ids: Dict[str, str] = {}
    previous_task_id = ""

    for phase_def in flow.get("fases", []):
        phase_name = phase_def.get("nombre", "desconocida")
        phase_result = completed_entries.get(phase_name)
        is_current = current_phase == phase_name and phase_result is None
        if phase_result is not None:
            target_status = "done"
        elif is_current:
            target_status = "in-progress"
        else:
            target_status = "backlog"

        title = _phase_task_title(command, phase_name, description)
        notes = _phase_task_notes(
            command,
            phase_def,
            phase_result=phase_result,
            current_phase=is_current,
        )
        body = _phase_task_body(
            phase_def,
            phase_result=phase_result,
            current_phase=is_current,
        )
        evidence = _phase_task_evidence(phase_result)
        dependency = previous_task_id if previous_task_id else ""
        agent = ", ".join(phase_def.get("agentes") or [])
        criteria = _normalize_task_criteria(None, title, notes, body, evidence)

        board = load_kanban_board(project_dir)
        match = _find_kanban_task_in_statuses(
            board,
            [stored_ids.get(phase_name, ""), title],
            ("in-progress", "backlog", "blocked", "done"),
        )

        if match is not None:
            _, _, task = match
            task_ref = task.get("id") or task.get("title", "")
            merged_notes = _merge_task_notes(task.get("notes", ""), notes)
            task_agent = task.get("agent") or agent
            if target_status == task.get("status"):
                synced = update_kanban_task(
                    project_dir,
                    task_ref,
                    agent=task_agent,
                    notes=merged_notes,
                    dependencies=dependency if dependency else task.get("dependencies", ""),
                    evidence=evidence if evidence else task.get("evidence", ""),
                    criteria=criteria,
                    body=body,
                    task_type="phase",
                )
            else:
                synced = move_kanban_task(
                    project_dir,
                    task_ref,
                    target_status,
                    agent=task_agent,
                    notes=merged_notes,
                    dependencies=dependency,
                    evidence=evidence if evidence else task.get("evidence", ""),
                    criteria=criteria,
                    body=body,
                    task_type="phase",
                )
        else:
            synced = create_kanban_task(
                project_dir,
                target_status,
                title=title,
                agent=agent,
                notes=notes,
                dependencies=dependency,
                evidence=evidence,
                criteria=criteria,
                body=body,
                task_type="phase",
            )

        phase_task_ids[phase_name] = synced.get("id", "")
        previous_task_id = synced.get("id", "") or previous_task_id

    return phase_task_ids


def _sync_session_main_task(project_dir: str, session: Dict[str, Any]) -> Dict[str, Any]:
    description = " ".join((session.get("descripcion", "") or "").split()).strip()
    command = str(session.get("comando", "alfred")).strip() or "alfred"
    agent_label = f"alfred:{command}"
    phase = str(session.get("fase_actual", "")).strip() or "desconocida"
    uat = _load_matching_session_uat(project_dir, session)
    uat_status = str(uat.get("status", "")).strip() if uat else ""

    if phase == "completado":
        if uat_status == "rejected":
            target_status = "blocked"
            session_note = (
                f"Flujo completado en estado, pero UAT rechazada. "
                f"{(uat.get('notes') or '').strip() or 'Necesita retrabajo antes de volver a verificar.'}"
            )
        elif uat_status == "approved":
            target_status = "done"
            session_note = "Flujo completado y UAT aprobada."
        else:
            target_status = "done"
            session_note = "Flujo completado en estado; pendiente verificación manual/UAT."
    else:
        target_status = "in-progress"
        session_note = f"Fase actual: {phase}."

    summary_note = _session_phase_summary(session)
    session_note = f"{session_note} {summary_note}".strip()

    board = load_kanban_board(project_dir)
    match = _find_kanban_task_in_statuses(
        board,
        [session.get("kanban_task_id", ""), description],
        ("in-progress", "backlog", "blocked", "done"),
    )

    evidence = ""
    if uat_status == "approved" and uat:
        evidence = f"UAT aprobada el {uat.get('updated_at', _now_utc().isoformat())}"
        if uat.get("notes"):
            evidence = f"{evidence} — {uat['notes']}"

    if match is not None:
        _, _, task = match
        task_ref = task.get("id") or task.get("title", "")
        merged_notes = _merge_task_notes(task.get("notes", ""), session_note)
        task_agent = task.get("agent") or agent_label
        if target_status == task.get("status"):
            return update_kanban_task(
                project_dir,
                task_ref,
                agent=task_agent,
                notes=merged_notes,
                dependencies=task.get("dependencies", ""),
                evidence=evidence if evidence else task.get("evidence", ""),
                criteria=task.get("criteria"),
                body=task.get("body", ""),
                task_type="main",
            )
        return move_kanban_task(
            project_dir,
            task_ref,
            target_status,
            agent=task_agent,
            notes=merged_notes,
            dependencies=task.get("dependencies", ""),
            evidence=evidence if evidence else task.get("evidence", ""),
            criteria=task.get("criteria"),
            body=task.get("body", ""),
            task_type="main",
        )

    return create_kanban_task(
        project_dir,
        target_status,
        title=description or f"Flujo {command}",
        agent=agent_label,
        notes=session_note,
        evidence=evidence,
        task_type="main",
    )


def sync_session_state_to_kanban(
    state_path: str,
    session: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(session, dict):
        return session
    if not session.get("comando") or not session.get("descripcion"):
        return session

    project_dir = _project_dir_from_state_path(state_path)
    normalize_kanban_task_types(project_dir)
    synced = _enrich_session_style_visual(project_dir, dict(session))
    main_task = _sync_session_main_task(project_dir, synced)
    synced["kanban_task_id"] = main_task.get("id", "")
    synced["kanban_phase_task_ids"] = _sync_session_phase_tasks(project_dir, synced)

    command = str(synced.get("comando", "alfred")).strip() or "alfred"
    description = " ".join((synced.get("descripcion", "") or "").split()).strip()
    phase = str(synced.get("fase_actual", "")).strip()
    uat = _load_matching_session_uat(project_dir, synced)
    uat_status = str(uat.get("status", "")).strip() if uat else ""

    if phase == "completado" and uat_status in {"approved", "rejected"}:
        _delete_first_matching_kanban_task(
            project_dir,
            [synced.get("kanban_verify_task_id", ""), _verification_task_title(description)],
            statuses=("backlog", "in-progress"),
        )
        synced.pop("kanban_verify_task_id", None)
        return synced

    verify_task = _ensure_verification_task(
        project_dir,
        description=description,
        command=command,
    )
    synced["kanban_verify_task_id"] = verify_task.get("id", "")
    return synced


def _dedupe_artifact_paths(paths: List[str]) -> List[str]:
    seen: set[str] = set()
    deduped: List[str] = []
    for item in paths:
        path = str(item).strip()
        if not path or path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def _kanban_tasks_by_id(board: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    tasks: Dict[str, Dict[str, Any]] = {}
    for status in ("backlog", "in-progress", "done", "blocked"):
        for task in board.get(status, []):
            if not isinstance(task, dict):
                continue
            task_id = str(task.get("id", "")).strip()
            if task_id:
                tasks[task_id] = task
    return tasks


def _phase_fallback_visible_criteria(phase_def: Dict[str, Any]) -> List[str]:
    """Devuelve criterios visibles mínimos cuando la fase no define IDs CA-*.

    El objetivo no es inventar criterios de aceptación formales, sino evitar
    que la documentación automática quede vacía en fases donde el runtime sí
    conoce el objetivo operativo y el tipo de gate.
    """
    criteria: List[str] = []
    description = " ".join((phase_def.get("descripcion", "") or "").split()).strip()
    gate = str(phase_def.get("gate_tipo", "")).strip()

    if description:
        criteria.append(description.rstrip("."))

    if gate and gate not in {"libre", "sin gate"}:
        criteria.append(f"Cerrar la gate `{gate}` sin bloqueos abiertos")

    if not criteria:
        phase_name = str(phase_def.get("nombre", "desconocida")).strip() or "desconocida"
        criteria.append(f"Completar la fase `{phase_name}` con evidencia operativa visible")

    return criteria


def _build_phase_doc_rows(
    session: Dict[str, Any],
    board: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    command = str(session.get("comando", "alfred")).strip() or "alfred"
    description = " ".join((session.get("descripcion", "") or "").split()).strip() or "sin descripción"
    flow = FLOWS.get(command, {})
    current_phase = str(session.get("fase_actual", "")).strip()
    completed_entries = {
        str(phase.get("nombre", "")).strip(): phase
        for phase in (session.get("fases_completadas") or [])
        if isinstance(phase, dict) and str(phase.get("nombre", "")).strip()
    }
    tasks_by_id = _kanban_tasks_by_id(board)
    stored_ids = session.get("kanban_phase_task_ids")
    if not isinstance(stored_ids, dict):
        stored_ids = {}
    optional_flags = _session_optional_agent_flags(session)

    rows: List[Dict[str, Any]] = []
    for phase_def in flow.get("fases", []):
        phase_name = str(phase_def.get("nombre", "")).strip() or "desconocida"
        phase_result = completed_entries.get(phase_name)
        if phase_result is not None:
            status = str(phase_result.get("resultado", "aprobado")).strip() or "aprobado"
        elif current_phase == phase_name:
            status = "en curso"
        else:
            status = "pendiente"

        phase_task = tasks_by_id.get(str(stored_ids.get(phase_name, "")).strip())
        if phase_task is None:
            title = _phase_task_title(command, phase_name, description)
            match = _find_kanban_task_in_statuses(
                board,
                [title],
                ("in-progress", "backlog", "blocked", "done"),
            )
            if match is not None:
                _, _, phase_task = match

        criteria = phase_task.get("criteria") if isinstance(phase_task, dict) else []
        if not isinstance(criteria, list):
            criteria = []
        criteria = [str(item).strip() for item in criteria if str(item).strip()]
        criteria_hints = _phase_fallback_visible_criteria(phase_def) if not criteria else []
        evidence = ""
        if isinstance(phase_task, dict):
            evidence = " ".join((phase_task.get("evidence", "") or "").split()).strip()
        artifacts = []
        if isinstance(phase_result, dict):
            artifacts = _dedupe_artifact_paths(list(phase_result.get("artefactos") or []))
        effective_optionals = get_effective_agents(phase_name, optional_flags)
        parallel_optionals = order_optional_agent_names(
            list(effective_optionals.get("paralelo") or [])
        )
        sequential_optionals = order_optional_agent_names(
            list(effective_optionals.get("secuencial") or [])
        )

        rows.append({
            "name": phase_name,
            "status": status,
            "gate": str(phase_def.get("gate_tipo", "sin gate")).strip() or "sin gate",
            "agents": list(phase_def.get("agentes") or []),
            "parallel_optionals": parallel_optionals,
            "sequential_optionals": sequential_optionals,
            "iterations": int(phase_result.get("iteraciones", 0)) if isinstance(phase_result, dict) else 0,
            "criteria": criteria,
            "criteria_hints": criteria_hints,
            "evidence": evidence,
            "artifacts": artifacts,
        })

    return rows


def _get_verify_task(
    session: Dict[str, Any],
    board: Dict[str, List[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    task_id = str(session.get("kanban_verify_task_id", "")).strip()
    if not task_id:
        return None
    return _kanban_tasks_by_id(board).get(task_id)


def _session_next_command(session: Dict[str, Any], uat: Optional[Dict[str, Any]]) -> str:
    phase = str(session.get("fase_actual", "")).strip()
    if phase != "completado":
        return "/alfred-dev:resume"

    uat_status = str((uat or {}).get("status", "")).strip()
    if uat_status == "approved":
        return "/alfred"

    next_after_completion = str(session.get("next_after_completion", "")).strip()
    if next_after_completion:
        return next_after_completion
    return "/alfred-dev:verify"


def _session_status_label(session: Dict[str, Any], uat: Optional[Dict[str, Any]]) -> str:
    phase = str(session.get("fase_actual", "")).strip()
    if phase == "completado":
        uat_status = str((uat or {}).get("status", "")).strip()
        if uat_status == "approved":
            return "completado y verificado"
        if uat_status == "rejected":
            return "completado con UAT rechazada"
        return "completado pendiente de UAT"
    if is_session_paused(session):
        return "pausado"
    return "activo"


def render_session_current_markdown(
    session: Dict[str, Any],
    *,
    uat: Optional[Dict[str, Any]] = None,
    board: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> str:
    command = str(session.get("comando", "alfred")).strip() or "alfred"
    description = " ".join((session.get("descripcion", "") or "").split()).strip() or "sin descripción"
    phase = str(session.get("fase_actual", "desconocida")).strip() or "desconocida"
    completed = [
        str(phase_entry.get("nombre", "")).strip()
        for phase_entry in (session.get("fases_completadas") or [])
        if isinstance(phase_entry, dict) and str(phase_entry.get("nombre", "")).strip()
    ]
    latest_completed = completed[-1] if completed else ""
    next_command = _session_next_command(session, uat)
    phase_rows = _build_phase_doc_rows(session, board or {})
    current_row = next((row for row in phase_rows if row["name"] == phase), None)
    team_source = _session_team_source_label(session)
    on_demand_optionals = _session_on_demand_optionals_for_flow(session)

    lines = [
        "# Current",
        "",
        f"- Flujo: `{command}`.",
        f"- Objetivo actual: {description}.",
        f"- Estado: {_session_status_label(session, uat)}.",
    ]
    if team_source:
        lines.append(f"- Origen del equipo runtime: {team_source}.")
    if phase != "completado":
        lines.append(f"- Fase actual: `{phase}`.")
        if current_row:
            lines.append(f"- Gate pendiente: `{current_row['gate']}`.")
            if current_row["agents"]:
                lines.append(
                    "- Equipo base en esta fase: "
                    + ", ".join(f"`{agent}`" for agent in current_row["agents"])
                    + "."
                )
            optional_summary = _format_optional_agent_summary(
                current_row.get("parallel_optionals", []),
                current_row.get("sequential_optionals", []),
            )
            if optional_summary:
                lines.append(f"- Especialistas opcionales activos: {optional_summary}.")
    else:
        lines.append("- Estado final registrado: `completado`.")
    if on_demand_optionals:
        lines.append(
            "- Opcionales activos solo bajo demanda en este flujo: "
            + ", ".join(f"`{agent}`" for agent in on_demand_optionals)
            + "."
        )
    if latest_completed:
        lines.append(f"- Última fase cerrada: `{latest_completed}`.")
    if uat:
        lines.append(f"- UAT: {_status_label(str(uat.get('status', '')).strip())}.")
    lines.append(f"- Siguiente comando recomendado: {next_command}")
    return "\n".join(lines) + "\n"


def render_session_progress_markdown(
    session: Dict[str, Any],
    *,
    board: Dict[str, List[Dict[str, Any]]],
    uat: Optional[Dict[str, Any]] = None,
) -> str:
    command = str(session.get("comando", "alfred")).strip() or "alfred"
    description = " ".join((session.get("descripcion", "") or "").split()).strip() or "sin descripción"
    phase = str(session.get("fase_actual", "desconocida")).strip() or "desconocida"
    flow = FLOWS.get(command, {})
    total_phases = len(flow.get("fases", []))
    completed_entries = [
        phase_entry
        for phase_entry in (session.get("fases_completadas") or [])
        if isinstance(phase_entry, dict)
    ]
    completed_names = [
        str(phase_entry.get("nombre", "")).strip()
        for phase_entry in completed_entries
        if str(phase_entry.get("nombre", "")).strip()
    ]
    visible_board = _filter_kanban_board_tasks(board, _is_visible_kanban_task)
    backlog_total = len(visible_board.get("backlog", []))
    in_progress_total = len(visible_board.get("in-progress", []))
    done_total = len(visible_board.get("done", []))
    blocked_total = len(visible_board.get("blocked", []))
    total_visible = backlog_total + in_progress_total + done_total + blocked_total
    progress_pct = round((done_total / total_visible) * 100) if total_visible else 0
    artifacts = _dedupe_artifact_paths(list(session.get("artefactos") or []))
    phase_rows = _build_phase_doc_rows(session, board)
    team_source = _session_team_source_label(session)
    on_demand_optionals = _session_on_demand_optionals_for_flow(session)

    lines = [
        "# Progress",
        "",
        f"- Flujo operativo: `{command}`.",
        f"- Trabajo en curso: {description}.",
        f"- Estado del flujo: {_session_status_label(session, uat)}.",
        f"- Fases completadas: {len(completed_names)}/{total_phases}.",
    ]
    if team_source:
        lines.append(f"- Origen del equipo runtime: {team_source}.")
    if phase != "completado":
        lines.append(f"- Fase actual: `{phase}`.")
    if completed_names:
        lines.append("- Fases cerradas: " + ", ".join(f"`{name}`" for name in completed_names) + ".")
    if on_demand_optionals:
        lines.append(
            "- Opcionales activos solo bajo demanda en este flujo: "
            + ", ".join(f"`{agent}`" for agent in on_demand_optionals)
            + "."
        )
    lines.append(
        f"- Kanban visible: {done_total} done, {in_progress_total} in progress, "
        f"{backlog_total} backlog, {blocked_total} blocked."
    )
    lines.append(f"- Progreso visible estimado: {progress_pct} %.")
    lines.append(f"- Artefactos acumulados: {len(artifacts)}.")
    if uat:
        lines.append(f"- Verificación/UAT: {_status_label(str(uat.get('status', '')).strip())}.")

    if phase_rows:
        lines.extend(["", "## Fases del flujo", ""])
        for row in phase_rows:
            summary = f"- `{row['name']}` -> `{row['status']}` · gate `{row['gate']}`"
            if row["iterations"] > 0:
                summary += f" · iteraciones {row['iterations']}"
            if row["artifacts"]:
                summary += f" · artefactos {len(row['artifacts'])}"
            optional_summary = _format_optional_agent_summary(
                row.get("parallel_optionals", []),
                row.get("sequential_optionals", []),
            )
            if optional_summary:
                summary += f" · opcionales {optional_summary}"
            lines.append(summary)
    return "\n".join(lines) + "\n"


def render_session_traceability_markdown(
    session: Dict[str, Any],
    *,
    uat: Optional[Dict[str, Any]] = None,
    board: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> str:
    command = str(session.get("comando", "alfred")).strip() or "alfred"
    description = " ".join((session.get("descripcion", "") or "").split()).strip() or "sin descripción"
    phase = str(session.get("fase_actual", "desconocida")).strip() or "desconocida"
    completed_entries = [
        phase_entry
        for phase_entry in (session.get("fases_completadas") or [])
        if isinstance(phase_entry, dict)
    ]
    artifacts = _dedupe_artifact_paths(list(session.get("artefactos") or []))
    phase_rows = _build_phase_doc_rows(session, board or {})
    verify_task = _get_verify_task(session, board or {})
    team_source = _session_team_source_label(session)
    on_demand_optionals = _session_on_demand_optionals_for_flow(session)

    if phase == "completado":
        uat_status = str((uat or {}).get("status", "")).strip()
        if uat_status == "approved":
            main_risk = "Sin bloqueo principal: el flujo ya quedó verificado."
        elif uat_status == "rejected":
            main_risk = "UAT rechazada: hace falta retrabajo antes de darlo por bueno."
        else:
            main_risk = "Falta cerrar la verificación manual/UAT del flujo completado."
        pending_gate = "sin gate pendiente"
    else:
        pending_gate = get_pending_gate(session)
        main_risk = f"Aún falta superar la gate `{pending_gate}` en la fase `{phase}`."

    lines = [
        "# Traceability",
        "",
        f"- Flujo: `{command}`.",
        f"- Objetivo trazado: {description}.",
        *( [f"- Origen del equipo runtime: {team_source}."] if team_source else [] ),
        f"- Gate pendiente: {pending_gate}.",
        *(
            [
                "- Opcionales activos solo bajo demanda en este flujo: "
                + ", ".join(f"`{agent}`" for agent in on_demand_optionals)
                + "."
            ]
            if on_demand_optionals
            else []
        ),
        (
            f"- UAT actual: {_status_label(str(uat.get('status', '')).strip())}."
            if uat
            else "- UAT actual: pendiente."
        ),
        f"- Riesgo principal: {main_risk}",
        "",
        "## Fases registradas",
        "",
    ]

    if completed_entries:
        for phase_entry in completed_entries:
            phase_name = str(phase_entry.get("nombre", "")).strip() or "desconocida"
            result = str(phase_entry.get("resultado", "")).strip() or "aprobado"
            phase_artifacts = _dedupe_artifact_paths(list(phase_entry.get("artefactos") or []))
            summary = f"- `{phase_name}` -> `{result}`"
            if phase_artifacts:
                summary += f" · artefactos: {', '.join(f'`{item}`' for item in phase_artifacts[:3])}"
            lines.append(summary)
    else:
        lines.append("- Todavía no hay fases completadas registradas.")

    lines.extend(["", "## Criterios y evidencia por fase", ""])
    if phase_rows:
        for row in phase_rows:
            lines.append(f"### `{row['name']}`")
            lines.append(f"- Gate: `{row['gate']}`.")
            lines.append(f"- Estado: `{row['status']}`.")
            if row["agents"]:
                lines.append(
                    "- Equipo base: "
                    + ", ".join(f"`{agent}`" for agent in row["agents"])
                    + "."
                )
            if row.get("parallel_optionals"):
                lines.append(
                    "- Opcionales en paralelo: "
                    + ", ".join(f"`{agent}`" for agent in row["parallel_optionals"])
                    + "."
                )
            if row.get("sequential_optionals"):
                lines.append(
                    "- Opcionales secuenciales: "
                    + ", ".join(f"`{agent}`" for agent in row["sequential_optionals"])
                    + "."
                )
            if row["criteria"]:
                lines.append("- Criterios visibles: " + ", ".join(f"`{item}`" for item in row["criteria"]) + ".")
            elif row["criteria_hints"]:
                lines.append("- Criterios visibles: " + "; ".join(row["criteria_hints"]) + ".")
            else:
                lines.append("- Criterios visibles: sin criterios explícitos todavía.")
            if row["evidence"]:
                lines.append(f"- Evidencia: {row['evidence']}.")
            else:
                lines.append("- Evidencia: sin evidencia explícita todavía.")
            if row["artifacts"]:
                lines.append(
                    "- Artefactos de fase: "
                    + ", ".join(f"`{item}`" for item in row["artifacts"])
                    + "."
                )
            else:
                lines.append("- Artefactos de fase: sin artefactos explícitos.")
            lines.append("")
    else:
        lines.append("- Todavía no hay filas de fase para trazar.")
        lines.append("")

    lines.extend(["## Verificación manual", ""])
    if verify_task:
        verify_status = str(verify_task.get("status", "backlog")).strip() or "backlog"
        verify_evidence = " ".join((verify_task.get("evidence", "") or "").split()).strip()
        verify_criteria = verify_task.get("criteria") if isinstance(verify_task.get("criteria"), list) else []
        lines.append(f"- Estado de verify: `{verify_status}`.")
        if verify_criteria:
            lines.append("- Criterios visibles: " + ", ".join(f"`{item}`" for item in verify_criteria) + ".")
        else:
            lines.append("- Criterios visibles: sin criterios explícitos todavía.")
        if verify_evidence:
            lines.append(f"- Evidencia: {verify_evidence}.")
        else:
            lines.append("- Evidencia: sin evidencia explícita todavía.")
    elif uat:
        uat_status = str(uat.get("status", "")).strip()
        verify_status = "done" if uat_status == "approved" else "blocked" if uat_status == "rejected" else "backlog"
        lines.append(f"- Estado de verify: `{verify_status}`.")
        lines.append(f"- Criterios visibles: status UAT `{uat_status or 'pending'}`.")
        notes = " ".join((uat.get("notes", "") or "").split()).strip()
        updated_at = str(uat.get("updated_at", "")).strip()
        evidence = []
        if updated_at:
            evidence.append(f"UAT registrada en {updated_at}")
        if notes:
            evidence.append(notes)
        if evidence:
            lines.append(f"- Evidencia: {' — '.join(evidence)}.")
        else:
            lines.append("- Evidencia: UAT registrada sin notas adicionales.")
    else:
        lines.append("- No hay tarea de verify sincronizada todavía.")

    lines.extend(["", "## Artefactos registrados", ""])
    if artifacts:
        lines.extend(f"- `{item}`" for item in artifacts)
    else:
        lines.append("- Todavía no hay artefactos registrados.")

    return "\n".join(lines) + "\n"


def sync_session_state_to_operational_docs(
    project_dir: str,
    session: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(session, dict):
        return session
    if not session.get("comando") or not session.get("descripcion"):
        return session

    synced = _enrich_session_style_visual(project_dir, dict(session))
    uat = _load_matching_session_uat(project_dir, synced)
    board = load_kanban_board(project_dir)
    os.makedirs(_project_path(project_dir, os.path.join("docs", "project")), exist_ok=True)

    current_path = _project_path(project_dir, CURRENT_RELATIVE_PATH)
    progress_path = _project_path(project_dir, PROGRESS_MD_RELATIVE_PATH)
    traceability_path = _project_path(project_dir, TRACEABILITY_MD_RELATIVE_PATH)
    synced["artefactos"] = _dedupe_artifact_paths(
        list(synced.get("artefactos") or [])
        + (
            [UAT_MD_RELATIVE_PATH, UAT_JSON_RELATIVE_PATH]
            if isinstance(uat, dict)
            else []
        )
        + [CURRENT_RELATIVE_PATH, PROGRESS_MD_RELATIVE_PATH, TRACEABILITY_MD_RELATIVE_PATH]
    )

    with open(current_path, "w", encoding="utf-8") as fh:
        fh.write(render_session_current_markdown(synced, uat=uat, board=board))
    with open(progress_path, "w", encoding="utf-8") as fh:
        fh.write(render_session_progress_markdown(synced, board=board, uat=uat))
    with open(traceability_path, "w", encoding="utf-8") as fh:
        fh.write(render_session_traceability_markdown(synced, uat=uat, board=board))

    return synced


def _summarize_tasks(
    tasks: List[Dict[str, Any]],
    limit: int = 3,
    *,
    newest_first: bool = False,
) -> List[str]:
    lines: List[str] = []
    ordered_tasks = sorted(tasks, key=_task_sort_key)
    if newest_first:
        ordered_tasks = list(reversed(ordered_tasks))

    for task in ordered_tasks[:limit]:
        suffix: List[str] = []
        if task.get("agent"):
            suffix.append(task["agent"])
        if task.get("dependencies"):
            suffix.append(f"dep: {task['dependencies']}")
        if task.get("notes"):
            suffix.append(task["notes"])
        extra = f" — {'; '.join(suffix)}" if suffix else ""
        lines.append(f"{_task_reference(task)}{extra}")
    return lines


def _task_is_skipped_phase(task: Dict[str, Any]) -> bool:
    body = _normalize_free_text(task.get("body", ""))
    notes = _normalize_free_text(task.get("notes", ""))
    return (
        "estado de fase: saltada" in body
        or "fase saltada por condicion del flujo" in notes
    )


def _filter_kanban_board_tasks(
    board: Dict[str, List[Dict[str, Any]]],
    predicate: Any,
) -> Dict[str, List[Dict[str, Any]]]:
    return {
        status: [task for task in board.get(status, []) if predicate(task)]
        for status in _KANBAN_RELATIVE_BY_STATUS
    }


def _count_kanban_task_types(board: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    counts = {task_type: 0 for task_type in _KNOWN_KANBAN_TASK_TYPES}
    for lane_tasks in board.values():
        for task in lane_tasks:
            counts[_effective_task_type(task)] += 1
    counts["internal"] = counts["phase"] + counts["verify"]
    counts["visible"] = counts["generic"] + counts["main"]
    counts["total"] = counts["internal"] + counts["visible"]
    return counts


def _build_progress_overview_cards(
    state: Optional[Dict[str, Any]],
    handoff: Optional[Dict[str, Any]],
    uat: Optional[Dict[str, Any]],
    next_action: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Construye tarjetas compactas y estables para overview/UI."""
    cards: List[Dict[str, Any]] = []
    has_active_state = bool(
        state and state.get("fase_actual") != "completado" and not is_session_paused(state)
    )
    has_paused_state = bool(
        state and state.get("fase_actual") != "completado" and is_session_paused(state)
    )
    has_handoff = bool(handoff and not handoff.get("resolved", False))

    if has_active_state:
        cards.append(
            {
                "label": "Flujo activo",
                "title": (
                    f"{state.get('comando', 'desconocido')} — "
                    f"{state.get('descripcion', 'sin descripción')}"
                ),
                "body": f"Fase actual: {state.get('fase_actual', 'desconocida')}",
                "chips": [state.get("fase_actual", "desconocida")],
            }
        )
    elif has_handoff:
        cards.append(
            {
                "label": "Handoff pendiente",
                "title": handoff.get("command", "desconocido"),
                "body": (
                    f"Fase: {handoff.get('phase', 'desconocida')} · "
                    f"Reanudar con {handoff.get('resume_command', '/alfred-dev:resume')}"
                ),
                "chips": ["pending"],
            }
        )
    elif has_paused_state:
        cards.append(
            {
                "label": "Sesión pausada",
                "title": (
                    f"{state.get('comando', 'desconocido')} — "
                    f"{state.get('descripcion', 'sin descripción')}"
                ),
                "body": f"Fase pausada: {state.get('fase_actual', 'desconocida')}",
                "chips": ["paused"],
            }
        )
    elif state and state.get("fase_actual") == "completado":
        cards.append(
            {
                "label": "Último flujo completado",
                "title": (
                    f"{state.get('comando', 'desconocido')} — "
                    f"{state.get('descripcion', 'sin descripción')}"
                ),
                "body": (
                    f"Estado final: completado"
                    + (
                        f" · UAT {_status_label(uat.get('status', ''))}"
                        if uat
                        else " · UAT pendiente"
                    )
                ),
                "chips": ["completado"],
            }
        )

    if uat:
        target_label = uat.get("target_description") or uat.get("target_command") or uat.get("target_id") or "sin objetivo"
        cards.append(
            {
                "label": "UAT",
                "title": target_label,
                "body": (
                    f"Estado actual: {_status_label(uat.get('status', ''))}"
                    + (
                        f" · Actualizada en {uat.get('updated_at')}"
                        if uat.get("updated_at")
                        else ""
                    )
                ),
                "chips": [uat.get("status", "pending")],
            }
        )

    cards.append(
        {
            "label": "Siguiente paso recomendado",
            "title": f"/alfred-dev:{next_action.get('command', 'alfred')}",
            "body": next_action.get(
                "directive",
                next_action.get("reason", "Sin razón disponible."),
            ),
            "chips": [next_action.get("source", "")] if next_action.get("source") else [],
        }
    )
    return cards


def _build_project_signal_cards(
    state: Optional[Dict[str, Any]],
    current_signals: List[str],
    progress_signals: List[str],
    traceability_signals: List[str],
    kanban: Dict[str, Any],
    overview_cards: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    overview_labels = {card.get("label", "") for card in (overview_cards or [])}
    filtered_current_signals = list(current_signals)
    filtered_progress_signals = list(progress_signals)
    filtered_traceability_signals = list(traceability_signals)

    if overview_labels & {
        "Flujo activo",
        "Handoff pendiente",
        "Sesión pausada",
        "Último flujo completado",
    }:
        filtered_current_signals = [
            item
            for item in filtered_current_signals
            if not item.startswith(
                (
                    "Flujo activo:",
                    "Flujo:",
                    "Handoff pendiente",
                    "Sesión pausada:",
                    "Objetivo actual:",
                    "Estado:",
                    "Estado final registrado:",
                    "Última fase cerrada:",
                    "Fase actual:",
                )
            )
        ]
        filtered_progress_signals = [
            item
            for item in filtered_progress_signals
            if not item.startswith(
                (
                    "Flujo operativo:",
                    "Trabajo en curso:",
                    "Estado del flujo:",
                )
            )
        ]
        filtered_traceability_signals = [
            item
            for item in filtered_traceability_signals
            if not item.startswith(
                (
                    "Flujo:",
                    "Objetivo trazado:",
                )
            )
        ]

    if "Siguiente paso recomendado" in overview_labels:
        filtered_current_signals = [
            item
            for item in filtered_current_signals
            if not item.startswith("Siguiente paso sugerido:")
        ]

    if "UAT" in overview_labels:
        filtered_traceability_signals = [
            item
            for item in filtered_traceability_signals
            if not item.startswith("UAT actual:")
        ]

    cards: List[Dict[str, Any]] = []
    team_items: List[str] = []
    if state:
        team_source = _session_team_source_label(state)
        if team_source:
            team_items.append(f"Origen runtime: {team_source}.")
        on_demand_optionals = _session_on_demand_optionals_for_flow(state)
        if on_demand_optionals:
            team_items.append(
                "Opcionales solo bajo demanda en este flujo: "
                + ", ".join(f"`{agent}`" for agent in on_demand_optionals)
                + "."
            )

    if team_items:
        cards.append(
            {
                "title": "Equipo runtime",
                "subtitle": "Cómo se compuso el equipo real de esta sesión y qué queda fuera del loop estándar.",
                "items": team_items,
            }
        )

    for title, items, subtitle in [
        ("Current", filtered_current_signals, "Lo último que Alfred ha dejado listo para seguir."),
        ("Bloqueos", kanban.get("blocked", []), "Lo que ahora mismo impide avanzar o cerrar trabajo."),
        ("En curso", kanban.get("in_progress", []), "Trabajo en marcha ahora mismo."),
        (
            "Trazabilidad",
            filtered_traceability_signals,
            "Huecos o señales de criterios y cobertura.",
        ),
        ("Progreso", filtered_progress_signals, "Señales humanas del avance del proyecto."),
        ("Backlog", kanban.get("backlog", []), "Pendiente por atacar."),
    ]:
        if not items:
            continue
        cards.append(
            {
                "title": title,
                "subtitle": subtitle,
                "items": list(items),
            }
        )
    return cards


def build_standup_snapshot(project_dir: str) -> Dict[str, Any]:
    snapshot = build_progress_snapshot(project_dir)
    board = _filter_kanban_board_tasks(load_kanban_board(project_dir), _is_visible_kanban_task)
    snapshot["standup_date"] = _now_utc().date().isoformat()
    snapshot["board_tasks"] = board
    snapshot["focus"] = {
        "in_progress": _summarize_tasks(board.get("in-progress", [])),
        "blocked": _summarize_tasks(board.get("blocked", [])),
        "done": _summarize_tasks(board.get("done", []), newest_first=True),
    }
    return snapshot


def render_standup_markdown(snapshot: Dict[str, Any]) -> str:
    next_action = snapshot.get("next_action", {"command": "alfred", "reason": ""})
    focus = snapshot.get("focus", {})
    kanban = snapshot.get("kanban", {})
    lines = [
        f"## Standup diario — {snapshot.get('standup_date', _now_utc().date().isoformat())}",
        "",
        f"- Done: {len(kanban.get('done', []))}",
        f"- In progress: {len(kanban.get('in_progress', []))}",
        f"- Backlog: {len(kanban.get('backlog', []))}",
        f"- Blocked: {len(kanban.get('blocked', []))}",
    ]
    if kanban.get("internal_total"):
        lines.append(
            f"- Internas: {kanban['internal_total']} "
            f"(fase: {kanban.get('phase_total', 0)}, verify: {kanban.get('verify_total', 0)})"
        )
    if kanban.get("progress_pct") is not None:
        lines.append(f"- Progreso estimado: {kanban['progress_pct']} %")

    if focus.get("in_progress"):
        lines.extend(["", "### En curso", ""])
        lines.extend(f"- {item}" for item in focus["in_progress"])

    if focus.get("blocked"):
        lines.extend(["", "### Bloqueos", ""])
        lines.extend(f"- {item}" for item in focus["blocked"])

    if focus.get("done"):
        lines.extend(["", "### Últimos completados", ""])
        lines.extend(f"- {item}" for item in focus["done"])

    progress_signals = snapshot.get("progress_signals") or snapshot.get("current_signals") or []
    if progress_signals:
        lines.extend(["", "### Señales", ""])
        lines.extend(f"- {item}" for item in progress_signals[:3])

    _extend_next_action_section(lines, next_action, heading="### Siguiente paso")
    return "\n".join(lines).strip() + "\n"


def build_lane_snapshot(project_dir: str, lane: str) -> Dict[str, Any]:
    board = load_kanban_board(project_dir)
    tasks = board.get(lane, [])
    next_action = suggest_next_action(project_dir)
    return {
        "lane": lane,
        "tasks": sorted(tasks, key=_task_sort_key),
        "next_action": next_action,
        "count": len(tasks),
    }


def render_lane_markdown(snapshot: Dict[str, Any]) -> str:
    lane = snapshot.get("lane", "desconocido")
    label = _KANBAN_STATUS_LABELS.get(lane, lane)
    tasks = snapshot.get("tasks", [])
    next_action = snapshot.get("next_action", {"command": "alfred", "reason": ""})
    lines = [f"## Tareas en {label}", ""]
    if not tasks:
        lines.append("No hay tareas en esta columna.")
    else:
        for task in tasks:
            lines.append(f"### {_task_reference(task)}")
            lines.append("")
            lines.append(f"- Estado: {label}")
            if task.get("agent"):
                lines.append(f"- Agente: {task['agent']}")
            if task.get("criteria"):
                lines.append(f"- Criterios: {', '.join(task['criteria'])}")
            if task.get("dependencies"):
                lines.append(f"- Dependencias: {task['dependencies']}")
            if task.get("notes"):
                lines.append(f"- Notas: {task['notes']}")
            if task.get("evidence"):
                lines.append(f"- Evidencia: {task['evidence']}")
            lines.append(f"- Fuente: `{task.get('path', '-')}`")
            lines.append("")
    _extend_next_action_section(lines, next_action)
    return "\n".join(lines).strip() + "\n"


def validate_operational_artifacts(project_dir: str) -> Dict[str, Any]:
    board = load_kanban_board(project_dir)
    tasks = [task for lane in board.values() for task in lane]
    visible_tasks = [task for task in tasks if _is_visible_kanban_task(task)]
    syncable_tasks = [task for task in tasks if _is_syncable_kanban_task(task)]
    internal_count = len(tasks) - len(visible_tasks)
    errors: List[str] = []
    warnings: List[str] = []
    checks: List[str] = []

    if not tasks:
        warnings.append("No hay tareas detectadas en docs/project/kanban/.")
    else:
        checks.append(f"Se han detectado {len(visible_tasks)} tareas visibles en el kanban.")
        if internal_count:
            checks.append(
                f"Hay {internal_count} tareas internas de coordinación (phase/verify)."
            )

    seen_ids: Dict[str, str] = {}
    missing_ids = 0
    for task in tasks:
        task_id = (task.get("id") or "").strip()
        if not task_id:
            missing_ids += 1
        elif task_id in seen_ids:
            errors.append(
                f"La tarea {task_id} aparece duplicada en '{seen_ids[task_id]}' y '{task['status']}'."
            )
        else:
            seen_ids[task_id] = task["status"]

        if (
            _is_visible_kanban_task(task)
            and task["status"] in {"in-progress", "blocked"}
            and not task.get("agent")
        ):
            warnings.append(f"{_task_reference(task)} no tiene agente responsable visible.")
        if (
            _is_visible_kanban_task(task)
            and task["status"] == "blocked"
            and not (task.get("dependencies") or task.get("notes"))
        ):
            warnings.append(
                f"{_task_reference(task)} está bloqueada, pero no indica dependencia ni motivo."
            )
        if (
            _is_visible_kanban_task(task)
            and task["status"] == "done"
            and not task.get("evidence")
            and not _task_is_skipped_phase(task)
        ):
            warnings.append(f"{_task_reference(task)} está en done sin evidencia explícita.")

    if missing_ids:
        warnings.append(
            f"Hay {missing_ids} tareas sin identificador [T-XXX]; el sync con GitHub será parcial."
        )

    traceability_md = _read_text_if_exists(project_dir, TRACEABILITY_MD_RELATIVE_PATH)
    progress_md = _read_text_if_exists(project_dir, PROGRESS_MD_RELATIVE_PATH)
    if traceability_md:
        checks.append("Existe docs/project/traceability.md.")
    else:
        warnings.append("Falta docs/project/traceability.md.")
    if progress_md:
        checks.append("Existe docs/project/progress.md.")
    else:
        warnings.append("Falta docs/project/progress.md.")

    traced_criteria = set(_extract_criteria_ids(traceability_md))
    referenced_criteria = {
        criterion
        for task in visible_tasks
        for criterion in (task.get("criteria") or [])
    }
    missing_traceability = sorted(referenced_criteria - traced_criteria)
    if missing_traceability:
        warnings.append(
            "Hay criterios referenciados en tareas que no aparecen en la trazabilidad: "
            + ", ".join(missing_traceability)
        )
    elif referenced_criteria:
        checks.append("Los criterios visibles en tareas también aparecen en la trazabilidad.")

    verify_suggestion = suggest_verify_action(project_dir)
    uat = load_uat(project_dir)
    if verify_suggestion is not None:
        if uat:
            warnings.append(
                "Existe UAT registrada, pero no cubre el último flujo completado o sigue pendiente de cierre."
            )
        else:
            warnings.append("La verificación/UAT del último flujo completado sigue pendiente.")
    elif uat:
        checks.append(f"Existe UAT en estado '{_status_label(uat.get('status', ''))}'.")

    state = _load_active_session_state(project_dir) or load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    if isinstance(state, dict):
        style_phase = _completed_style_visual_phase(state)
        if style_phase is not None:
            if os.path.isfile(_project_path(project_dir, STYLE_DIRECTION_RELATIVE_PATH)):
                checks.append("Existe docs/style-direction.md para la fase estilo_visual.")
            else:
                warnings.append(
                    "La fase estilo_visual figura como completada, pero falta docs/style-direction.md."
                )

    sync_state = _read_json_file(_project_path(project_dir, GITHUB_SYNC_JSON_RELATIVE_PATH))
    if isinstance(sync_state, dict):
        task_map = sync_state.get("tasks")
        mapped = task_map if isinstance(task_map, dict) else {}
        syncable_ids = {
            task.get("id")
            for task in syncable_tasks
            if task.get("id")
        }
        sync_missing = [
            task.get("id")
            for task in syncable_tasks
            if task.get("id") and task.get("id") not in mapped
        ]
        if sync_missing:
            warnings.append(
                "Hay tareas no sincronizadas con GitHub: " + ", ".join(sync_missing[:5])
            )
        else:
            checks.append("El mapa de sincronización con GitHub cubre todas las tareas con ID.")
        stale_sync = sorted(
            task_id
            for task_id in mapped
            if task_id not in syncable_ids
        )
        if stale_sync:
            warnings.append(
                "El mapa de GitHub conserva tareas que ya no existen en el kanban local: "
                + ", ".join(stale_sync[:5])
            )

    status = "ok"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "next_action": suggest_next_action(project_dir),
    }


def render_validation_markdown(report: Dict[str, Any]) -> str:
    status = report.get("status", "desconocido")
    verdict = {
        "ok": "APROBADO",
        "warning": "APROBADO CON AVISOS",
        "error": "RECHAZADO",
    }.get(status, status.upper())
    next_action = report.get("next_action", {"command": "alfred", "reason": ""})
    lines = [
        f"## Validación operativa — {verdict}",
        "",
        "### Resumen",
        "",
        f"- Checks en verde: {len(report.get('checks') or [])}",
        f"- Avisos: {len(report.get('warnings') or [])}",
        f"- Errores: {len(report.get('errors') or [])}",
    ]

    if report.get("checks"):
        lines.extend(["", "### Checks", ""])
        lines.extend(f"- {item}" for item in report["checks"])

    if report.get("warnings"):
        lines.extend(["", "### Avisos", ""])
        lines.extend(f"- {item}" for item in report["warnings"])

    if report.get("errors"):
        lines.extend(["", "### Errores", ""])
        lines.extend(f"- {item}" for item in report["errors"])

    _extend_next_action_section(lines, next_action)
    return "\n".join(lines).strip() + "\n"


def render_normalize_kanban_markdown(result: Dict[str, Any]) -> str:
    lines = [
        "## Normalización de kanban",
        "",
        f"- Tareas ajustadas: {result.get('count', 0)}",
    ]
    changed = result.get("changed", [])
    if changed:
        lines.extend(["", "### Tipos asignados", ""])
        for item in changed:
            task_id = item.get("id") or "sin-id"
            title = item.get("title") or "sin título"
            task_type = item.get("task_type") or "generic"
            status = item.get("status") or "desconocido"
            lines.append(f"- [{task_id}] {title} -> `{task_type}` ({status})")
    else:
        lines.append("- El tablero ya estaba normalizado.")
    return "\n".join(lines).strip() + "\n"


def search_project_context(project_dir: str, query: str, limit: int = 10) -> Dict[str, Any]:
    if not (query or "").strip():
        raise RuntimeError("Debes indicar un término de búsqueda para /alfred-dev:search.")

    normalized_query = _normalize_free_text(query)
    doc_results: List[Dict[str, Any]] = []
    doc_paths = [
        CODEBASE_MAP_RELATIVE_PATH,
        CURRENT_RELATIVE_PATH,
        DISCOVERY_MD_RELATIVE_PATH,
        PROGRESS_MD_RELATIVE_PATH,
        TRACEABILITY_MD_RELATIVE_PATH,
        UAT_MD_RELATIVE_PATH,
        GITHUB_SYNC_MD_RELATIVE_PATH,
        KANBAN_BACKLOG_RELATIVE_PATH,
        KANBAN_IN_PROGRESS_RELATIVE_PATH,
        KANBAN_DONE_RELATIVE_PATH,
        KANBAN_BLOCKED_RELATIVE_PATH,
    ]
    for relative_path in doc_paths:
        markdown = _read_text_if_exists(project_dir, relative_path)
        if not markdown:
            continue
        for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            if normalized_query not in _normalize_free_text(stripped):
                continue
            doc_results.append(
                {
                    "path": relative_path,
                    "line": line_number,
                    "snippet": stripped,
                }
            )
            if len(doc_results) >= limit:
                break
        if len(doc_results) >= limit:
            break

    memory_results: List[Dict[str, Any]] = []
    db_path = _project_path(project_dir, os.path.join(".claude", "alfred-memory.db"))
    if os.path.isfile(db_path):
        try:
            from core.memory import MemoryDB

            db = MemoryDB(db_path)
            try:
                for item in db.search(query, limit=limit):
                    source_type = item.get("source_type", "unknown")
                    if source_type == "decision":
                        label = f"[D#{item.get('id')}] {item.get('title', 'sin título')}"
                    elif source_type == "commit":
                        sha = str(item.get("sha", ""))[:8]
                        label = f"[commit {sha}] {item.get('message', 'sin mensaje')}"
                    else:
                        label = (
                            f"[evento #{item.get('id')}] "
                            f"{item.get('summary') or item.get('event_type') or 'sin resumen'}"
                        )
                    memory_results.append(
                        {
                            "source_type": source_type,
                            "label": label,
                        }
                    )
            finally:
                db.close()
        except Exception:
            memory_results = []

    return {
        "query": query.strip(),
        "docs": doc_results[:limit],
        "memory": memory_results[:limit],
    }


def render_search_markdown(results: Dict[str, Any]) -> str:
    query = results.get("query", "")
    doc_results = results.get("docs", [])
    memory_results = results.get("memory", [])
    lines = [f"## Resultados para `{query}`", ""]

    if doc_results:
        lines.extend(["### Artefactos del proyecto", ""])
        for item in doc_results:
            lines.append(
                f"- `{item['path']}:{item['line']}` — {item['snippet']}"
            )

    if memory_results:
        lines.extend(["", "### Memoria SQLite", ""])
        for item in memory_results:
            lines.append(f"- {item['label']}")

    if not doc_results and not memory_results:
        lines.append("No se han encontrado coincidencias en SonIA ni en la memoria del proyecto.")

    return "\n".join(lines).strip() + "\n"


def _load_memory_ui_state(project_dir: str) -> Optional[Dict[str, Any]]:
    path = _project_path(project_dir, MEMORY_UI_JSON_RELATIVE_PATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _save_memory_ui_state(project_dir: str, payload: Dict[str, Any]) -> str:
    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    path = _project_path(project_dir, MEMORY_UI_JSON_RELATIVE_PATH)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


def _clear_memory_ui_state(project_dir: str) -> None:
    for relative_path in (
        MEMORY_UI_JSON_RELATIVE_PATH,
        GUI_PORT_RELATIVE_PATH,
    ):
        try:
            os.remove(_project_path(project_dir, relative_path))
        except FileNotFoundError:
            continue
        except OSError:
            continue


def _normalize_local_path(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return os.path.normcase(os.path.realpath(os.path.abspath(raw)))


def _is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _get_process_command_line(pid: int) -> str:
    if pid <= 0:
        return ""

    try:
        if os.name == "nt":
            proc = subprocess.run(
                [
                    "wmic",
                    "process",
                    "where",
                    f"processid={pid}",
                    "get",
                    "CommandLine",
                    "/value",
                ],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
            )
            if proc.returncode != 0:
                return ""
            for line in (proc.stdout or "").splitlines():
                if line.startswith("CommandLine="):
                    return line.split("=", 1)[1].strip()
            return ""

        proc = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        if proc.returncode != 0:
            return ""
        return " ".join((proc.stdout or "").split()).strip()
    except Exception:
        return ""


def _is_expected_memory_ui_process(
    pid: int,
    *,
    url: str,
    expected_project_dir: str,
    expected_db_path: str,
) -> bool:
    if not _is_process_alive(pid):
        return False

    if url and _is_memory_ui_reachable(
        url,
        expected_project_dir=expected_project_dir,
        expected_db_path=expected_db_path,
    ):
        return True

    command_line = _get_process_command_line(pid)
    if not command_line:
        return False

    try:
        parts = shlex.split(command_line, posix=os.name != "nt")
    except ValueError:
        parts = command_line.split()

    has_server_script = any(os.path.basename(part) == "memory_ui_server.py" for part in parts)
    if not has_server_script:
        return False

    normalized_project_dir = _normalize_local_path(expected_project_dir)
    normalized_db_path = _normalize_local_path(expected_db_path)
    normalized_parts = {
        _normalize_local_path(part)
        for part in parts
        if isinstance(part, str) and part.strip()
    }

    if normalized_project_dir and normalized_project_dir not in normalized_parts:
        return False
    if normalized_db_path and normalized_db_path not in normalized_parts:
        return False
    return True


def _is_memory_ui_reachable(
    url: str,
    timeout: float = 0.35,
    expected_project_dir: Optional[str] = None,
    expected_db_path: Optional[str] = None,
) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/api/healthz", timeout=timeout) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            if not payload.get("ok"):
                return False

            if expected_project_dir is not None:
                health_project_dir = _normalize_local_path(payload.get("project_dir"))
                if health_project_dir != _normalize_local_path(expected_project_dir):
                    return False

            if expected_db_path is not None:
                health_db_path = _normalize_local_path(payload.get("db_path"))
                if health_db_path != _normalize_local_path(expected_db_path):
                    return False

            return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        return False


def _find_available_port(host: str, preferred: int = 4311) -> int:
    for port in range(preferred, preferred + 40):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _open_browser(url: str) -> None:
    if webbrowser.open(url, new=2):
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif os.name == "nt":
        os.startfile(url)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def launch_memory_ui(
    project_dir: str,
    *,
    open_browser_window: bool = True,
    host: str = "127.0.0.1",
    preferred_port: int = 4311,
    startup_timeout: float = 6.0,
) -> Dict[str, Any]:
    from core.memory import MemoryDB

    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    db_path = _project_path(project_dir, os.path.join(".claude", "alfred-memory.db"))
    db = MemoryDB(db_path)
    db.close()

    current_state = _load_memory_ui_state(project_dir)
    if current_state:
        url = str(current_state.get("url", "")).rstrip("/")
        pid = int(current_state.get("pid", 0) or 0)
        if (
            url
            and _is_process_alive(pid)
            and _is_memory_ui_reachable(
                url,
                expected_project_dir=project_dir,
                expected_db_path=db_path,
            )
        ):
            if open_browser_window:
                _open_browser(url)
            return {
                **current_state,
                "reused": True,
                "state_path": _project_path(project_dir, MEMORY_UI_JSON_RELATIVE_PATH),
                "log_path": _project_path(project_dir, GUI_LOG_RELATIVE_PATH),
            }

    port = _find_available_port(host, preferred=preferred_port)
    log_path = _project_path(project_dir, GUI_LOG_RELATIVE_PATH)
    port_path = _project_path(project_dir, GUI_PORT_RELATIVE_PATH)
    server_script = os.path.join(os.path.dirname(__file__), "memory_ui_server.py")

    with open(log_path, "a", encoding="utf-8") as log_handle:
        proc = subprocess.Popen(
            [
                sys.executable,
                server_script,
                "--project-dir",
                project_dir,
                "--db-path",
                db_path,
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=project_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    url = f"http://{host}:{port}"
    deadline = _now_utc().timestamp() + startup_timeout
    while _now_utc().timestamp() < deadline:
        if proc.poll() is not None:
            detail = _read_text_if_exists(project_dir, GUI_LOG_RELATIVE_PATH).strip()
            raise RuntimeError(detail or "La Memory UI terminó antes de quedar lista.")
        if _is_memory_ui_reachable(
            url,
            expected_project_dir=project_dir,
            expected_db_path=db_path,
        ):
            break
        import time
        time.sleep(0.15)
    else:
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except OSError:
            pass
        detail = _read_text_if_exists(project_dir, GUI_LOG_RELATIVE_PATH).strip()
        raise RuntimeError(detail or "La Memory UI no respondió dentro del tiempo esperado.")

    with open(port_path, "w", encoding="utf-8") as fh:
        fh.write(str(port))

    payload = {
        "pid": proc.pid,
        "host": host,
        "port": port,
        "url": url,
        "db_path": db_path,
        "project_dir": project_dir,
        "started_at": _now_utc().isoformat(),
        "reused": False,
    }
    state_path = _save_memory_ui_state(project_dir, payload)
    payload["state_path"] = state_path
    payload["log_path"] = log_path

    if open_browser_window:
        _open_browser(url)

    return payload


def stop_memory_ui(project_dir: str) -> Dict[str, Any]:
    state = _load_memory_ui_state(project_dir)
    if not state:
        return {"stopped": False, "reason": "not-running"}

    pid = int(state.get("pid", 0) or 0)
    url = str(state.get("url", "")).rstrip("/")
    db_path = _project_path(project_dir, os.path.join(".claude", "alfred-memory.db"))

    if not _is_expected_memory_ui_process(
        pid,
        url=url,
        expected_project_dir=project_dir,
        expected_db_path=db_path,
    ):
        _clear_memory_ui_state(project_dir)
        return {
            "stopped": False,
            "reason": "stale-state",
            "pid": pid,
            "url": state.get("url"),
        }

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    _clear_memory_ui_state(project_dir)
    return {
        "stopped": True,
        "pid": pid,
        "url": state.get("url"),
    }


def render_memory_ui_markdown(result: Dict[str, Any]) -> str:
    reused = bool(result.get("reused"))
    lines = [
        "## Memory UI lista",
        "",
        f"- URL: {result.get('url', 'desconocida')}",
        f"- SQLite: `{result.get('db_path', '.claude/alfred-memory.db')}`",
        f"- Estado: {'reutilizada' if reused else 'arrancada ahora'}",
        "- Refresco automático: cada 4 segundos",
        "- Vistas: overview, timeline, decisiones, grafo, commits y búsqueda",
        "",
        "### Qué verás",
        "",
        "- Estado operativo del proyecto y siguiente paso recomendado",
        "- Timeline de iteraciones y eventos",
        "- Decisiones con sus relaciones visibles",
        "- Commits recientes y salud de la memoria",
    ]
    return "\n".join(lines).strip() + "\n"


def _run_command(
    args: List[str],
    cwd: Optional[str] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(detail or f"El comando falló: {' '.join(args)}")
    return proc


def _run_command_json(args: List[str], cwd: Optional[str] = None) -> Any:
    proc = _run_command(args, cwd=cwd, check=True)
    output = (proc.stdout or "").strip()
    if not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Respuesta JSON inesperada de {' '.join(args)}: {exc}"
        ) from exc


def _detect_github_repo(project_dir: str, raw_request: str = "") -> str:
    candidate = (raw_request or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", candidate):
        return candidate

    proc = _run_command(
        ["git", "-C", project_dir, "remote", "get-url", "origin"],
        check=False,
    )
    remote = (proc.stdout or "").strip()
    if not remote:
        raise RuntimeError(
            "No se pudo detectar el repositorio GitHub. Añade un remoto `origin` o pasa `owner/repo`."
        )

    patterns = [
        r"github\.com[:/](?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$",
        r"^https://github\.com/(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote)
        if match:
            return match.group("repo")

    raise RuntimeError(
        f"El remoto origin no apunta a GitHub o no se pudo parsear: {remote}"
    )


def _ensure_gh_ready() -> None:
    _run_command(["gh", "--version"])
    _run_command(["gh", "auth", "status", "-h", "github.com"])


def _ensure_github_labels(repo: str) -> None:
    labels = [
        ("alfred", "0E8A16", "Artefactos y automatizaciones de Alfred Dev"),
        ("alfred:task", "1D76DB", "Tarea sincronizada desde el kanban de SonIA"),
        (_GH_SYNC_LABEL, "5319E7", "Issue paraguas de SonIA Sync"),
        ("alfred:backlog", "BFD4F2", "Tarea pendiente"),
        ("alfred:in-progress", "FBCA04", "Tarea en curso"),
        ("alfred:blocked", "D93F0B", "Tarea bloqueada"),
        ("alfred:done", "0E8A16", "Tarea completada"),
    ]
    for name, color, description in labels:
        _run_command(
            [
                "gh",
                "label",
                "create",
                name,
                "--repo",
                repo,
                "--color",
                color,
                "--description",
                description,
                "--force",
            ]
        )


def _get_issue(repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
    proc = _run_command(
        [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo,
            "--json",
            "number,title,state,url,labels",
        ],
        cwd=None,
        check=False,
    )
    if proc.returncode != 0:
        return None
    output = (proc.stdout or "").strip()
    if not output:
        return None
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _find_issue_by_title(repo: str, title: str, label: str) -> Optional[Dict[str, Any]]:
    data = _run_command_json(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--label",
            label,
            "--state",
            "all",
            "--search",
            f'"{title}" in:title',
            "--json",
            "number,title,state,url,labels",
        ]
    )
    if not isinstance(data, list):
        return None
    for item in data:
        if item.get("title") == title:
            return item
    return None


def _sync_issue_labels(repo: str, issue_number: int, desired_labels: List[str]) -> None:
    issue = _get_issue(repo, issue_number)
    existing = {
        label.get("name")
        for label in (issue or {}).get("labels", [])
        if isinstance(label, dict) and isinstance(label.get("name"), str)
    }
    managed = {
        "alfred",
        "alfred:task",
        _GH_SYNC_LABEL,
        _GH_LEGACY_BOARD_LABEL,
        *set(_GH_STATUS_LABELS.values()),
    }
    to_add = [label for label in desired_labels if label not in existing]
    to_remove = sorted((existing & managed) - set(desired_labels))
    if not to_add and not to_remove:
        return

    args = ["gh", "issue", "edit", str(issue_number), "--repo", repo]
    for label in to_add:
        args.extend(["--add-label", label])
    for label in to_remove:
        args.extend(["--remove-label", label])
    _run_command(args)


def _retire_missing_synced_issues(
    repo: str,
    previous_task_map: Dict[str, Any],
    active_task_ids: List[str],
) -> List[Dict[str, Any]]:
    """Cierra issues Alfred previamente sincronizados y hoy ausentes localmente."""
    active = {
        str(task_id).strip()
        for task_id in active_task_ids
        if str(task_id).strip()
    }
    retired: List[Dict[str, Any]] = []

    for task_id, payload in previous_task_map.items():
        normalized_task_id = str(task_id).strip()
        if not normalized_task_id or normalized_task_id in active:
            continue
        if not isinstance(payload, dict):
            continue

        issue_number = payload.get("number")
        if not isinstance(issue_number, int):
            continue

        _set_issue_state(repo, issue_number, should_close=True)
        _sync_issue_labels(repo, issue_number, ["alfred", "alfred:task"])
        issue = _get_issue(repo, issue_number) or {}
        retired.append(
            {
                "id": normalized_task_id,
                "number": issue_number,
                "url": (issue or {}).get("url", payload.get("url", "")),
                "title": payload.get("title") or (issue or {}).get("title", ""),
                "retired_at": _now_utc().isoformat(),
            }
        )

    return retired


def _set_issue_state(repo: str, issue_number: int, should_close: bool) -> None:
    issue = _get_issue(repo, issue_number)
    if not issue:
        return
    state = str(issue.get("state", "")).upper()
    if should_close and state != "CLOSED":
        _run_command(["gh", "issue", "close", str(issue_number), "--repo", repo])
    elif not should_close and state == "CLOSED":
        _run_command(["gh", "issue", "reopen", str(issue_number), "--repo", repo])


def _issue_body_for_task(task: Dict[str, Any]) -> str:
    lines = [
        "## Sincronizado por Alfred Dev",
        "",
        f"- Estado SonIA: `{task.get('status', 'desconocido')}`",
        f"- Fuente: `{task.get('path', '-')}`",
    ]
    if task.get("agent"):
        lines.append(f"- Agente: {task['agent']}")
    if task.get("criteria"):
        lines.append(f"- Criterios: {', '.join(task['criteria'])}")
    if task.get("dependencies"):
        lines.append(f"- Dependencias: {task['dependencies']}")
    if task.get("notes"):
        lines.append(f"- Notas: {task['notes']}")
    if task.get("evidence"):
        lines.append(f"- Evidencia: {task['evidence']}")
    lines.extend(["", "## Descripción", "", task.get("body") or task.get("title", "Sin descripción.")])
    return "\n".join(lines).strip() + "\n"


def _create_or_update_issue(
    repo: str,
    task: Dict[str, Any],
    sync_state: Dict[str, Any],
) -> Dict[str, Any]:
    task_id = task.get("id")
    if not task_id:
        raise RuntimeError("No se puede sincronizar una tarea sin identificador.")

    desired_title = _task_reference(task)
    body = _issue_body_for_task(task)
    desired_labels = ["alfred", "alfred:task", _GH_STATUS_LABELS[task["status"]]]

    task_map = sync_state.get("tasks", {}) if isinstance(sync_state.get("tasks"), dict) else {}
    existing_entry = task_map.get(task_id, {}) if isinstance(task_map.get(task_id), dict) else {}
    issue_number = existing_entry.get("number")
    issue = None
    drift = None
    if isinstance(issue_number, int):
        issue = _get_issue(repo, issue_number)
        if issue is None:
            drift = {
                "scope": "task",
                "kind": "missing_remote_issue",
                "task_id": task_id,
                "title": desired_title,
                "previous_number": issue_number,
            }
    if issue is None:
        issue = _find_issue_by_title(repo, desired_title, "alfred:task")
        if issue is not None and isinstance(issue_number, int):
            drift = {
                "scope": "task",
                "kind": "relinked_by_title",
                "task_id": task_id,
                "title": desired_title,
                "previous_number": issue_number,
            }

    if issue is None:
        proc = _run_command(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                repo,
                "--title",
                desired_title,
                "--body",
                body,
                "--label",
                "alfred",
                "--label",
                "alfred:task",
                "--label",
                _GH_STATUS_LABELS[task["status"]],
            ]
        )
        issue_url = (proc.stdout or "").strip().splitlines()[-1].strip()
        match = re.search(r"/issues/(?P<number>\d+)$", issue_url)
        if not match:
            raise RuntimeError(f"No se pudo extraer el número del issue creado: {issue_url}")
        issue_number = int(match.group("number"))
        if drift is not None:
            drift = {
                **drift,
                "resolution": "recreated",
                "number": issue_number,
                "url": issue_url,
            }
    else:
        issue_number = int(issue["number"])
        if drift is not None:
            drift = {
                **drift,
                "resolution": "relinked",
                "number": issue_number,
                "url": issue.get("url", ""),
            }
        _run_command(
            [
                "gh",
                "issue",
                "edit",
                str(issue_number),
                "--repo",
                repo,
                "--title",
                desired_title,
                "--body",
                body,
            ]
        )
        _sync_issue_labels(repo, issue_number, desired_labels)

    _set_issue_state(repo, issue_number, should_close=task["status"] == "done")
    _sync_issue_labels(repo, issue_number, desired_labels)
    issue = _get_issue(repo, issue_number)
    return {
        "number": issue_number,
        "url": (issue or {}).get("url", ""),
        "title": desired_title,
        "status": task["status"],
        "updated_at": _now_utc().isoformat(),
        "drift": drift,
    }


def _board_issue_body(
    project_name: str,
    repo: str,
    tasks: List[Dict[str, Any]],
    task_map: Dict[str, Dict[str, Any]],
    next_action: Dict[str, str],
    internal_omitted: int = 0,
) -> str:
    grouped: Dict[str, List[str]] = {key: [] for key in _KANBAN_RELATIVE_BY_STATUS}
    for task in tasks:
        task_id = task.get("id", "")
        sync = task_map.get(task_id, {})
        issue_ref = f"#{sync['number']}" if sync.get("number") else "sin issue"
        grouped[task["status"]].append(f"- {_task_reference(task)} — {issue_ref}")

    lines = [
        f"## SonIA Sync para `{project_name}`",
        "",
        f"- Repositorio: `{repo}`",
        f"- Sincronizado en: {_now_utc().isoformat()}",
        f"- Foco operativo actual: {next_action.get('focus', 'Siguiente paso recomendado')}",
        (
            f"- Fuente de la recomendación: {next_action.get('source_label', next_action.get('source', 'desconocida'))} "
            f"(`{next_action.get('source', 'desconocida')}`)"
        ),
        f"- Siguiente paso recomendado: `/alfred-dev:{next_action.get('command', 'alfred')}`",
        (
            "- Qué hacer ahora: "
            + next_action.get(
                "directive",
                "Avanza con el siguiente comando recomendado.",
            )
        ),
        f"- Motivo: {next_action.get('reason', 'Sin razón disponible.')}",
    ]
    if internal_omitted:
        lines.append(f"- Tareas internas omitidas del sync: {internal_omitted}")
    for status in ("in-progress", "blocked", "backlog", "done"):
        items = grouped.get(status) or []
        lines.extend(["", f"### {_KANBAN_STATUS_LABELS[status].title()}", ""])
        if items:
            lines.extend(items)
        else:
            lines.append("- Sin tareas.")
    return "\n".join(lines).strip() + "\n"


def _ensure_board_issue(
    repo: str,
    project_name: str,
    board_body: str,
    sync_state: Dict[str, Any],
) -> Dict[str, Any]:
    board_title = f"SonIA Sync: {project_name}"
    legacy_board_title = f"SonIA Board: {project_name}"
    board_issue_number = None
    existing_board = sync_state.get("board_issue") if isinstance(sync_state, dict) else None
    if isinstance(existing_board, dict):
        value = existing_board.get("number")
        if isinstance(value, int):
            board_issue_number = value

    issue = _get_issue(repo, board_issue_number) if board_issue_number else None
    drift = None
    if board_issue_number and issue is None:
        drift = {
            "scope": "board",
            "kind": "missing_remote_issue",
            "title": board_title,
            "previous_number": board_issue_number,
        }
    if issue is None:
        issue = _find_issue_by_title(repo, board_title, _GH_SYNC_LABEL)
        if issue is not None and board_issue_number:
            drift = {
                **(drift or {"scope": "board", "kind": "relinked_by_title", "title": board_title}),
                "resolution": "relinked",
                "number": int(issue["number"]),
                "url": issue.get("url", ""),
            }
    if issue is None:
        issue = _find_issue_by_title(repo, legacy_board_title, _GH_LEGACY_BOARD_LABEL)
        if issue is not None and board_issue_number:
            drift = {
                **(drift or {"scope": "board", "kind": "relinked_legacy_title", "title": board_title}),
                "resolution": "relinked",
                "number": int(issue["number"]),
                "url": issue.get("url", ""),
            }

    desired_labels = ["alfred", _GH_SYNC_LABEL]
    if issue is None:
        proc = _run_command(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                repo,
                "--title",
                board_title,
                "--body",
                board_body,
                "--label",
                "alfred",
                "--label",
                _GH_SYNC_LABEL,
            ]
        )
        issue_url = (proc.stdout or "").strip().splitlines()[-1].strip()
        match = re.search(r"/issues/(?P<number>\d+)$", issue_url)
        if not match:
            raise RuntimeError(f"No se pudo extraer el número del issue paraguas de SonIA Sync: {issue_url}")
        issue_number = int(match.group("number"))
        if drift is not None:
            drift = {
                **drift,
                "resolution": "recreated",
                "number": issue_number,
                "url": issue_url,
            }
    else:
        issue_number = int(issue["number"])
        _run_command(
            [
                "gh",
                "issue",
                "edit",
                str(issue_number),
                "--repo",
                repo,
                "--title",
                board_title,
                "--body",
                board_body,
            ]
        )
        _sync_issue_labels(repo, issue_number, desired_labels)

    _set_issue_state(repo, issue_number, should_close=False)
    _sync_issue_labels(repo, issue_number, desired_labels)
    final_issue = _get_issue(repo, issue_number)
    return {
        "number": issue_number,
        "url": (final_issue or {}).get("url", ""),
        "title": board_title,
        "drift": drift,
    }


def render_github_sync_markdown(result: Dict[str, Any]) -> str:
    next_action = result.get("next_action", {"command": "alfred", "reason": ""})
    lines = [
        "## SonIA Sync",
        "",
        f"- Repo: `{result.get('repo', '-')}`",
        f"- Issue paraguas: {result.get('board_issue', {}).get('url', 'pendiente')}",
        f"- Tareas sincronizadas: {len(result.get('tasks', []))}",
        f"- Foco operativo actual: {next_action.get('focus', 'Siguiente paso recomendado')}",
        (
            f"- Fuente de la recomendación: {next_action.get('source_label', next_action.get('source', 'desconocida'))} "
            f"(`{next_action.get('source', 'desconocida')}`)"
        ),
    ]
    skipped = result.get("skipped", [])
    internal_omitted = result.get("internal_omitted", [])
    retired = result.get("retired", [])
    remote_drift = result.get("remote_drift", [])
    if skipped:
        lines.append(f"- Tareas omitidas: {len(skipped)}")
    if internal_omitted:
        lines.append(f"- Tareas internas omitidas: {len(internal_omitted)}")
    if retired:
        lines.append(f"- Issues retiradas por drift local: {len(retired)}")
    if remote_drift:
        lines.append(f"- Drift remoto corregido: {len(remote_drift)}")
    lines.extend(
        [
            f"- Siguiente paso recomendado: `/alfred-dev:{next_action.get('command', 'alfred')}`",
            (
                "- Qué hacer ahora: "
                + next_action.get(
                    "directive",
                    "Avanza con el siguiente comando recomendado.",
                )
            ),
            f"- Motivo: {next_action.get('reason', 'Sin razón disponible.')}",
        ]
    )
    lines.extend(["", "### Issues", ""])
    for item in result.get("tasks", []):
        lines.append(
            f"- {_task_reference(item)} → #{item.get('number')} ({_KANBAN_STATUS_LABELS.get(item.get('status', ''), item.get('status', ''))})"
        )
    if skipped:
        lines.extend(["", "### Omitidas", ""])
        for task in skipped:
            lines.append(f"- {task.get('title', 'sin título')} — sin ID [T-XXX]")
    if internal_omitted:
        lines.extend(["", "### Internas omitidas", ""])
        for task in internal_omitted:
            lines.append(f"- {_task_reference(task)} — tipo `{_effective_task_type(task)}`")
    if retired:
        lines.extend(["", "### Retiradas del espejo GitHub", ""])
        for item in retired:
            issue_ref = f"#{item.get('number')}" if item.get("number") else "sin issue"
            label = item.get("title") or item.get("id") or "sin título"
            lines.append(f"- {label} — {issue_ref} cerrado por no existir ya en SonIA")
    if remote_drift:
        lines.extend(["", "### Drift remoto corregido", ""])
        for item in remote_drift:
            resolution = item.get("resolution", "")
            new_issue_ref = f"#{item.get('number')}" if item.get("number") else "sin issue"
            old_issue_ref = (
                f"#{item.get('previous_number')}"
                if item.get("previous_number")
                else "sin issue previa"
            )
            if item.get("scope") == "board":
                label = "Issue paraguas SonIA Sync"
            else:
                label = item.get("title") or item.get("task_id") or "sin título"

            if resolution == "recreated":
                lines.append(
                    f"- {label} — {old_issue_ref} ya no existía en remoto; recreada como {new_issue_ref}."
                )
            elif resolution == "relinked":
                lines.append(
                    f"- {label} — {old_issue_ref} ya no cuadraba; religada a {new_issue_ref}."
                )
            else:
                lines.append(
                    f"- {label} — se detectó drift remoto y quedó resuelto en {new_issue_ref}."
                )
    return "\n".join(lines).strip() + "\n"


def render_github_sync_cli_summary(result: Dict[str, Any]) -> str:
    next_action = result.get("next_action", {"command": "alfred", "directive": ""})
    counts = [
        f"sincronizadas={len(result.get('tasks', []))}",
        f"omitidas={len(result.get('skipped', []))}",
        f"internas={len(result.get('internal_omitted', []))}",
        f"retiradas={len(result.get('retired', []))}",
        f"drift={len(result.get('remote_drift', []))}",
    ]
    lines = [
        "## SonIA Sync listo",
        "",
        f"- Repo: `{result.get('repo', '-')}`",
        f"- Issue paraguas: {result.get('board_issue', {}).get('url', 'pendiente')}",
        f"- Conteo: {', '.join(counts)}",
        f"- Estado local: `{GITHUB_SYNC_JSON_RELATIVE_PATH}`",
        f"- Informe detallado: `{GITHUB_SYNC_MD_RELATIVE_PATH}`",
        (
            f"- Siguiente paso: `/alfred-dev:{next_action.get('command', 'alfred')}` "
            f"— {next_action.get('directive', 'Avanza con el siguiente comando recomendado.')}"
        ),
    ]
    return "\n".join(lines).strip() + "\n"


def sync_project_to_github(project_dir: str, raw_request: str = "") -> Dict[str, Any]:
    normalize_kanban_task_types(project_dir)
    board = load_kanban_board(project_dir)
    tasks = [
        task
        for status in ("backlog", "in-progress", "blocked", "done")
        for task in board.get(status, [])
    ]
    if not tasks:
        raise RuntimeError("No hay tareas en docs/project/kanban/ para sincronizar.")

    validation = validate_operational_artifacts(project_dir)
    if validation.get("errors"):
        raise RuntimeError(
            "El kanban no se puede sincronizar de forma fiable: "
            + "; ".join(validation["errors"])
        )

    syncable_tasks = [
        task for task in tasks
        if _is_syncable_kanban_task(task) and task.get("id")
    ]
    skipped = [
        task for task in tasks
        if _is_syncable_kanban_task(task) and not task.get("id")
    ]
    internal_omitted = [task for task in tasks if not _is_syncable_kanban_task(task)]
    if not syncable_tasks:
        raise RuntimeError(
            "No hay tareas con identificador [T-XXX] para sincronizar a GitHub Issues."
        )

    _ensure_gh_ready()
    repo = _detect_github_repo(project_dir, raw_request=raw_request)
    _ensure_github_labels(repo)

    sync_path = _project_path(project_dir, GITHUB_SYNC_JSON_RELATIVE_PATH)
    sync_state = _read_json_file(sync_path)
    if not isinstance(sync_state, dict) or sync_state.get("repo") != repo:
        sync_state = {"version": 1, "repo": repo, "tasks": {}}

    previous_task_map = sync_state.get("tasks", {}) if isinstance(sync_state.get("tasks"), dict) else {}
    task_map: Dict[str, Dict[str, Any]] = {}
    synced_tasks: List[Dict[str, Any]] = []
    remote_drift: List[Dict[str, Any]] = []
    for task in syncable_tasks:
        issue_info = _create_or_update_issue(repo, task, sync_state)
        merged = {**task, **issue_info}
        task_map[task["id"]] = issue_info
        synced_tasks.append(merged)
        if isinstance(issue_info.get("drift"), dict):
            remote_drift.append(issue_info["drift"])
    retired = _retire_missing_synced_issues(
        repo,
        previous_task_map,
        [task.get("id", "") for task in syncable_tasks],
    )

    project_name = _detect_project_name(project_dir, _load_package_json(project_dir))
    next_action = suggest_next_action(project_dir)
    board_body = _board_issue_body(
        project_name,
        repo,
        syncable_tasks,
        task_map,
        next_action,
        internal_omitted=len(internal_omitted),
    )
    board_issue = _ensure_board_issue(repo, project_name, board_body, sync_state)
    if isinstance(board_issue.get("drift"), dict):
        remote_drift.append(board_issue["drift"])

    sync_record = {
        "version": 1,
        "repo": repo,
        "synced_at": _now_utc().isoformat(),
        "board_issue": board_issue,
        "tasks": task_map,
        "skipped": [task.get("title", "") for task in skipped],
        "internal_omitted": [_task_reference(task) for task in internal_omitted],
        "retired": retired,
        "remote_drift": remote_drift,
    }
    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    with open(sync_path, "w", encoding="utf-8") as fh:
        json.dump(sync_record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    sync_md_path = _project_path(project_dir, GITHUB_SYNC_MD_RELATIVE_PATH)
    os.makedirs(os.path.dirname(sync_md_path), exist_ok=True)
    with open(sync_md_path, "w", encoding="utf-8") as fh:
        fh.write(render_github_sync_markdown({
            "repo": repo,
            "board_issue": board_issue,
            "tasks": synced_tasks,
            "skipped": skipped,
            "internal_omitted": internal_omitted,
            "retired": retired,
            "remote_drift": remote_drift,
            "next_action": next_action,
        }))

    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    bypass_path = None
    if state and state.get("fase_actual") != "completado":
        bypass_path = arm_stop_hook_bypass(project_dir, "/alfred-dev:sync-github")

    return {
        "repo": repo,
        "board_issue": board_issue,
        "tasks": synced_tasks,
        "skipped": skipped,
        "internal_omitted": internal_omitted,
        "retired": retired,
        "remote_drift": remote_drift,
        "sync_path": sync_path,
        "sync_md_path": sync_md_path,
        "bypass_path": bypass_path,
        "next_action": next_action,
    }


def _extract_recommended_alfred_command(markdown: str) -> Optional[str]:
    """Extrae un comando recomendado de un artefacto Markdown de Alfred."""
    if not markdown:
        return None

    def _extract_commands(text: str) -> List[str]:
        commands: List[str] = []
        seen = set()
        for match in re.finditer(
            r"/alfred-dev:(?P<command>[a-z0-9-]+)\b",
            text,
            flags=re.IGNORECASE,
        ):
            command = match.group("command").lower()
            if (
                command not in _KNOWN_ALFRED_COMMANDS
                or command in _SELF_ROUTING_COMMANDS
                or command in seen
            ):
                continue
            seen.add(command)
            commands.append(command)
        return commands

    lines = markdown.splitlines()
    for index, raw_line in enumerate(lines):
        normalized_line = _normalize_free_text(re.sub(r"[*_`#>-]+", " ", raw_line))
        if (
            "comando recomendado" not in normalized_line
            and "siguiente comando recomendado" not in normalized_line
        ):
            continue
        window = "\n".join(lines[index : index + 4])
        commands = _extract_commands(window)
        if commands:
            return commands[0]

    commands = _extract_commands(markdown)
    if len(commands) == 1:
        return commands[0]
    return None


def _read_json_file(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None


def _load_package_json(project_dir: str) -> Dict[str, Any]:
    data = _read_json_file(os.path.join(project_dir, "package.json"))
    return data if isinstance(data, dict) else {}


def _detect_project_name(project_dir: str, package_data: Dict[str, Any]) -> str:
    name = package_data.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return os.path.basename(os.path.abspath(project_dir)) or "proyecto"


def _extract_readme_summary(project_dir: str, project_name: str) -> str:
    readme = _read_text_if_exists(project_dir, "README.md")
    for raw_line in readme.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        return line
    return (
        f"Repositorio `{project_name}` sin descripción explícita en README. "
        "Conviene validar su objetivo con el equipo antes de abrir cambios grandes."
    )


def _collect_visible_top_level(project_dir: str) -> List[str]:
    try:
        names = sorted(os.listdir(project_dir))
    except OSError:
        return []

    visible: List[str] = []
    for name in names:
        if name.startswith(".") and name not in {".github"}:
            continue
        if name in _SKIP_DIRS:
            continue
        visible.append(name)
    return visible


def _detect_entrypoints(project_dir: str, package_data: Dict[str, Any]) -> List[str]:
    candidates: List[str] = []
    main_file = package_data.get("main")
    if isinstance(main_file, str) and main_file.strip():
        candidates.append(main_file.strip())

    candidates.extend(
        [
            "index.js",
            "index.ts",
            "main.js",
            "main.ts",
            "app.py",
            "main.py",
            "manage.py",
            "main.go",
            "src/index.js",
            "src/index.ts",
            "src/main.js",
            "src/main.ts",
            "src/main.py",
            "src/app.py",
            "src/app.tsx",
            "src/main.tsx",
            "app/page.tsx",
            "pages/index.tsx",
        ]
    )

    found: List[str] = []
    seen = set()
    for relative_path in candidates:
        normalized = relative_path.strip().lstrip("./")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if os.path.isfile(os.path.join(project_dir, normalized)):
            found.append(normalized)
        if len(found) >= 5:
            break

    if found:
        return found

    fallback_files: List[str] = []
    for file_path in _iter_code_files(project_dir, max_depth=1):
        relative = os.path.relpath(file_path, project_dir)
        fallback_files.append(relative)
        if len(fallback_files) >= 5:
            break
    return fallback_files


def _detect_primary_modules(project_dir: str) -> List[str]:
    preferred = [
        "src",
        "app",
        "lib",
        "packages",
        "services",
        "api",
        "web",
        "site",
        "tests",
        "docs",
        "infra",
        "hooks",
        "mcp",
    ]
    modules = [name for name in preferred if os.path.exists(os.path.join(project_dir, name))]
    if modules:
        return modules[:8]

    top_level = _collect_visible_top_level(project_dir)
    return top_level[:8]


def _describe_stack(stack: Dict[str, str]) -> List[str]:
    details = [
        f"Runtime: `{stack.get('runtime', 'desconocido')}`",
        f"Lenguaje principal: `{stack.get('lenguaje', 'desconocido')}`",
        f"Framework: `{stack.get('framework', 'desconocido')}`",
    ]
    orm = stack.get("orm")
    if orm and orm != "ninguno":
        details.append(f"ORM: `{orm}`")
    test_runner = stack.get("test_runner")
    if test_runner and test_runner != "desconocido":
        details.append(f"Test runner: `{test_runner}`")
    bundler = stack.get("bundler")
    if bundler and bundler != "desconocido":
        details.append(f"Bundler: `{bundler}`")
    return details


def _summarize_tests_build_deploy(project_dir: str, package_data: Dict[str, Any], stack: Dict[str, str]) -> Dict[str, List[str]]:
    scripts = package_data.get("scripts")
    scripts = scripts if isinstance(scripts, dict) else {}

    tests: List[str] = []
    build: List[str] = []
    deploy: List[str] = []

    if os.path.isdir(os.path.join(project_dir, "tests")):
        tests.append("Existe directorio `tests/`.")
    if os.path.isdir(os.path.join(project_dir, "__tests__")):
        tests.append("Existe directorio `__tests__/`.")
    if stack.get("test_runner") not in {None, "", "desconocido"}:
        tests.append(f"Runner detectado: `{stack['test_runner']}`.")
    if "test" in scripts:
        tests.append(f"Script `test`: `{scripts['test']}`.")
    if not tests:
        tests.append("No se detecta una infraestructura clara de tests automatizados.")

    for script_name in ("build", "dev", "start"):
        value = scripts.get(script_name)
        if isinstance(value, str) and value.strip():
            build.append(f"Script `{script_name}`: `{value.strip()}`.")
    if os.path.isfile(os.path.join(project_dir, "Dockerfile")):
        build.append("Existe `Dockerfile`.")
    if not build:
        build.append("No se detectan scripts claros de build o arranque más allá del código fuente.")

    deploy_markers = [
        ("docker-compose.yml", "Compose"),
        ("docker-compose.yaml", "Compose"),
        ("render.yaml", "Render"),
        ("vercel.json", "Vercel"),
        ("netlify.toml", "Netlify"),
        ("fly.toml", "Fly.io"),
        (".github/workflows", "GitHub Actions"),
    ]
    for relative_path, label in deploy_markers:
        if os.path.exists(os.path.join(project_dir, relative_path)):
            deploy.append(f"Artefacto de despliegue/CI detectado: `{relative_path}` ({label}).")
    if not deploy:
        deploy.append("No se detectan artefactos claros de despliegue o CI/CD en la raíz.")

    return {
        "tests": tests,
        "build": build,
        "deploy": deploy,
    }


def _infer_conventions(project_dir: str, stack: Dict[str, str], modules: List[str]) -> List[str]:
    conventions: List[str] = []
    runtime = stack.get("runtime")
    framework = stack.get("framework")

    if runtime == "node":
        conventions.append("Respetar `package.json` como fuente principal de scripts y dependencias.")
    elif runtime == "python":
        conventions.append("Mantener el punto de verdad de dependencias y tooling en los ficheros Python detectados.")
    elif runtime != "desconocido":
        conventions.append(f"Respetar las convenciones del runtime `{runtime}` ya presentes en el repo.")

    if framework not in {None, "", "desconocido"}:
        conventions.append(f"Seguir los patrones del framework `{framework}` antes de introducir estructuras nuevas.")

    if "docs" in modules or os.path.isdir(os.path.join(project_dir, "docs")):
        conventions.append("Mantener `docs/` como lugar visible para artefactos operativos y documentación.")

    if not conventions:
        conventions.append("El repositorio es pequeño; conviene mantener la estructura actual y evitar introducir capas innecesarias.")

    return conventions


def _infer_risks(project_dir: str, stack: Dict[str, str], analysis: Dict[str, List[str]]) -> List[str]:
    risks: List[str] = []

    tests = analysis.get("tests", [])
    if any("No se detecta" in item for item in tests):
        risks.append("La ausencia de tests claros aumenta el riesgo de regresión al tocar el repo.")

    deploy = analysis.get("deploy", [])
    if any("No se detectan" in item for item in deploy):
        risks.append("No hay señales claras de despliegue/CI, así que conviene validar el camino de entrega antes de cambios grandes.")

    if stack.get("framework") in {None, "", "desconocido"} and project_has_codebase(project_dir):
        risks.append("El framework no está claramente declarado; hay riesgo de asumir una arquitectura equivocada si no se contrasta con el código.")

    if not risks:
        risks.append("No se aprecian riesgos críticos inmediatos en el mapa inicial, pero conviene validar edge cases antes de implementar.")

    return risks


def _render_bullet_list(items: List[str]) -> str:
    if not items:
        return "- Sin datos relevantes."
    return "\n".join(f"- {item}" for item in items)


def _merge_unique_items(existing: List[str], new_items: List[str]) -> List[str]:
    merged: List[str] = []
    seen = set()
    for item in [*(new_items or []), *(existing or [])]:
        cleaned = (item or "").strip()
        if not cleaned:
            continue
        normalized = _normalize_free_text(cleaned)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(cleaned)
    return merged


def _append_helper_list_artifact(
    project_dir: str,
    relative_path: str,
    *,
    title: str,
    intro: str,
    items: List[str],
    task_agent: str = "",
) -> str:
    path = _project_path(project_dir, relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing_markdown = _read_text_if_exists(project_dir, relative_path)

    if relative_path in _KANBAN_RELATIVE_PATHS:
        status = next(
            lane for lane, lane_path in _KANBAN_RELATIVE_BY_STATUS.items()
            if lane_path == relative_path
        )
        for item in items:
            create_kanban_task(
                project_dir,
                status,
                title=item,
                agent=task_agent,
                notes=intro,
            )
        return path

    existing_items = _extract_markdown_list_items(existing_markdown)
    merged_items = _merge_unique_items(existing_items, items)

    if existing_markdown.strip():
        if merged_items == existing_items:
            return path
        extra_lines = [f"- {item}" for item in merged_items if item not in existing_items]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(existing_markdown.rstrip() + "\n" + "\n".join(extra_lines) + "\n")
        return path

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(
            f"# {title}\n\n"
            f"{intro}\n\n"
            f"{_render_bullet_list(merged_items)}\n"
        )
    return path


def _seed_helper_operational_artifacts(
    project_dir: str,
    *,
    helper_name: str = "alfred",
    progress_items: Optional[List[str]] = None,
    traceability_items: Optional[List[str]] = None,
    backlog_items: Optional[List[str]] = None,
    in_progress_items: Optional[List[str]] = None,
    blocked_items: Optional[List[str]] = None,
) -> List[str]:
    artifact_paths: List[str] = []

    if progress_items:
        artifact_paths.append(
            _append_helper_list_artifact(
                project_dir,
                PROGRESS_MD_RELATIVE_PATH,
                title="Progress",
                intro="Señales humanas del estado operativo que Alfred ya ha dejado listas.",
                items=progress_items,
            )
        )

    if traceability_items:
        artifact_paths.append(
            _append_helper_list_artifact(
                project_dir,
                TRACEABILITY_MD_RELATIVE_PATH,
                title="Traceability",
                intro="Criterios, riesgos y huecos de cobertura visibles desde los primeros pasos.",
                items=traceability_items,
            )
        )

    if backlog_items:
        artifact_paths.append(
            _append_helper_list_artifact(
                project_dir,
                KANBAN_BACKLOG_RELATIVE_PATH,
                title="Backlog",
                intro="Pendiente por atacar a continuación.",
                items=backlog_items,
                task_agent=f"alfred:{helper_name}",
            )
        )

    if in_progress_items:
        artifact_paths.append(
            _append_helper_list_artifact(
                project_dir,
                KANBAN_IN_PROGRESS_RELATIVE_PATH,
                title="In progress",
                intro="Trabajo activo visible para SonIA y la Memory UI.",
                items=in_progress_items,
                task_agent=f"alfred:{helper_name}",
            )
        )

    if blocked_items:
        artifact_paths.append(
            _append_helper_list_artifact(
                project_dir,
                KANBAN_BLOCKED_RELATIVE_PATH,
                title="Blocked",
                intro="Dependencias o riesgos que frenan el avance.",
                items=blocked_items,
                task_agent=f"alfred:{helper_name}",
            )
        )

    return artifact_paths


def render_codebase_map_markdown(record: Dict[str, Any]) -> str:
    previous_notes = record.get("previous_notes") or []
    previous_section = ""
    if previous_notes:
        previous_section = (
            "\n## Notas previas conservadas\n\n"
            f"{_render_bullet_list(previous_notes)}\n"
        )

    focus_line = ""
    if record.get("focus_area"):
        focus_line = f"**Área de foco solicitada:** {record['focus_area']}\n\n"

    return (
        "# Codebase Map\n\n"
        f"**Actualizado en:** {record['updated_at']}\n"
        f"**Proyecto:** {record['project_name']}\n\n"
        f"{focus_line}"
        "## Propósito aparente del proyecto\n\n"
        f"{record['purpose']}\n\n"
        "## Stack y runtime detectados\n\n"
        f"{_render_bullet_list(record['stack_details'])}\n\n"
        "## Entry points y rutas críticas\n\n"
        f"{_render_bullet_list(record['entrypoints'])}\n\n"
        "## Módulos o dominios principales\n\n"
        f"{_render_bullet_list(record['modules'])}\n\n"
        "## Pruebas, build y despliegue\n\n"
        "### Tests\n\n"
        f"{_render_bullet_list(record['tests'])}\n\n"
        "### Build / arranque\n\n"
        f"{_render_bullet_list(record['build'])}\n\n"
        "### Despliegue / operación\n\n"
        f"{_render_bullet_list(record['deploy'])}\n\n"
        "## Convenciones y patrones que conviene respetar\n\n"
        f"{_render_bullet_list(record['conventions'])}\n\n"
        "## Riesgos, deuda visible y preguntas abiertas\n\n"
        f"{_render_bullet_list(record['risks'])}\n"
        f"{previous_section}"
    )


def render_codebase_current_markdown(record: Dict[str, Any]) -> str:
    previous_notes = record.get("previous_current_notes") or []
    previous_section = ""
    if previous_notes:
        previous_section = (
            "\n## Notas previas conservadas\n\n"
            f"{_render_bullet_list(previous_notes)}\n"
        )

    focus_line = ""
    if record.get("focus_area"):
        focus_line = f"- Foco solicitado: {record['focus_area']}.\n"

    return (
        "# Current\n\n"
        "- Estado: mapa brownfield preparado y persistido en `docs/project/codebase-map.md`.\n"
        f"{focus_line}"
        f"- Stack detectado: runtime `{record['stack'].get('runtime', 'desconocido')}`, "
        f"framework `{record['stack'].get('framework', 'desconocido')}`.\n"
        f"- Qué falta: elegir el siguiente flujo con el mapa ya consolidado.\n"
        f"- Riesgo principal: {record['risks'][0]}\n"
        f"- Siguiente comando recomendado: /alfred-dev:{record['recommended_command']}\n"
        f"{previous_section}"
    )


def render_codebase_map_summary(result: Dict[str, Any]) -> str:
    """Resumen breve listo para devolver en CLI tras map-codebase."""
    stack = result.get("stack", {})
    focus_area = result.get("focus_area")
    focus_line = f"- Foco analizado: {focus_area}\n" if focus_area else ""
    return (
        "## Mapeo brownfield completado\n\n"
        f"- Proyecto: `{result.get('project_name', 'proyecto')}`\n"
        f"- Stack detectado: runtime `{stack.get('runtime', 'desconocido')}`, "
        f"framework `{stack.get('framework', 'desconocido')}`\n"
        f"{focus_line}"
        f"- Artefactos: `{CODEBASE_MAP_RELATIVE_PATH}` y `{CURRENT_RELATIVE_PATH}`\n"
        f"- Siguiente comando recomendado: `/alfred-dev:{result.get('recommended_command', 'alfred')}`\n"
    )


def render_discovery_summary(result: Dict[str, Any]) -> str:
    """Resumen breve listo para devolver tras discuss helper-first."""
    scope_items = result.get("scope_items") or []
    open_questions = result.get("open_questions") or []
    risks = result.get("risks") or []
    scope_line = (
        f"- Alcance inicial: {scope_items[0]}\n"
        if isinstance(scope_items, list) and scope_items
        else ""
    )
    question_line = (
        f"- Pregunta abierta clave: {open_questions[0]}\n"
        if isinstance(open_questions, list) and open_questions
        else ""
    )
    risk_line = (
        f"- Riesgo principal: {risks[0]}\n"
        if isinstance(risks, list) and risks
        else ""
    )
    return (
        "## Refinado preparado\n\n"
        f"- Foco: `{result.get('description', 'siguiente trabajo')}`\n"
        f"- Actor principal: `{result.get('actor', 'por definir')}`\n"
        f"{scope_line}"
        f"{question_line}"
        f"{risk_line}"
        f"- Artefactos: `{DISCOVERY_MD_RELATIVE_PATH}` y `{CURRENT_RELATIVE_PATH}`\n"
        f"- Siguiente comando recomendado: `/alfred-dev:{result.get('recommended_command', 'feature')}`\n"
    )


def render_quick_setup_summary(result: Dict[str, Any]) -> str:
    """Resumen breve para devolver cuando quick ya quedó sembrado por prefetch."""
    needs_map = result.get("needs_codebase_map")
    map_note = (
        "- Nota: el repo parece brownfield y conviene ejecutar `/alfred-dev:map-codebase` antes de tocar código.\n"
        if needs_map
        else ""
    )
    return (
        "## Quick preparado\n\n"
        f"- Sesión activa: `{result.get('command', 'quick')}` en fase `{result.get('phase', 'ejecucion_acotada')}`\n"
        f"- Cambio pedido: `{result.get('description', 'cambio rápido acotado')}`\n"
        f"- Estado persistido: `{STATE_RELATIVE_PATH}`\n"
        f"{map_note}"
        f"- Siguiente paso esperado al cerrar: `{result.get('next_command', '/alfred-dev:verify')}`\n"
        "- Cierre canónico: responde con este resumen, sin bloques Insight ni explicación larga.\n"
    )


_HELPER_FIRST_FLOW_COMMANDS = frozenset({"feature", "fix", "spike", "ship", "audit"})
_LUCIUS_SCOPES = frozenset({"all", "security", "tests", "architecture", "performance"})


def _default_flow_description(command: str) -> str:
    defaults = {
        "feature": "Nueva funcionalidad por definir",
        "fix": "Bug por diagnosticar y corregir",
        "spike": "Investigacion tecnica por acotar",
        "ship": "Preparar entrega a produccion",
        "audit": "Auditoria completa del proyecto",
    }
    return defaults.get(command, "Trabajo Alfred Dev")


def _first_phase_description(command: str, phase: str) -> str:
    flow = FLOWS.get(command, {})
    for candidate in flow.get("fases", []):
        if candidate.get("nombre") == phase:
            return str(candidate.get("descripcion", "")).strip()
    return ""


def render_flow_start_current_markdown(result: Dict[str, Any]) -> str:
    """Resume en current.md el arranque determinista de un flujo largo."""
    command = result.get("command", "flujo")
    phase = result.get("phase", "fase_inicial")
    description = result.get("description", "trabajo")
    pending_gate = result.get("pending_gate") or "sin gate pendiente detectada"
    return (
        "# Current\n\n"
        f"- Estado: `{command}` activo, preparado por helper-first.\n"
        f"- Trabajo: {description}.\n"
        f"- Fase actual: `{phase}`.\n"
        f"- Gate pendiente: {pending_gate}.\n"
        "- Qué está listo: estado operativo, trazabilidad mínima y tarea principal en SonIA.\n"
        "- Qué falta: ejecutar la fase actual, aportar evidencia y resolver la gate correspondiente.\n"
        "- Siguiente comando recomendado: /alfred-dev:resume\n"
    )


def render_flow_start_progress_markdown(result: Dict[str, Any]) -> str:
    """Deja una señal humana mínima para progress tras arrancar un flujo largo."""
    command = result.get("command", "flujo")
    phase = result.get("phase", "fase_inicial")
    phase_description = result.get("phase_description") or "Primera fase del flujo."
    return (
        "# Progress\n\n"
        f"- Flujo activo: `{command}`.\n"
        f"- Fase inicial pendiente: `{phase}`.\n"
        f"- Objetivo de la fase: {phase_description}\n"
        "- No hay fases completadas todavía; el helper solo sembró continuidad y guardrails.\n"
        "- Retomar con `/alfred-dev:resume` para ejecutar el trabajo real con sus gates.\n"
    )


def render_flow_start_traceability_markdown(result: Dict[str, Any]) -> str:
    """Registra los criterios iniciales del flujo sin fingir evidencia."""
    command = result.get("command", "flujo")
    pending_gate = result.get("pending_gate") or "sin gate pendiente detectada"
    return (
        "# Traceability\n\n"
        f"- `{command}` arrancó por helper-first; no se marca ninguna fase como completada.\n"
        f"- Gate inicial pendiente: {pending_gate}.\n"
        "- Evidencia requerida: artefactos de la fase, tests/checks cuando apliquen y validación de seguridad según el flujo.\n"
        "- Comando de continuidad: `/alfred-dev:resume`.\n"
    )


def render_flow_start_summary(result: Dict[str, Any]) -> str:
    """Resumen breve para devolver cuando un flujo largo quedó sembrado."""
    command = result.get("command", "flujo")
    marker = result.get("headless_marker") or f"{command.upper()}_HEADLESS_START"
    pending_gate = result.get("pending_gate") or "sin gate pendiente detectada"
    phase_description = result.get("phase_description") or "Primera fase del flujo."
    artifacts = result.get("artifacts") or []
    artifact_lines = "\n".join(f"- `{item}`" for item in artifacts) if artifacts else "- Ninguno"
    sonarqube_section = _render_audit_sonarqube_summary(result)
    return (
        f"`{marker}`\n\n"
        "## Flujo preparado\n\n"
        f"- Sesión activa: `{command}` en fase `{result.get('phase', 'fase_inicial')}`\n"
        f"- Trabajo pedido: `{result.get('description', 'trabajo')}`\n"
        f"- Gate pendiente: {pending_gate}\n"
        f"- Estado persistido: `{STATE_RELATIVE_PATH}`\n"
        f"- Siguiente paso: `{result.get('next_command', '/alfred-dev:resume')}`\n\n"
        f"{sonarqube_section}"
        "### Primera fase\n\n"
        f"{phase_description}\n\n"
        "### Artefactos preparados\n\n"
        f"{artifact_lines}\n\n"
        "No he marcado fases como completadas ni he aprobado gates humanas: el helper solo deja el flujo listo para continuar sin bloquear `claude -p`.\n"
    )


def _parse_lucius_request(raw_request: str) -> Dict[str, Any]:
    try:
        tokens = shlex.split(raw_request or "")
    except ValueError:
        tokens = (raw_request or "").split()

    scope = "all"
    target = "."
    invalid_scope = ""
    consumed_next_scope = False
    positional: List[str] = []

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if consumed_next_scope:
            consumed_next_scope = False
            index += 1
            continue
        if token == "--scope":
            if index + 1 >= len(tokens):
                invalid_scope = ""
            else:
                candidate = tokens[index + 1].strip().lower()
                if candidate in _LUCIUS_SCOPES:
                    scope = candidate
                else:
                    invalid_scope = candidate
                consumed_next_scope = True
            index += 1
            continue
        if token.startswith("--scope="):
            candidate = token.split("=", 1)[1].strip().lower()
            if candidate in _LUCIUS_SCOPES:
                scope = candidate
            else:
                invalid_scope = candidate
            index += 1
            continue
        if token.startswith("--"):
            index += 1
            continue
        positional.append(token)
        index += 1

    if positional:
        target = positional[0]

    return {
        "scope": scope,
        "target": target,
        "invalid_scope": invalid_scope,
        "valid": not bool(invalid_scope),
    }


def render_lucius_summary(result: Dict[str, Any]) -> str:
    marker = result.get("headless_marker", "LUCIUS_HEADLESS_START")
    valid = bool(result.get("valid", True))
    if not valid:
        return (
            "`LUCIUS_INVALID_SCOPE`\n\n"
            "## Scope inválido\n\n"
            f"- Valor recibido: `{result.get('invalid_scope', '')}`\n"
            f"- Scopes válidos: `{', '.join(sorted(_LUCIUS_SCOPES))}`\n"
            "- No lanzo Lucius, no ejecuto Codex CLI y no modifico el proyecto.\n"
        )

    codex_status = result.get("codex_status", "unknown")
    codex_version = result.get("codex_version", "")
    version_line = f"- Codex CLI: `{codex_version}`\n" if codex_version else f"- Codex CLI: `{codex_status}`\n"
    return (
        f"`{marker}`\n\n"
        "## Lucius preparado\n\n"
        f"- Directorio objetivo: `{result.get('target', '.')}`\n"
        f"- Scope: `{result.get('scope', 'all')}`\n"
        f"{version_line}"
        "- Ejecución externa: pendiente de sesión interactiva.\n"
        "- No he lanzado Agent, no he ejecutado `codex exec` y no presento esto como sign-off de QA, seguridad o arquitectura.\n\n"
        "### Siguiente paso\n\n"
        "Ejecuta `/alfred-dev:lucius` en sesión interactiva si quieres autorizar la revisión externa con Codex CLI.\n"
    )


def prepare_lucius_review(project_dir: str, raw_request: str = "") -> Dict[str, Any]:
    parsed = _parse_lucius_request(raw_request)
    result = {
        "command": "lucius",
        "target": parsed["target"],
        "scope": parsed["scope"],
        "valid": parsed["valid"],
        "invalid_scope": parsed["invalid_scope"],
        "headless_marker": "LUCIUS_HEADLESS_START",
        "next_command": "/alfred-dev:lucius",
    }

    if not parsed["valid"]:
        result["headless_marker"] = "LUCIUS_INVALID_SCOPE"
        result["codex_status"] = "not_checked"
        return result

    codex = shutil.which("codex")
    if not codex:
        result["codex_status"] = "missing"
        return result

    try:
        version = _run_short_command([codex, "--version"], timeout=5)
    except (OSError, subprocess.SubprocessError):
        result["codex_status"] = "unavailable"
        return result

    if version.returncode == 0:
        result["codex_status"] = "available"
        result["codex_version"] = " ".join((version.stdout or "").split()).strip()
    else:
        result["codex_status"] = "unavailable"
        result["codex_version"] = " ".join((version.stderr or version.stdout or "").split()).strip()
    return result


def _run_short_command(command: List[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def _build_audit_sonarqube_preflight() -> Dict[str, Any]:
    docker = shutil.which("docker")
    if not docker:
        return {
            "status": "docker_missing",
            "sonarqube_autorizado": False,
            "headless_marker": "AUDIT_DOCKER_INSTALL_MENU_HEADLESS",
            "summary": "Docker no esta disponible en PATH; SonarQube requiere decision humana antes de instalar o preparar Docker.",
            "menu_title": "Preparar Docker para SonarQube",
            "menu_options": [
                "Instalar/preparar Docker (Recomendado)",
                "Seguir sin SonarQube",
            ],
        }

    version = _run_short_command([docker, "--version"], timeout=5)
    info = _run_short_command([docker, "info"], timeout=5)
    version_text = " ".join(part for part in (version.stderr, version.stdout) if part)
    info_text = " ".join(part for part in (info.stderr, info.stdout) if part)
    missing_signal = " ".join((version_text, info_text)).lower()
    if (
        version.returncode == 127
        or info.returncode == 127
        or "command not found" in missing_signal
        or "no such file or directory" in missing_signal
    ):
        return {
            "status": "docker_missing",
            "sonarqube_autorizado": False,
            "headless_marker": "AUDIT_DOCKER_INSTALL_MENU_HEADLESS",
            "summary": "Docker no esta disponible en PATH; SonarQube requiere decision humana antes de instalar o preparar Docker.",
            "detail": missing_signal[:500],
            "menu_title": "Preparar Docker para SonarQube",
            "menu_options": [
                "Instalar/preparar Docker (Recomendado)",
                "Seguir sin SonarQube",
            ],
        }

    if version.returncode == 0 and info.returncode == 0:
        return {
            "status": "docker_ready",
            "sonarqube_autorizado": True,
            "headless_marker": "AUDIT_HEADLESS_START",
            "summary": "Docker esta instalado y el daemon responde; SonarQube queda autorizado para la auditoria interactiva.",
            "menu_title": "",
            "menu_options": [],
        }

    detail = " ".join(part.strip() for part in [version_text, info_text] if part and part.strip())
    return {
        "status": "docker_daemon_down",
        "sonarqube_autorizado": False,
        "headless_marker": "AUDIT_DOCKER_START_MENU_HEADLESS",
        "summary": (
            "Docker existe, pero el daemon no responde; SonarQube requiere decision humana "
            "antes de arrancar Docker Desktop o el servicio."
        ),
        "detail": detail[:500],
        "menu_title": "Arrancar Docker para SonarQube",
        "menu_options": [
            "Arrancar Docker y ejecutar SonarQube (Recomendado)",
            "Seguir sin SonarQube",
        ],
    }


def _render_audit_sonarqube_summary(result: Dict[str, Any]) -> str:
    preflight = result.get("sonarqube_preflight")
    if not isinstance(preflight, dict):
        return ""

    marker = preflight.get("headless_marker", "")
    option_lines = "\n".join(
        f"- {option}" for option in preflight.get("menu_options", []) if option
    )
    menu_block = ""
    if option_lines:
        menu_block = (
            "### Menú SonarQube pendiente\n\n"
            f"`{marker}`\n\n"
            f"**{preflight.get('menu_title', 'Decision SonarQube')}**\n\n"
            f"{option_lines}\n\n"
            "En headless no elijo por el usuario ni intento instalar/arrancar Docker.\n\n"
        )

    detail = preflight.get("detail")
    detail_line = f"- Detalle Docker: {detail}\n" if detail else ""
    return (
        "### Preflight SonarQube\n\n"
        f"- Estado: `{preflight.get('status', 'desconocido')}`\n"
        f"- Autorizado para SonarQube: `{str(preflight.get('sonarqube_autorizado', False)).lower()}`\n"
        f"- Lectura: {preflight.get('summary', 'sin resumen')}\n"
        f"{detail_line}\n"
        f"{menu_block}"
    )


def start_flow_session(project_dir: str, command: str, raw_request: str = "") -> Dict[str, Any]:
    """Crea la sesión inicial de un flujo largo sin ejecutar sus fases."""
    normalized_command = (command or "").strip().lower()
    if normalized_command not in _HELPER_FIRST_FLOW_COMMANDS:
        raise RuntimeError(
            "start-flow solo admite feature, fix, spike, ship o audit."
        )

    description = _normalize_request_description(
        raw_request,
        _default_flow_description(normalized_command),
    )
    state_path = _project_path(project_dir, STATE_RELATIVE_PATH)
    state = load_state(state_path)
    if state and state.get("fase_actual") != "completado":
        if state.get("comando") == normalized_command and state.get("descripcion") == description:
            pending_gate = get_pending_gate(state)
            result = {
                "state_path": state_path,
                "command": state.get("comando", normalized_command),
                "phase": state.get("fase_actual", ""),
                "description": state.get("descripcion", description),
                "pending_gate": pending_gate,
                "phase_description": _first_phase_description(
                    str(state.get("comando", normalized_command)),
                    str(state.get("fase_actual", "")),
                ),
                "next_command": "/alfred-dev:resume",
                "headless_marker": f"{normalized_command.upper()}_HEADLESS_START",
                "artifacts": state.get("artefactos", []),
                "already_active": True,
                "bypass_path": arm_stop_hook_bypass(project_dir, f"/alfred-dev:{normalized_command}"),
            }
            if normalized_command == "audit":
                result["sonarqube_preflight"] = state.get("sonarqube_preflight") or _build_audit_sonarqube_preflight()
                result["headless_marker"] = result["sonarqube_preflight"].get("headless_marker", "AUDIT_HEADLESS_START")
            return result
        raise RuntimeError(
            "Ya existe una sesión activa. Usa /alfred-dev:next o /alfred-dev:resume antes de abrir otro flujo."
        )

    handoff = load_handoff(project_dir)
    if handoff and not handoff.get("resolved", False):
        raise RuntimeError(
            "Hay un handoff pendiente. Retómalo con /alfred-dev:resume antes de abrir otro flujo."
        )

    session = run_flow(normalized_command, description, project_dir=project_dir)
    session["origen"] = f"/alfred-dev:{normalized_command}"
    session["helper_first"] = True
    session["next_after_completion"] = "/alfred-dev:verify"

    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    os.makedirs(_project_path(project_dir, os.path.join("docs", "project")), exist_ok=True)
    bypass_path = arm_stop_hook_bypass(project_dir, f"/alfred-dev:{normalized_command}")

    pending_gate = get_pending_gate(session)
    phase = str(session.get("fase_actual", ""))
    phase_description = _first_phase_description(normalized_command, phase)
    sonarqube_preflight = (
        _build_audit_sonarqube_preflight()
        if normalized_command == "audit"
        else None
    )
    result = {
        "state_path": state_path,
        "command": normalized_command,
        "phase": phase,
        "description": session.get("descripcion", description),
        "pending_gate": pending_gate,
        "phase_description": phase_description,
        "next_command": "/alfred-dev:resume",
        "headless_marker": (
            sonarqube_preflight.get("headless_marker", "AUDIT_HEADLESS_START")
            if sonarqube_preflight
            else f"{normalized_command.upper()}_HEADLESS_START"
        ),
        "artifacts": [
            CURRENT_RELATIVE_PATH,
            PROGRESS_MD_RELATIVE_PATH,
            TRACEABILITY_MD_RELATIVE_PATH,
        ],
        "already_active": False,
        "bypass_path": bypass_path,
    }
    if sonarqube_preflight is not None:
        result["sonarqube_preflight"] = sonarqube_preflight
        session["sonarqube_preflight"] = sonarqube_preflight
        session["sonarqube_autorizado"] = sonarqube_preflight.get("sonarqube_autorizado", False)

    with open(_project_path(project_dir, CURRENT_RELATIVE_PATH), "w", encoding="utf-8") as fh:
        fh.write(render_flow_start_current_markdown(result))
    with open(_project_path(project_dir, PROGRESS_MD_RELATIVE_PATH), "w", encoding="utf-8") as fh:
        fh.write(render_flow_start_progress_markdown(result))
    with open(_project_path(project_dir, TRACEABILITY_MD_RELATIVE_PATH), "w", encoding="utf-8") as fh:
        fh.write(render_flow_start_traceability_markdown(result))

    active_task = _ensure_session_execution_task(project_dir, session)
    session["kanban_task_id"] = active_task.get("id", "")
    session["artefactos"] = result["artifacts"]
    save_state(session, state_path)

    _capture_helper_memory(
        project_dir,
        helper_name=normalized_command,
        phase=phase,
        event_summary=f"{normalized_command} preparado: {session['descripcion']}",
        event_content=(
            f"Flujo {normalized_command} activo para '{session['descripcion']}'. "
            f"Fase inicial: {phase}. Gate pendiente: {pending_gate}. "
            "No se completaron fases durante el helper-first."
        ),
        decision_title=f"Abrir flujo {normalized_command}: {session['descripcion']}",
        decision_choice=f"Sembrar estado y continuar con /alfred-dev:resume",
        decision_context=(
            "El comando necesita continuidad y gates verificables; en modo headless "
            "no debe intentar completar todo el flujo interactivo."
        ),
        decision_rationale=(
            "Arrancar el estado canónico evita bloqueos en claude -p y mantiene visible "
            "la primera gate pendiente para una sesión interactiva."
        ),
        tags=[normalized_command, "helper-first"],
        payload={
            "pending_gate": pending_gate,
            "artifacts": result["artifacts"],
            "next_command": result["next_command"],
        },
    )

    return result


def render_prefetch_response(payload: Dict[str, Any]) -> str:
    """Construye la respuesta final que puede devolver consume-prefetch."""
    source_command = payload.get("source_command", "")
    prefetched_command = payload.get("prefetched_command", "")

    if prefetched_command == "map-codebase":
        if source_command == "alfred":
            recommended = payload.get("recommended_command", "discuss")
            return (
                "## Ruta decidida: `/alfred-dev:map-codebase`\n\n"
                "- Detectado repo brownfield sin mapa persistente.\n"
                f"- Artefactos preparados: `{CODEBASE_MAP_RELATIVE_PATH}` y `{CURRENT_RELATIVE_PATH}`\n"
                f"- Siguiente comando recomendado: `/alfred-dev:{recommended}`\n"
            )
        return render_codebase_map_summary(payload)

    if prefetched_command == "discuss":
        return render_discovery_summary(payload)

    if prefetched_command == "quick":
        return render_quick_setup_summary(payload)

    if prefetched_command in _HELPER_FIRST_FLOW_COMMANDS:
        return render_flow_start_summary(payload)

    if prefetched_command == "lucius":
        return render_lucius_summary(payload)

    if prefetched_command == "memory-ui":
        return render_memory_ui_markdown(payload)

    return ""


def write_codebase_map_files(project_dir: str, raw_request: str = "") -> Dict[str, Any]:
    """Crea un mapa brownfield persistente para `/alfred-dev:map-codebase`."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    if state and state.get("fase_actual") != "completado":
        raise RuntimeError(
            "Ya existe una sesión activa. Usa /alfred-dev:next antes de volver a mapear el codebase."
        )

    handoff = load_handoff(project_dir)
    if handoff and not handoff.get("resolved", False):
        raise RuntimeError(
            "Hay un handoff pendiente. Usa /alfred-dev:resume antes de abrir /alfred-dev:map-codebase."
        )

    package_data = _load_package_json(project_dir)
    stack = detect_stack(project_dir)
    project_name = _detect_project_name(project_dir, package_data)
    focus_area = _normalize_request_description(raw_request, "") if raw_request else ""
    analysis = _summarize_tests_build_deploy(project_dir, package_data, stack)
    modules = _detect_primary_modules(project_dir)
    entrypoints = _detect_entrypoints(project_dir, package_data)
    risks = _infer_risks(project_dir, stack, analysis)

    existing_map = _read_text_if_exists(project_dir, CODEBASE_MAP_RELATIVE_PATH)
    existing_current = _read_text_if_exists(project_dir, CURRENT_RELATIVE_PATH)

    record = {
        "updated_at": _now_utc().isoformat(),
        "project_name": project_name,
        "focus_area": focus_area,
        "purpose": _extract_readme_summary(project_dir, project_name),
        "stack": stack,
        "stack_details": _describe_stack(stack),
        "entrypoints": entrypoints or ["No se detectan entrypoints claros; conviene revisar el código fuente principal."],
        "modules": modules or ["No se detectan módulos claros más allá de los ficheros de raíz."],
        "tests": analysis["tests"],
        "build": analysis["build"],
        "deploy": analysis["deploy"],
        "conventions": _infer_conventions(project_dir, stack, modules),
        "risks": risks,
        "recommended_command": "discuss" if focus_area else "alfred",
        "previous_notes": _extract_signal_lines(existing_map, max_items=3),
        "previous_current_notes": _extract_signal_lines(existing_current, max_items=3),
    }

    os.makedirs(_project_path(project_dir, os.path.join("docs", "project")), exist_ok=True)

    codebase_map_path = _project_path(project_dir, CODEBASE_MAP_RELATIVE_PATH)
    current_path = _project_path(project_dir, CURRENT_RELATIVE_PATH)

    with open(codebase_map_path, "w", encoding="utf-8") as fh:
        fh.write(render_codebase_map_markdown(record))

    with open(current_path, "w", encoding="utf-8") as fh:
        fh.write(render_codebase_current_markdown(record))

    stack_summary = ", ".join(record["stack_details"])
    seeded_artifacts = _seed_helper_operational_artifacts(
        project_dir,
        helper_name="map-codebase",
        progress_items=[
            "Mapa brownfield preparado y persistido para orientar el siguiente trabajo.",
            f"Stack detectado: {stack_summary}.",
            (
                f"Foco actual: {focus_area}."
                if focus_area
                else "Foco actual: mapa general del codebase."
            ),
            f"Siguiente paso recomendado: /alfred-dev:{record['recommended_command']}.",
        ],
        traceability_items=[
            "Todavía faltan criterios de aceptación concretos antes de implementar.",
            f"Riesgo principal a vigilar: {record['risks'][0]}",
            "Conviene revisar el mapa brownfield antes de abrir una ejecución larga.",
        ],
        backlog_items=[
            (
                f"Refinar '{focus_area}' con /alfred-dev:{record['recommended_command']}."
                if focus_area
                else "Revisar el mapa brownfield y decidir el flujo siguiente."
            ),
            f"Contrastar riesgos y convenciones en `{CODEBASE_MAP_RELATIVE_PATH}`.",
        ],
    )

    _capture_helper_memory(
        project_dir,
        helper_name="map-codebase",
        phase="brownfield",
        event_summary="Mapa brownfield preparado",
        event_content=(
            f"Proyecto '{project_name}' analizado. {stack_summary}. "
            f"Foco: {focus_area or 'general'}. "
            f"Siguiente comando recomendado: /alfred-dev:{record['recommended_command']}. "
            f"Artefactos: {CODEBASE_MAP_RELATIVE_PATH} y {CURRENT_RELATIVE_PATH}."
        ),
        decision_title="Arrancar por map-codebase antes de implementar",
        decision_choice=(
            f"Persistir `{CODEBASE_MAP_RELATIVE_PATH}` y `{CURRENT_RELATIVE_PATH}` "
            "como base operativa del repo."
        ),
        decision_context=(
            f"Repo brownfield '{project_name}' sin mapa persistente listo para guiar el siguiente trabajo."
        ),
        decision_rationale=(
            "Reducir cambios a ciegas en brownfield y dejar contexto reutilizable antes de refinar o implementar."
        ),
        tags=["brownfield", stack.get("runtime", "unknown"), stack.get("framework", "unknown")],
        payload={
            "recommended_command": record["recommended_command"],
            "focus_area": focus_area,
            "artifacts": [
                CODEBASE_MAP_RELATIVE_PATH,
                CURRENT_RELATIVE_PATH,
                *[os.path.relpath(path, project_dir) for path in seeded_artifacts],
            ],
        },
    )

    return {
        "codebase_map_path": codebase_map_path,
        "current_path": current_path,
        "seeded_artifacts": seeded_artifacts,
        "recommended_command": record["recommended_command"],
        "stack": stack,
        "project_name": project_name,
        "focus_area": focus_area,
    }


def get_pending_gate(session: Optional[Dict[str, Any]]) -> Optional[str]:
    """Devuelve la gate pendiente de la fase actual si existe."""
    if not session:
        return None

    command = session.get("comando")
    phase_name = session.get("fase_actual")
    phase_index = session.get("fase_numero")

    if (
        not isinstance(command, str)
        or not isinstance(phase_name, str)
        or not isinstance(phase_index, int)
        or phase_name == "completado"
    ):
        return None

    flow = FLOWS.get(command)
    if not flow:
        return None

    phases = flow.get("fases", [])
    if phase_index < 0 or phase_index >= len(phases):
        return None

    return phases[phase_index].get("gate_tipo")


def is_session_paused(session: Optional[Dict[str, Any]]) -> bool:
    """Indica si la sesión activa quedó pausada explícitamente."""
    if not session or not isinstance(session, dict):
        return False
    paused_at = session.get("paused_at")
    return isinstance(paused_at, str) and bool(paused_at.strip())


def _normalize_free_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower().strip()


def _last_completed_at(state: Dict[str, Any]) -> str:
    completed = state.get("fases_completadas") or []
    if completed and isinstance(completed[-1], dict):
        completed_at = completed[-1].get("completada_en")
        if isinstance(completed_at, str) and completed_at.strip():
            return completed_at

    for key in ("actualizado_en", "creado_en"):
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return _now_utc().isoformat()


def build_verification_target(project_dir: str) -> Optional[Dict[str, Any]]:
    """Resuelve el entregable actual susceptible de verificación manual."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    if state and state.get("fase_actual") != "completado":
        return {
            "blocked": True,
            "reason": (
                f"La sesión '{state.get('comando', 'desconocido')}' sigue activa "
                f"en la fase '{state.get('fase_actual', 'desconocida')}'."
            ),
            "command": state.get("comando", "desconocido"),
            "phase": state.get("fase_actual", "desconocida"),
        }

    if state and state.get("fase_actual") == "completado":
        completed_at = _last_completed_at(state)
        command = state.get("comando", "desconocido")
        description = state.get("descripcion", "")
        return {
            "blocked": False,
            "source": "completed-session",
            "target_id": f"session:{command}:{completed_at}",
            "target_command": command,
            "target_description": description,
            "target_completed_at": completed_at,
            "checklist": [
                "Levanta el proyecto o el entorno necesario para reproducir el cambio.",
                "Recorre el flujo principal que debía quedar listo y confirma el resultado esperado.",
                "Valida al menos un caso límite o de error relacionado con el cambio.",
                "Comprueba que no hay regresiones visibles en la zona tocada.",
            ],
        }

    current_md = _project_path(project_dir, CURRENT_RELATIVE_PATH)
    codebase_map = _project_path(project_dir, CODEBASE_MAP_RELATIVE_PATH)
    if os.path.isfile(current_md) or os.path.isfile(codebase_map):
        return {
            "blocked": False,
            "source": "project",
            "target_id": "project:current",
            "target_command": "project",
            "target_description": "Estado actual del proyecto",
            "target_completed_at": "",
            "checklist": [
                "Arranca la aplicación o el entorno principal del proyecto.",
                "Recorre el caso de uso que quieras aceptar manualmente.",
                "Anota cualquier desviación observable frente a lo esperado.",
                "Decide si el estado actual se puede dar por aceptado o necesita ajustes.",
            ],
        }

    return None


def _parse_verify_request(raw_request: str) -> Dict[str, str]:
    raw = (raw_request or "").strip()
    if not raw:
        return {"status": "", "notes": ""}

    parts = raw.split(None, 1)
    token = _normalize_free_text(parts[0])
    notes = parts[1].strip() if len(parts) > 1 else ""
    notes = notes.lstrip(":.- ").strip()

    approved = {"aprobado", "aprobar", "ok", "pass", "passed", "aceptado", "validado"}
    rejected = {"rechazado", "rechazar", "ko", "fail", "failed", "falla", "fallado"}
    pending = {"pendiente", "preparar", "prepare", "reset", "reabrir", "abrir"}

    if token in approved:
        return {"status": "approved", "notes": notes}
    if token in rejected:
        return {"status": "rejected", "notes": notes}
    if token in pending:
        return {"status": "pending", "notes": notes}
    return {"status": "", "notes": raw}


def _status_label(status: str) -> str:
    return {
        "pending": "pendiente",
        "approved": "aprobada",
        "rejected": "rechazada",
    }.get(status, status or "desconocido")


def _next_command_for_uat(status: str) -> str:
    if status == "approved":
        return "/alfred"
    if status == "rejected":
        return "/alfred"
    return "/alfred-dev:verify aprobado"


def _build_uat_record(
    target: Dict[str, Any],
    existing: Optional[Dict[str, Any]],
    requested_status: str,
    notes: str,
) -> Dict[str, Any]:
    now = _now_utc().isoformat()
    same_target = existing and existing.get("target_id") == target["target_id"]

    if requested_status:
        status = requested_status
    elif same_target and existing:
        status = existing.get("status", "pending")
    else:
        status = "pending"

    record = {
        "version": 1,
        "created_at": existing.get("created_at", now) if same_target and existing else now,
        "updated_at": now,
        "target_id": target["target_id"],
        "target_source": target["source"],
        "target_command": target["target_command"],
        "target_description": target["target_description"],
        "target_completed_at": target["target_completed_at"],
        "status": status,
        "checklist": target["checklist"],
        "notes": (
            notes if notes else (existing.get("notes", "") if same_target and existing else "")
        ),
        "next_command": _next_command_for_uat(status),
    }

    if status == "approved":
        record["approved_at"] = now
    elif same_target and existing and existing.get("approved_at") and not requested_status:
        record["approved_at"] = existing["approved_at"]

    if status == "rejected":
        record["rejected_at"] = now
    elif same_target and existing and existing.get("rejected_at") and not requested_status:
        record["rejected_at"] = existing["rejected_at"]

    return record


def render_uat_markdown(uat: Dict[str, Any]) -> str:
    """Renderiza el estado de verificación/UAT en Markdown."""
    checklist = "\n".join(f"- {item}" for item in (uat.get("checklist") or []))
    notes = uat.get("notes") or "Sin notas registradas."
    target_completed_at = uat.get("target_completed_at") or "No aplica"
    next_step = uat.get("next_command", "/alfred")

    if uat.get("status") == "pending":
        action = (
            "Ejecuta la validación manual y registra el resultado con "
            "`/alfred-dev:verify aprobado` o `/alfred-dev:verify rechazado <nota>`."
        )
    elif uat.get("status") == "approved":
        action = (
            "La validación manual ya está aprobada. Si toca seguir trabajando o "
            "preparar release, usa Alfred con el contexto actual."
        )
    else:
        action = (
            "La validación manual ha fallado. Usa Alfred para corregir los ajustes "
            "pendientes y vuelve a pasar `/alfred-dev:verify` cuando proceda."
        )

    return (
        "# Verificación manual / UAT\n\n"
        f"**Estado:** {_status_label(uat.get('status', ''))}\n"
        f"**Objetivo:** {uat.get('target_command', '-')}\n"
        f"**Descripción:** {uat.get('target_description', '-')}\n"
        f"**Referencia temporal:** {target_completed_at}\n"
        f"**Actualizado en:** {uat.get('updated_at', '-')}\n\n"
        "## Checklist de validación\n\n"
        f"{checklist}\n\n"
        "## Notas y hallazgos\n\n"
        f"{notes}\n\n"
        "## Siguiente paso\n\n"
        f"- Comando sugerido: `{next_step}`\n"
        f"- Acción: {action}\n"
    )


def write_uat_files(project_dir: str, raw_request: str = "") -> Dict[str, Any]:
    """Crea o actualiza los artefactos de verificación manual."""
    target = build_verification_target(project_dir)
    if target is None:
        raise RuntimeError(
            "No hay suficiente contexto para preparar una verificación manual todavía."
        )
    if target.get("blocked"):
        raise RuntimeError(target["reason"])

    existing = load_uat(project_dir)
    request = _parse_verify_request(raw_request)
    record = _build_uat_record(target, existing, request["status"], request["notes"])

    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    os.makedirs(_project_path(project_dir, os.path.join("docs", "project")), exist_ok=True)

    json_path = _project_path(project_dir, UAT_JSON_RELATIVE_PATH)
    markdown_path = _project_path(project_dir, UAT_MD_RELATIVE_PATH)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)

    with open(markdown_path, "w", encoding="utf-8") as fh:
        fh.write(render_uat_markdown(record))

    kanban_sync = _sync_kanban_after_verify(project_dir, target, record)
    if target.get("source") == "completed-session":
        state_path = _project_path(project_dir, STATE_RELATIVE_PATH)
        session = load_state(state_path)
        if (
            isinstance(session, dict)
            and session.get("fase_actual") == "completado"
            and record.get("target_id") == target.get("target_id")
        ):
            save_state(session, state_path)

    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
        "status": record["status"],
        "target_id": record["target_id"],
        "next_command": record["next_command"],
        **kanban_sync,
    }


def _build_next_action_payload(
    command: str,
    reason: str,
    source: str,
    *,
    focus: str,
    directive: str,
    urgency: str = "media",
) -> Dict[str, str]:
    return {
        "command": command,
        "reason": reason,
        "source": source,
        "source_label": _NEXT_ACTION_SOURCE_LABELS.get(source, source or "desconocida"),
        "focus": focus,
        "directive": directive,
        "urgency": urgency,
    }


def suggest_verify_action(project_dir: str) -> Optional[Dict[str, str]]:
    """Sugiere verify cuando el último flujo completado aún no tiene UAT aprobada."""
    target = build_verification_target(project_dir)
    if not target or target.get("blocked") or target.get("source") != "completed-session":
        return None

    uat = load_uat(project_dir)
    if not uat or uat.get("target_id") != target["target_id"]:
        return _build_next_action_payload(
            "verify",
            (
                "El último flujo completado todavía no tiene una verificación "
                "manual/UAT registrada."
            ),
            "verify",
            focus="Cerrar la verificación pendiente",
            directive=(
                "Prepara o registra la UAT del último entregable antes de abrir "
                "otro flujo nuevo."
            ),
            urgency="alta",
        )

    if uat.get("status") == "pending":
        return _build_next_action_payload(
            "verify",
            "La verificación manual/UAT del último flujo completado sigue pendiente.",
            "verify",
            focus="Cerrar la verificación pendiente",
            directive=(
                "Completa o actualiza la UAT pendiente antes de continuar con un "
                "nuevo ciclo de trabajo."
            ),
            urgency="alta",
        )

    return None


def suggest_next_action(project_dir: str) -> Dict[str, str]:
    """Sugiere el siguiente comando operativo con una prioridad estable."""
    state = _load_active_session_state(project_dir)
    if state is not None:
        command = state.get("comando", "desconocido")
        phase = state.get("fase_actual", "desconocida")
        return _build_next_action_payload(
            "resume",
            f"Hay una sesión activa de '{command}' en la fase '{phase}'.",
            "state",
            focus="Retomar el flujo en curso",
            directive=(
                f"Reanuda `{command}` en `{phase}` y trabaja sobre la gate pendiente "
                "sin abrir otro flujo."
            ),
            urgency="alta",
        )

    handoff = load_handoff(project_dir)
    if handoff and not handoff.get("resolved", False):
        return _build_next_action_payload(
            "resume",
            (
                f"Existe un handoff pendiente para '{handoff['command']}' "
                f"en la fase '{handoff['phase']}'."
            ),
            "handoff",
            focus="Recuperar el handoff pendiente",
            directive=(
                f"Retoma `{handoff['command']}` desde `{handoff['phase']}` con "
                f"`{handoff.get('resume_command', '/alfred-dev:resume')}`."
            ),
            urgency="alta",
        )

    verify_suggestion = suggest_verify_action(project_dir)
    if verify_suggestion is not None:
        return verify_suggestion

    if needs_codebase_map(project_dir):
        return _build_next_action_payload(
            "map-codebase",
            (
                "El proyecto ya tiene código, pero todavía no existe un mapa "
                "persistente del codebase en docs/project/."
            ),
            "brownfield",
            focus="Mapear el codebase brownfield",
            directive=(
                "Genera el mapa brownfield antes de abrir un flujo nuevo para que "
                "el contexto operativo quede persistido."
            ),
            urgency="alta",
        )

    discovery_md = _read_text_if_exists(project_dir, DISCOVERY_MD_RELATIVE_PATH)
    discovery_command = _extract_recommended_alfred_command(discovery_md)
    if discovery_command is not None:
        return _build_next_action_payload(
            discovery_command,
            (
                "Existe un refinado previo en docs/project/discovery.md "
                f"que recomienda continuar con '{discovery_command}'."
            ),
            "discovery",
            focus="Seguir la recomendación del discovery",
            directive=(
                f"Continúa con `/alfred-dev:{discovery_command}` usando el refinado "
                "persistido como base operativa."
            ),
            urgency="media",
        )

    current_md = _read_text_if_exists(project_dir, CURRENT_RELATIVE_PATH)
    current_command = _extract_recommended_alfred_command(current_md)
    if current_command is not None:
        return _build_next_action_payload(
            current_command,
            (
                "Existe un estado operativo en docs/project/current.md "
                f"que recomienda continuar con '{current_command}'."
            ),
            "current",
            focus="Seguir el estado operativo persistido",
            directive=(
                f"Continúa con `/alfred-dev:{current_command}` apoyándote en "
                "`docs/project/current.md` y los artefactos ya sembrados."
            ),
            urgency="media",
        )

    if project_has_codebase(project_dir):
        return _build_next_action_payload(
            _GREENFIELD_COMMAND,
            (
                "No hay sesión activa. Alfred puede dirigir el siguiente flujo "
                "usando el contexto ya existente del proyecto."
            ),
            "project",
            focus="Elegir el siguiente flujo razonable",
            directive=(
                "Abre `/alfred` para decidir el siguiente flujo sobre el "
                "contexto ya existente del proyecto."
            ),
            urgency="media",
        )

    return _build_next_action_payload(
        _GREENFIELD_COMMAND,
        (
            "No hay trabajo en curso ni un codebase brownfield claro. "
            "Conviene empezar por el asistente contextual."
        ),
        "default",
        focus="Arrancar el contexto de trabajo",
        directive=(
            "Empieza por `/alfred` para elegir el flujo correcto y "
            "sembrar el contexto inicial."
        ),
        urgency="media",
    )


def render_next_markdown(suggestion: Dict[str, str]) -> str:
    lines = [
        "## Siguiente paso operativo",
        "",
        f"- Foco: {suggestion.get('focus', 'Siguiente paso recomendado')}",
        (
            f"- Fuente: {suggestion.get('source_label', suggestion.get('source', 'desconocida'))} "
            f"(`{suggestion.get('source', 'desconocida')}`)"
        ),
        f"- Comando: `/alfred-dev:{suggestion.get('command', 'alfred')}`",
        (
            "- Qué hacer ahora: "
            + suggestion.get(
                "directive",
                "Avanza con el siguiente comando recomendado.",
            )
        ),
        f"- Motivo: {suggestion.get('reason', 'Sin razón disponible.')}",
    ]
    return "\n".join(lines).strip() + "\n"


def build_progress_snapshot(
    project_dir: str,
    *,
    arm_bypass: bool = False,
    source_command: str = "/alfred-dev:progress",
) -> Dict[str, Any]:
    """Construye un resumen operativo a partir de artefactos de SonIA y continuidad."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    handoff = load_handoff(project_dir)
    uat = load_uat(project_dir)
    has_active_state = bool(
        state
        and state.get("fase_actual") != "completado"
        and not is_session_paused(state)
    )
    has_paused_state = bool(
        state
        and state.get("fase_actual") != "completado"
        and is_session_paused(state)
    )

    progress_md = _read_text_if_exists(project_dir, PROGRESS_MD_RELATIVE_PATH)
    traceability_md = _read_text_if_exists(project_dir, TRACEABILITY_MD_RELATIVE_PATH)
    current_md = _read_text_if_exists(project_dir, CURRENT_RELATIVE_PATH)
    board = load_kanban_board(project_dir)
    visible_board = _filter_kanban_board_tasks(board, _is_visible_kanban_task)
    type_counts = _count_kanban_task_types(board)

    backlog_items = [_task_reference(task) for task in visible_board.get("backlog", [])]
    in_progress_items = [_task_reference(task) for task in visible_board.get("in-progress", [])]
    done_items = [_task_reference(task) for task in visible_board.get("done", [])]
    blocked_items = [_task_reference(task) for task in visible_board.get("blocked", [])]

    total_items = (
        len(backlog_items)
        + len(in_progress_items)
        + len(done_items)
        + len(blocked_items)
    )
    progress_pct = round((len(done_items) / total_items) * 100) if total_items else None

    next_action = suggest_next_action(project_dir)
    progress_signals = _extract_signal_lines(progress_md)
    current_signals = _extract_signal_lines(current_md, max_items=2)
    traceability_signals = _extract_signal_lines(traceability_md)

    if not current_signals:
        current_signals = [
            item
            for item in [
                (
                    f"Flujo activo: `{state.get('comando', 'desconocido')}` en "
                    f"`{state.get('fase_actual', 'desconocida')}`."
                    if has_active_state
                    else ""
                ),
                (
                    f"Handoff pendiente para `{handoff.get('command', 'desconocido')}` "
                    f"en `{handoff.get('phase', 'desconocida')}`."
                    if handoff and not handoff.get("resolved", False)
                    else ""
                ),
                (
                    f"Sesión pausada: `{state.get('comando', 'desconocido')}` en "
                    f"`{state.get('fase_actual', 'desconocida')}`."
                    if has_paused_state and not (handoff and not handoff.get("resolved", False))
                    else ""
                ),
                f"Siguiente paso sugerido: `/alfred-dev:{next_action.get('command', 'alfred')}`.",
            ]
            if item
        ]

    if not progress_signals:
        progress_signals = [
            item
            for item in [
                (
                    f"Kanban actual: {len(done_items)} done, {len(in_progress_items)} in progress, "
                    f"{len(backlog_items)} backlog, {len(blocked_items)} blocked."
                ),
                (
                    f"Tareas internas de coordinación: {type_counts['internal']} "
                    f"(fase: {type_counts['phase']}, verify: {type_counts['verify']})."
                    if type_counts["internal"]
                    else ""
                ),
                (
                    f"Progreso estimado: {progress_pct} %."
                    if progress_pct is not None
                    else "Todavía no hay suficientes señales para estimar progreso."
                ),
                next_action.get("reason", ""),
            ]
            if item
        ]

    if not traceability_signals:
        traceability_signals = [
            item
            for item in [
                (
                    f"UAT actual: {_status_label(uat.get('status', ''))}."
                    if uat
                    else "Todavía no hay UAT registrada."
                ),
                (
                    "La trazabilidad crecerá cuando Alfred deje decisiones enlazadas, criterios o "
                    "`docs/project/traceability.md`."
                ),
            ]
            if item
        ]

    bypass_path = None
    if arm_bypass and state and state.get("fase_actual") != "completado":
        bypass_path = arm_stop_hook_bypass(project_dir, source_command)

    kanban_payload = {
        "backlog": backlog_items,
        "in_progress": in_progress_items,
        "done": done_items,
        "blocked": blocked_items,
        "total": total_items,
        "progress_pct": progress_pct,
        "internal_total": type_counts["internal"],
        "phase_total": type_counts["phase"],
        "verify_total": type_counts["verify"],
    }
    overview_cards = _build_progress_overview_cards(
        state,
        handoff,
        uat,
        next_action,
    )

    return {
        "state": state,
        "handoff": handoff,
        "uat": uat,
        "overview_cards": overview_cards,
        "progress_signals": progress_signals,
        "current_signals": current_signals,
        "traceability_signals": traceability_signals,
        "project_signal_cards": _build_project_signal_cards(
            state,
            current_signals,
            progress_signals,
            traceability_signals,
            kanban_payload,
            overview_cards=overview_cards,
        ),
        "kanban": kanban_payload,
        "next_action": next_action,
        "bypass_path": bypass_path,
    }


def _extend_next_action_section(
    lines: List[str],
    next_action: Dict[str, str],
    *,
    heading: str = "### Siguiente paso recomendado",
) -> None:
    lines.extend(
        [
            "",
            heading,
            "",
            f"- Foco: {next_action.get('focus', 'Siguiente paso recomendado')}",
            (
                f"- Fuente: {next_action.get('source_label', next_action.get('source', 'desconocida'))} "
                f"(`{next_action.get('source', 'desconocida')}`)"
            ),
            f"- Comando: `/alfred-dev:{next_action.get('command', 'alfred')}`",
            (
                "- Qué hacer ahora: "
                + next_action.get(
                    "directive",
                    "Avanza con el siguiente comando recomendado.",
                )
            ),
            f"- Motivo: {next_action.get('reason', 'Sin razón disponible.')}",
        ]
    )


def build_status_snapshot(
    project_dir: str,
    *,
    arm_bypass: bool = False,
    source_command: str = "/alfred-dev:status",
) -> Dict[str, Any]:
    snapshot = build_progress_snapshot(project_dir, arm_bypass=False)
    state = snapshot.get("state")
    board = load_kanban_board(project_dir)
    uat = snapshot.get("uat")
    phase_rows = _build_phase_doc_rows(state, board) if isinstance(state, dict) else []
    artifacts = (
        _dedupe_artifact_paths(list((state or {}).get("artefactos") or []))
        if isinstance(state, dict)
        else []
    )
    bypass_path = None
    if (
        arm_bypass
        and isinstance(state, dict)
        and state.get("fase_actual") != "completado"
    ):
        bypass_path = arm_stop_hook_bypass(project_dir, source_command)

    return {
        **snapshot,
        "phase_rows": phase_rows,
        "artifacts": artifacts,
        "session_status_label": (
            _session_status_label(state, uat)
            if isinstance(state, dict)
            else "sin sesión activa"
        ),
        "team_source": (
            _session_team_source_label(state)
            if isinstance(state, dict)
            else ""
        ),
        "pending_gate": (
            get_pending_gate(state)
            if isinstance(state, dict) and state.get("fase_actual") != "completado"
            else ""
        ),
        "bypass_path": bypass_path,
    }


def render_status_markdown(snapshot: Dict[str, Any]) -> str:
    state = snapshot.get("state")
    handoff = snapshot.get("handoff")
    uat = snapshot.get("uat")
    kanban = snapshot.get("kanban", {})
    phase_rows = snapshot.get("phase_rows", [])
    next_action = snapshot.get("next_action", {"command": "alfred", "reason": ""})
    team_source = snapshot.get("team_source", "")
    pending_gate = snapshot.get("pending_gate", "")
    artifacts = snapshot.get("artifacts", [])

    lines = ["## Estado operativo de Alfred Dev", ""]

    if isinstance(state, dict):
        lines.extend(
            [
                "### Sesión",
                "",
                f"- Flujo: `{state.get('comando', 'desconocido')}`",
                f"- Descripción: {state.get('descripcion', 'Sin descripción')}",
                f"- Estado: {snapshot.get('session_status_label', 'desconocido')}",
            ]
        )
        if state.get("fase_actual") != "completado":
            lines.append(f"- Fase actual: `{state.get('fase_actual', 'desconocida')}`")
        if pending_gate:
            lines.append(f"- Gate pendiente: `{pending_gate}`")
        if team_source:
            lines.append(f"- Origen del equipo runtime: {team_source}.")
        if handoff and not handoff.get("resolved", False):
            lines.append(
                f"- Handoff pendiente: reanudar con `{handoff.get('resume_command', '/alfred-dev:resume')}` desde `{handoff.get('phase', 'desconocida')}`."
            )
        on_demand_optionals = _session_on_demand_optionals_for_flow(state)
        if on_demand_optionals:
            lines.append(
                "- Opcionales solo bajo demanda: "
                + ", ".join(f"`{agent}`" for agent in on_demand_optionals)
                + "."
            )
    elif handoff and not handoff.get("resolved", False):
        lines.extend(
            [
                "### Handoff",
                "",
                f"- Flujo pendiente: `{handoff.get('command', 'desconocido')}`",
                f"- Fase: `{handoff.get('phase', 'desconocida')}`",
                f"- Reanudar con: `{handoff.get('resume_command', '/alfred-dev:resume')}`",
            ]
        )
    else:
        lines.extend(
            [
                "### Sesión",
                "",
                "No hay sesión activa ni handoff pendiente visible.",
            ]
        )

    lines.extend(
        [
            "",
            "### Proyecto",
            "",
            f"- Kanban visible: {len(kanban.get('done', []))} done, {len(kanban.get('in_progress', []))} in progress, {len(kanban.get('backlog', []))} backlog, {len(kanban.get('blocked', []))} blocked.",
        ]
    )
    if kanban.get("internal_total"):
        lines.append(
            f"- Tareas internas: {kanban['internal_total']} (fase: {kanban.get('phase_total', 0)}, verify: {kanban.get('verify_total', 0)})."
        )
    if kanban.get("progress_pct") is not None:
        lines.append(f"- Progreso visible estimado: {kanban['progress_pct']} %.")
    if artifacts:
        lines.append(f"- Artefactos acumulados en la sesión: {len(artifacts)}.")
    if uat:
        lines.append(f"- UAT: {_status_label(uat.get('status', ''))}.")

    if phase_rows:
        lines.extend(["", "### Fases registradas", ""])
        for row in phase_rows:
            summary = f"- `{row['name']}` -> `{row['status']}` · gate `{row['gate']}`"
            if row["iterations"] > 0:
                summary += f" · iteraciones {row['iterations']}"
            if row["artifacts"]:
                summary += f" · artefactos {len(row['artifacts'])}"
            lines.append(summary)

    project_signal_cards = snapshot.get("project_signal_cards") or []
    if project_signal_cards:
        lines.extend(["", "### Señales operativas", ""])
        for card in project_signal_cards[:3]:
            lines.append(f"#### {card.get('title', 'Señal')}")
            lines.append("")
            if card.get("description"):
                lines.append(f"- {card.get('description')}")
            for item in (card.get("items") or [])[:2]:
                lines.append(f"- {item}")
            lines.append("")

    _extend_next_action_section(lines, next_action)
    return "\n".join(lines).strip() + "\n"


def render_progress_markdown(snapshot: Dict[str, Any]) -> str:
    """Renderiza un resumen operativo breve para `/alfred-dev:progress`."""
    state = snapshot.get("state")
    handoff = snapshot.get("handoff")
    uat = snapshot.get("uat")
    kanban = snapshot.get("kanban", {})
    next_action = snapshot.get("next_action", {"command": "alfred", "reason": ""})

    lines = ["## Resumen operativo del proyecto", ""]

    if state and state.get("fase_actual") != "completado" and not is_session_paused(state):
        lines.extend(
            [
                "### Flujo activo",
                "",
                f"- Flujo: `{state.get('comando', 'desconocido')}`",
                f"- Descripción: {state.get('descripcion', 'Sin descripción')}",
                f"- Fase actual: `{state.get('fase_actual', 'desconocida')}`",
            ]
        )
    elif handoff and not handoff.get("resolved", False):
        lines.extend(
            [
                "### Handoff pendiente",
                "",
                f"- Flujo: `{handoff.get('command', 'desconocido')}`",
                f"- Fase: `{handoff.get('phase', 'desconocida')}`",
                f"- Siguiente paso: `{handoff.get('resume_command', '/alfred-dev:resume')}`",
            ]
        )
    elif state and state.get("fase_actual") != "completado" and is_session_paused(state):
        lines.extend(
            [
                "### Sesión pausada",
                "",
                f"- Flujo: `{state.get('comando', 'desconocido')}`",
                f"- Descripción: {state.get('descripcion', 'Sin descripción')}",
                f"- Fase pausada: `{state.get('fase_actual', 'desconocida')}`",
                "- Falta un handoff visible; conviene regenerarlo con `/alfred-dev:pause` o retomar con `/alfred-dev:resume`.",
            ]
        )
    else:
        lines.extend(
            [
                "### Flujo activo",
                "",
                "No hay sesión activa de Alfred, ni handoff pendiente, ni trabajo en curso detectado.",
            ]
        )

    lines.extend(["", "### Kanban", ""])
    lines.extend(
        [
            f"- Done: {len(kanban.get('done', []))}",
            f"- In progress: {len(kanban.get('in_progress', []))}",
            f"- Backlog: {len(kanban.get('backlog', []))}",
            f"- Blocked: {len(kanban.get('blocked', []))}",
        ]
    )
    if kanban.get("internal_total"):
        lines.append(
            f"- Internas: {kanban['internal_total']} "
            f"(fase: {kanban.get('phase_total', 0)}, verify: {kanban.get('verify_total', 0)})"
        )
    if kanban.get("progress_pct") is not None:
        lines.append(f"- Progreso estimado: {kanban['progress_pct']} %")

    progress_signals = snapshot.get("progress_signals") or snapshot.get("current_signals") or []
    if progress_signals:
        lines.extend(["", "### Notas de progreso", ""])
        lines.extend(f"- {item}" for item in progress_signals)

    traceability_signals = snapshot.get("traceability_signals") or []
    if traceability_signals:
        lines.extend(["", "### Trazabilidad", ""])
        lines.extend(f"- {item}" for item in traceability_signals)

    if uat:
        lines.extend(["", "### UAT", ""])
        lines.extend(
            [
                f"- Estado: {_status_label(uat.get('status', ''))}",
                f"- Objetivo: `{uat.get('target_command', 'desconocido')}`",
            ]
        )
        notes = uat.get("notes")
        if notes:
            lines.append(f"- Nota principal: {notes}")

    _extend_next_action_section(lines, next_action)

    return "\n".join(lines).strip() + "\n"


def _infer_primary_actor(description: str) -> str:
    normalized = _normalize_free_text(description)
    if "onboarding" in normalized and "desarroll" in normalized:
        return "desarrollador o colaborador técnico"
    if "onboarding" in normalized or "registro" in normalized or "primer acceso" in normalized:
        return "usuario nuevo"
    if "admin" in normalized or "administr" in normalized:
        return "administrador"
    if "equipo" in normalized or "operacion" in normalized:
        return "equipo interno"
    return "actor principal por confirmar"


def _infer_recommended_command(description: str) -> str:
    normalized = _normalize_free_text(description)

    if any(token in normalized for token in ("bug", "error", "fallo", "regresion", "arreglar", "corregir")):
        return "fix"
    if any(token in normalized for token in ("investig", "compar", "benchmark", "poc", "viable", "explorar")):
        return "spike"
    if any(
        token in normalized
        for token in ("copy", "texto", "ajuste pequeno", "ajuste menor", "cambio pequeno", "tooltip")
    ):
        return "quick"
    return "feature"


def _build_scope_items(description: str, recommended_command: str) -> List[str]:
    base_items = [
        f"Clarificar el flujo principal asociado a: {description}.",
        "Definir qué pasos y estados visibles forman parte del alcance inicial.",
        "Acordar criterios de éxito observables antes de abrir implementación.",
    ]
    if recommended_command == "quick":
        base_items.append("Mantener el cambio acotado para poder ejecutarlo en quick mode.")
    elif recommended_command == "fix":
        base_items.append("Aislar el comportamiento roto y la expectativa correcta antes de corregirlo.")
    elif recommended_command == "spike":
        base_items.append("Cerrar primero las incógnitas técnicas o de enfoque antes de comprometer desarrollo.")
    else:
        base_items.append("Preparar una base lo bastante clara como para abrir PRD e implementación completa.")
    return base_items


def render_discovery_markdown(record: Dict[str, Any]) -> str:
    """Renderiza un refinado ligero y reutilizable para discuss."""
    scope = "\n".join(f"- {item}" for item in record["scope_items"])
    out_of_scope = "\n".join(f"- {item}" for item in record["out_of_scope"])
    decisions = "\n".join(f"- {item}" for item in record["decisions"])
    assumptions = "\n".join(f"- {item}" for item in record["assumptions"])
    open_questions = "\n".join(f"- {item}" for item in record["open_questions"])
    risks = "\n".join(f"- {item}" for item in record["risks"])

    return (
        "# Discovery / Refinado previo\n\n"
        f"**Actualizado en:** {record['updated_at']}\n"
        f"**Petición origen:** {record['description']}\n\n"
        "## Problema y objetivo\n\n"
        f"{record['problem_and_goal']}\n\n"
        "## Actor principal\n\n"
        f"{record['actor']}\n\n"
        "## Alcance propuesto\n\n"
        f"{scope}\n\n"
        "## Fuera de alcance\n\n"
        f"{out_of_scope}\n\n"
        "## Decisiones ya tomadas\n\n"
        f"{decisions}\n\n"
        "## Supuestos\n\n"
        f"{assumptions}\n\n"
        "## Preguntas abiertas\n\n"
        f"{open_questions}\n\n"
        "## Riesgos o puntos delicados\n\n"
        f"{risks}\n\n"
        "## Comando recomendado\n\n"
        f"/alfred-dev:{record['recommended_command']}\n"
    )


def render_discovery_current_markdown(record: Dict[str, Any]) -> str:
    """Resume en current.md el resultado operativo del refinado ligero."""
    return (
        "# Current\n\n"
        f"- Estado: refinado previo preparado para `{record['recommended_command']}`.\n"
        f"- Foco actual: {record['description']}.\n"
        f"- Actor principal: {record['actor']}.\n"
        f"- Qué falta: validar supuestos y cerrar preguntas abiertas en `docs/project/discovery.md`.\n"
        f"- Siguiente comando recomendado: /alfred-dev:{record['recommended_command']}\n"
    )


def render_quick_current_markdown(record: Dict[str, Any]) -> str:
    """Resume en current.md la sesión activa de quick."""
    warning_line = ""
    if record.get("needs_codebase_map"):
        warning_line = (
            f"- Atención: el repo parece brownfield; revisa `{CODEBASE_MAP_RELATIVE_PATH}` "
            "si el cambio deja de ser pequeño.\n"
        )
    return (
        "# Current\n\n"
        f"- Estado: quick activo para `{record['description']}`.\n"
        f"- Fase actual: `{record['phase']}`.\n"
        "- Qué está listo: Alfred ya ha sembrado la sesión rápida y el contexto mínimo para continuar.\n"
        f"{warning_line}"
        "- Qué falta: ejecutar el cambio acotado, validarlo y cerrar con `/alfred-dev:verify`.\n"
        "- Siguiente comando recomendado: /alfred-dev:resume\n"
    )


def render_quick_progress_markdown(record: Dict[str, Any]) -> str:
    """Deja una señal humana mínima para progress y la UI."""
    guardrail = "Mantener el alcance pequeño y no convertirlo en un feature completo."
    if record.get("needs_codebase_map"):
        guardrail = (
            "Cambio clasificado como quick, pero con aviso brownfield: si el alcance crece, "
            "conviene volver a map-codebase antes de seguir."
        )
    return (
        "# Progress\n\n"
        "- Flujo activo: `quick`.\n"
        f"- Cambio acotado en curso: {record['description']}.\n"
        f"- Guardrail principal: {guardrail}\n"
        "- Cierre esperado: `/alfred-dev:verify` tras implementar y comprobar el cambio.\n"
    )


def write_discovery_files(project_dir: str, raw_request: str = "") -> Dict[str, Any]:
    """Crea un refinado ligero reutilizable para /alfred-dev:discuss."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    if state and state.get("fase_actual") != "completado":
        raise RuntimeError(
            "Ya existe una sesión activa. Usa /alfred-dev:next antes de abrir discuss."
        )

    handoff = load_handoff(project_dir)
    if handoff and not handoff.get("resolved", False):
        raise RuntimeError(
            "Hay un handoff pendiente. Usa /alfred-dev:resume antes de abrir discuss."
        )

    description = _normalize_request_description(raw_request, "Siguiente trabajo a refinar")
    actor = _infer_primary_actor(description)
    recommended_command = _infer_recommended_command(description)
    now = _now_utc().isoformat()

    record = {
        "version": 1,
        "updated_at": now,
        "description": description,
        "actor": actor,
        "recommended_command": recommended_command,
        "problem_and_goal": (
            f"Necesitamos aterrizar '{description}' antes de abrir implementación, "
            "para convertir una intención todavía difusa en un trabajo ejecutable y verificable."
        ),
        "scope_items": _build_scope_items(description, recommended_command),
        "out_of_scope": [
            "Diseño técnico detallado o arquitectura final.",
            "Implementación de código o despliegue.",
            "Cambios no relacionados con el flujo principal descrito.",
        ],
        "decisions": [
            "Se documenta primero el refinado en discovery.md antes de abrir trabajo de implementación.",
            f"El siguiente flujo sugerido tras este refinado es `/alfred-dev:{recommended_command}`.",
        ],
        "assumptions": [
            "El mapa brownfield actual sigue siendo válido como contexto técnico base.",
            "Si aparecen detalles menores no críticos, Alfred puede continuar con supuestos razonables.",
        ],
        "open_questions": [
            "Qué criterio de éxito marcaría que este trabajo ha quedado realmente resuelto.",
            "Qué edge case o restricción de negocio no puede quedarse fuera del primer alcance.",
        ],
        "risks": [
            "Arrancar implementación sin cerrar alcance puede generar retrabajo o UX inconsistente.",
            "Si el actor principal está mal identificado, el flujo refinado puede desviarse del problema real.",
        ],
    }

    os.makedirs(_project_path(project_dir, os.path.join("docs", "project")), exist_ok=True)

    discovery_path = _project_path(project_dir, DISCOVERY_MD_RELATIVE_PATH)
    current_path = _project_path(project_dir, CURRENT_RELATIVE_PATH)

    with open(discovery_path, "w", encoding="utf-8") as fh:
        fh.write(render_discovery_markdown(record))

    with open(current_path, "w", encoding="utf-8") as fh:
        fh.write(render_discovery_current_markdown(record))

    seeded_artifacts = _seed_helper_operational_artifacts(
        project_dir,
        helper_name="discuss",
        progress_items=[
            f"Refinado previo listo para abrir /alfred-dev:{recommended_command}.",
            f"Objetivo aterrizado: {description}.",
            f"Actor principal: {actor}.",
        ],
        traceability_items=[
            f"Quedan preguntas abiertas por cerrar antes de ejecutar /alfred-dev:{recommended_command}.",
            f"Principal riesgo del refinado: {record['risks'][0]}",
            "Los criterios y edge cases deberán confirmarse durante implementación y UAT.",
        ],
        backlog_items=[
            f"Abrir /alfred-dev:{recommended_command} para '{description}'.",
            "Cerrar las preguntas abiertas de docs/project/discovery.md.",
        ],
    )

    _capture_helper_memory(
        project_dir,
        helper_name="discuss",
        phase="discovery",
        event_summary=f"Refinado preparado para /alfred-dev:{recommended_command}",
        event_content=(
            f"Refinado previo listo para '{description}'. Actor principal: {actor}. "
            f"Siguiente comando recomendado: /alfred-dev:{recommended_command}. "
            f"Artefactos actualizados: {DISCOVERY_MD_RELATIVE_PATH} y {CURRENT_RELATIVE_PATH}."
        ),
        decision_title=f"Refinar antes de implementar: {description}",
        decision_choice=f"Preparar discovery.md y continuar con /alfred-dev:{recommended_command}",
        decision_context=(
            "La petición todavía necesitaba aclarar alcance, actor principal y preguntas abiertas "
            "antes de abrir implementación."
        ),
        decision_rationale=(
            "Cerrar el refinado primero reduce retrabajo y mejora el handoff hacia el flujo de ejecución adecuado."
        ),
        tags=["discovery", recommended_command],
        payload={
            "recommended_command": recommended_command,
            "actor": actor,
            "artifacts": [
                DISCOVERY_MD_RELATIVE_PATH,
                CURRENT_RELATIVE_PATH,
                *[os.path.relpath(path, project_dir) for path in seeded_artifacts],
            ],
        },
    )

    return {
        "discovery_path": discovery_path,
        "current_path": current_path,
        "seeded_artifacts": seeded_artifacts,
        "recommended_command": recommended_command,
        "actor": actor,
        "description": description,
        "scope_items": record["scope_items"],
        "open_questions": record["open_questions"],
        "risks": record["risks"],
    }


def start_quick_session(project_dir: str, raw_request: str = "") -> Dict[str, Any]:
    """Crea una sesión ligera para quick mode y devuelve su contexto básico."""
    state_path = _project_path(project_dir, STATE_RELATIVE_PATH)
    state = load_state(state_path)
    description = _normalize_request_description(
        raw_request,
        "Cambio rápido acotado",
    )
    if state and state.get("fase_actual") != "completado":
        if state.get("comando") == "quick" and state.get("descripcion") == description:
            return {
                "state_path": state_path,
                "command": state["comando"],
                "phase": state["fase_actual"],
                "description": state["descripcion"],
                "needs_codebase_map": needs_codebase_map(project_dir),
                "next_command": state.get("next_after_completion", "/alfred-dev:verify"),
                "bypass_path": arm_stop_hook_bypass(project_dir, "/alfred-dev:quick"),
            }
        raise RuntimeError(
            "Ya existe una sesión activa. Usa /alfred-dev:next o /alfred-dev:resume antes de abrir quick."
        )

    handoff = load_handoff(project_dir)
    if handoff and not handoff.get("resolved", False):
        raise RuntimeError(
            "Hay un handoff pendiente. Retómalo con /alfred-dev:resume antes de abrir quick."
        )

    verify_suggestion = suggest_verify_action(project_dir)
    if verify_suggestion is not None:
        raise RuntimeError(
            "Todavía hay una verificación manual/UAT pendiente. Usa /alfred-dev:verify antes de abrir quick."
        )

    session = run_flow("quick", description, project_dir=project_dir)
    session["modo_rapido"] = True
    session["origen"] = "/alfred-dev:quick"
    session["next_after_completion"] = "/alfred-dev:verify"
    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    bypass_path = arm_stop_hook_bypass(project_dir, "/alfred-dev:quick")
    os.makedirs(_project_path(project_dir, os.path.join("docs", "project")), exist_ok=True)

    quick_record = {
        "description": session["descripcion"],
        "phase": session["fase_actual"],
        "needs_codebase_map": needs_codebase_map(project_dir),
    }
    with open(_project_path(project_dir, CURRENT_RELATIVE_PATH), "w", encoding="utf-8") as fh:
        fh.write(render_quick_current_markdown(quick_record))
    with open(_project_path(project_dir, PROGRESS_MD_RELATIVE_PATH), "w", encoding="utf-8") as fh:
        fh.write(render_quick_progress_markdown(quick_record))

    seeded_artifacts = _seed_helper_operational_artifacts(
        project_dir,
        helper_name="quick",
        traceability_items=[
            "El cambio quick debe seguir siendo acotado y verificable manualmente.",
            (
                "Si el alcance crece o afecta varias zonas, conviene volver a map-codebase."
                if quick_record["needs_codebase_map"]
                else "Si aparecen dependencias nuevas, conviene promocionarlo a feature o fix."
            ),
        ],
    )

    active_task = _ensure_session_execution_task(project_dir, session)
    verify_task = _ensure_verification_task(
        project_dir,
        description=session["descripcion"],
        command=session["comando"],
    )
    session["kanban_task_id"] = active_task.get("id", "")
    session["kanban_verify_task_id"] = verify_task.get("id", "")
    save_state(session, state_path)

    _capture_helper_memory(
        project_dir,
        helper_name="quick",
        phase=session["fase_actual"],
        event_summary=f"Quick preparado: {session['descripcion']}",
        event_content=(
            f"Quick activo para '{session['descripcion']}'. "
            f"Siguiente cierre esperado: {session['next_after_completion']}. "
            f"Artefactos actualizados: {CURRENT_RELATIVE_PATH} y {PROGRESS_MD_RELATIVE_PATH}."
        ),
        decision_title=f"Clasificar como quick: {session['descripcion']}",
        decision_choice=f"Resolverlo con /alfred-dev:quick y cerrar con {session['next_after_completion']}",
        decision_context=(
            "Se trata como cambio acotado, sin abrir un feature completo, salvo que el alcance crezca."
        ),
        decision_rationale=(
            "Mantener el trabajo pequeño, verificable y con el mínimo ceremonial sin perder trazabilidad."
        ),
        tags=["quick", "execution"],
        payload={
            "next_command": session["next_after_completion"],
            "needs_codebase_map": quick_record["needs_codebase_map"],
            "artifacts": [
                CURRENT_RELATIVE_PATH,
                PROGRESS_MD_RELATIVE_PATH,
                os.path.relpath(_project_path(project_dir, KANBAN_IN_PROGRESS_RELATIVE_PATH), project_dir),
                os.path.relpath(_project_path(project_dir, KANBAN_BACKLOG_RELATIVE_PATH), project_dir),
                *[os.path.relpath(path, project_dir) for path in seeded_artifacts],
            ],
        },
    )

    return {
        "state_path": state_path,
        "command": session["comando"],
        "phase": session["fase_actual"],
        "description": session["descripcion"],
        "needs_codebase_map": quick_record["needs_codebase_map"],
        "next_command": session["next_after_completion"],
        "bypass_path": bypass_path,
        "seeded_artifacts": seeded_artifacts,
        "kanban_task_id": session["kanban_task_id"],
        "kanban_verify_task_id": session["kanban_verify_task_id"],
    }


def build_handoff(project_dir: str) -> Optional[Dict[str, Any]]:
    """Construye un handoff a partir del estado de sesión activo."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    if not state or state.get("fase_actual") == "completado":
        return None

    gate = get_pending_gate(state)
    completed = [phase.get("nombre", "desconocida") for phase in state.get("fases_completadas", [])]

    return {
        "version": 1,
        "created_at": _now_utc().isoformat(),
        "command": state.get("comando", "desconocido"),
        "description": state.get("descripcion", ""),
        "phase": state.get("fase_actual", "desconocida"),
        "phase_number": state.get("fase_numero", 0) + 1,
        "completed_phases": completed,
        "pending_gate": gate,
        "artifacts": state.get("artefactos", []),
        "resume_command": "/alfred-dev:resume",
        "next_step": (
            f"Retomar '{state.get('comando', 'desconocido')}' "
            f"desde la fase '{state.get('fase_actual', 'desconocida')}'."
        ),
        "resolved": False,
    }


def mark_session_paused(project_dir: str) -> Optional[Dict[str, Any]]:
    """Marca la sesión activa como pausada sin cerrarla."""
    state_path = _project_path(project_dir, STATE_RELATIVE_PATH)
    state = _load_active_session_state(project_dir)
    if state is None:
        return None

    state["paused_at"] = _now_utc().isoformat()
    state["paused_via"] = "/alfred-dev:pause"
    save_state(state, state_path)
    return state


def clear_session_paused(project_dir: str) -> Optional[Dict[str, Any]]:
    """Elimina la marca de pausa al retomar trabajo."""
    state_path = _project_path(project_dir, STATE_RELATIVE_PATH)
    state = _load_active_session_state(project_dir)
    if state is None:
        return None

    state.pop("paused_at", None)
    state.pop("paused_via", None)
    state["resumed_at"] = _now_utc().isoformat()
    save_state(state, state_path)
    return state


def resolve_handoff(project_dir: str) -> Optional[Dict[str, Any]]:
    """Marca el handoff existente como resuelto."""
    handoff = load_handoff(project_dir)
    if not handoff:
        return None

    handoff["resolved"] = True
    handoff["resolved_at"] = _now_utc().isoformat()
    save_handoff(project_dir, handoff)
    return handoff


def load_stop_hook_bypass(project_dir: str) -> Optional[Dict[str, Any]]:
    """Carga el bypass transitorio del stop hook si existe."""
    bypass_path = _project_path(project_dir, STOP_BYPASS_RELATIVE_PATH)
    try:
        with open(bypass_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    required = {"command", "created_at", "expires_at"}
    if not required.issubset(data.keys()):
        return None

    return data


def clear_stop_hook_bypass(project_dir: str) -> None:
    """Elimina el bypass transitorio del stop hook si existe."""
    bypass_path = _project_path(project_dir, STOP_BYPASS_RELATIVE_PATH)
    try:
        os.remove(bypass_path)
    except FileNotFoundError:
        return
    except OSError:
        return


def load_prefetch_result(project_dir: str) -> Optional[Dict[str, Any]]:
    """Carga el prefetch helper-first si existe y tiene estructura válida."""
    prefetch_path = _project_path(project_dir, PREFETCH_RELATIVE_PATH)
    try:
        with open(prefetch_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        clear_prefetch_result(project_dir)
        return None

    if not isinstance(data, dict):
        clear_prefetch_result(project_dir)
        return None

    required = {"source_command", "prefetched_command", "response_text", "created_at", "expires_at"}
    if not required.issubset(data.keys()):
        clear_prefetch_result(project_dir)
        return None

    expires_at_raw = data.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(expires_at_raw)
    except (TypeError, ValueError):
        clear_prefetch_result(project_dir)
        return None

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= _now_utc():
        clear_prefetch_result(project_dir)
        return None

    return data


def clear_prefetch_result(project_dir: str) -> None:
    """Elimina el artefacto transitorio de prefetch helper-first."""
    prefetch_path = _project_path(project_dir, PREFETCH_RELATIVE_PATH)
    try:
        os.remove(prefetch_path)
    except FileNotFoundError:
        return
    except OSError:
        return


def load_prefetch_consumed_marker(project_dir: str) -> Optional[Dict[str, Any]]:
    """Carga la barrera temporal que sigue a un consume-prefetch exitoso."""
    marker_path = _project_path(project_dir, PREFETCH_CONSUMED_RELATIVE_PATH)
    try:
        with open(marker_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        clear_prefetch_consumed_marker(project_dir)
        return None

    if not isinstance(data, dict):
        clear_prefetch_consumed_marker(project_dir)
        return None

    required = {"source_command", "prefetched_command", "created_at", "expires_at"}
    if not required.issubset(data.keys()):
        clear_prefetch_consumed_marker(project_dir)
        return None

    expires_at_raw = data.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(expires_at_raw)
    except (TypeError, ValueError):
        clear_prefetch_consumed_marker(project_dir)
        return None

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= _now_utc():
        clear_prefetch_consumed_marker(project_dir)
        return None

    return data


def clear_prefetch_consumed_marker(project_dir: str) -> None:
    """Limpia el marcador que evita deriva después del helper-first."""
    marker_path = _project_path(project_dir, PREFETCH_CONSUMED_RELATIVE_PATH)
    try:
        os.remove(marker_path)
    except FileNotFoundError:
        return
    except OSError:
        return


def save_prefetch_consumed_marker(
    project_dir: str,
    payload: Dict[str, Any],
    ttl_seconds: int = 45,
) -> str:
    """Persiste una barrera corta tras consumir el prefetch helper-first."""
    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    now = _now_utc()
    stored = {
        "source_command": str(payload.get("source_command", "")).strip().lower(),
        "prefetched_command": str(payload.get("prefetched_command", "")).strip().lower(),
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=max(ttl_seconds, 5))).isoformat(),
    }

    marker_path = _project_path(project_dir, PREFETCH_CONSUMED_RELATIVE_PATH)
    with open(marker_path, "w", encoding="utf-8") as fh:
        json.dump(stored, fh, indent=2, ensure_ascii=False)
    return marker_path


def save_prefetch_result(
    project_dir: str,
    payload: Dict[str, Any],
    ttl_seconds: int = 180,
) -> Optional[str]:
    """Persiste un prefetch reciente para que el comando pueda consumirlo."""
    source_command = payload.get("source_command")
    prefetched_command = payload.get("prefetched_command")
    response_text = render_prefetch_response(payload)

    if not isinstance(source_command, str) or not source_command.strip():
        return None
    if not isinstance(prefetched_command, str) or not prefetched_command.strip():
        return None
    if not response_text.strip():
        return None

    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    now = _now_utc()
    stored = dict(payload)
    stored["created_at"] = now.isoformat()
    stored["expires_at"] = (now + timedelta(seconds=ttl_seconds)).isoformat()
    stored["response_text"] = response_text

    prefetch_path = _project_path(project_dir, PREFETCH_RELATIVE_PATH)
    with open(prefetch_path, "w", encoding="utf-8") as fh:
        json.dump(stored, fh, indent=2, ensure_ascii=False)
    return prefetch_path


def _prefetch_is_stale_for_current_context(
    project_dir: str,
    payload: Dict[str, Any],
    expected_command: str,
) -> bool:
    """Detecta si un prefetch helper-first ha quedado obsoleto."""
    expected = (expected_command or "").strip().lower()
    if expected == "memory-ui":
        return False

    active_state = _load_active_session_state(project_dir)
    handoff = load_handoff(project_dir)
    has_unresolved_handoff = bool(handoff and not handoff.get("resolved", False))

    if expected in {"map-codebase", "discuss"}:
        return active_state is not None or has_unresolved_handoff

    if expected == "alfred":
        next_action = suggest_next_action(project_dir)
        return str(next_action.get("source", "")).strip().lower() in {
            "state",
            "handoff",
            "verify",
        }

    return False


def consume_prefetch_result(project_dir: str, expected_command: str) -> Optional[Dict[str, Any]]:
    """Devuelve y consume un prefetch reciente si aplica al comando actual."""
    payload = load_prefetch_result(project_dir)
    if payload is None:
        return None

    expires_at_raw = payload.get("expires_at")
    try:
        expires_at = datetime.fromisoformat(expires_at_raw)
    except (TypeError, ValueError):
        clear_prefetch_result(project_dir)
        return None

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= _now_utc():
        clear_prefetch_result(project_dir)
        return None

    expected = (expected_command or "").strip().lower()
    source_command = str(payload.get("source_command", "")).strip().lower()
    prefetched_command = str(payload.get("prefetched_command", "")).strip().lower()

    if expected and expected not in {source_command, prefetched_command}:
        return None

    if _prefetch_is_stale_for_current_context(project_dir, payload, expected):
        clear_prefetch_result(project_dir)
        return None

    save_prefetch_consumed_marker(project_dir, payload)
    clear_prefetch_result(project_dir)
    return payload


def arm_stop_hook_bypass(
    project_dir: str,
    command: str,
    ttl_seconds: int = 120,
) -> str:
    """Autoriza una sola parada inmediata tras comandos de continuidad."""
    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    now = _now_utc()
    payload = {
        "version": 1,
        "command": command,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
    }
    bypass_path = _project_path(project_dir, STOP_BYPASS_RELATIVE_PATH)
    with open(bypass_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return bypass_path


def render_handoff_markdown(handoff: Dict[str, Any]) -> str:
    """Renderiza el handoff en Markdown legible."""
    completed = handoff.get("completed_phases") or []
    artifacts = handoff.get("artifacts") or []
    completed_text = ", ".join(completed) if completed else "ninguna"
    artifact_lines = "\n".join(f"- `{item}`" for item in artifacts) if artifacts else "- Ninguno"
    gate = handoff.get("pending_gate") or "sin gate pendiente detectada"

    return (
        "# Handoff de Alfred Dev\n\n"
        f"**Fecha:** {handoff.get('created_at', '-')}\n"
        f"**Flujo:** {handoff.get('command', '-')}\n"
        f"**Descripción:** {handoff.get('description', '-')}\n"
        f"**Fase actual:** {handoff.get('phase', '-')} (#{handoff.get('phase_number', '-')})\n"
        f"**Gate pendiente:** {gate}\n\n"
        "## Fases completadas\n\n"
        f"{completed_text}\n\n"
        "## Artefactos registrados\n\n"
        f"{artifact_lines}\n\n"
        "## Próximo paso\n\n"
        f"- Comando de retorno: `{handoff.get('resume_command', '/alfred-dev:resume')}`\n"
        f"- Acción sugerida: {handoff.get('next_step', '-')}\n"
    )


def render_pause_markdown(result: Dict[str, Any]) -> str:
    """Renderiza una pausa helper-first en formato humano."""
    gate = result.get("pending_gate") or "sin gate pendiente detectada"
    next_step = result.get("next_step") or "Retomar la sesión con `/alfred-dev:resume`."
    return (
        "## Sesión pausada\n\n"
        f"- Flujo: `{result.get('command', '-')}`\n"
        f"- Descripción: `{result.get('description', '-')}`\n"
        f"- Fase actual: `{result.get('phase', '-')}`\n"
        f"- Gate pendiente: {gate}\n"
        f"- Handoff guardado en: `{HANDOFF_JSON_RELATIVE_PATH}` y `{HANDOFF_MD_RELATIVE_PATH}`\n"
        f"- Estado actualizado en: `{STATE_RELATIVE_PATH}`\n"
        f"- Comando de retorno: `/alfred-dev:resume`\n"
        f"- Siguiente acción: {next_step}\n"
    )


def render_resume_markdown(result: Dict[str, Any]) -> str:
    """Renderiza una reanudación helper-first en formato humano."""
    gate = result.get("pending_gate") or "sin gate pendiente detectada"
    next_step = result.get("next_step") or "Consulta `/alfred-dev:next` para seguir."
    handoff_note = (
        f"- Handoff resuelto: `{HANDOFF_JSON_RELATIVE_PATH}`\n"
        if result.get("handoff_path")
        else ""
    )
    return (
        "## Sesión reanudada\n\n"
        f"- Flujo: `{result.get('command', '-')}`\n"
        f"- Descripción: `{result.get('description', '-')}`\n"
        f"- Fase actual: `{result.get('phase', '-')}`\n"
        f"- Gate pendiente: {gate}\n"
        f"{handoff_note}"
        f"- Estado activo: `{STATE_RELATIVE_PATH}`\n"
        f"- Siguiente acción: {next_step}\n"
    )


def write_handoff_files(project_dir: str) -> Optional[Dict[str, str]]:
    """Escribe el handoff en JSON y Markdown. Devuelve sus rutas."""
    handoff = build_handoff(project_dir)
    if handoff is None:
        return None

    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    os.makedirs(_project_path(project_dir, os.path.join("docs", "project")), exist_ok=True)

    handoff_md_path = _project_path(project_dir, HANDOFF_MD_RELATIVE_PATH)

    handoff_json_path = save_handoff(project_dir, handoff)
    with open(handoff_md_path, "w", encoding="utf-8") as fh:
        fh.write(render_handoff_markdown(handoff))

    return {
        "json_path": handoff_json_path,
        "markdown_path": handoff_md_path,
    }


def pause_session(project_dir: str) -> Optional[Dict[str, str]]:
    """Genera handoff y marca la sesión como pausada."""
    handoff_paths = write_handoff_files(project_dir)
    if handoff_paths is None:
        return None

    state = mark_session_paused(project_dir)
    if state is None:
        return None

    handoff = load_handoff(project_dir) or {}

    return {
        **handoff_paths,
        "state_path": _project_path(project_dir, STATE_RELATIVE_PATH),
        "paused_at": state["paused_at"],
        "command": handoff.get("command", state.get("comando", "")),
        "description": handoff.get("description", state.get("descripcion", "")),
        "phase": handoff.get("phase", state.get("fase_actual", "")),
        "pending_gate": handoff.get("pending_gate", ""),
        "next_step": handoff.get("next_step", ""),
    }


def resume_session(project_dir: str) -> Optional[Dict[str, str]]:
    """Quita la marca de pausa y resuelve el handoff si existe."""
    state_path = _project_path(project_dir, STATE_RELATIVE_PATH)
    state = _load_active_session_state(project_dir)
    handoff = load_handoff(project_dir)
    active_handoff = handoff is not None and not handoff.get("resolved", False)

    if state is None and not active_handoff:
        return None

    resumed_at = _now_utc().isoformat()
    result: Dict[str, str] = {
        "resumed_at": resumed_at,
    }

    if state is not None:
        result["command"] = state.get("comando", "")
        result["description"] = state.get("descripcion", "")
        result["phase"] = state.get("fase_actual", "")
        result["pending_gate"] = get_pending_gate(state)
        result["next_step"] = (
            f"Retomar '{state.get('comando', 'flujo')}' desde la fase "
            f"'{state.get('fase_actual', 'desconocida')}'."
        )
    elif active_handoff and handoff is not None:
        result["command"] = handoff.get("command", "")
        result["description"] = handoff.get("description", "")
        result["phase"] = handoff.get("phase", "")
        result["pending_gate"] = handoff.get("pending_gate", "")
        result["next_step"] = handoff.get(
            "next_step",
            f"Retomar con {handoff.get('resume_command', '/alfred-dev:resume')}.",
        )

    if state is not None:
        state.pop("paused_at", None)
        state.pop("paused_via", None)
        state["resumed_at"] = resumed_at
        if state.get("kanban_task_id") or state.get("comando") == "quick":
            synced_task = _ensure_session_execution_task(project_dir, state)
            state["kanban_task_id"] = synced_task.get("id", "")
        save_state(state, state_path)
        result["state_path"] = state_path

    if active_handoff:
        handoff["resolved"] = True
        handoff["resolved_at"] = resumed_at
        save_handoff(project_dir, handoff)
        result["handoff_path"] = _project_path(project_dir, HANDOFF_JSON_RELATIVE_PATH)

    bypass_path = arm_stop_hook_bypass(project_dir, "/alfred-dev:resume")
    result["bypass_path"] = bypass_path
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Herramientas de continuidad de Alfred Dev")
    subparsers = parser.add_subparsers(dest="command", required=True)

    next_parser = subparsers.add_parser("next", help="Sugiere el siguiente comando")
    next_parser.add_argument("project_dir", nargs="?", default=".")
    next_parser.add_argument("--json", action="store_true", dest="as_json")

    handoff_parser = subparsers.add_parser("write-handoff", help="Escribe el handoff actual")
    handoff_parser.add_argument("project_dir", nargs="?", default=".")

    pause_parser = subparsers.add_parser("pause", help="Genera el handoff y marca la sesión como pausada")
    pause_parser.add_argument("project_dir", nargs="?", default=".")
    pause_parser.add_argument("--json", action="store_true", dest="as_json")

    resume_parser = subparsers.add_parser("resume", help="Quita la marca de pausa y resuelve el handoff")
    resume_parser.add_argument("project_dir", nargs="?", default=".")
    resume_parser.add_argument("--json", action="store_true", dest="as_json")

    verify_parser = subparsers.add_parser(
        "verify",
        help="Crea o actualiza la verificación manual/UAT",
    )
    verify_parser.add_argument("project_dir", nargs="?", default=".")
    verify_parser.add_argument("--json", action="store_true", dest="as_json")
    verify_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Argumento libre recibido desde /alfred-dev:verify",
    )

    progress_parser = subparsers.add_parser(
        "progress",
        help="Resume progreso, kanban, bloqueos y trazabilidad",
    )
    progress_parser.add_argument("project_dir", nargs="?", default=".")
    progress_parser.add_argument("--json", action="store_true", dest="as_json")

    status_parser = subparsers.add_parser(
        "status",
        help="Resume el estado operativo de la sesión y del proyecto",
    )
    status_parser.add_argument("project_dir", nargs="?", default=".")
    status_parser.add_argument("--json", action="store_true", dest="as_json")

    standup_parser = subparsers.add_parser(
        "standup",
        help="Genera un standup operativo breve desde SonIA",
    )
    standup_parser.add_argument("project_dir", nargs="?", default=".")

    blocked_parser = subparsers.add_parser(
        "blocked",
        help="Lista las tareas bloqueadas",
    )
    blocked_parser.add_argument("project_dir", nargs="?", default=".")

    in_progress_parser = subparsers.add_parser(
        "in-progress",
        help="Lista las tareas en curso",
    )
    in_progress_parser.add_argument("project_dir", nargs="?", default=".")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Valida la integridad operativa de SonIA y continuidad",
    )
    validate_parser.add_argument("project_dir", nargs="?", default=".")

    normalize_parser = subparsers.add_parser(
        "normalize-kanban",
        help="Normaliza tipos de tareas en tableros heredados de SonIA",
    )
    normalize_parser.add_argument("project_dir", nargs="?", default=".")
    normalize_parser.add_argument("--json", action="store_true", dest="as_json")

    search_parser = subparsers.add_parser(
        "search",
        help="Busca en artefactos de SonIA y memoria SQLite",
    )
    search_parser.add_argument("project_dir", nargs="?", default=".")
    search_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Texto de búsqueda recibido desde /alfred-dev:search",
    )

    sync_parser = subparsers.add_parser(
        "sync-github",
        help="Ejecuta SonIA Sync sobre GitHub Issues",
    )
    sync_parser.add_argument("project_dir", nargs="?", default=".")
    sync_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="owner/repo opcional recibido desde /alfred-dev:sync-github",
    )

    memory_ui_parser = subparsers.add_parser(
        "memory-ui",
        help="Arranca la UI local de memoria y la abre en el navegador",
    )
    memory_ui_parser.add_argument("project_dir", nargs="?", default=".")
    memory_ui_parser.add_argument("--json", action="store_true", dest="as_json")
    memory_ui_parser.add_argument("--no-open", action="store_true", dest="no_open")
    memory_ui_parser.add_argument("--stop", action="store_true", dest="stop")

    map_parser = subparsers.add_parser(
        "map-codebase",
        help="Crea un mapa brownfield persistente",
    )
    map_parser.add_argument("project_dir", nargs="?", default=".")
    map_parser.add_argument("--json", action="store_true", dest="as_json")
    map_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Área o foco opcional recibido desde /alfred-dev:map-codebase",
    )

    discuss_parser = subparsers.add_parser(
        "discuss",
        help="Prepara un refinado ligero para /alfred-dev:discuss",
    )
    discuss_parser.add_argument("project_dir", nargs="?", default=".")
    discuss_parser.add_argument("--json", action="store_true", dest="as_json")
    discuss_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Argumento libre recibido desde /alfred-dev:discuss",
    )

    quick_parser = subparsers.add_parser(
        "quick",
        help="Crea una sesión ligera para /alfred-dev:quick",
    )
    quick_parser.add_argument("project_dir", nargs="?", default=".")
    quick_parser.add_argument("--json", action="store_true", dest="as_json")
    quick_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Argumento libre recibido desde /alfred-dev:quick",
    )

    lucius_parser = subparsers.add_parser(
        "lucius",
        help="Prepara una revisión Lucius sin ejecutar Codex CLI",
    )
    lucius_parser.add_argument("project_dir", nargs="?", default=".")
    lucius_parser.add_argument("--json", action="store_true", dest="as_json")
    lucius_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Argumentos recibidos desde /alfred-dev:lucius",
    )

    start_flow_parser = subparsers.add_parser(
        "start-flow",
        help="Crea la sesión inicial de un flujo largo sin ejecutar sus fases",
    )
    start_flow_parser.add_argument("project_dir", nargs="?", default=".")
    start_flow_parser.add_argument("--json", action="store_true", dest="as_json")
    start_flow_parser.add_argument(
        "--command",
        required=True,
        choices=sorted(_HELPER_FIRST_FLOW_COMMANDS),
        dest="flow_command",
        help="Flujo a preparar: feature, fix, spike, ship o audit",
    )
    start_flow_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Argumento libre recibido desde el slash command",
    )

    consume_prefetch_parser = subparsers.add_parser(
        "consume-prefetch",
        help="Consume un prefetch helper-first reciente",
    )
    consume_prefetch_parser.add_argument("project_dir", nargs="?", default=".")
    consume_prefetch_parser.add_argument(
        "--expected",
        required=True,
        dest="expected_command",
        help="Comando que espera consumir el prefetch",
    )

    allow_stop_parser = subparsers.add_parser(
        "allow-stop-once",
        help="Permite una parada inmediata del stop hook",
    )
    allow_stop_parser.add_argument("project_dir", nargs="?", default=".")
    allow_stop_parser.add_argument(
        "--command",
        default="/alfred-dev:next",
        dest="source_command",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    project_dir = os.path.abspath(args.project_dir)

    if args.command == "next":
        suggestion = suggest_next_action(project_dir)
        if args.as_json:
            print(json.dumps(suggestion, ensure_ascii=False))
        else:
            print(render_next_markdown(suggestion))
        return 0

    if args.command == "write-handoff":
        result = write_handoff_files(project_dir)
        if result is None:
            print("No hay sesión activa para generar handoff.", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "pause":
        result = pause_session(project_dir)
        if result is None:
            print("No hay sesión activa para pausar.", file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_pause_markdown(result))
        return 0

    if args.command == "resume":
        result = resume_session(project_dir)
        if result is None:
            print("No hay sesión pausada o activa para reanudar.", file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_resume_markdown(result))
        return 0

    if args.command == "verify":
        try:
            result = write_uat_files(project_dir, raw_request=args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            uat = load_uat(project_dir)
            if uat is None:
                print(json.dumps(result, ensure_ascii=False))
            else:
                print(render_uat_markdown(uat))
        return 0

    if args.command == "progress":
        snapshot = build_progress_snapshot(
            project_dir,
            arm_bypass=True,
            source_command="/alfred-dev:progress",
        )
        if args.as_json:
            print(json.dumps(snapshot, ensure_ascii=False))
        else:
            print(render_progress_markdown(snapshot))
        return 0

    if args.command == "status":
        snapshot = build_status_snapshot(
            project_dir,
            arm_bypass=True,
            source_command="/alfred-dev:status",
        )
        if args.as_json:
            print(json.dumps(snapshot, ensure_ascii=False))
        else:
            print(render_status_markdown(snapshot))
        return 0

    if args.command == "standup":
        print(render_standup_markdown(build_standup_snapshot(project_dir)))
        return 0

    if args.command == "blocked":
        print(render_lane_markdown(build_lane_snapshot(project_dir, "blocked")))
        return 0

    if args.command == "in-progress":
        print(render_lane_markdown(build_lane_snapshot(project_dir, "in-progress")))
        return 0

    if args.command == "validate":
        print(render_validation_markdown(validate_operational_artifacts(project_dir)))
        return 0

    if args.command == "normalize-kanban":
        result = normalize_kanban_task_types(project_dir)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_normalize_kanban_markdown(result))
        return 0

    if args.command == "search":
        try:
            results = search_project_context(project_dir, args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(render_search_markdown(results))
        return 0

    if args.command == "sync-github":
        try:
            result = sync_project_to_github(project_dir, raw_request=args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(render_github_sync_cli_summary(result))
        return 0

    if args.command == "memory-ui":
        try:
            if args.stop:
                result = stop_memory_ui(project_dir)
            else:
                result = launch_memory_ui(
                    project_dir,
                    open_browser_window=not args.no_open,
                )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            if args.stop:
                if result.get("stopped"):
                    print(
                        "## Memory UI detenida\n\n"
                        f"- PID: {result.get('pid', 'desconocido')}\n"
                        f"- URL previa: {result.get('url', 'desconocida')}\n"
                    )
                else:
                    print("La Memory UI no estaba en ejecución.\n")
            else:
                print(render_memory_ui_markdown(result))
        return 0

    if args.command == "map-codebase":
        try:
            result = write_codebase_map_files(project_dir, raw_request=args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_codebase_map_summary(result))
        return 0

    if args.command == "discuss":
        try:
            result = write_discovery_files(project_dir, raw_request=args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_discovery_summary(result))
        return 0

    if args.command == "quick":
        try:
            result = start_quick_session(project_dir, raw_request=args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_quick_setup_summary(result))
        return 0

    if args.command == "lucius":
        result = prepare_lucius_review(project_dir, raw_request=args.raw_request)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_lucius_summary(result))
        return 0

    if args.command == "start-flow":
        try:
            result = start_flow_session(
                project_dir,
                command=args.flow_command,
                raw_request=args.raw_request,
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(render_flow_start_summary(result))
        return 0

    if args.command == "consume-prefetch":
        payload = consume_prefetch_result(project_dir, args.expected_command)
        if payload is None:
            return 1
        print(payload.get("response_text", ""))
        return 0

    if args.command == "allow-stop-once":
        bypass_path = arm_stop_hook_bypass(project_dir, args.source_command)
        print(
            json.dumps(
                {
                    "bypass_path": bypass_path,
                    "command": args.source_command,
                },
                ensure_ascii=False,
            )
        )
        return 0

    parser.error("Comando no soportado")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
