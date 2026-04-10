#!/usr/bin/env python3
"""Tests para la capa PM determinista y sync GitHub de Alfred 0.4.5."""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.continuity import (  # noqa: E402
    GITHUB_SYNC_JSON_RELATIVE_PATH,
    GITHUB_SYNC_MD_RELATIVE_PATH,
    KANBAN_BACKLOG_RELATIVE_PATH,
    _append_helper_list_artifact,
    build_lane_snapshot,
    build_standup_snapshot,
    create_kanban_task,
    load_kanban_board,
    move_kanban_task,
    normalize_kanban_task_types,
    render_lane_markdown,
    render_standup_markdown,
    render_validation_markdown,
    search_project_context,
    sync_project_to_github,
    validate_operational_artifacts,
)
from core.memory import MemoryDB  # noqa: E402


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


class TestPmHelpers(unittest.TestCase):
    def _seed_board(self, tmpdir: str) -> None:
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
            """# Backlog

### [T-001] Diseñar login

- **Historia:** HU-01
- **Criterios:** CA-01, CA-02
- **Agente:** architect
- **Dependencias:** ninguna
- **Notas:** Aterrizar el flujo base
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
            """# In Progress

### [T-002] Implementar endpoint POST /login

- **Historia:** HU-01
- **Criterios:** CA-01, CA-03
- **Agente:** senior-dev
- **Dependencias:** T-001
- **Notas:** Pendiente de cerrar tests de error
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "done.md"),
            """# Done

### [T-003] Preparar esquema de usuarios

- **Historia:** HU-01
- **Criterios:** CA-01
- **Agente:** data-engineer
- **Evidencia:** tests/test_users.py::test_schema_users
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"),
            """# Blocked

### [T-004] Integrar sesión persistente

