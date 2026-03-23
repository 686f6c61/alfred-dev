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
from core.orchestrator import FLOWS, create_session, load_state, save_state


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
_GH_STATUS_LABELS = {
    "backlog": "alfred:backlog",
    "in-progress": "alfred:in-progress",
    "done": "alfred:done",
    "blocked": "alfred:blocked",
}
_GH_SYNC_LABEL = "alfred:sync"
_GH_LEGACY_BOARD_LABEL = "alfred:board"


def _project_path(project_dir: str, relative_path: str) -> str:
    return os.path.join(project_dir, relative_path)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


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
    current_md = _project_path(project_dir, CURRENT_RELATIVE_PATH)
    return not (os.path.isfile(codebase_map) and os.path.isfile(current_md))


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

        current.update(
            {
                "body": body,
                "criteria": criteria,
                "dependencies": dependencies,
                "evidence": evidence,
                "agent": agent,
                "notes": notes,
                "status": status,
                "path": relative_path,
            }
        )
        current.pop("body_lines", None)
        tasks.append(current)
        current = None

    heading_re = re.compile(r"^###\s+(?:\[(?P<id>[^\]]+)\]\s+)?(?P<title>.+?)\s*$")
    metadata_re = re.compile(r"^- \*\*(?P<key>.+?):\*\*\s*(?P<value>.+?)\s*$")

    for raw_line in markdown.splitlines():
        heading = heading_re.match(raw_line.strip())
        if heading:
            flush()
            current = {
                "id": (heading.group("id") or "").strip(),
                "title": heading.group("title").strip(),
                "metadata": {},
                "body_lines": [],
            }
            continue

        if current is None:
            continue

        current["body_lines"].append(raw_line.rstrip())
        metadata = metadata_re.match(raw_line.strip())
        if metadata:
            key = _normalize_free_text(metadata.group("key")).replace(" ", "_")
            current["metadata"][key] = _clean_inline_markdown(metadata.group("value"))

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


def _summarize_tasks(tasks: List[Dict[str, Any]], limit: int = 3) -> List[str]:
    lines: List[str] = []
    for task in sorted(tasks, key=_task_sort_key)[:limit]:
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


