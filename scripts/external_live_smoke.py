#!/usr/bin/env python3
"""Preflight seguro para pendientes externos de release 0.6.0.

Por defecto no escribe en GitHub, no arranca SonarQube y no ejecuta Codex. Solo
captura si el entorno esta preparado para esas pruebas reales y genera una
evidencia JSON saneada. Las acciones con efectos externos requieren flags
explicitos.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.continuity import (  # noqa: E402
    _build_audit_sonarqube_preflight,
    sync_project_to_github,
)
from core.secrets import sanitize_text  # noqa: E402


VERSION = "0.6.0"
DEFAULT_OUTPUT = ROOT / "docs" / "external-live-smoke-0.6.0.json"


def _safe_preview(value: Any, limit: int = 2000) -> str:
    text = sanitize_text("" if value is None else str(value))
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _run(
    command: list[str],
    timeout: int = 20,
    cwd: Path | None = None,
    preview_limit: int = 2000,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd or ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "stdout_preview": _safe_preview(result.stdout, limit=preview_limit),
            "stderr_preview": _safe_preview(result.stderr, limit=preview_limit),
        }
    except FileNotFoundError as exc:
        return {
            "command": command,
            "returncode": 127,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "stdout_preview": "",
            "stderr_preview": _safe_preview(str(exc), limit=preview_limit),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "stdout_preview": _safe_preview(exc.stdout, limit=preview_limit),
            "stderr_preview": _safe_preview(exc.stderr or f"Timeout after {timeout}s", limit=preview_limit),
        }


def _github_preflight(repo: str | None) -> dict[str, Any]:
    gh = shutil.which("gh")
    payload: dict[str, Any] = {
        "status": "missing",
        "write_attempted": False,
        "repo": repo or "",
        "checks": [],
    }
    if not gh:
        payload["reason"] = "gh no esta disponible en PATH."
        return payload

    version = _run([gh, "--version"], timeout=10)
    auth = _run([gh, "auth", "status"], timeout=15)
    payload["checks"].extend([version, auth])
    if version["returncode"] != 0:
        payload["status"] = "unavailable"
        payload["reason"] = "gh existe pero no responde correctamente."
        return payload
    if auth["returncode"] != 0:
        payload["status"] = "auth_required"
        payload["reason"] = "gh no tiene autenticacion activa para GitHub."
        return payload

    payload["status"] = "ready"
    payload["reason"] = "gh esta instalado y autenticado."
    if repo:
        repo_view = _run(
            [gh, "repo", "view", repo, "--json", "nameWithOwner,isPrivate"],
            timeout=20,
        )
        payload["checks"].append(repo_view)
        if repo_view["returncode"] != 0:
            payload["status"] = "repo_unavailable"
            payload["reason"] = "gh no puede leer el repositorio indicado."
    return payload


def _seed_github_sync_fixture(project: Path) -> None:
    kanban = project / "docs" / "project" / "kanban"
    kanban.mkdir(parents=True, exist_ok=True)
    (project / "package.json").write_text('{"name":"alfred-external-live-smoke"}\n', encoding="utf-8")
    (project / "README.md").write_text("# Alfred external live smoke\n", encoding="utf-8")
    (project / "docs" / "project" / "progress.md").write_text("# Progress\n", encoding="utf-8")
    (project / "docs" / "project" / "traceability.md").write_text("# Traceability\n", encoding="utf-8")
    (kanban / "backlog.md").write_text(
        "# Backlog\n\n"
        "### [T-990] Smoke externo Alfred 0.6.0\n\n"
        "- **Agente:** project-manager\n"
        "- **Tipo:** delivery\n",
        encoding="utf-8",
    )
    for lane in ("in-progress", "done", "blocked"):
        (kanban / f"{lane}.md").write_text(f"# {lane.title()}\n", encoding="utf-8")


def _github_live_sync(repo: str | None) -> dict[str, Any]:
    if not repo:
        return {
            "status": "skipped",
            "write_attempted": False,
            "reason": "--allow-github-write requiere --github-repo owner/repo.",
        }

    with tempfile.TemporaryDirectory(prefix="alfred-external-github-") as tmp:
        project = Path(tmp)
        _seed_github_sync_fixture(project)
        try:
            result = sync_project_to_github(str(project), raw_request=repo)
        except Exception as exc:  # pragma: no cover - exact gh failures vary by host
            return {
                "status": "failed",
                "write_attempted": True,
                "repo": repo,
                "reason": _safe_preview(exc),
            }

    return {
        "status": "ok",
        "write_attempted": True,
        "repo": repo,
        "synced_tasks": len(result.get("tasks", [])),
        "board_issue": result.get("board_issue", {}).get("url", ""),
        "retired": len(result.get("retired", [])),
        "remote_drift": len(result.get("remote_drift", [])),
    }


def _docker_sonarqube_preflight() -> dict[str, Any]:
    preflight = _build_audit_sonarqube_preflight()
    return {
        "status": preflight.get("status", "unknown"),
        "sonarqube_autorizado": bool(preflight.get("sonarqube_autorizado", False)),
        "live_attempted": False,
        "reason": preflight.get("summary", ""),
        "detail": _safe_preview(preflight.get("detail", "")),
        "headless_marker": preflight.get("headless_marker", ""),
        "menu_options": preflight.get("menu_options", []),
    }


def _codex_preflight() -> dict[str, Any]:
    codex = shutil.which("codex")
    payload: dict[str, Any] = {
        "status": "missing",
        "live_attempted": False,
        "checks": [],
    }
    if not codex:
        payload["reason"] = "codex no esta disponible en PATH."
        return payload

    version = _run([codex, "--version"], timeout=10)
    help_result = _run(
        [codex, "exec", "--sandbox", "read-only", "--ephemeral", "--help"],
        timeout=15,
        preview_limit=8000,
    )
    payload["checks"].extend([version, help_result])
    if version["returncode"] != 0:
        payload["status"] = "unavailable"
        payload["reason"] = "codex existe pero no informa version correctamente."
    elif help_result["returncode"] != 0:
        payload["status"] = "exec_help_failed"
        payload["reason"] = "codex exec no acepta el preflight read-only/ephemeral."
    elif missing_flags := [
        flag
        for flag in ("--sandbox", "--ephemeral", "--json", "--output-last-message")
        if flag not in help_result["stdout_preview"]
    ]:
        payload["status"] = "exec_help_missing_flags"
        payload["reason"] = "codex exec no expone flags requeridos para Lucius."
        payload["missing_flags"] = missing_flags
    else:
        payload["status"] = "ready"
        payload["reason"] = (
            "codex exec acepta --sandbox read-only, --ephemeral, --json "
            "y --output-last-message."
        )
    return payload


def _codex_live_exec() -> dict[str, Any]:
    codex = shutil.which("codex")
    if not codex:
        return {
            "status": "missing",
            "live_attempted": False,
            "reason": "codex no esta disponible en PATH.",
        }
    with tempfile.TemporaryDirectory(prefix="alfred-codex-live-") as tmp:
        final_message = Path(tmp) / "last-message.md"
        command = [
            codex,
            "exec",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--json",
            "--output-last-message",
            str(final_message),
            "-c",
            "approval_policy=never",
            "Responde exactamente OK_ALFRED_CODEX_EXTERNAL_060 y nada mas.",
        ]
        result = _run(command, timeout=120)
        final_preview = _safe_preview(
            final_message.read_text(encoding="utf-8")
            if final_message.is_file()
            else ""
        )
    return {
        "status": "ok" if result["returncode"] == 0 and "OK_ALFRED_CODEX_EXTERNAL_060" in final_preview else "failed",
        "live_attempted": True,
        "check": result,
        "final_message_preview": final_preview,
    }


def _counts(payload: dict[str, Any]) -> dict[str, int]:
    statuses = [
        payload.get("github", {}).get("status", "unknown"),
        payload.get("docker_sonarqube", {}).get("status", "unknown"),
        payload.get("codex_lucius", {}).get("status", "unknown"),
    ]
    return {
        "ready": sum(1 for status in statuses if status in {"ready", "docker_ready", "ok"}),
        "blocked": sum(1 for status in statuses if status not in {"ready", "docker_ready", "ok"}),
        "live_attempted": sum(
            1
            for section in ("github", "docker_sonarqube", "codex_lucius")
            if payload.get(section, {}).get("write_attempted")
            or payload.get(section, {}).get("live_attempted")
        ),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": VERSION,
        "mode": "preflight",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "github": _github_preflight(args.github_repo),
        "docker_sonarqube": _docker_sonarqube_preflight(),
        "codex_lucius": _codex_preflight(),
    }

    if args.allow_github_write:
        payload["mode"] = "live"
        payload["github"] = _github_live_sync(args.github_repo)
    if args.allow_codex_exec:
        payload["mode"] = "live"
        payload["codex_lucius"] = _codex_live_exec()

    payload["counts"] = _counts(payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Ruta JSON de evidencia.")
    parser.add_argument("--github-repo", help="Repositorio owner/repo para preflight o sync vivo.")
    parser.add_argument(
        "--allow-github-write",
        action="store_true",
        help="Permite crear/actualizar issues de smoke en --github-repo.",
    )
    parser.add_argument(
        "--allow-codex-exec",
        action="store_true",
        help="Permite ejecutar un prompt real de codex exec read-only.",
    )
    parser.add_argument(
        "--require-all-ready",
        action="store_true",
        help="Devuelve 2 si algun preflight no esta listo.",
    )
    args = parser.parse_args(argv)

    payload = build_payload(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    _write_json(output_path, payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.allow_github_write and payload["github"].get("status") != "ok":
        return 1
    if args.allow_codex_exec and payload["codex_lucius"].get("status") != "ok":
        return 1
    if args.require_all_ready and payload["counts"]["blocked"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
