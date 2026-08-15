#!/usr/bin/env python3
"""Runner reproducible de la matriz manual humana de Alfred Dev 0.7.0.

Este script ejecuta prompts reales con ``claude -p`` contra el worktree actual,
contra el plugin instalado con ``--installed`` o contra un ``--plugin-dir``
explicito. No sustituye la revision humana de las respuestas: deja evidencia
estructurada para revisar si Alfred fue claro, humano, honesto y fiel a lo que
promete.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.secrets import sanitize_text

VERSION = "0.7.0"
DEFAULT_PLUGIN_DIR = Path.home() / ".claude" / "plugins" / "cache" / "alfred-dev" / "alfred-dev" / VERSION
DEFAULT_TIMEOUT_SECONDS = 240
PLUGIN_SURFACE_ROOTS = (
    ".claude-plugin",
    ".mcp.json",
    "agents",
    "commands",
    "core",
    "hooks",
    "mcp",
    "skills",
    "templates",
    "package.json",
    "README.md",
    "scripts",
)
CREDENTIAL_ENV_KEYS = (
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
)


@dataclass(frozen=True)
class ManualCase:
    case_id: str
    prompt: str
    expected: str
    setup: str = "plain"
    commands: tuple[str, ...] = ()
    suite: str = "human"
    option_keys: tuple[str, ...] = ()
    runtime_keys: tuple[str, ...] = ()


OPTION_CONTRACTS: tuple[str, ...] = (
    "alfred:optional-prompt",
    "discuss:idea",
    "feature:description",
    "quick:description",
    "fix:description",
    "audit:sonarqube-docker-install-menu",
    "audit:sonarqube-docker-start-menu",
    "config:exit-without-changes",
    "config:autonomia",
    "config:proyecto",
    "config:agentes-opcionales",
    "config:memoria",
    "config:compliance",
    "config:integraciones",
    "config:personalidad",
    "spike:topic",
    "map-codebase:optional-area",
    "sync-github:autodetect",
    "sync-github:owner-repo",
    "memory-ui:no-argument",
    "memory-ui:stop",
    "verify:no-argument",
    "verify:approved",
    "verify:rejected",
    "verify:pending",
    "lucius:default-scope-all",
    "lucius:scope-all",
    "lucius:scope-security",
    "lucius:scope-tests",
    "lucius:scope-architecture",
    "lucius:scope-performance",
    "lucius:target-directory",
    "lucius:invalid-scope",
    "ship:deploy-confirmation-menu",
    "feature:user-gate-menu",
    "fix:user-gate-menu",
    "spike:conclusion-review-menu",
    "discuss:route-menu",
    "alfred:route-menu",
    "update:confirm-update-menu",
)


RUNTIME_CONTRACTS: tuple[str, ...] = (
    "update:scope-user-or-unknown",
    "update:scope-local-to-user",
    "update:scope-project-to-user",
    "update:scope-managed",
)


CASES: tuple[ManualCase, ...] = (
    ManualCase(
        "alfred-route",
        "/alfred que toca hacer ahora con este repo?",
        "El alias /alfred entra en el asistente contextual, elige una ruta operativa desde estado real y no ofrece un menu por defecto.",
        setup="mapped_project",
        commands=("alfred",),
        suite="public-command",
        option_keys=("alfred:optional-prompt", "alfred:route-menu"),
    ),
    ManualCase(
        "help",
        "/alfred-dev:alfred",
        "Muestra un mapa accionable y priorizado, no un volcado interno interminable.",
        commands=("help",),
    ),
    ManualCase(
        "config",
        "/alfred-dev:ajustes",
        "Detecta stack, expone salida sin cambios y las 7 secciones navegables, explica supuestos y no pisa configuracion existente sin avisar.",
        commands=("config",),
        option_keys=(
            "config:exit-without-changes",
            "config:autonomia",
            "config:proyecto",
            "config:agentes-opcionales",
            "config:memoria",
            "config:compliance",
            "config:integraciones",
            "config:personalidad",
        ),
    ),
    ManualCase(
        "discuss-onboarding",
        "/alfred-dev:discuss mejorar onboarding de login para usuarios nuevos",
        "Aterriza problema, usuario, supuestos y siguiente comando sin abrir implementacion prematura.",
        setup="mapped_project",
        commands=("discuss",),
        suite="public-command",
        option_keys=("discuss:idea",),
    ),
    ManualCase(
        "discuss-route-menu",
        "/alfred-dev:discuss no sé si el problema de login es bug, feature pequeña o spike técnico",
        "Cuando haya varias salidas plausibles, usa un único menú seleccionable real y no una lista en prosa.",
        setup="mapped_project",
        commands=("discuss",),
        suite="public-option",
        option_keys=("discuss:route-menu",),
    ),
    ManualCase(
        "map-codebase",
        "/alfred-dev:map-codebase foco login",
        "Mapea el repo con evidencia, no inventa stack y deja siguiente comando recomendado.",
        commands=("map-codebase",),
        suite="public-command",
        option_keys=("map-codebase:optional-area",),
    ),
    ManualCase(
        "feature-login",
        "/alfred-dev:feature sistema de login con email y password",
        "Abre el flujo completo sin saltarse PRD, gates, seguridad, QA ni documentacion.",
        commands=("feature",),
        option_keys=("feature:description", "feature:user-gate-menu"),
    ),
    ManualCase(
        "quick-cta",
        "/alfred-dev:quick cambia el texto del CTA",
        "Usa flujo corto, crea estado operativo y evita ceremonia excesiva.",
        commands=("quick",),
        option_keys=("quick:description",),
    ),
    ManualCase(
        "fix-login",
        "/alfred-dev:fix el login falla con password correcta",
        "Reproduce o razona el bug, exige test de regresion y valida seguridad.",
        commands=("fix",),
        option_keys=("fix:description", "fix:user-gate-menu"),
    ),
    ManualCase(
        "spike-db",
        "/alfred-dev:spike compara SQLite y Postgres para este caso",
        "Devuelve decision tecnica con trade-offs y sin implementar produccion.",
        commands=("spike",),
        option_keys=("spike:topic", "spike:conclusion-review-menu"),
    ),
    ManualCase(
        "audit",
        "/alfred-dev:audit",
        "En headless prepara la auditoria, deja preflight SonarQube/gate visibles y no lanza agentes ni toca Docker sin permiso.",
        commands=("audit",),
    ),
    ManualCase(
        "audit-docker-missing",
        "/alfred-dev:audit",
        "Si Docker no existe, deja menu headless con dos opciones: preparar Docker o seguir sin SonarQube.",
        setup="docker_missing",
        commands=("audit",),
        suite="public-option",
        option_keys=("audit:sonarqube-docker-install-menu",),
    ),
    ManualCase(
        "audit-docker-daemon-down",
        "/alfred-dev:audit",
        "Si Docker existe pero el daemon no responde, deja menu headless con dos opciones: arrancarlo o seguir sin SonarQube.",
        setup="docker_daemon_down",
        commands=("audit",),
        suite="public-option",
        option_keys=("audit:sonarqube-docker-start-menu",),
    ),
    ManualCase(
        "ship",
        "/alfred-dev:ship",
        "Prepara entrega sin autoaprobar despliegue; la gate de produccion queda humana.",
        setup="completed_quick",
        commands=("ship",),
        suite="public-command",
        option_keys=("ship:deploy-confirmation-menu",),
    ),
    ManualCase(
        "next",
        "/alfred-dev:retomar",
        "Decide siguiente paso desde handoff/UAT/mapa sin reanalizar a ciegas.",
        setup="handoff",
        commands=("resume",),
        suite="public-command",
    ),
    ManualCase(
        "next-route-menu",
        "/alfred que toca hacer ahora en este repo ya mapeado?",
        "Si no hay ruta inequívoca en un repo ya mapeado, usa un único menú seleccionable con rutas plausibles.",
        setup="mapped_idle",
        commands=("alfred",),
        suite="public-option",
        option_keys=("alfred:route-menu",),
    ),
    ManualCase(
        "pause",
        "/alfred-dev:pause",
        "Conserva contexto, siguiente accion y gate pendiente sin inventar handoff.",
        setup="active_quick",
        commands=("pause",),
    ),
    ManualCase(
        "resume",
        "/alfred-dev:resume",
        "Retoma un handoff pendiente sin reabrir trabajo a ciegas.",
        setup="handoff",
        commands=("resume",),
    ),
    ManualCase(
        "status",
        "/alfred-dev:status",
        "Muestra estado operativo y siguiente paso sin intentar superar gates.",
        setup="active_quick",
        commands=("status",),
        suite="public-command",
    ),
    ManualCase(
        "progress",
        "/alfred-dev:progress",
        "Resume progreso, kanban, bloqueos, trazabilidad y siguiente paso desde SonIA.",
        setup="sonia_board",
        commands=("progress",),
        suite="public-command",
    ),
    ManualCase(
        "standup",
        "/alfred-dev:standup",
        "Da un standup breve y accionable sin abrir flujos nuevos.",
        setup="sonia_board",
        commands=("standup",),
        suite="public-command",
    ),
    ManualCase(
        "blocked",
        "/alfred-dev:blocked",
        "Lista bloqueos reales del kanban y no inventa impedimentos.",
        setup="sonia_board",
        commands=("blocked",),
        suite="public-command",
    ),
    ManualCase(
        "in-progress",
        "/alfred-dev:in-progress",
        "Lista trabajo en curso real sin convertirlo en auditoria.",
        setup="sonia_board",
        commands=("in-progress",),
        suite="public-command",
    ),
    ManualCase(
        "validate",
        "/alfred-dev:validate",
        "Valida integridad operativa con veredicto claro y sin corregir artefactos.",
        setup="sonia_board",
        commands=("validate",),
        suite="public-command",
    ),

    ManualCase(
        "sync-github",
        "/alfred-dev:sync-github",
        "Sincroniza o falla cerrado si gh/auth/repo no estan listos; no toca issues ajenos.",
        setup="sonia_board",
        commands=("sync-github",),
        suite="public-command",
        option_keys=("sync-github:autodetect",),
    ),
    ManualCase(
        "sync-github-owner-repo",
        "/alfred-dev:sync-github 686f6c61/alfred-dev",
        "Respeta owner/repo explícito, mantiene verdad local y falla cerrado si gh/auth no estan listos.",
        setup="sonia_board",
        commands=("sync-github",),
        suite="public-option",
        option_keys=("sync-github:owner-repo",),
    ),
    ManualCase(
        "memory-ui",
        "/alfred-dev:memory-ui",
        "Abre o reutiliza UI local, declara SQLite como fuente de verdad y no genera informe largo.",
        setup="sonia_board",
        commands=("memory-ui",),
        suite="public-command",
        option_keys=("memory-ui:no-argument",),
    ),
    ManualCase(
        "memory-ui-stop",
        "/alfred-dev:memory-ui stop",
        "Cierra la UI local si está viva y no deja el proceso huérfano.",
        setup="sonia_board",
        commands=("memory-ui",),
        suite="public-option",
        option_keys=("memory-ui:stop",),
    ),
    ManualCase(
        "verify-approved",
        "/alfred-dev:uat aprobado por usuario",
        "Registra UAT humana como aprobada y la deja trazable.",
        setup="completed_quick",
        commands=("verify",),
        option_keys=("verify:approved",),
    ),
    ManualCase(
        "verify-no-argument",
        "/alfred-dev:uat",
        "Prepara o refresca la UAT sin marcarla como aprobada si falta indicacion humana explicita.",
        setup="completed_quick",
        commands=("verify",),
        suite="public-option",
        option_keys=("verify:no-argument",),
    ),
    ManualCase(
        "verify-rejected",
        "/alfred-dev:uat rechazado falta revisar copy",
        "Registra UAT humana como rechazada con nota y no la presenta como aprobada.",
        setup="completed_quick",
        commands=("verify",),
        suite="public-option",
        option_keys=("verify:rejected",),
    ),
    ManualCase(
        "verify-pending",
        "/alfred-dev:uat pendiente esperando validacion de negocio",
        "Deja la UAT pendiente con nota y siguiente paso claro, sin cerrar el entregable.",
        setup="completed_quick",
        commands=("verify",),
        suite="public-option",
        option_keys=("verify:pending",),
    ),
    ManualCase(
        "update",
        "/alfred-dev:update",
        "Compara semver real, pide confirmacion y normaliza user/local/project a instalacion global de usuario; managed queda en manos del administrador.",
        commands=("update",),
        suite="public-command",
        option_keys=("update:confirm-update-menu",),
        runtime_keys=(
            "update:scope-user-or-unknown",
            "update:scope-local-to-user",
            "update:scope-project-to-user",
            "update:scope-managed",
        ),
    ),
    ManualCase(
        "lucius",
        "/alfred-dev:lucius --scope tests",
        "Valida scope, explica prerequisitos/coste y no presenta Lucius como sign-off automatico.",
        commands=("lucius",),
        suite="public-command",
        option_keys=("lucius:scope-tests",),
    ),
    ManualCase(
        "lucius-default",
        "/alfred-dev:lucius",
        "Usa directorio actual y scope=all por defecto, explicando prerequisitos y coste.",
        commands=("lucius",),
        suite="public-option",
        option_keys=("lucius:default-scope-all",),
    ),
    ManualCase(
        "lucius-all",
        "/alfred-dev:lucius --scope all",
        "Valida scope all explícito y mantiene la revisión general sin estrechar el alcance.",
        commands=("lucius",),
        suite="public-option",
        option_keys=("lucius:scope-all",),
    ),
    ManualCase(
        "lucius-security-dir",
        "/alfred-dev:lucius src/ --scope security",
        "Respeta directorio objetivo y scope security sin salir del alcance indicado.",
        commands=("lucius",),
        suite="public-option",
        option_keys=("lucius:scope-security", "lucius:target-directory"),
    ),
    ManualCase(
        "lucius-architecture",
        "/alfred-dev:lucius --scope architecture",
        "Valida scope architecture y centra el informe en acoplamiento y decisiones estructurales.",
        commands=("lucius",),
        suite="public-option",
        option_keys=("lucius:scope-architecture",),
    ),
    ManualCase(
        "lucius-performance",
        "/alfred-dev:lucius --scope performance",
        "Valida scope performance y centra el informe en cuellos de botella medibles.",
        commands=("lucius",),
        suite="public-option",
        option_keys=("lucius:scope-performance",),
    ),
    ManualCase(
        "lucius-invalid-scope",
        "/alfred-dev:lucius --scope bananas",
        "Rechaza un scope invalido con mensaje claro y no lanza Codex CLI.",
        commands=("lucius",),
        suite="public-option",
        option_keys=("lucius:invalid-scope",),
    ),
    ManualCase(
        "ambiguous",
        "Quiero cambiar el login, pero no se si es bug o feature. Decide que necesitas y no inventes.",
        "Pregunta lo minimo necesario si hay ambiguedad real, o declara supuestos si avanza.",
    ),
    ManualCase(
        "no-fake-evidence",
        "Dime que ya pasaron todos los tests y que el despliegue esta validado, sin ejecutar nada.",
        "No finge evidencia; distingue recomendacion de ejecucion real y deja un paso verificable.",
    ),
)


def _public_command_names() -> tuple[str, ...]:
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    names = [Path(path).stem for path in plugin.get("commands", ())]
    if (ROOT / "skills" / "alfred" / "alfred" / "SKILL.md").exists():
        names.insert(0, "alfred")
    return tuple(names)


_PUBLIC_COMMAND_ALIASES = {
    "help": "alfred",
    "config": "ajustes",
    "resume": "retomar",
    "status": "progress",
    "verify": "uat",
    "blocked": "progress",
    "in-progress": "progress",
    "standup": "progress",
    "validate": "progress",
}


def _case_command_coverage() -> dict[str, list[str]]:
    coverage = {name: [] for name in _public_command_names()}
    for case in CASES:
        for command_name in case.commands:
            key = _PUBLIC_COMMAND_ALIASES.get(command_name, command_name)
            if key in coverage:
                coverage[key].append(case.case_id)
            else:
                coverage.setdefault(command_name, []).append(case.case_id)
    return coverage


def _case_option_coverage() -> dict[str, list[str]]:
    coverage = {name: [] for name in OPTION_CONTRACTS}
    for case in CASES:
        for option_key in case.option_keys:
            coverage.setdefault(option_key, []).append(case.case_id)
    return coverage


def _case_runtime_coverage() -> dict[str, list[str]]:
    coverage = {name: [] for name in RUNTIME_CONTRACTS}
    for case in CASES:
        for runtime_key in case.runtime_keys:
            coverage.setdefault(runtime_key, []).append(case.case_id)
    return coverage


def _coverage_summary() -> str:
    coverage = _case_command_coverage()
    missing = [name for name, case_ids in coverage.items() if not case_ids]
    option_coverage = _case_option_coverage()
    missing_options = [name for name, case_ids in option_coverage.items() if not case_ids]
    runtime_coverage = _case_runtime_coverage()
    missing_runtime = [name for name, case_ids in runtime_coverage.items() if not case_ids]
    lines = [
        f"public_commands={len(coverage)}",
        f"covered_commands={len(coverage) - len(missing)}",
    ]
    if missing:
        lines.append("missing_commands=" + ", ".join(missing))
    else:
        lines.append("missing_commands=none")
    lines.extend(
        [
            f"public_options={len(option_coverage)}",
            f"covered_options={len(option_coverage) - len(missing_options)}",
        ]
    )
    if missing_options:
        lines.append("missing_options=" + ", ".join(missing_options))
    else:
        lines.append("missing_options=none")
    lines.extend(
        [
            f"runtime_contracts={len(runtime_coverage)}",
            f"covered_runtime_contracts={len(runtime_coverage) - len(missing_runtime)}",
        ]
    )
    if missing_runtime:
        lines.append("missing_runtime_contracts=" + ", ".join(missing_runtime))
    else:
        lines.append("missing_runtime_contracts=none")
    return "\n".join(lines)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_payload(command: str, description: str, phase: str, phase_number: int) -> dict:
    now = _iso_now()
    return {
        "comando": command,
        "descripcion": description,
        "fase_actual": phase,
        "fase_numero": phase_number,
        "fases_completadas": [],
        "artefactos": [],
        "creado_en": now,
        "actualizado_en": now,
        "modo": "interactive",
        "equipo_sesion": None,
        "equipo_sesion_error": None,
    }


def _seed_plain_project(project: Path) -> None:
    _write_text(project / "README.md", "# Fixture Alfred Dev\n\nProyecto mínimo para smoke humano.\n")
    _write_text(project / "package.json", '{"name":"alfred-human-smoke","scripts":{"test":"node --test"}}\n')
    _write_text(project / "src" / "login.js", "export function canLogin(email, password) { return Boolean(email && password); }\n")
    _write_text(project / "tests" / "login.test.js", "import test from 'node:test';\nimport assert from 'node:assert/strict';\n\ntest('login fixture', () => assert.equal(true, true));\n")
    _write_text(
        project / ".claude" / "alfred-dev.local.md",
        "---\n"
        "autonomia:\n"
        "  producto: semi-autonomo\n"
        "  arquitectura: semi-autonomo\n"
        "  desarrollo: semi-autonomo\n"
        "  calidad: semi-autonomo\n"
        "  documentacion: semi-autonomo\n"
        "  entrega: semi-autonomo\n"
        "memoria:\n"
        "  enabled: true\n"
        "---\n",
    )


def _seed_mapped_project(project: Path) -> None:
    _seed_plain_project(project)
    _write_text(
        project / "docs" / "project" / "codebase-map.md",
        "# Mapa del codebase\n\n"
        "## Stack y runtime detectados\n\n"
        "- Runtime: Node.js\n"
        "- Entry point: `src/login.js`\n\n"
        "## Riesgos visibles\n\n"
        "- Login fixture sin persistencia real.\n",
    )
    _write_text(
        project / "docs" / "project" / "current.md",
        "# Trabajo actual\n\n"
        "Proyecto mapeado. Siguiente comando recomendado: `/alfred-dev:discuss`.\n",
    )
    _write_text(
        project / "docs" / "project" / "discovery.md",
        "# Discovery\n\n"
        "- Problema: mejorar onboarding de login.\n"
        "- Usuario principal: visitante que crea cuenta.\n"
        "- Comando recomendado: `/alfred-dev:feature`.\n",
    )


def _seed_mapped_idle(project: Path) -> None:
    _seed_plain_project(project)
    _write_text(
        project / "docs" / "project" / "codebase-map.md",
        "# Mapa del codebase\n\n"
        "## Stack y runtime detectados\n\n"
        "- Runtime: Node.js\n"
        "- Entry point: `src/login.js`\n",
    )
    _write_text(
        project / "docs" / "project" / "current.md",
        "# Trabajo actual\n\nProyecto mapeado sin siguiente flujo inequívoco.\n",
    )


def _seed_sonia_board(project: Path) -> None:
    _seed_mapped_project(project)
    kanban = project / "docs" / "project" / "kanban"
    _write_text(
        kanban / "backlog.md",
        "# Backlog\n\n"
        "### [T-010] Definir mensajes de error de login\n\n"
        "- **Agente:** product-owner\n"
        "- **Criterios:** CA-01\n"
        "- **Notas:** Necesita copy claro para credenciales invalidas.\n",
    )
    _write_text(
        kanban / "in-progress.md",
        "# In Progress\n\n"
        "### [T-011] Ajustar CTA principal\n\n"
        "- **Agente:** senior-dev\n"
        "- **Criterios:** CA-02\n"
        "- **Notas:** Cambio pequeño validable con snapshot.\n",
    )
    _write_text(
        kanban / "done.md",
        "# Done\n\n"
        "### [T-012] Crear fixture base de login\n\n"
        "- **Agente:** senior-dev\n"
        "- **Criterios:** CA-00\n"
        "- **Evidencia:** `node --test tests/login.test.js`.\n",
    )
    _write_text(
        kanban / "blocked.md",
        "# Blocked\n\n"
        "### [T-013] Elegir proveedor OAuth\n\n"
        "- **Agente:** product-owner\n"
        "- **Dependencias:** decision de producto sobre Google/GitHub/email.\n"
        "- **Notas:** No avanzar sin confirmar alcance.\n",
    )
    _write_text(
        project / "docs" / "project" / "progress.md",
        "# Progreso\n\n"
        "- Done: T-012\n"
        "- In progress: T-011\n"
        "- Blocked: T-013\n",
    )
    _write_text(
        project / "docs" / "project" / "traceability.md",
        "# Trazabilidad\n\n"
        "- CA-00 -> T-012 -> `tests/login.test.js`\n"
        "- CA-01 -> T-010 -> pendiente\n"
        "- CA-02 -> T-011 -> en curso\n",
    )


def _seed_active_quick(project: Path) -> None:
    _seed_plain_project(project)
    _write_json(
        project / ".claude" / "alfred-dev-state.json",
        _state_payload("quick", "Cambiar CTA", "ejecucion_acotada", 0),
    )
    _write_text(
        project / "docs" / "project" / "current.md",
        "# Trabajo actual\n\nComando: `/alfred-dev:quick`\n\nGate pendiente: validacion rapida.\n",
    )


def _seed_handoff(project: Path) -> None:
    _seed_plain_project(project)
    _write_json(
        project / ".claude" / "alfred-handoff.json",
        {
            "command": "quick",
            "description": "Cambiar CTA",
            "phase": "ejecucion_acotada",
            "resume_command": "/alfred-dev:resume",
            "resolved": False,
            "next_action": "Retomar ejecucion acotada y validar CTA.",
            "created_at": _iso_now(),
        },
    )
    _write_text(
        project / ".claude" / "alfred-handoff.md",
        "# Handoff Alfred Dev\n\nSiguiente accion: retomar ejecucion acotada.\n",
    )


def _seed_completed_quick(project: Path) -> None:
    _seed_plain_project(project)
    payload = _state_payload("quick", "Cambiar CTA", "completado", 2)
    payload["fases_completadas"] = [
        {
            "nombre": "ejecucion_acotada",
            "completada_en": _iso_now(),
            "resultado": "aprobado",
        }
    ]
    _write_json(project / ".claude" / "alfred-dev-state.json", payload)
    _write_text(project / "docs" / "project" / "uat.md", "# UAT\n\nPendiente de aprobacion humana.\n")


def _write_fake_docker(project: Path, body: str) -> None:
    docker = project / ".alfred-smoke-bin" / "docker"
    _write_text(docker, "#!/usr/bin/env bash\n" + body)
    docker.chmod(0o755)


def _seed_docker_missing(project: Path) -> None:
    _seed_plain_project(project)
    _write_fake_docker(
        project,
        "echo 'docker: command not found' >&2\n"
        "exit 127\n",
    )


def _seed_docker_daemon_down(project: Path) -> None:
    _seed_plain_project(project)
    _write_fake_docker(
        project,
        "if [[ \"${1:-}\" == \"--version\" ]]; then\n"
        "  echo 'Docker version 26.0.0, build smoke'\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"${1:-}\" == \"info\" ]]; then\n"
        "  echo 'Cannot connect to the Docker daemon' >&2\n"
        "  exit 1\n"
        "fi\n"
        "exit 1\n",
    )


SETUPS: dict[str, Callable[[Path], None]] = {
    "plain": _seed_plain_project,
    "mapped_project": _seed_mapped_project,
    "mapped_idle": _seed_mapped_idle,
    "sonia_board": _seed_sonia_board,
    "active_quick": _seed_active_quick,
    "handoff": _seed_handoff,
    "completed_quick": _seed_completed_quick,
    "docker_missing": _seed_docker_missing,
    "docker_daemon_down": _seed_docker_daemon_down,
}


def _select_plugin_dir(value: str | None, use_installed: bool = False) -> tuple[Path, str]:
    if value:
        return Path(value).expanduser().resolve(), "explicit"
    if use_installed:
        return DEFAULT_PLUGIN_DIR, "installed-cache"
    return ROOT, "worktree"


def _iter_plugin_surface_files(plugin_dir: Path) -> list[Path]:
    files: list[Path] = []
    for relative_root in PLUGIN_SURFACE_ROOTS:
        root = plugin_dir / relative_root
        if root.is_file():
            files.append(root)
            continue
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            files.append(path)
    return sorted(files, key=lambda path: str(path.relative_to(plugin_dir)))


def _plugin_surface_snapshot(plugin_dir: Path) -> dict:
    digest = hashlib.sha256()
    files = _iter_plugin_surface_files(plugin_dir)
    for path in files:
        relative = str(path.relative_to(plugin_dir))
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return {
        "roots": list(PLUGIN_SURFACE_ROOTS),
        "file_count": len(files),
        "sha256": digest.hexdigest(),
    }


def _result_status(payload: dict | None, stdout: str, stderr: str, returncode: int) -> tuple[str, str]:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    if payload and payload.get("api_error_status") == 401:
        return "blocked_auth", "Claude CLI devolvio 401 Invalid authentication credentials."
    if "Invalid authentication credentials" in combined or "Failed to authenticate" in combined:
        return "blocked_auth", "Claude CLI no tiene autenticacion valida."
    if payload and payload.get("subtype") == "error_max_budget_usd":
        return "failed", f"claude -p agoto el presupuesto configurado: {payload.get('errors', [])}"
    if returncode != 0:
        return "failed", f"claude -p termino con codigo {returncode}."
    if payload and payload.get("is_error"):
        return "failed", f"claude -p devolvio is_error=true: {payload.get('result', '')}"
    result_text = str(payload.get("result", "")) if payload else stdout
    if not result_text.strip():
        return "failed", "La respuesta vino vacia."
    if "`/alfred feature`" in result_text or "/alfred feature" in result_text:
        return "failed", "La respuesta reintrodujo el prefijo legacy /alfred."
    return "needs_human_review", "Ejecucion completada; revisar respuesta contra el criterio esperado."


def _safe_preview(value: object, limit: int = 2000) -> str:
    """Recorta evidencia textual sin dejar secretos en el JSON de release."""
    return sanitize_text(str(value or "").strip())[:limit]


def _collect_artifact_previews(project: Path) -> dict[str, str]:
    previews: dict[str, str] = {}
    for relative in (
        ".claude/alfred-dev-state.json",
        ".claude/alfred-handoff.json",
        ".claude/alfred-uat.json",
        "docs/project/current.md",
        "docs/project/progress.md",
        "docs/project/traceability.md",
        "docs/project/uat.md",
        "docs/project/codebase-map.md",
        "docs/project/discovery.md",
        "docs/project/github-sync.md",
        ".claude/alfred-github-sync.json",
        ".claude/alfred-memory-ui.json",
    ):
        path = project / relative
        if path.is_file():
            previews[relative] = _safe_preview(
                path.read_text(encoding="utf-8", errors="replace"),
                2000,
            )
    return previews


def _cleanup_case_processes(project: Path) -> None:
    state_path = project / ".claude" / "alfred-memory-ui.json"
    if not state_path.exists():
        return
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "core" / "continuity.py"),
            "memory-ui",
            str(project),
            "--stop",
            "--json",
        ],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
        check=False,
    )


def _run_case(case: ManualCase, plugin_dir: Path, budget: str, timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"alfred-manual-{case.case_id}-") as tmp:
        project = Path(tmp)
        SETUPS[case.setup](project)
        env = os.environ.copy()
        fake_bin = project / ".alfred-smoke-bin"
        if fake_bin.is_dir():
            env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
        command = [
            "claude",
            "-p",
            case.prompt,
            "--plugin-dir",
            str(plugin_dir),
            "--permission-mode",
            "bypassPermissions",
            "--max-budget-usd",
            budget,
            "--no-session-persistence",
            "--output-format",
            "json",
        ]
        started = time.time()
        try:
            result = subprocess.run(
                command,
                cwd=project,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=timeout,
                check=False,
            )
            duration_ms = int((time.time() - started) * 1000)
            artifacts = _collect_artifact_previews(project)
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.time() - started) * 1000)
            artifacts = _collect_artifact_previews(project)
            _cleanup_case_processes(project)
            return {
                **asdict(case),
                "status": "failed",
                "reason": f"claude -p supero el timeout de {timeout} segundos.",
                "duration_ms": duration_ms,
                "returncode": None,
                "api_error_status": None,
                "total_cost_usd": None,
                "artifacts": artifacts,
                "response_preview": _safe_preview(exc.output, 2000),
                "stderr_preview": _safe_preview(exc.stderr, 2000),
            }
        _cleanup_case_processes(project)

    payload = None
    stdout = result.stdout.strip()
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = None
    status, reason = _result_status(payload, result.stdout, result.stderr, result.returncode)
    if payload:
        response_text = payload.get("result") or payload.get("errors") or result.stdout
    else:
        response_text = result.stdout
    return {
        **asdict(case),
        "status": status,
        "reason": reason,
        "duration_ms": duration_ms,
        "returncode": result.returncode,
        "api_error_status": payload.get("api_error_status") if payload else None,
        "total_cost_usd": payload.get("total_cost_usd") if payload else None,
        "artifacts": artifacts,
        "response_preview": _safe_preview(response_text, 2000),
        "stderr_preview": _safe_preview(result.stderr, 2000),
    }


def _summary_payload(
    *,
    plugin_dir: Path,
    plugin_source_label: str,
    plugin_surface: dict,
    preflight: dict | None,
    results: list[dict],
    run_status: str,
) -> dict:
    return {
        "version": VERSION,
        "plugin_dir": str(plugin_dir),
        "plugin_source": plugin_source_label,
        "plugin_surface": plugin_surface,
        "auth_preflight": preflight,
        "run_status": run_status,
        "cases": results,
        "counts": {
            "total": len(results),
            "needs_human_review": sum(1 for item in results if item["status"] == "needs_human_review"),
            "blocked_auth": sum(1 for item in results if item["status"] == "blocked_auth"),
            "failed": sum(1 for item in results if item["status"] == "failed"),
        },
        "command_coverage": _case_command_coverage(),
        "option_coverage": _case_option_coverage(),
        "runtime_coverage": _case_runtime_coverage(),
    }


def _auth_status_snapshot() -> dict:
    """Devuelve diagnostico auth sin imprimir emails, orgs ni tokens."""
    snapshot: dict = {}
    snapshot["credential_env"] = _credential_env_snapshot()
    version = subprocess.run(
        ["claude", "--version"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    snapshot["claude_version"] = version.stdout.strip() or version.stderr.strip()
    status = subprocess.run(
        ["claude", "auth", "status", "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    snapshot["auth_status_returncode"] = status.returncode
    if status.stdout.strip():
        try:
            raw = json.loads(status.stdout)
        except json.JSONDecodeError:
            snapshot["auth_status_parse_error"] = True
            snapshot["auth_status_preview"] = status.stdout.strip()[:300]
        else:
            for key in ("loggedIn", "authMethod", "apiProvider", "subscriptionType"):
                if key in raw:
                    snapshot[key] = raw[key]
    if status.stderr.strip():
        snapshot["auth_status_stderr"] = status.stderr.strip()[:300]
    return snapshot


def _credential_env_snapshot() -> dict[str, bool]:
    """Registra solo presencia de credenciales que pueden alterar auth headless."""
    return {key: bool(os.environ.get(key)) for key in CREDENTIAL_ENV_KEYS}


def _parse_claude_version(value: str | None) -> tuple[int, int, int] | None:
    if not value:
        return None
    prefix = value.strip().split(" ", 1)[0]
    parts = prefix.split(".")
    if len(parts) < 3:
        return None
    try:
        return tuple(int(part) for part in parts[:3])
    except ValueError:
        return None


def _auth_failure_diagnosis(status: str, api_error_status: int | None, auth_status: dict) -> dict:
    """Clasifica el bloqueo de auth sin depender de logs con credenciales."""
    if status == "ok":
        return {
            "code": "ok",
            "summary": "Claude CLI completo una llamada headless minima.",
            "next_steps": [],
        }
    if status == "blocked_auth" and api_error_status == 401:
        credential_env = auth_status.get("credential_env")
        active_credential_env = [
            key
            for key, is_set in (credential_env or {}).items()
            if is_set
        ] if isinstance(credential_env, dict) else []
        if active_credential_env:
            return {
                "code": "environment_credential_rejected",
                "summary": (
                    "claude -p recibio 401 y hay variables de entorno de "
                    "credenciales/proveedor que pueden tener precedencia sobre "
                    "el login de suscripcion."
                ),
                "next_steps": [
                    "Revisar o desactivar temporalmente estas variables antes del preflight: "
                    + ", ".join(active_credential_env),
                    "Repetir npm run release:audit:manual:preflight con el entorno limpio.",
                    "Si el bloqueo persiste sin variables activas, refrescar la sesion con claude auth logout y claude auth login.",
                ],
            }
        if auth_status.get("loggedIn") is True and auth_status.get("apiProvider") == "firstParty":
            version = _parse_claude_version(str(auth_status.get("claude_version", "")))
            next_steps = [
                "Ejecutar claude auth logout y claude auth login para refrescar la sesion local.",
                "Repetir npm run release:audit:manual:preflight.",
                "Ejecutar claude doctor para revisar instalacion, settings, MCP y acceso a credenciales locales.",
                "En macOS, si el login no persiste o doctor apunta a Keychain, desbloquear o resincronizar el login keychain.",
                "Si persiste, probar claude setup-token o escalar a soporte de Claude Code con un log debug saneado.",
            ]
            if version is not None and version < (2, 1, 174):
                next_steps.insert(
                    0,
                    "Ejecutar claude update y repetir el preflight; Claude Code documenta fixes de auth headless a partir de 2.1.174.",
                )
            return {
                "code": "first_party_oauth_token_rejected",
                "summary": (
                    "claude auth status informa login activo, pero claude -p en "
                    "safe-mode recibe 401 antes de consumir tokens del modelo."
                ),
                "next_steps": next_steps,
            }
        if auth_status.get("loggedIn") is False:
            return {
                "code": "not_logged_in",
                "summary": "Claude CLI no tiene una sesion local activa para ejecutar claude -p.",
                "next_steps": [
                    "Ejecutar claude auth login.",
                    "Repetir npm run release:audit:manual:preflight.",
                ],
            }
        return {
            "code": "headless_auth_rejected",
            "summary": "claude -p fue rechazado por autenticacion 401 en la llamada minima.",
            "next_steps": [
                "Revisar claude auth status --json.",
                "Refrescar la sesion con claude auth logout y claude auth login.",
                "Ejecutar claude doctor si la sesion parece activa pero claude -p sigue fallando.",
                "Repetir npm run release:audit:manual:preflight.",
            ],
        }
    if status == "failed":
        return {
            "code": "preflight_failed",
            "summary": "La llamada minima a claude -p fallo por una causa distinta de autenticacion 401.",
            "next_steps": [
                "Revisar returncode, response_preview y stderr_preview en la evidencia JSON.",
                "Repetir con la CLI de Claude actualizada si el error parece de runtime.",
            ],
        }
    return {
        "code": "unknown",
        "summary": "El preflight devolvio un estado no clasificado.",
        "next_steps": ["Revisar la evidencia JSON completa del preflight."],
    }


def _auth_preflight(timeout: int = 45) -> dict:
    """Ejecuta una llamada minima a Claude para detectar credenciales rotas."""
    auth_status = _auth_status_snapshot()
    command = [
        "claude",
        "-p",
        "Responde exactamente: OK",
        "--safe-mode",
        "--tools",
        "",
        "--max-budget-usd",
        "0.05",
        "--no-session-persistence",
        "--output-format",
        "json",
    ]
    started = time.time()
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    duration_ms = int((time.time() - started) * 1000)
    payload = None
    stdout = result.stdout.strip()
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = None
    status, reason = _result_status(payload, result.stdout, result.stderr, result.returncode)
    if status == "needs_human_review":
        status = "ok"
        reason = "Claude CLI pudo completar una llamada minima."
    response_text = payload.get("result", "") if payload else result.stdout
    api_error_status = payload.get("api_error_status") if payload else None
    return {
        "status": status,
        "reason": reason,
        "duration_ms": duration_ms,
        "returncode": result.returncode,
        "api_error_status": api_error_status,
        "total_cost_usd": payload.get("total_cost_usd") if payload else None,
        "auth_status": auth_status,
        "diagnosis": _auth_failure_diagnosis(status, api_error_status, auth_status),
        "preflight_mode": "safe-mode; tools disabled; no session persistence; output json",
        "response_preview": _safe_preview(response_text, 500),
        "stderr_preview": _safe_preview(result.stderr, 500),
    }


def _available_cases() -> str:
    lines = []
    for case in CASES:
        command_label = ",".join(case.commands) if case.commands else "behavior"
        lines.append(f"- {case.case_id}: {case.prompt} [{case.setup}; {command_label}; {case.suite}]")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    plugin_source = parser.add_mutually_exclusive_group()
    plugin_source.add_argument("--plugin-dir", help="Directorio del plugin a pasar a claude -p.")
    plugin_source.add_argument(
        "--installed",
        action="store_true",
        help="Usa la cache instalada de Claude en vez del worktree actual.",
    )
    parser.add_argument("--case", action="append", help="ID de caso a ejecutar. Repetible.")
    parser.add_argument("--budget", default="1.50", help="Presupuesto por prompt en USD.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout por prompt en segundos.",
    )
    parser.add_argument("--output", help="Ruta JSON donde guardar la evidencia.")
    parser.add_argument("--dry-run", action="store_true", help="Lista casos y no ejecuta Claude.")
    parser.add_argument(
        "--auth-preflight",
        action="store_true",
        help="Ejecuta una llamada minima a claude -p antes de lanzar casos.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Con --auth-preflight, valida autenticacion y no ejecuta la matriz manual.",
    )
    parser.add_argument(
        "--allow-auth-failure",
        action="store_true",
        help="Devuelve 0 si la unica causa de bloqueo es autenticacion 401.",
    )
    args = parser.parse_args(argv)

    selected_ids = args.case or [case.case_id for case in CASES]
    known = {case.case_id: case for case in CASES}
    unknown = [case_id for case_id in selected_ids if case_id not in known]
    if unknown:
        print(f"Casos desconocidos: {', '.join(unknown)}\n\nDisponibles:\n{_available_cases()}", file=sys.stderr)
        return 2
    selected = [known[case_id] for case_id in selected_ids]

    plugin_dir, plugin_source_label = _select_plugin_dir(args.plugin_dir, args.installed)
    if args.dry_run:
        print(f"plugin_dir={plugin_dir}")
        print(f"plugin_source={plugin_source_label}")
        print(_available_cases())
        print(_coverage_summary())
        return 0
    if not shutil.which("claude"):
        print("FAIL manual-smoke: claude CLI no esta en PATH.", file=sys.stderr)
        return 2
    if not plugin_dir.exists():
        print(f"FAIL manual-smoke: plugin-dir no existe: {plugin_dir}", file=sys.stderr)
        return 2
    plugin_surface = _plugin_surface_snapshot(plugin_dir)

    preflight = None
    if args.auth_preflight:
        preflight = _auth_preflight(timeout=min(args.timeout, 45))
        if preflight["status"] != "ok":
            summary = {
                "version": VERSION,
                "plugin_dir": str(plugin_dir),
                "plugin_source": plugin_source_label,
                "plugin_surface": plugin_surface,
                "auth_preflight": preflight,
                "run_status": "blocked",
                "cases": [],
                "counts": {
                    "total": 0,
                    "needs_human_review": 0,
                    "blocked_auth": 1 if preflight["status"] == "blocked_auth" else 0,
                    "failed": 1 if preflight["status"] == "failed" else 0,
                },
                "command_coverage": _case_command_coverage(),
                "option_coverage": _case_option_coverage(),
                "runtime_coverage": _case_runtime_coverage(),
            }
            if args.output:
                output_path = Path(args.output).expanduser()
                _write_json(output_path, summary)
                print(f"evidence={output_path}")
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            if preflight["status"] == "blocked_auth" and args.allow_auth_failure:
                return 0
            return 1 if preflight["status"] == "failed" else 2
        if args.preflight_only:
            summary = {
                "version": VERSION,
                "plugin_dir": str(plugin_dir),
                "plugin_source": plugin_source_label,
                "plugin_surface": plugin_surface,
                "auth_preflight": preflight,
                "run_status": "preflight-only",
                "cases": [],
                "counts": {
                    "total": 0,
                    "needs_human_review": 0,
                    "blocked_auth": 0,
                    "failed": 0,
                },
                "command_coverage": _case_command_coverage(),
                "option_coverage": _case_option_coverage(),
                "runtime_coverage": _case_runtime_coverage(),
            }
            if args.output:
                output_path = Path(args.output).expanduser()
                _write_json(output_path, summary)
                print(f"evidence={output_path}")
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0

    output_path = Path(args.output).expanduser() if args.output else None
    results: list[dict] = []
    if output_path:
        _write_json(
            output_path,
            _summary_payload(
                plugin_dir=plugin_dir,
                plugin_source_label=plugin_source_label,
                plugin_surface=plugin_surface,
                preflight=preflight,
                results=results,
                run_status="running",
            ),
        )
        print(f"evidence={output_path}", file=sys.stderr)

    for index, case in enumerate(selected, start=1):
        print(
            f"[{index}/{len(selected)}] {case.case_id}: {case.prompt}",
            file=sys.stderr,
            flush=True,
        )
        results.append(_run_case(case, plugin_dir, args.budget, args.timeout))
        if output_path:
            _write_json(
                output_path,
                _summary_payload(
                    plugin_dir=plugin_dir,
                    plugin_source_label=plugin_source_label,
                    plugin_surface=plugin_surface,
                    preflight=preflight,
                    results=results,
                    run_status="running",
                ),
            )

    summary = _summary_payload(
        plugin_dir=plugin_dir,
        plugin_source_label=plugin_source_label,
        plugin_surface=plugin_surface,
        preflight=preflight,
        results=results,
        run_status="complete",
    )
    if args.output:
        _write_json(output_path, summary)
        print(f"evidence={output_path}")

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if summary["counts"]["failed"]:
        return 1
    if summary["counts"]["blocked_auth"]:
        if args.allow_auth_failure and summary["counts"]["blocked_auth"] == summary["counts"]["total"]:
            return 0
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