def build_standup_snapshot(project_dir: str) -> Dict[str, Any]:
    snapshot = build_progress_snapshot(project_dir)
    board = load_kanban_board(project_dir)
    snapshot["standup_date"] = _now_utc().date().isoformat()
    snapshot["board_tasks"] = board
    snapshot["focus"] = {
        "in_progress": _summarize_tasks(board.get("in-progress", [])),
        "blocked": _summarize_tasks(board.get("blocked", [])),
        "done": _summarize_tasks(board.get("done", [])),
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

    lines.extend(
        [
            "",
            "### Siguiente paso",
            "",
            f"- `/alfred-dev:{next_action.get('command', 'alfred')}`",
            f"- {next_action.get('reason', 'Sin razón disponible.')}",
        ]
    )
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
    lines.extend(
        [
            "### Siguiente paso recomendado",
            "",
            f"- `/alfred-dev:{next_action.get('command', 'alfred')}`",
            f"- {next_action.get('reason', 'Sin razón disponible.')}",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def validate_operational_artifacts(project_dir: str) -> Dict[str, Any]:
    board = load_kanban_board(project_dir)
    tasks = [task for lane in board.values() for task in lane]
    errors: List[str] = []
    warnings: List[str] = []
    checks: List[str] = []

    if not tasks:
        warnings.append("No hay tareas detectadas en docs/project/kanban/.")
    else:
        checks.append(f"Se han detectado {len(tasks)} tareas en el kanban.")

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

        if task["status"] in {"in-progress", "blocked"} and not task.get("agent"):
            warnings.append(f"{_task_reference(task)} no tiene agente responsable visible.")
        if task["status"] == "blocked" and not (task.get("dependencies") or task.get("notes")):
            warnings.append(
                f"{_task_reference(task)} está bloqueada, pero no indica dependencia ni motivo."
            )
        if task["status"] == "done" and not task.get("evidence"):
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
        for task in tasks
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

    uat = load_uat(project_dir)
    verify_suggestion = suggest_verify_action(project_dir)
    if uat:
        checks.append(f"Existe UAT en estado '{_status_label(uat.get('status', ''))}'.")
    elif verify_suggestion is not None:
        warnings.append("La verificación/UAT del último flujo completado sigue pendiente.")

    sync_state = _read_json_file(_project_path(project_dir, GITHUB_SYNC_JSON_RELATIVE_PATH))
    if isinstance(sync_state, dict):
        task_map = sync_state.get("tasks")
        mapped = task_map if isinstance(task_map, dict) else {}
        sync_missing = [
            task.get("id")
            for task in tasks
            if task.get("id") and task.get("id") not in mapped
        ]
        if sync_missing:
            warnings.append(
                "Hay tareas no sincronizadas con GitHub: " + ", ".join(sync_missing[:5])
            )
        else:
            checks.append("El mapa de sincronización con GitHub cubre todas las tareas con ID.")

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
    lines = [f"## Validación operativa — {verdict}", ""]

    if report.get("checks"):
        lines.extend(["### Checks", ""])
        lines.extend(f"- {item}" for item in report["checks"])

    if report.get("warnings"):
        lines.extend(["", "### Avisos", ""])
        lines.extend(f"- {item}" for item in report["warnings"])

    if report.get("errors"):
        lines.extend(["", "### Errores", ""])
        lines.extend(f"- {item}" for item in report["errors"])

    lines.extend(
        [
            "",
            "### Siguiente paso recomendado",
            "",
            f"- `/alfred-dev:{next_action.get('command', 'alfred')}`",
            f"- {next_action.get('reason', 'Sin razón disponible.')}",
        ]
    )
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


def _is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _is_memory_ui_reachable(url: str, timeout: float = 0.35) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/api/healthz", timeout=timeout) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            return bool(payload.get("ok"))
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
        if url and _is_process_alive(pid) and _is_memory_ui_reachable(url):
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
        if _is_memory_ui_reachable(url):
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
    if _is_process_alive(pid):
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
    if isinstance(issue_number, int):
        issue = _get_issue(repo, issue_number)
    if issue is None:
        issue = _find_issue_by_title(repo, desired_title, "alfred:task")

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
    }


def _board_issue_body(
    project_name: str,
    repo: str,
    tasks: List[Dict[str, Any]],
    task_map: Dict[str, Dict[str, Any]],
    next_action: Dict[str, str],
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
        f"- Siguiente paso recomendado: `/alfred-dev:{next_action.get('command', 'alfred')}`",
        f"- Motivo: {next_action.get('reason', 'Sin razón disponible.')}",
    ]
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
    if issue is None:
        issue = _find_issue_by_title(repo, board_title, _GH_SYNC_LABEL)
    if issue is None:
        issue = _find_issue_by_title(repo, legacy_board_title, _GH_LEGACY_BOARD_LABEL)

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
    }


def render_github_sync_markdown(result: Dict[str, Any]) -> str:
    lines = [
        "## SonIA Sync",
        "",
        f"- Repo: `{result.get('repo', '-')}`",
        f"- Issue paraguas: {result.get('board_issue', {}).get('url', 'pendiente')}",
        f"- Tareas sincronizadas: {len(result.get('tasks', []))}",
    ]
    skipped = result.get("skipped", [])
    if skipped:
        lines.append(f"- Tareas omitidas: {len(skipped)}")
    lines.extend(["", "### Issues", ""])
    for item in result.get("tasks", []):
        lines.append(
            f"- {_task_reference(item)} → #{item.get('number')} ({_KANBAN_STATUS_LABELS.get(item.get('status', ''), item.get('status', ''))})"
        )
    if skipped:
        lines.extend(["", "### Omitidas", ""])
        for task in skipped:
            lines.append(f"- {task.get('title', 'sin título')} — sin ID [T-XXX]")
    return "\n".join(lines).strip() + "\n"


def sync_project_to_github(project_dir: str, raw_request: str = "") -> Dict[str, Any]:
    board = load_kanban_board(project_dir)
    tasks = [
        task
        for status in ("backlog", "in-progress", "blocked", "done")
        for task in board.get(status, [])
    ]
    if not tasks:
        raise RuntimeError("No hay tareas en docs/project/kanban/ para sincronizar.")

    _ensure_gh_ready()
    repo = _detect_github_repo(project_dir, raw_request=raw_request)
    _ensure_github_labels(repo)

    sync_path = _project_path(project_dir, GITHUB_SYNC_JSON_RELATIVE_PATH)
    sync_state = _read_json_file(sync_path)
    if not isinstance(sync_state, dict) or sync_state.get("repo") != repo:
        sync_state = {"version": 1, "repo": repo, "tasks": {}}

    task_map: Dict[str, Dict[str, Any]] = {}
    synced_tasks: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for task in tasks:
        if not task.get("id"):
            skipped.append(task)
            continue
        issue_info = _create_or_update_issue(repo, task, sync_state)
        merged = {**task, **issue_info}
        task_map[task["id"]] = issue_info
        synced_tasks.append(merged)

    project_name = _detect_project_name(project_dir, _load_package_json(project_dir))
    next_action = suggest_next_action(project_dir)
    board_body = _board_issue_body(project_name, repo, tasks, task_map, next_action)
    board_issue = _ensure_board_issue(repo, project_name, board_body, sync_state)

    sync_record = {
        "version": 1,
        "repo": repo,
        "synced_at": _now_utc().isoformat(),
        "board_issue": board_issue,
        "tasks": task_map,
        "skipped": [task.get("title", "") for task in skipped],
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
        "sync_path": sync_path,
        "sync_md_path": sync_md_path,
        "bypass_path": bypass_path,
    }


def _extract_recommended_alfred_command(markdown: str) -> Optional[str]:
    """Extrae un comando recomendado de un artefacto Markdown de Alfred."""
    if not markdown:
        return None

    match = re.search(
        r"/alfred-dev:(feature|quick|fix|spike|audit|ship|discuss|map-codebase)",
        markdown,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    return match.group(1).lower()


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
) -> str:
    path = _project_path(project_dir, relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing_markdown = _read_text_if_exists(project_dir, relative_path)
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
    return (
        "## Refinado preparado\n\n"
        f"- Foco: `{result.get('description', 'siguiente trabajo')}`\n"
        f"- Actor principal: `{result.get('actor', 'por definir')}`\n"
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
    )


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
        return "/alfred-dev:alfred"
    if status == "rejected":
        return "/alfred-dev:alfred"
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
    next_step = uat.get("next_command", "/alfred-dev:alfred")

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

    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
        "status": record["status"],
        "target_id": record["target_id"],
        "next_command": record["next_command"],
    }


def suggest_verify_action(project_dir: str) -> Optional[Dict[str, str]]:
    """Sugiere verify cuando el último flujo completado aún no tiene UAT aprobada."""
    target = build_verification_target(project_dir)
    if not target or target.get("blocked") or target.get("source") != "completed-session":
        return None

    uat = load_uat(project_dir)
    if not uat or uat.get("target_id") != target["target_id"]:
        return {
            "command": "verify",
            "reason": (
                "El último flujo completado todavía no tiene una verificación "
                "manual/UAT registrada."
            ),
            "source": "verify",
        }

    if uat.get("status") == "pending":
        return {
            "command": "verify",
            "reason": (
                "La verificación manual/UAT del último flujo completado sigue pendiente."
            ),
            "source": "verify",
        }

    return None


def suggest_next_action(project_dir: str) -> Dict[str, str]:
    """Sugiere el siguiente comando operativo con una prioridad estable."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    if state and state.get("fase_actual") != "completado":
        return {
            "command": "resume",
            "reason": (
                f"Hay una sesión activa de '{state['comando']}' "
                f"en la fase '{state['fase_actual']}'."
            ),
            "source": "state",
        }

    handoff = load_handoff(project_dir)
    if handoff and not handoff.get("resolved", False):
        return {
            "command": "resume",
            "reason": (
                f"Existe un handoff pendiente para '{handoff['command']}' "
                f"en la fase '{handoff['phase']}'."
            ),
            "source": "handoff",
        }

    verify_suggestion = suggest_verify_action(project_dir)
    if verify_suggestion is not None:
        return verify_suggestion

    if needs_codebase_map(project_dir):
        return {
            "command": "map-codebase",
            "reason": (
                "El proyecto ya tiene código, pero todavía no existe un mapa "
                "persistente del codebase en docs/project/."
            ),
            "source": "brownfield",
        }

    discovery_md = _read_text_if_exists(project_dir, DISCOVERY_MD_RELATIVE_PATH)
    discovery_command = _extract_recommended_alfred_command(discovery_md)
    if discovery_command is not None:
        return {
            "command": discovery_command,
            "reason": (
                "Existe un refinado previo en docs/project/discovery.md "
                f"que recomienda continuar con '{discovery_command}'."
            ),
            "source": "discovery",
        }

    if project_has_codebase(project_dir):
        return {
            "command": _GREENFIELD_COMMAND,
            "reason": (
                "No hay sesión activa. Alfred puede dirigir el siguiente flujo "
                "usando el contexto ya existente del proyecto."
            ),
            "source": "project",
        }

    return {
        "command": _GREENFIELD_COMMAND,
        "reason": (
            "No hay trabajo en curso ni un codebase brownfield claro. "
            "Conviene empezar por el asistente contextual."
        ),
        "source": "default",
    }


def build_progress_snapshot(project_dir: str) -> Dict[str, Any]:
    """Construye un resumen operativo a partir de artefactos de SonIA y continuidad."""
    state = load_state(_project_path(project_dir, STATE_RELATIVE_PATH))
    handoff = load_handoff(project_dir)
    uat = load_uat(project_dir)

    progress_md = _read_text_if_exists(project_dir, PROGRESS_MD_RELATIVE_PATH)
    traceability_md = _read_text_if_exists(project_dir, TRACEABILITY_MD_RELATIVE_PATH)
    backlog_md = _read_text_if_exists(project_dir, KANBAN_BACKLOG_RELATIVE_PATH)
    in_progress_md = _read_text_if_exists(project_dir, KANBAN_IN_PROGRESS_RELATIVE_PATH)
    done_md = _read_text_if_exists(project_dir, KANBAN_DONE_RELATIVE_PATH)
    blocked_md = _read_text_if_exists(project_dir, KANBAN_BLOCKED_RELATIVE_PATH)
    current_md = _read_text_if_exists(project_dir, CURRENT_RELATIVE_PATH)

    backlog_items = _extract_markdown_list_items(backlog_md)
    in_progress_items = _extract_markdown_list_items(in_progress_md)
    done_items = _extract_markdown_list_items(done_md)
    blocked_items = _extract_markdown_list_items(blocked_md)

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
                    if state and state.get("fase_actual") != "completado"
                    else ""
                ),
                (
                    f"Handoff pendiente para `{handoff.get('command', 'desconocido')}` "
                    f"en `{handoff.get('phase', 'desconocida')}`."
                    if handoff and not handoff.get("resolved", False)
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
    if state and state.get("fase_actual") != "completado":
        bypass_path = arm_stop_hook_bypass(project_dir, "/alfred-dev:progress")

    return {
        "state": state,
        "handoff": handoff,
        "uat": uat,
        "progress_signals": progress_signals,
        "current_signals": current_signals,
        "traceability_signals": traceability_signals,
        "kanban": {
            "backlog": backlog_items,
            "in_progress": in_progress_items,
            "done": done_items,
            "blocked": blocked_items,
            "total": total_items,
            "progress_pct": progress_pct,
        },
        "next_action": next_action,
        "bypass_path": bypass_path,
    }


def render_progress_markdown(snapshot: Dict[str, Any]) -> str:
    """Renderiza un resumen operativo breve para `/alfred-dev:progress`."""
    state = snapshot.get("state")
    handoff = snapshot.get("handoff")
    uat = snapshot.get("uat")
    kanban = snapshot.get("kanban", {})
    next_action = snapshot.get("next_action", {"command": "alfred", "reason": ""})

    lines = ["## Resumen operativo del proyecto", ""]

    if state and state.get("fase_actual") != "completado":
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

    lines.extend(
        [
            "",
            "### Siguiente paso recomendado",
            "",
            f"- `/alfred-dev:{next_action.get('command', 'alfred')}`",
            f"- {next_action.get('reason', 'Sin razón disponible.')}",
        ]
    )

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

    session = create_session("quick", description)
    session["modo_rapido"] = True
    session["origen"] = "/alfred-dev:quick"
    session["next_after_completion"] = "/alfred-dev:verify"
    os.makedirs(_project_path(project_dir, ".claude"), exist_ok=True)
    save_state(session, state_path)
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
        traceability_items=[
            "El cambio quick debe seguir siendo acotado y verificable manualmente.",
            (
                "Si el alcance crece o afecta varias zonas, conviene volver a map-codebase."
                if quick_record["needs_codebase_map"]
                else "Si aparecen dependencias nuevas, conviene promocionarlo a feature o fix."
            ),
        ],
        backlog_items=[
            f"Validar '{session['descripcion']}' con /alfred-dev:verify.",
        ],
        in_progress_items=[
            session["descripcion"],
        ],
    )

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
    state = load_state(state_path)
    if not state or state.get("fase_actual") == "completado":
        return None

    state["paused_at"] = _now_utc().isoformat()
    state["paused_via"] = "/alfred-dev:pause"
    save_state(state, state_path)
    return state


def clear_session_paused(project_dir: str) -> Optional[Dict[str, Any]]:
    """Elimina la marca de pausa al retomar trabajo."""
    state_path = _project_path(project_dir, STATE_RELATIVE_PATH)
    state = load_state(state_path)
    if not state:
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
        return None

    if not isinstance(data, dict):
        return None

    required = {"source_command", "prefetched_command", "response_text", "created_at", "expires_at"}
    if not required.issubset(data.keys()):
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

    return {
        **handoff_paths,
        "state_path": _project_path(project_dir, STATE_RELATIVE_PATH),
        "paused_at": state["paused_at"],
    }


def resume_session(project_dir: str) -> Optional[Dict[str, str]]:
    """Quita la marca de pausa y resuelve el handoff si existe."""
    state = clear_session_paused(project_dir)
    if state is None:
        return None

    handoff = resolve_handoff(project_dir)
    bypass_path = arm_stop_hook_bypass(project_dir, "/alfred-dev:resume")
    result = {
        "state_path": _project_path(project_dir, STATE_RELATIVE_PATH),
        "resumed_at": state["resumed_at"],
        "bypass_path": bypass_path,
    }
    if handoff is not None:
        result["handoff_path"] = _project_path(project_dir, HANDOFF_JSON_RELATIVE_PATH)
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

    resume_parser = subparsers.add_parser("resume", help="Quita la marca de pausa y resuelve el handoff")
    resume_parser.add_argument("project_dir", nargs="?", default=".")

    verify_parser = subparsers.add_parser(
        "verify",
        help="Crea o actualiza la verificación manual/UAT",
    )
    verify_parser.add_argument("project_dir", nargs="?", default=".")
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
    quick_parser.add_argument(
        "--raw",
        default="",
        dest="raw_request",
        help="Argumento libre recibido desde /alfred-dev:quick",
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
            print(f"/alfred-dev:{suggestion['command']}")
            print(suggestion["reason"])
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
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "resume":
        result = resume_session(project_dir)
        if result is None:
            print("No hay sesión pausada o activa para reanudar.", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "verify":
        try:
            result = write_uat_files(project_dir, raw_request=args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "progress":
        snapshot = build_progress_snapshot(project_dir)
        if args.as_json:
            print(json.dumps(snapshot, ensure_ascii=False))
        else:
            print(render_progress_markdown(snapshot))
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
        print(render_github_sync_markdown(result))
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
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "quick":
        try:
            result = start_quick_session(project_dir, raw_request=args.raw_request)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
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
