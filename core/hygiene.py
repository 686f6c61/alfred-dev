#!/usr/bin/env python3
"""Avisos antes de que duela y cierre enseñable de un quick/fix."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Optional

from core.continuity import (
    STATE_RELATIVE_PATH,
    load_state,
    load_uat,
    suggest_verify_action,
)
from core.project_docs import inspect_docs
from core.session_brief import build_session_brief


MANIFEST_NAMES = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "poetry.lock",
    "Pipfile.lock",
    "pyproject.toml",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "composer.json",
    "composer.lock",
)

EVIDENCE_RELATIVE = os.path.join(".claude", "alfred-evidence.json")
CIERRE_RELATIVE = os.path.join(".claude", "alfred-last-cierre.md")


def _git_changed_files(project_dir: str) -> List[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    names: List[str] = []
    for line in result.stdout.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            names.append(path.replace("\\", "/"))
    return names


def _latest_evidence(project_dir: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(project_dir, EVIDENCE_RELATIVE)
    if not os.path.isfile(path):
        return None
    try:
        payload = json.loads(open(path, encoding="utf-8").read())
    except (OSError, ValueError):
        return None
    if isinstance(payload, list) and payload:
        last = payload[-1]
        return last if isinstance(last, dict) else None
    if isinstance(payload, dict):
        records = payload.get("records") or payload.get("evidence")
        if isinstance(records, list) and records:
            last = records[-1]
            return last if isinstance(last, dict) else None
        if payload.get("command") or payload.get("result"):
            return payload
    return None


def _doc_status_map(project_dir: str) -> Dict[str, str]:
    mapping = {row["key"]: row["status"] for row in inspect_docs(project_dir)}
    return mapping


def run_hygiene(project_dir: str, command: str = "") -> Dict[str, Any]:
    """Comprueba UAT, docs vivos y manifiestos tocados sin evaluación."""
    root = os.path.abspath(project_dir)
    comando = (command or "").strip().lower()
    blockers: List[str] = []
    warnings: List[str] = []

    uat = load_uat(root) or {}
    uat_status = str(uat.get("status") or "")
    verify = suggest_verify_action(root)
    if uat_status == "rejected":
        msg = "UAT rechazada: no despliegues hasta corregir lo apuntado en docs/project/uat.md."
        if comando in {"ship", "audit"}:
            blockers.append(msg)
        else:
            warnings.append(msg)
    elif verify is not None or uat_status == "pending":
        msg = "UAT pendiente del último entregable. Cierra `/alfred-dev:uat` antes de ship."
        if comando == "ship":
            blockers.append(msg)
        else:
            warnings.append(msg)

    statuses = _doc_status_map(root)
    arch = statuses.get("architecture", "missing")
    threat = statuses.get("threat_model", "missing")
    compliance = statuses.get("compliance", "missing")
    deps = statuses.get("dependencies", "missing")

    if arch == "filled" and threat in {"scaffold", "missing", "empty"}:
        msg = (
            "La arquitectura está rellena y el threat-model sigue en esqueleto. "
            "Actualiza `docs/project/threat-model.md`."
        )
        if comando in {"ship", "audit", "feature"}:
            blockers.append(msg)
        else:
            warnings.append(msg)

    if comando in {"ship", "audit"} and compliance in {"scaffold", "missing", "empty"}:
        blockers.append(
            "El registro de compliance sigue en esqueleto. "
            "Rellena `docs/project/compliance.md` con evidencia."
        )

    changed = _git_changed_files(root)
    touched_manifests = [
        name for name in changed
        if os.path.basename(name) in MANIFEST_NAMES
    ]
    if touched_manifests and deps in {"scaffold", "missing", "empty"}:
        warnings.append(
            "Hay manifiestos de dependencias tocados ("
            + ", ".join(touched_manifests)
            + ") y `docs/project/dependencies.md` no tiene evaluación. "
            "Usa el skill evaluate-dependency."
        )

    passed = not blockers
    return {
        "passed": passed,
        "command": comando,
        "blockers": blockers,
        "warnings": warnings,
        "uat_status": uat_status,
        "docs": statuses,
    }


def render_hygiene_markdown(result: Dict[str, Any]) -> str:
    lines = ["## Higiene del repo", ""]
    if result["passed"] and not result["warnings"]:
        lines.append("Nada urgente. Puedes seguir.")
        return "\n".join(lines)
    if result["blockers"]:
        lines.append("Bloquea:")
        lines.extend(f"- {item}" for item in result["blockers"])
        lines.append("")
    if result["warnings"]:
        lines.append("Aviso:")
        lines.extend(f"- {item}" for item in result["warnings"])
    if not result["passed"]:
        lines.append("")
        lines.append("No declares ship ni la gate de entrega hasta resolver los bloqueos.")
    return "\n".join(lines)


def build_cierre(project_dir: str) -> Dict[str, Any]:
    root = os.path.abspath(project_dir)
    state_path = os.path.join(root, STATE_RELATIVE_PATH)
    state = load_state(state_path) if os.path.isfile(state_path) else {}
    if not isinstance(state, dict):
        state = {}
    evidence = _latest_evidence(root)
    hygiene = run_hygiene(root, str(state.get("comando") or ""))
    brief = build_session_brief(root)

    what = str(state.get("descripcion") or "cambio de esta sesión")
    command = str(state.get("comando") or "quick")
    phase = str(state.get("fase_actual") or "")

    verified = "sin evidencia de tests en los últimos minutos"
    if evidence:
        command_run = str(evidence.get("command") or "tests")
        result = str(evidence.get("result") or evidence.get("status") or "")
        verified = f"`{command_run}` → {result or 'registrado'}"

    pending: List[str] = []
    if hygiene["blockers"] or hygiene["warnings"]:
        pending.extend(hygiene["blockers"])
        pending.extend(hygiene["warnings"])
    if brief.get("verify_pending") or brief.get("uat_status") == "pending":
        pending.append("UAT: `/alfred-dev:uat`")
    if not pending:
        pending.append("nada bloqueante")

    return {
        "command": command,
        "phase": phase,
        "what": what,
        "verified": verified,
        "pending": pending,
        "hygiene_passed": hygiene["passed"],
    }


def write_session_cierre(project_dir: str) -> Optional[str]:
    """Persiste el cierre al salir de la sesión si hubo trabajo."""
    root = os.path.abspath(project_dir)
    state_path = os.path.join(root, STATE_RELATIVE_PATH)
    state = load_state(state_path) if os.path.isfile(state_path) else None
    has_state = isinstance(state, dict) and bool(
        state.get("comando") or state.get("descripcion")
    )
    has_evidence = os.path.isfile(os.path.join(root, EVIDENCE_RELATIVE))
    if not has_state and not has_evidence:
        return None
    payload = build_cierre(root)
    dest = os.path.join(root, CIERRE_RELATIVE)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as handle:
        handle.write(render_cierre_markdown(payload) + "\n")
    return dest


def render_cierre_markdown(result: Dict[str, Any]) -> str:
    pending = result.get("pending") or ["nada bloqueante"]
    lines = [
        "## Cierre Alfred",
        "",
        f"- Qué: {result.get('what')}",
        f"- Flujo: `{result.get('command')}`"
        + (f" / `{result.get('phase')}`" if result.get("phase") else ""),
        f"- Cómo se comprobó: {result.get('verified')}",
        "- Pendiente:",
    ]
    lines.extend(f"  - {item}" for item in pending)
    lines.append("")
    lines.append("Puedes pegar este bloque en el PR o en el chat del equipo.")
    return "\n".join(lines)