- **Historia:** HU-01
- **Criterios:** CA-04
- **Agente:** senior-dev
- **Dependencias:** Decisión de cookies seguras
- **Notas:** Bloqueado por criterio legal pendiente
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "progress.md"),
            "# Progreso\n\n- Login base ya modelado\n- Queda cerrar la persistencia de sesión\n",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "traceability.md"),
            "# Traceability\n\n- CA-01 -> T-001, T-002, T-003\n- CA-02 -> T-001\n- CA-03 -> T-002\n- CA-04 -> T-004\n",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "current.md"),
            "# Current\n\n- Estado: implementación en curso\n- Comando recomendado: /alfred-dev:verify\n",
        )

    def test_load_kanban_board_parses_heading_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            board = load_kanban_board(tmpdir)

        self.assertEqual(board["backlog"][0]["id"], "T-001")
        self.assertEqual(board["in-progress"][0]["agent"], "senior-dev")
        self.assertEqual(board["done"][0]["evidence"], "tests/test_users.py::test_schema_users")
        self.assertEqual(board["blocked"][0]["dependencies"], "Decisión de cookies seguras")

    def test_load_kanban_board_accepts_deeper_headings_and_bold_colon_outside(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                """# Backlog

#### [T-101] Diseñar login

- **Agente**: architect
- **Criterios**: CA-01, CA-02
""",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"), "# In Progress\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")

            board = load_kanban_board(tmpdir)

        self.assertEqual(board["backlog"][0]["id"], "T-101")
        self.assertEqual(board["backlog"][0]["agent"], "architect")
        self.assertEqual(board["backlog"][0]["criteria"], ["CA-01", "CA-02"])

    def test_load_kanban_board_accepts_checkbox_tasks_with_nested_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                """# Backlog

- [ ] [T-102] Diseñar login
  - Agente: architect
  - Criterios: CA-01
  - Dependencias: ninguna
""",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"), "# In Progress\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")

            board = load_kanban_board(tmpdir)

        self.assertEqual(board["backlog"][0]["id"], "T-102")
        self.assertEqual(board["backlog"][0]["agent"], "architect")
        self.assertEqual(board["backlog"][0]["criteria"], ["CA-01"])
        self.assertEqual(board["backlog"][0]["dependencies"], "ninguna")

    def test_normalize_kanban_task_types_upgrades_legacy_runtime_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                """# Backlog

### [T-010] Validar 'Login' con /alfred-dev:verify.

- **Agente:** alfred:verify
""",
            )
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
                """# In Progress

### [T-011] Login

- **Agente:** alfred:feature
- **Notas:** Fase actual: producto. Fases completadas: ninguna.

### [T-012] feature:producto — Login

- **Agente:** analyst
""",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")

            result = normalize_kanban_task_types(tmpdir)
            board = load_kanban_board(tmpdir)

        self.assertEqual(result["count"], 3)
        self.assertEqual(board["backlog"][0]["task_type"], "verify")
        self.assertEqual(board["in-progress"][0]["task_type"], "main")
        self.assertEqual(board["in-progress"][1]["task_type"], "phase")

    def test_helper_append_keeps_structured_kanban_parseable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, KANBAN_BACKLOG_RELATIVE_PATH),
                """# Backlog

### [T-001] Diseñar login

- **Agente:** architect
- **Notas:** flujo base
""",
            )

            _append_helper_list_artifact(
                tmpdir,
                KANBAN_BACKLOG_RELATIVE_PATH,
                title="Backlog",
                intro="Pendiente por atacar a continuación.",
                items=["Validar con /alfred-dev:feature"],
                task_agent="alfred:test",
            )

            board = load_kanban_board(tmpdir)

            with open(os.path.join(tmpdir, KANBAN_BACKLOG_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                markdown = fh.read()

        self.assertEqual(len(board["backlog"]), 2)
        self.assertEqual(board["backlog"][0]["id"], "T-001")
        self.assertEqual(board["backlog"][0]["notes"], "flujo base")
        self.assertEqual(board["backlog"][1]["id"], "T-002")
        self.assertEqual(board["backlog"][1]["agent"], "alfred:test")
        self.assertEqual(board["backlog"][1]["title"], "Validar con /alfred-dev:feature")
        self.assertIn("### [T-002] Validar con /alfred-dev:feature", markdown)

    def test_create_and_move_kanban_task_preserve_id_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)

            created = create_kanban_task(
                tmpdir,
                "backlog",
                title="Preparar UAT final",
                agent="alfred:discuss",
                notes="Pendiente al cerrar desarrollo.",
            )
            moved = move_kanban_task(
                tmpdir,
                created["id"],
                "in-progress",
                agent="qa-engineer",
                dependencies="T-002",
            )
            board = load_kanban_board(tmpdir)

        self.assertEqual(created["id"], "T-005")
        self.assertEqual(moved["id"], "T-005")
        self.assertEqual(moved["status"], "in-progress")
        self.assertEqual(moved["agent"], "qa-engineer")
        self.assertEqual(moved["dependencies"], "T-002")
        self.assertFalse(any(task["id"] == "T-005" for task in board["backlog"]))
        self.assertTrue(any(task["id"] == "T-005" for task in board["in-progress"]))

    def test_standup_snapshot_and_render_include_focus_and_next(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            snapshot = build_standup_snapshot(tmpdir)
            content = render_standup_markdown(snapshot)

        self.assertIn("## Standup diario", content)
        self.assertIn("[T-002] Implementar endpoint POST /login", content)
        self.assertIn("[T-004] Integrar sesión persistente", content)
        self.assertIn("/alfred-dev:verify", content)

    def test_standup_snapshot_lists_latest_done_tasks_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "done.md"),
                """# Done

### [T-003] Preparar esquema de usuarios

- **Agente:** data-engineer
- **Evidencia:** tests/test_users.py::test_schema_users

### [T-009] Cerrar UAT de login

- **Agente:** qa-engineer
- **Evidencia:** docs/project/uat.md
""",
            )

            snapshot = build_standup_snapshot(tmpdir)

        self.assertEqual(snapshot["focus"]["done"][0], "[T-009] Cerrar UAT de login — qa-engineer")

    def test_lane_snapshot_renders_blocked_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            snapshot = build_lane_snapshot(tmpdir, "blocked")
            content = render_lane_markdown(snapshot)

        self.assertIn("Tareas en blocked", content)
        self.assertIn("Decisión de cookies seguras", content)

    def test_validate_detects_warnings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "done.md"),
                """# Done

### [T-003] Preparar esquema de usuarios

- **Historia:** HU-01
- **Criterios:** CA-01
- **Agente:** data-engineer
""",
            )
            report = validate_operational_artifacts(tmpdir)
            content = render_validation_markdown(report)

        self.assertEqual(report["status"], "warning")
        self.assertIn("### Resumen", content)
        self.assertIn("- Avisos: 1", content)
        self.assertIn("done sin evidencia", content)

    def test_validate_warns_when_uat_is_stale_for_latest_completed_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)

            stale_uat = {
                "version": 1,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "target_id": "session:feature:old",
                "target_source": "completed-session",
                "target_command": "feature",
                "target_description": "login antiguo",
                "target_completed_at": "2026-01-01T00:00:00+00:00",
                "status": "approved",
                "checklist": [],
                "notes": "",
                "next_command": "/alfred-dev:alfred",
            }
            _write(
                os.path.join(tmpdir, ".claude", "alfred-uat.json"),
                json.dumps(stale_uat, ensure_ascii=False, indent=2),
            )

            from core.orchestrator import advance_phase, create_session, save_state  # noqa: E402

            session = create_session("feature", "Login y usuarios")
            while session["fase_actual"] != "completado":
                session = advance_phase(session, resultado="aprobado", artefactos=[])
            save_state(session, os.path.join(tmpdir, ".claude", "alfred-dev-state.json"))

            report = validate_operational_artifacts(tmpdir)
            content = render_validation_markdown(report)

        self.assertEqual(report["status"], "warning")
        self.assertIn("no cubre el último flujo completado", content)

    def test_validate_does_not_require_evidence_for_skipped_phase_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)

            from core.orchestrator import advance_phase, create_session, save_state  # noqa: E402

            session = create_session("feature", "Login sin UI")
            session["stack"] = {"runtime": "python", "framework": "fastapi"}
            session = advance_phase(session, resultado="aprobado", artefactos=["docs/producto.md"])
            save_state(session, os.path.join(tmpdir, ".claude", "alfred-dev-state.json"))

            report = validate_operational_artifacts(tmpdir)

        self.assertIn(report["status"], {"ok", "warning"})
        self.assertFalse(
            any("feature:estilo_visual" in warning and "done sin evidencia" in warning for warning in report["warnings"])
        )

    def test_validate_warns_when_completed_estilo_visual_has_no_style_direction_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)

            from core.orchestrator import advance_phase, create_session, save_state  # noqa: E402

            session = create_session("feature", "Login con UI")
            session = advance_phase(session, resultado="aprobado", artefactos=["docs/producto.md"])
            session = advance_phase(session, resultado="aprobado", artefactos=[])
            save_state(session, os.path.join(tmpdir, ".claude", "alfred-dev-state.json"))

            report = validate_operational_artifacts(tmpdir)

        self.assertEqual(report["status"], "warning")
        self.assertTrue(
            any("estilo_visual figura como completada" in warning for warning in report["warnings"])
        )

    def test_validate_ignores_internal_tasks_for_sync_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                """# Backlog

### [T-010] Validar 'Login' con /alfred-dev:verify.

- **Agente:** alfred:verify
""",
            )
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
                """# In Progress

### [T-011] Login

- **Agente:** alfred:feature

### [T-012] feature:producto — Login

- **Agente:** analyst
""",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")
            _write(os.path.join(tmpdir, "docs", "project", "traceability.md"), "# Traceability\n")
            _write(os.path.join(tmpdir, "docs", "project", "progress.md"), "# Progress\n")
            _write(
                os.path.join(tmpdir, ".claude", "alfred-github-sync.json"),
                json.dumps(
                    {
                        "version": 1,
                        "repo": "686f6c61/alfred-e2e",
                        "tasks": {"T-011": {"number": 101}},
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            report = validate_operational_artifacts(tmpdir)

        self.assertFalse(any("T-012" in warning for warning in report["warnings"]))
        self.assertFalse(any("T-010" in warning for warning in report["warnings"]))

    def test_validate_warns_when_sync_map_keeps_tasks_missing_from_local_board(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            _write(
                os.path.join(tmpdir, ".claude", "alfred-github-sync.json"),
                json.dumps(
                    {
                        "version": 1,
                        "repo": "686f6c61/alfred-e2e",
                        "tasks": {
                            "T-010": {"number": 101},
                            "T-011": {"number": 102},
                            "T-099": {"number": 199},
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            report = validate_operational_artifacts(tmpdir)
            content = render_validation_markdown(report)

        self.assertEqual(report["status"], "warning")
        self.assertIn("ya no existen en el kanban local", content)
        self.assertIn("T-099", content)

    def test_search_finds_docs_and_memory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            db_path = os.path.join(tmpdir, ".claude", "alfred-memory.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db = MemoryDB(db_path)
            try:
                iteration_id = db.start_iteration("feature", "Login")
                db.log_decision(
                    title="Cookies seguras en login",
                    chosen="Usar cookies HttpOnly",
                    context="Autenticación web",
                    rationale="Evita acceso desde JS",
                    iteration_id=iteration_id,
                )
            finally:
                db.close()

            result = search_project_context(tmpdir, "login")

        self.assertTrue(result["docs"])
        self.assertTrue(result["memory"])

    def test_cli_standup_and_search_modes_support_direct_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            continuity_script = os.path.join(
                os.path.dirname(__file__), "..", "core", "continuity.py"
            )
            standup = subprocess.run(
                [sys.executable, continuity_script, "standup", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )
            search = subprocess.run(
                [sys.executable, continuity_script, "search", tmpdir, "--raw", "login"],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(standup.returncode, 0, msg=standup.stderr)
        self.assertIn("## Standup diario", standup.stdout)
        self.assertEqual(search.returncode, 0, msg=search.stderr)
        self.assertIn("## Resultados para `login`", search.stdout)

    def test_cli_normalize_kanban_normalizes_legacy_task_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                """# Backlog

### [T-010] Validar 'Login' con /alfred-dev:verify.

- **Agente:** alfred:verify
""",
            )
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
                """# In Progress

### [T-011] Login

- **Agente:** alfred:feature

### [T-012] feature:producto — Login

- **Agente:** analyst
""",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")

            continuity_script = os.path.join(
                os.path.dirname(__file__), "..", "core", "continuity.py"
            )
            proc = subprocess.run(
                [sys.executable, continuity_script, "normalize-kanban", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )
            board = load_kanban_board(tmpdir)

        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("## Normalización de kanban", proc.stdout)
        self.assertIn("Tareas ajustadas: 3", proc.stdout)
        self.assertEqual(board["backlog"][0]["task_type"], "verify")
        self.assertEqual(board["in-progress"][0]["task_type"], "main")
        self.assertEqual(board["in-progress"][1]["task_type"], "phase")


class TestGitHubSyncHelpers(unittest.TestCase):
    def _seed_board(self, tmpdir: str) -> None:
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
            """# Backlog

### [T-010] Preparar labels de issues

- **Agente:** github-manager
- **Criterios:** CA-10
""",
        )
        _write(
            os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
            """# In Progress

### [T-011] Sincronizar tablero

- **Agente:** project-manager
- **Criterios:** CA-11
""",
        )
        _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
        _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")
        _write(os.path.join(tmpdir, "docs", "project", "traceability.md"), "# Traceability\n\n- CA-10 -> T-010\n- CA-11 -> T-011\n")

    def test_sync_project_to_github_writes_mapping_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)

            created = {}

            def fake_create_or_update_issue(repo, task, sync_state):
                number = 100 + len(created) + 1
                payload = {
                    "number": number,
                    "url": f"https://github.com/{repo}/issues/{number}",
                    "title": f"[{task['id']}] {task['title']}",
                    "status": task["status"],
                    "updated_at": "2026-03-22T00:00:00+00:00",
                }
                created[task["id"]] = payload
                return payload

            with mock.patch("core.continuity._ensure_gh_ready"), \
                mock.patch("core.continuity._ensure_github_labels"), \
                mock.patch("core.continuity._detect_github_repo", return_value="686f6c61/alfred-e2e"), \
                mock.patch("core.continuity._create_or_update_issue", side_effect=fake_create_or_update_issue), \
                mock.patch(
                    "core.continuity._ensure_board_issue",
                    return_value={
                        "number": 99,
                        "url": "https://github.com/686f6c61/alfred-e2e/issues/99",
                        "title": "SonIA Sync: alfred-e2e",
                    },
                ):
                result = sync_project_to_github(tmpdir)

            self.assertEqual(result["repo"], "686f6c61/alfred-e2e")
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH)))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH)))

            with open(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            with open(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                markdown = fh.read()

        self.assertEqual(payload["repo"], "686f6c61/alfred-e2e")
        self.assertIn("T-010", payload["tasks"])
        self.assertIn("SonIA Sync", markdown)
        self.assertIn("#101", markdown)
        self.assertNotIn("[T-010] [T-010]", markdown)

    def test_sync_project_to_github_rejects_duplicate_task_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                """# Backlog

### [T-010] Preparar labels de issues

- **Agente:** github-manager
""",
            )
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
                """# In Progress

### [T-010] Sincronizar tablero

- **Agente:** project-manager
""",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")
            _write(os.path.join(tmpdir, "docs", "project", "traceability.md"), "# Traceability\n")
            _write(os.path.join(tmpdir, "docs", "project", "progress.md"), "# Progress\n")

            with self.assertRaises(RuntimeError) as ctx:
                sync_project_to_github(tmpdir)

        self.assertIn("no se puede sincronizar de forma fiable", str(ctx.exception))
        self.assertIn("T-010", str(ctx.exception))

    def test_sync_project_to_github_requires_at_least_one_task_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                "# Backlog\n\n- Preparar labels sin identificador\n",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"), "# In Progress\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")
            _write(os.path.join(tmpdir, "docs", "project", "traceability.md"), "# Traceability\n")
            _write(os.path.join(tmpdir, "docs", "project", "progress.md"), "# Progress\n")

            with self.assertRaises(RuntimeError) as ctx:
                sync_project_to_github(tmpdir)

        self.assertIn("No hay tareas con identificador", str(ctx.exception))

    def test_sync_project_to_github_omits_internal_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"),
                """# Backlog

### [T-010] Validar 'Login' con /alfred-dev:verify.

- **Agente:** alfred:verify
""",
            )
            _write(
                os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"),
                """# In Progress

### [T-011] Login

- **Agente:** alfred:feature

### [T-012] feature:producto — Login

- **Agente:** analyst
""",
            )
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "# Done\n")
            _write(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "# Blocked\n")
            _write(os.path.join(tmpdir, "docs", "project", "traceability.md"), "# Traceability\n")
            _write(os.path.join(tmpdir, "docs", "project", "progress.md"), "# Progress\n")

            created = {}

            def fake_create_or_update_issue(repo, task, sync_state):
                number = 100 + len(created) + 1
                payload = {
                    "number": number,
                    "url": f"https://github.com/{repo}/issues/{number}",
                    "title": f"[{task['id']}] {task['title']}",
                    "status": task["status"],
                    "updated_at": "2026-03-22T00:00:00+00:00",
                }
                created[task["id"]] = payload
                return payload

            with mock.patch("core.continuity._ensure_gh_ready"), \
                mock.patch("core.continuity._ensure_github_labels"), \
                mock.patch("core.continuity._detect_github_repo", return_value="686f6c61/alfred-e2e"), \
                mock.patch("core.continuity._create_or_update_issue", side_effect=fake_create_or_update_issue), \
                mock.patch(
                    "core.continuity._ensure_board_issue",
                    return_value={
                        "number": 99,
                        "url": "https://github.com/686f6c61/alfred-e2e/issues/99",
                        "title": "SonIA Sync: alfred-e2e",
                    },
                ):
                result = sync_project_to_github(tmpdir)

        self.assertEqual([task["id"] for task in result["tasks"]], ["T-011"])
        self.assertEqual(sorted(task["id"] for task in result["internal_omitted"]), ["T-010", "T-012"])

    def test_sync_project_to_github_retires_stale_remote_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            _write(
                os.path.join(tmpdir, ".claude", "alfred-github-sync.json"),
                json.dumps(
                    {
                        "version": 1,
                        "repo": "686f6c61/alfred-e2e",
                        "tasks": {
                            "T-010": {"number": 101, "title": "[T-010] Preparar labels de issues"},
                            "T-011": {"number": 102, "title": "[T-011] Sincronizar tablero"},
                            "T-099": {"number": 199, "title": "[T-099] Tarea vieja"},
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            created = {}

            def fake_create_or_update_issue(repo, task, sync_state):
                number = 100 + len(created) + 1
                payload = {
                    "number": number,
                    "url": f"https://github.com/{repo}/issues/{number}",
                    "title": f"[{task['id']}] {task['title']}",
                    "status": task["status"],
                    "updated_at": "2026-03-22T00:00:00+00:00",
                }
                created[task["id"]] = payload
                return payload

            retired_calls = []

            with mock.patch("core.continuity._ensure_gh_ready"), \
                mock.patch("core.continuity._ensure_github_labels"), \
                mock.patch("core.continuity._detect_github_repo", return_value="686f6c61/alfred-e2e"), \
                mock.patch("core.continuity._create_or_update_issue", side_effect=fake_create_or_update_issue), \
                mock.patch(
                    "core.continuity._ensure_board_issue",
                    return_value={
                        "number": 99,
                        "url": "https://github.com/686f6c61/alfred-e2e/issues/99",
                        "title": "SonIA Sync: alfred-e2e",
                    },
                ), \
                mock.patch(
                    "core.continuity._retire_missing_synced_issues",
                    side_effect=lambda repo, previous_map, active_ids: retired_calls.append(
                        (repo, sorted(previous_map.keys()), sorted(active_ids))
                    ) or [
                        {
                            "id": "T-099",
                            "number": 199,
                            "url": "https://github.com/686f6c61/alfred-e2e/issues/199",
                            "title": "[T-099] Tarea vieja",
                            "retired_at": "2026-03-22T00:00:00+00:00",
                        }
                    ],
                ):
                result = sync_project_to_github(tmpdir)

            with open(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            with open(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                markdown = fh.read()

        self.assertEqual(retired_calls[0][0], "686f6c61/alfred-e2e")
        self.assertIn("T-099", retired_calls[0][1])
        self.assertEqual(sorted(result["retired"][0].keys())[:2], ["id", "number"])
        self.assertIn("retired", payload)
        self.assertEqual(payload["retired"][0]["id"], "T-099")
        self.assertIn("Issues retiradas por drift local: 1", markdown)
        self.assertIn("Tarea vieja", markdown)

    def test_sync_project_to_github_persists_remote_drift_repairs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)

            created = {}

            def fake_create_or_update_issue(repo, task, sync_state):
                number = 300 + len(created) + 1
                payload = {
                    "number": number,
                    "url": f"https://github.com/{repo}/issues/{number}",
                    "title": f"[{task['id']}] {task['title']}",
                    "status": task["status"],
                    "updated_at": "2026-04-09T00:00:00+00:00",
                }
                if task["id"] == "T-010":
                    payload["drift"] = {
                        "scope": "task",
                        "kind": "missing_remote_issue",
                        "task_id": "T-010",
                        "title": "[T-010] Preparar labels de issues",
                        "previous_number": 41,
                        "resolution": "recreated",
                        "number": number,
                        "url": payload["url"],
                    }
                created[task["id"]] = payload
                return payload

            board_payload = {
                "number": 99,
                "url": "https://github.com/686f6c61/alfred-e2e/issues/99",
                "title": "SonIA Sync: alfred-e2e",
                "drift": {
                    "scope": "board",
                    "kind": "missing_remote_issue",
                    "title": "SonIA Sync: alfred-e2e",
                    "previous_number": 12,
                    "resolution": "recreated",
                    "number": 99,
                    "url": "https://github.com/686f6c61/alfred-e2e/issues/99",
                },
            }

            with mock.patch("core.continuity._ensure_gh_ready"), \
                mock.patch("core.continuity._ensure_github_labels"), \
                mock.patch("core.continuity._detect_github_repo", return_value="686f6c61/alfred-e2e"), \
                mock.patch("core.continuity._create_or_update_issue", side_effect=fake_create_or_update_issue), \
                mock.patch("core.continuity._ensure_board_issue", return_value=board_payload), \
                mock.patch("core.continuity._retire_missing_synced_issues", return_value=[]):
                result = sync_project_to_github(tmpdir)

            with open(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            with open(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                markdown = fh.read()

        self.assertEqual(len(result["remote_drift"]), 2)
        self.assertEqual(len(payload["remote_drift"]), 2)
        self.assertIn("Drift remoto corregido: 2", markdown)
        self.assertIn("[T-010] Preparar labels de issues — #41 ya no existía en remoto; recreada como #301.", markdown)
        self.assertIn("Issue paraguas SonIA Sync", markdown)

    def test_rendered_sync_markdown_includes_remote_drift_section(self):
        from core.continuity import render_github_sync_markdown  # noqa: E402

        markdown = render_github_sync_markdown(
            {
                "repo": "686f6c61/alfred-e2e",
                "board_issue": {"url": "https://github.com/686f6c61/alfred-e2e/issues/9"},
                "tasks": [],
                "skipped": [],
                "retired": [],
                "next_action": {
                    "command": "ship",
                    "reason": "El tablero remoto ya quedó coherente.",
                    "source": "current",
                    "source_label": "estado operativo actual",
                    "focus": "Cerrar la entrega",
                    "directive": "Continúa con el cierre de release y la validación final.",
                },
                "remote_drift": [
                    {
                        "scope": "task",
                        "title": "[T-010] Preparar labels de issues",
                        "previous_number": 101,
                        "number": 201,
                        "resolution": "relinked",
                    },
                    {
                        "scope": "board",
                        "title": "SonIA Sync: alfred-e2e",
                        "previous_number": 9,
                        "number": 11,
                        "resolution": "recreated",
                    },
                ],
            }
        )

        self.assertIn("### Drift remoto corregido", markdown)
        self.assertIn("[T-010] Preparar labels de issues — #101 ya no cuadraba; religada a #201.", markdown)
        self.assertIn("Issue paraguas SonIA Sync — #9 ya no existía en remoto; recreada como #11.", markdown)
        self.assertIn("Foco operativo actual: Cerrar la entrega", markdown)
        self.assertIn("Fuente de la recomendación: estado operativo actual (`current`)", markdown)
        self.assertIn("Siguiente paso recomendado: `/alfred-dev:ship`", markdown)
        self.assertIn("Qué hacer ahora: Continúa con el cierre de release y la validación final.", markdown)

    def test_cli_sync_github_supports_end_to_end_with_fake_gh(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._seed_board(tmpdir)
            _write(
                os.path.join(tmpdir, "package.json"),
                json.dumps({"name": "alfred-e2e-pm"}, ensure_ascii=False),
            )
            subprocess.run(["git", "-C", tmpdir, "init", "-q"], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    tmpdir,
                    "remote",
                    "add",
                    "origin",
                    "git@github.com:686f6c61/alfred-e2e-pm.git",
                ],
                check=True,
            )

            fake_bin = os.path.join(tmpdir, "fake-bin")
            os.makedirs(fake_bin, exist_ok=True)
            gh_state = os.path.join(tmpdir, "gh-state.json")
            gh_script = os.path.join(fake_bin, "gh")
            _write(
                gh_script,
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    import os
                    import re
                    import sys

                    state_path = os.environ["GH_STUB_STATE"]
                    if os.path.exists(state_path):
                        with open(state_path, "r", encoding="utf-8") as fh:
                            state = json.load(fh)
                    else:
                        state = {"issues": [], "labels": [], "next_issue": 1}

                    def save():
                        with open(state_path, "w", encoding="utf-8") as fh:
                            json.dump(state, fh, ensure_ascii=False, indent=2)

                    def issue_payload(issue):
                        return {
                            "number": issue["number"],
                            "title": issue["title"],
                            "state": issue["state"],
                            "url": issue["url"],
                            "labels": [{"name": label} for label in issue.get("labels", [])],
                        }

                    args = sys.argv[1:]
                    if args == ["--version"]:
                        print("gh version 0.0.0-fake")
                        raise SystemExit(0)
                    if args[:3] == ["auth", "status", "-h"]:
                        print("github.com\\n  ✓ Logged in")
                        raise SystemExit(0)
                    if args[:2] == ["label", "create"]:
                        name = args[2]
                        if name not in state["labels"]:
                            state["labels"].append(name)
                            save()
                        raise SystemExit(0)
                    if args[:2] == ["issue", "view"]:
                        number = int(args[2])
                        for issue in state["issues"]:
                            if issue["number"] == number:
                                print(json.dumps(issue_payload(issue), ensure_ascii=False))
                                raise SystemExit(0)
                        raise SystemExit(1)
                    if args[:2] == ["issue", "list"]:
                        label = None
                        title = None
                        for idx, token in enumerate(args):
                            if token == "--label":
                                label = args[idx + 1]
                            elif token == "--search":
                                raw = args[idx + 1]
                                match = re.match(r'"(?P<title>.*)" in:title', raw)
                                title = match.group("title") if match else raw
                        matches = []
                        for issue in state["issues"]:
                            if label and label not in issue.get("labels", []):
                                continue
                            if title and issue["title"] != title:
                                continue
                            matches.append(issue_payload(issue))
                        print(json.dumps(matches, ensure_ascii=False))
                        raise SystemExit(0)
                    if args[:2] == ["issue", "create"]:
                        repo = ""
                        title = ""
                        body = ""
                        labels = []
                        idx = 2
                        while idx < len(args):
                            token = args[idx]
                            if token == "--repo":
                                repo = args[idx + 1]
                                idx += 2
                            elif token == "--title":
                                title = args[idx + 1]
                                idx += 2
                            elif token == "--body":
                                body = args[idx + 1]
                                idx += 2
                            elif token == "--label":
                                labels.append(args[idx + 1])
                                idx += 2
                            else:
                                idx += 1
                        number = state["next_issue"]
                        state["next_issue"] += 1
                        issue = {
                            "number": number,
                            "title": title,
                            "body": body,
                            "state": "OPEN",
                            "url": f"https://github.com/{repo}/issues/{number}",
                            "labels": labels,
                        }
                        state["issues"].append(issue)
                        save()
                        print(issue["url"])
                        raise SystemExit(0)
                    if args[:2] == ["issue", "edit"]:
                        number = int(args[2])
                        issue = next(item for item in state["issues"] if item["number"] == number)
                        idx = 3
                        while idx < len(args):
                            token = args[idx]
                            if token == "--title":
                                issue["title"] = args[idx + 1]
                                idx += 2
                            elif token == "--body":
                                issue["body"] = args[idx + 1]
                                idx += 2
                            elif token == "--add-label":
                                label = args[idx + 1]
                                if label not in issue["labels"]:
                                    issue["labels"].append(label)
                                idx += 2
                            elif token == "--remove-label":
                                label = args[idx + 1]
                                issue["labels"] = [item for item in issue["labels"] if item != label]
                                idx += 2
                            else:
                                idx += 1
                        save()
                        raise SystemExit(0)
                    if args[:2] == ["issue", "close"]:
                        number = int(args[2])
                        issue = next(item for item in state["issues"] if item["number"] == number)
                        issue["state"] = "CLOSED"
                        save()
                        raise SystemExit(0)
                    if args[:2] == ["issue", "reopen"]:
                        number = int(args[2])
                        issue = next(item for item in state["issues"] if item["number"] == number)
                        issue["state"] = "OPEN"
                        save()
                        raise SystemExit(0)

                    print(f"Unsupported gh invocation: {args}", file=sys.stderr)
                    raise SystemExit(1)
                    """
                ),
            )
            os.chmod(gh_script, 0o755)

            continuity_script = os.path.join(
                os.path.dirname(__file__), "..", "core", "continuity.py"
            )
            env = os.environ.copy()
            env["PATH"] = fake_bin + os.pathsep + env.get("PATH", "")
            env["GH_STUB_STATE"] = gh_state
            proc = subprocess.run(
                [sys.executable, continuity_script, "sync-github", tmpdir],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertIn("## SonIA Sync", proc.stdout)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_JSON_RELATIVE_PATH)))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, GITHUB_SYNC_MD_RELATIVE_PATH)))

            with open(gh_state, "r", encoding="utf-8") as fh:
                gh_payload = json.load(fh)

        self.assertGreaterEqual(len(gh_payload["issues"]), 3)
        self.assertTrue(any(issue["title"].startswith("[T-010]") for issue in gh_payload["issues"]))
        self.assertTrue(any(issue["title"].startswith("SonIA Sync:") for issue in gh_payload["issues"]))

    def test_rendered_sync_markdown_does_not_duplicate_task_prefix(self):
        result = {
            "repo": "686f6c61/alfred-e2e",
            "board_issue": {"url": "https://github.com/686f6c61/alfred-e2e/issues/9"},
            "tasks": [
                {
                    "id": "T-010",
                    "title": "[T-010] Preparar labels de issues",
                    "status": "backlog",
                    "number": 101,
                }
            ],
            "skipped": [],
        }

        from core.continuity import render_github_sync_markdown  # noqa: E402

        markdown = render_github_sync_markdown(result)

        self.assertIn("## SonIA Sync", markdown)
        self.assertIn("[T-010] Preparar labels de issues", markdown)
        self.assertNotIn("[T-010] [T-010]", markdown)


if __name__ == "__main__":
    unittest.main()
