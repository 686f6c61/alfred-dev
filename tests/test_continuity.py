#!/usr/bin/env python3
"""Tests para la capa de continuidad inspirada en GSD."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.continuity import (
    CODEBASE_MAP_RELATIVE_PATH,
    CURRENT_RELATIVE_PATH,
    DISCOVERY_MD_RELATIVE_PATH,
    HANDOFF_JSON_RELATIVE_PATH,
    HANDOFF_MD_RELATIVE_PATH,
    KANBAN_BACKLOG_RELATIVE_PATH,
    KANBAN_BLOCKED_RELATIVE_PATH,
    KANBAN_IN_PROGRESS_RELATIVE_PATH,
    PROGRESS_MD_RELATIVE_PATH,
    PREFETCH_CONSUMED_RELATIVE_PATH,
    PREFETCH_RELATIVE_PATH,
    STATE_RELATIVE_PATH,
    STOP_BYPASS_RELATIVE_PATH,
    TRACEABILITY_MD_RELATIVE_PATH,
    UAT_JSON_RELATIVE_PATH,
    UAT_MD_RELATIVE_PATH,
    arm_stop_hook_bypass,
    build_handoff,
    build_progress_snapshot,
    build_status_snapshot,
    load_kanban_board,
    write_codebase_map_files,
    write_discovery_files,
    build_verification_target,
    clear_session_paused,
    clear_prefetch_result,
    clear_prefetch_consumed_marker,
    clear_stop_hook_bypass,
    consume_prefetch_result,
    get_pending_gate,
    is_session_paused,
    load_prefetch_result,
    load_stop_hook_bypass,
    mark_session_paused,
    needs_codebase_map,
    pause_session,
    project_has_codebase,
    save_prefetch_result,
    load_prefetch_consumed_marker,
    resume_session,
    render_discovery_summary,
    render_next_markdown,
    render_quick_setup_summary,
    render_progress_markdown,
    render_status_markdown,
    start_quick_session,
    suggest_verify_action,
    suggest_next_action,
    write_uat_files,
    write_handoff_files,
)
from core.memory import MemoryDB
from core.orchestrator import advance_phase, create_session, save_state


def _complete_session(command: str, description: str):
    session = create_session(command, description)
    while session["fase_actual"] != "completado":
        session = advance_phase(session, resultado="aprobado", artefactos=[])
    return session


def _enable_memory(tmpdir: str) -> None:
    os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
    with open(
        os.path.join(tmpdir, ".claude", "alfred-dev.local.md"),
        "w",
        encoding="utf-8",
    ) as fh:
        fh.write(
            "---\n"
            "memoria:\n"
            "  enabled: true\n"
            "  capture_decisions: true\n"
            "  capture_commits: true\n"
            "  retention_days: 365\n"
            "---\n"
        )


class TestContinuitySuggestions(unittest.TestCase):
    def test_greenfield_defaults_to_contextual_assistant(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            suggestion = suggest_next_action(tmpdir)
        self.assertEqual(suggestion["command"], "alfred")
        self.assertEqual(suggestion["source"], "default")

    def test_brownfield_without_map_suggests_map_codebase(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            suggestion = suggest_next_action(tmpdir)
        self.assertEqual(suggestion["command"], "map-codebase")
        self.assertEqual(suggestion["source"], "brownfield")

    def test_existing_codebase_map_without_current_does_not_force_remap(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, CODEBASE_MAP_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")

            self.assertFalse(needs_codebase_map(tmpdir))
            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "alfred")
        self.assertEqual(suggestion["source"], "project")

    def test_start_quick_session_uses_persisted_optional_agents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(
                os.path.join(tmpdir, ".claude", "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "---\n"
                    "agentes_opcionales:\n"
                    "  copywriter: true\n"
                    "  lucius: true\n"
                    "---\n"
                )

            result = start_quick_session(tmpdir, raw_request="Ajustar copy del signup")
            with open(
                os.path.join(tmpdir, STATE_RELATIVE_PATH),
                "r",
                encoding="utf-8",
            ) as fh:
                state = json.load(fh)
            with open(
                os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH),
                "r",
                encoding="utf-8",
            ) as fh:
                traceability = fh.read()

        self.assertEqual(result["command"], "quick")
        self.assertEqual(state["equipo_sesion"]["fuente"], "config_persistida")
        self.assertTrue(state["equipo_sesion"]["opcionales_activos"]["copywriter"])
        self.assertTrue(state["equipo_sesion"]["opcionales_activos"]["lucius"])
        self.assertIn("Opcionales en paralelo: `copywriter`.", traceability)
        self.assertIn("Opcionales secuenciales: `lucius`.", traceability)

    def test_active_state_has_priority_over_brownfield_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            save_state(
                create_session("feature", "Panel de administración"),
                os.path.join(tmpdir, STATE_RELATIVE_PATH),
            )
            suggestion = suggest_next_action(tmpdir)
        self.assertEqual(suggestion["command"], "resume")
        self.assertEqual(suggestion["source"], "state")

    def test_active_state_suggestion_exposes_structured_guidance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            save_state(
                create_session("feature", "Panel de administración"),
                os.path.join(tmpdir, STATE_RELATIVE_PATH),
            )

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["focus"], "Retomar el flujo en curso")
        self.assertEqual(suggestion["source_label"], "sesión activa")
        self.assertEqual(suggestion["urgency"], "alta")
        self.assertIn("Reanuda `feature`", suggestion["directive"])

    def test_unresolved_handoff_suggests_resume(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(
                os.path.join(tmpdir, HANDOFF_JSON_RELATIVE_PATH),
                "w",
                encoding="utf-8",
            ) as fh:
                json.dump(
                    {
                        "command": "fix",
                        "phase": "validacion",
                        "resume_command": "/alfred-dev:resume",
                        "resolved": False,
                    },
                    fh,
                )
            suggestion = suggest_next_action(tmpdir)
        self.assertEqual(suggestion["command"], "resume")
        self.assertEqual(suggestion["source"], "handoff")

    def test_completed_session_without_uat_suggests_verify(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "docs", "project", "codebase-map.md"), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")
            with open(os.path.join(tmpdir, "docs", "project", "current.md"), "w", encoding="utf-8") as fh:
                fh.write("# current\n")
            session = _complete_session("feature", "Login y usuarios")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "verify")
        self.assertEqual(suggestion["source"], "verify")

    def test_approved_uat_stops_verify_suggestion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "docs", "project", "codebase-map.md"), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")
            with open(os.path.join(tmpdir, "docs", "project", "current.md"), "w", encoding="utf-8") as fh:
                fh.write("# current\n")
            session = _complete_session("feature", "Login y usuarios")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))
            write_uat_files(tmpdir, raw_request="aprobado validado en manual")

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "alfred")
        self.assertEqual(suggestion["source"], "current")

    def test_active_quick_session_suggests_resume(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            start_quick_session(tmpdir, raw_request="ajuste pequeño en cabecera")

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "resume")
        self.assertEqual(suggestion["source"], "state")

    def test_discovery_recommended_command_is_used_when_project_is_mapped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "docs", "project", "codebase-map.md"), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")
            with open(os.path.join(tmpdir, "docs", "project", "current.md"), "w", encoding="utf-8") as fh:
                fh.write("# current\n")
            with open(os.path.join(tmpdir, DISCOVERY_MD_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# Discovery\n\nComando recomendado: /alfred-dev:feature\n")

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "feature")
        self.assertEqual(suggestion["source"], "discovery")

    def test_discovery_can_recommend_verify(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "docs", "project", "codebase-map.md"), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")
            with open(os.path.join(tmpdir, "docs", "project", "current.md"), "w", encoding="utf-8") as fh:
                fh.write("# current\n")
            with open(os.path.join(tmpdir, DISCOVERY_MD_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# Discovery\n\nComando recomendado: /alfred-dev:verify\n")

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "verify")
        self.assertEqual(suggestion["source"], "discovery")

    def test_discovery_can_recommend_lucius(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "docs", "project", "codebase-map.md"), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")
            with open(os.path.join(tmpdir, "docs", "project", "current.md"), "w", encoding="utf-8") as fh:
                fh.write("# current\n")
            with open(os.path.join(tmpdir, DISCOVERY_MD_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# Discovery\n\nComando recomendado: /alfred-dev:lucius\n")

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "lucius")
        self.assertEqual(suggestion["source"], "discovery")

    def test_discovery_prefers_explicit_recommended_command_over_other_mentions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, CODEBASE_MAP_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")
            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# current\n")
            with open(os.path.join(tmpdir, DISCOVERY_MD_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Discovery\n\n"
                    "- Si al final se reduce mucho, podria resolverse con /alfred-dev:quick.\n\n"
                    "## Comando recomendado\n\n"
                    "/alfred-dev:feature\n"
                )

            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "feature")
        self.assertEqual(suggestion["source"], "discovery")

    def test_current_markdown_can_drive_next_after_map_codebase(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Demo\n\nProyecto de prueba.\n")

            write_codebase_map_files(tmpdir, raw_request="login")
            suggestion = suggest_next_action(tmpdir)

        self.assertEqual(suggestion["command"], "discuss")
        self.assertEqual(suggestion["source"], "current")


class TestContinuityHelpers(unittest.TestCase):
    def test_cli_script_mode_supports_direct_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )
            result = subprocess.run(
                [sys.executable, continuity_script, "next", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["command"], "map-codebase")

    def test_cli_status_mode_supports_direct_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            save_state(
                create_session("quick", "Ajuste pequeño en cabecera"),
                os.path.join(tmpdir, STATE_RELATIVE_PATH),
            )

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )
            result = subprocess.run(
                [sys.executable, continuity_script, "status", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("## Estado operativo de Alfred Dev", result.stdout)
        self.assertIn("Foco: Retomar el flujo en curso", result.stdout)
        self.assertIn("/alfred-dev:resume", result.stdout)

    def test_cli_map_codebase_mode_supports_direct_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo", "scripts": {"test": "vitest", "build": "vite build"}}, fh)
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Demo\n\nRepositorio de prueba para map-codebase.\n")
            with open(os.path.join(tmpdir, "index.js"), "w", encoding="utf-8") as fh:
                fh.write("console.log('demo')\n")

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )
            result = subprocess.run(
                [sys.executable, continuity_script, "map-codebase", tmpdir, "--raw", "login", "--json"],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["recommended_command"], "discuss")
            self.assertEqual(payload["stack"]["runtime"], "node")
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, CODEBASE_MAP_RELATIVE_PATH)))

    def test_cli_map_codebase_defaults_to_markdown_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Demo\n\nRepositorio de prueba.\n")

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )
            result = subprocess.run(
                [sys.executable, continuity_script, "map-codebase", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("## Mapeo brownfield completado", result.stdout)
        self.assertIn("/alfred-dev:alfred", result.stdout)

    def test_cli_consume_prefetch_prints_and_clears_recent_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "source_command": "map-codebase",
                "prefetched_command": "map-codebase",
                "project_name": "demo",
                "stack": {"runtime": "node", "framework": "desconocido"},
                "recommended_command": "discuss",
            }
            save_prefetch_result(tmpdir, payload)

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    continuity_script,
                    "consume-prefetch",
                    tmpdir,
                    "--expected",
                    "map-codebase",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("## Mapeo brownfield completado", result.stdout)
            self.assertFalse(os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH)))

    def test_cli_verify_approved_resyncs_operational_docs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state_path = os.path.join(tmpdir, STATE_RELATIVE_PATH)
            session = create_session("quick", "Ajustar copy login")
            while session["fase_actual"] != "completado":
                session = advance_phase(session, resultado="aprobado", artefactos=["docs/cambio.md"])
            save_state(session, state_path)

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    continuity_script,
                    "verify",
                    tmpdir,
                    "--raw",
                    "aprobado smoke manual correcto",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)

            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability = fh.read()

        self.assertIn("Estado: completado y verificado.", current)
        self.assertIn("Siguiente comando recomendado: /alfred-dev:alfred", current)
        self.assertIn("Verificación/UAT: aprobada.", progress)
        self.assertIn("UAT actual: aprobada.", traceability)
        self.assertIn("Estado de verify: `done`.", traceability)

    def test_cli_helper_first_chain_updates_next_step_consistently(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "name": "demo-chain",
                        "scripts": {"test": "vitest"},
                        "dependencies": {"react": "^18.0.0"},
                    },
                    fh,
                )
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Demo chain\n")

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )

            next_initial = subprocess.run(
                [sys.executable, continuity_script, "next", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(next_initial.returncode, 0, msg=next_initial.stderr)
            self.assertEqual(json.loads(next_initial.stdout)["command"], "map-codebase")

            mapped = subprocess.run(
                [
                    sys.executable,
                    continuity_script,
                    "map-codebase",
                    tmpdir,
                    "--raw",
                    "login",
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(mapped.returncode, 0, msg=mapped.stderr)
            self.assertEqual(json.loads(mapped.stdout)["recommended_command"], "discuss")

            next_after_map = subprocess.run(
                [sys.executable, continuity_script, "next", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(next_after_map.returncode, 0, msg=next_after_map.stderr)
            next_after_map_payload = json.loads(next_after_map.stdout)
            self.assertEqual(next_after_map_payload["command"], "discuss")
            self.assertEqual(next_after_map_payload["source"], "current")

            discuss = subprocess.run(
                [
                    sys.executable,
                    continuity_script,
                    "discuss",
                    tmpdir,
                    "--raw",
                    "refinar onboarding de login social",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(discuss.returncode, 0, msg=discuss.stderr)
            self.assertIn("## Refinado preparado", discuss.stdout)
            self.assertIn("Alcance inicial", discuss.stdout)
            self.assertIn("/alfred-dev:feature", discuss.stdout)
            self.assertFalse(discuss.stdout.lstrip().startswith("{"))

            discuss_json = subprocess.run(
                [
                    sys.executable,
                    continuity_script,
                    "discuss",
                    tmpdir,
                    "--raw",
                    "refinar onboarding de login social",
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(discuss_json.returncode, 0, msg=discuss_json.stderr)
            self.assertEqual(json.loads(discuss_json.stdout)["recommended_command"], "feature")

            next_after_discuss = subprocess.run(
                [sys.executable, continuity_script, "next", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(next_after_discuss.returncode, 0, msg=next_after_discuss.stderr)
            self.assertEqual(json.loads(next_after_discuss.stdout)["command"], "feature")

            quick = subprocess.run(
                [
                    sys.executable,
                    continuity_script,
                    "quick",
                    tmpdir,
                    "--raw",
                    "ajustar copy login",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(quick.returncode, 0, msg=quick.stderr)

            next_after_quick = subprocess.run(
                [sys.executable, continuity_script, "next", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(next_after_quick.returncode, 0, msg=next_after_quick.stderr)
            self.assertEqual(json.loads(next_after_quick.stdout)["command"], "resume")

    def test_project_has_codebase_detects_source_tree(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
            with open(os.path.join(tmpdir, "src", "main.py"), "w", encoding="utf-8") as fh:
                fh.write("print('hola')\n")
            self.assertTrue(project_has_codebase(tmpdir))
            self.assertTrue(needs_codebase_map(tmpdir))

    def test_pending_gate_comes_from_flow_definition(self):
        session = create_session("feature", "Autenticación")
        self.assertEqual(get_pending_gate(session), "usuario")

    def test_build_handoff_uses_active_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Sistema de login")
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))
            handoff = build_handoff(tmpdir)
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["command"], "feature")
        self.assertEqual(handoff["phase"], "producto")
        self.assertEqual(handoff["resume_command"], "/alfred-dev:resume")
        self.assertIn("Retomar", handoff["next_step"])

    def test_write_handoff_files_creates_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("fix", "Bug en login")
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))
            result = write_handoff_files(tmpdir)
            self.assertIsNotNone(result)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, HANDOFF_JSON_RELATIVE_PATH)))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, HANDOFF_MD_RELATIVE_PATH)))

            with open(os.path.join(tmpdir, HANDOFF_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                content = fh.read()

        self.assertIn("Handoff de Alfred Dev", content)
        self.assertIn("Comando de retorno", content)

    def test_mark_and_clear_paused_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Panel de usuarios")
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            paused = mark_session_paused(tmpdir)
            self.assertIsNotNone(paused)
            self.assertTrue(is_session_paused(paused))
            self.assertEqual(paused["paused_via"], "/alfred-dev:pause")

            resumed = clear_session_paused(tmpdir)
            self.assertIsNotNone(resumed)
            self.assertFalse(is_session_paused(resumed))
            self.assertNotIn("paused_via", resumed)
            self.assertIn("resumed_at", resumed)

    def test_pause_and_resume_session_helpers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Panel de usuarios")
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            paused = pause_session(tmpdir)
            self.assertIsNotNone(paused)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, HANDOFF_JSON_RELATIVE_PATH)))

            resumed = resume_session(tmpdir)
            self.assertIsNotNone(resumed)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, STOP_BYPASS_RELATIVE_PATH)))

            with open(os.path.join(tmpdir, HANDOFF_JSON_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                handoff = json.load(fh)

        self.assertTrue(handoff["resolved"])
        self.assertIn("resolved_at", handoff)

    def test_cli_pause_and_resume_render_markdown_by_default_and_json_on_demand(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Panel de usuarios")
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )

            paused = subprocess.run(
                [sys.executable, continuity_script, "pause", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(paused.returncode, 0, msg=paused.stderr)
            self.assertIn("## Sesión pausada", paused.stdout)
            self.assertIn("`/alfred-dev:resume`", paused.stdout)
            self.assertFalse(paused.stdout.lstrip().startswith("{"))

            paused_json = subprocess.run(
                [sys.executable, continuity_script, "pause", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(paused_json.returncode, 0, msg=paused_json.stderr)
            self.assertIn("paused_at", json.loads(paused_json.stdout))

            resumed = subprocess.run(
                [sys.executable, continuity_script, "resume", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, msg=resumed.stderr)
            self.assertIn("## Sesión reanudada", resumed.stdout)
            self.assertIn("Siguiente acción", resumed.stdout)
            self.assertFalse(resumed.stdout.lstrip().startswith("{"))

            resumed_json = subprocess.run(
                [sys.executable, continuity_script, "resume", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(resumed_json.returncode, 0, msg=resumed_json.stderr)
            self.assertIn("resumed_at", json.loads(resumed_json.stdout))

    def test_resume_session_can_resolve_handoff_without_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(
                os.path.join(tmpdir, HANDOFF_JSON_RELATIVE_PATH),
                "w",
                encoding="utf-8",
            ) as fh:
                json.dump(
                    {
                        "command": "fix",
                        "phase": "calidad",
                        "resume_command": "/alfred-dev:resume",
                        "resolved": False,
                    },
                    fh,
                )

            resumed = resume_session(tmpdir)

            self.assertIsNotNone(resumed)
            self.assertNotIn("state_path", resumed)
            self.assertIn("handoff_path", resumed)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, STOP_BYPASS_RELATIVE_PATH)))

            with open(os.path.join(tmpdir, HANDOFF_JSON_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                handoff = json.load(fh)

        self.assertTrue(handoff["resolved"])
        self.assertIn("resolved_at", handoff)

    def test_resume_session_does_not_reopen_completed_state_without_handoff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("feature", "Entrega cerrada")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            resumed = resume_session(tmpdir)

            self.assertIsNone(resumed)
            self.assertFalse(os.path.exists(os.path.join(tmpdir, STOP_BYPASS_RELATIVE_PATH)))

    def test_arm_and_clear_stop_hook_bypass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            bypass_path = arm_stop_hook_bypass(tmpdir, "/alfred-dev:next")
            self.assertTrue(os.path.isfile(bypass_path))

            bypass = load_stop_hook_bypass(tmpdir)
            self.assertIsNotNone(bypass)
            self.assertEqual(bypass["command"], "/alfred-dev:next")

            clear_stop_hook_bypass(tmpdir)
            self.assertFalse(os.path.exists(bypass_path))

    def test_build_verification_target_blocks_active_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = create_session("feature", "Panel de usuarios")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            target = build_verification_target(tmpdir)

        self.assertTrue(target["blocked"])
        self.assertIn("sigue activa", target["reason"])

    def test_write_uat_files_creates_pending_artifacts_for_completed_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("fix", "Bug de login")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            result = write_uat_files(tmpdir)

            self.assertEqual(result["status"], "pending")
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, UAT_JSON_RELATIVE_PATH)))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, UAT_MD_RELATIVE_PATH)))

            with open(os.path.join(tmpdir, UAT_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                content = fh.read()

        self.assertIn("Verificación manual / UAT", content)
        self.assertIn("/alfred-dev:verify aprobado", content)

    def test_cli_verify_renders_markdown_by_default_and_json_on_demand(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("quick", "Ajustar copy login")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            continuity_script = os.path.join(
                os.path.dirname(__file__),
                "..",
                "core",
                "continuity.py",
            )

            verify = subprocess.run(
                [sys.executable, continuity_script, "verify", tmpdir],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verify.returncode, 0, msg=verify.stderr)
            self.assertIn("Verificación manual / UAT", verify.stdout)
            self.assertIn("**Estado:** pendiente", verify.stdout)
            self.assertIn("## Checklist de validación", verify.stdout)
            self.assertFalse(verify.stdout.lstrip().startswith("{"))

            verify_json = subprocess.run(
                [sys.executable, continuity_script, "verify", tmpdir, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verify_json.returncode, 0, msg=verify_json.stderr)
            self.assertEqual(json.loads(verify_json.stdout)["status"], "pending")

    def test_write_uat_files_can_approve_and_reject(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("feature", "Checkout")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            pending = write_uat_files(tmpdir)
            self.assertEqual(pending["status"], "pending")

            approved = write_uat_files(tmpdir, raw_request="aprobado smoke manual correcto")
            self.assertEqual(approved["status"], "approved")

            rejected = write_uat_files(tmpdir, raw_request="rechazado fallo al guardar usuario")
            self.assertEqual(rejected["status"], "rejected")

            verify_suggestion = suggest_verify_action(tmpdir)

            with open(os.path.join(tmpdir, UAT_JSON_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                payload = json.load(fh)

        self.assertIsNone(verify_suggestion)

    def test_write_uat_files_approved_moves_task_to_done_and_clears_verify_task(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            active = start_quick_session(tmpdir, raw_request="Ajustar copy login")
            session = _complete_session("quick", "Ajustar copy login")
            session["kanban_task_id"] = active["kanban_task_id"]
            session["kanban_verify_task_id"] = active["kanban_verify_task_id"]
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            result = write_uat_files(tmpdir, raw_request="aprobado smoke correcto")
            board = load_kanban_board(tmpdir)

        self.assertEqual(result["status"], "approved")
        self.assertTrue(any(task["id"] == active["kanban_task_id"] for task in board["done"]))
        self.assertFalse(any(task["id"] == active["kanban_verify_task_id"] for task in board["backlog"]))

    def test_write_uat_files_rejected_moves_task_to_blocked_and_clears_verify_task(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            active = start_quick_session(tmpdir, raw_request="Ajustar copy login")
            session = _complete_session("quick", "Ajustar copy login")
            session["kanban_task_id"] = active["kanban_task_id"]
            session["kanban_verify_task_id"] = active["kanban_verify_task_id"]
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            result = write_uat_files(tmpdir, raw_request="rechazado falta pulir mensaje")
            board = load_kanban_board(tmpdir)

        self.assertEqual(result["status"], "rejected")
        blocked = next(task for task in board["blocked"] if task["id"] == active["kanban_task_id"])
        self.assertIn("UAT rechazada", blocked["notes"])
        self.assertFalse(any(task["id"] == active["kanban_verify_task_id"] for task in board["backlog"]))

    def test_write_uat_files_approved_creates_done_task_when_no_kanban_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("feature", "Checkout")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            result = write_uat_files(tmpdir, raw_request="aprobado smoke correcto")
            board = load_kanban_board(tmpdir)

        self.assertEqual(result["status"], "approved")
        self.assertTrue(any(task["title"] == "Checkout" for task in board["done"]))

    def test_start_quick_session_creates_state_and_marks_map_requirement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)

            result = start_quick_session(tmpdir, raw_request="cambiar copy del login")

            self.assertTrue(os.path.isfile(os.path.join(tmpdir, STATE_RELATIVE_PATH)))
            self.assertEqual(result["command"], "quick")
            self.assertEqual(result["phase"], "ejecucion_acotada")
            self.assertEqual(result["description"], "cambiar copy del login")
            self.assertTrue(result["needs_codebase_map"])
            self.assertTrue(os.path.isfile(result["bypass_path"]))

    def test_start_quick_session_promotes_matching_backlog_task(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project", "kanban"), exist_ok=True)
            with open(os.path.join(tmpdir, KANBAN_BACKLOG_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Backlog\n\n"
                    "### [T-010] cambiar copy del login\n\n"
                    "- **Agente:** content-designer\n"
                )
            with open(os.path.join(tmpdir, KANBAN_IN_PROGRESS_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# In Progress\n")

            result = start_quick_session(tmpdir, raw_request="cambiar copy del login")
            board = load_kanban_board(tmpdir)

        self.assertFalse(any(task["id"] == "T-010" for task in board["backlog"]))
        self.assertTrue(any(task["id"] == "T-010" for task in board["in-progress"]))
        self.assertEqual(result["kanban_task_id"], "T-010")
        self.assertTrue(result["kanban_verify_task_id"].startswith("T-"))

    def test_prefetch_storage_can_be_consumed_by_source_or_target_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "source_command": "alfred",
                "prefetched_command": "map-codebase",
                "recommended_command": "discuss",
                "project_name": "demo",
                "stack": {"runtime": "node", "framework": "desconocido"},
            }

            prefetch_path = save_prefetch_result(tmpdir, payload)
            self.assertTrue(os.path.isfile(prefetch_path))
            loaded = load_prefetch_result(tmpdir)
            self.assertIsNotNone(loaded)
            self.assertIn("Ruta decidida", loaded["response_text"])

            consumed = consume_prefetch_result(tmpdir, "alfred")
            self.assertIsNotNone(consumed)
            self.assertIn("Ruta decidida", consumed["response_text"])
            self.assertFalse(os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH)))
            marker = load_prefetch_consumed_marker(tmpdir)
            self.assertIsNotNone(marker)
            self.assertEqual(marker["prefetched_command"], "map-codebase")

            save_prefetch_result(tmpdir, payload)
            consumed_by_target = consume_prefetch_result(tmpdir, "map-codebase")
            self.assertIsNotNone(consumed_by_target)
            self.assertFalse(os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH)))
            self.assertTrue(
                os.path.exists(os.path.join(tmpdir, PREFETCH_CONSUMED_RELATIVE_PATH))
            )

    def test_consume_prefetch_discards_stale_map_codebase_when_active_session_appears(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "source_command": "map-codebase",
                "prefetched_command": "map-codebase",
                "recommended_command": "discuss",
                "project_name": "demo",
                "stack": {"runtime": "node", "framework": "desconocido"},
            }
            save_prefetch_result(tmpdir, payload)
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            save_state(
                create_session("feature", "Panel de usuarios"),
                os.path.join(tmpdir, STATE_RELATIVE_PATH),
            )

            consumed = consume_prefetch_result(tmpdir, "map-codebase")
            prefetch_exists = os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH))

        self.assertIsNone(consumed)
        self.assertFalse(prefetch_exists)

    def test_consume_prefetch_discards_stale_discuss_when_handoff_appears(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "source_command": "discuss",
                "prefetched_command": "discuss",
                "description": "Refinar onboarding",
                "actor": "usuario nuevo",
                "recommended_command": "feature",
            }
            save_prefetch_result(tmpdir, payload)
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(os.path.join(tmpdir, HANDOFF_JSON_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "command": "feature",
                        "phase": "producto",
                        "resume_command": "/alfred-dev:resume",
                        "resolved": False,
                    },
                    fh,
                )

            consumed = consume_prefetch_result(tmpdir, "discuss")
            prefetch_exists = os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH))

        self.assertIsNone(consumed)
        self.assertFalse(prefetch_exists)

    def test_consume_prefetch_discards_contextual_alfred_prefetch_when_verify_is_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "source_command": "alfred",
                "prefetched_command": "map-codebase",
                "recommended_command": "discuss",
                "project_name": "demo",
                "stack": {"runtime": "node", "framework": "desconocido"},
            }
            save_prefetch_result(tmpdir, payload)
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("feature", "Login y usuarios")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            consumed = consume_prefetch_result(tmpdir, "alfred")
            prefetch_exists = os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH))

        self.assertIsNone(consumed)
        self.assertFalse(prefetch_exists)

    def test_load_prefetch_result_discards_expired_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            expired = {
                "source_command": "alfred",
                "prefetched_command": "map-codebase",
                "response_text": "caducado",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat(),
            }
            prefetch_path = os.path.join(tmpdir, PREFETCH_RELATIVE_PATH)
            with open(prefetch_path, "w", encoding="utf-8") as fh:
                json.dump(expired, fh, indent=2, ensure_ascii=False)

            loaded = load_prefetch_result(tmpdir)

            self.assertIsNone(loaded)
            self.assertFalse(os.path.exists(prefetch_path))

    def test_prefetch_clear_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            clear_prefetch_result(tmpdir)
            payload = {
                "source_command": "discuss",
                "prefetched_command": "discuss",
                "description": "Refinar onboarding",
                "actor": "usuario nuevo",
                "recommended_command": "feature",
            }
            save_prefetch_result(tmpdir, payload)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH)))
            clear_prefetch_result(tmpdir)
            clear_prefetch_result(tmpdir)
            self.assertFalse(os.path.exists(os.path.join(tmpdir, PREFETCH_RELATIVE_PATH)))

    def test_prefetch_consumed_marker_clear_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "source_command": "map-codebase",
                "prefetched_command": "map-codebase",
                "recommended_command": "discuss",
                "project_name": "demo",
                "stack": {"runtime": "node", "framework": "desconocido"},
            }
            save_prefetch_result(tmpdir, payload)
            consume_prefetch_result(tmpdir, "map-codebase")
            self.assertTrue(
                os.path.exists(os.path.join(tmpdir, PREFETCH_CONSUMED_RELATIVE_PATH))
            )
            clear_prefetch_consumed_marker(tmpdir)
            clear_prefetch_consumed_marker(tmpdir)
            self.assertFalse(
                os.path.exists(os.path.join(tmpdir, PREFETCH_CONSUMED_RELATIVE_PATH))
            )

    def test_prefetch_summaries_cover_discuss_and_quick(self):
        discuss_summary = render_discovery_summary(
            {
                "description": "Refinar onboarding",
                "actor": "usuario nuevo",
                "recommended_command": "feature",
                "scope_items": ["Clarificar el flujo principal de onboarding."],
                "open_questions": ["Qué criterio de éxito marca que el onboarding quedó resuelto."],
                "risks": ["Entrar a implementar sin cerrar alcance puede generar retrabajo."],
            }
        )
        quick_summary = render_quick_setup_summary(
            {
                "command": "quick",
                "phase": "ejecucion_acotada",
                "description": "Ajustar copy",
                "needs_codebase_map": False,
                "next_command": "/alfred-dev:verify",
            }
        )

        self.assertIn("## Refinado preparado", discuss_summary)
        self.assertIn("Alcance inicial", discuss_summary)
        self.assertIn("Pregunta abierta clave", discuss_summary)
        self.assertIn("Riesgo principal", discuss_summary)
        self.assertIn("/alfred-dev:feature", discuss_summary)
        self.assertIn("## Quick preparado", quick_summary)
        self.assertIn("/alfred-dev:verify", quick_summary)

    def test_start_quick_session_blocks_when_uat_is_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "docs", "project"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)
            with open(os.path.join(tmpdir, "docs", "project", "codebase-map.md"), "w", encoding="utf-8") as fh:
                fh.write("# mapa\n")
            with open(os.path.join(tmpdir, "docs", "project", "current.md"), "w", encoding="utf-8") as fh:
                fh.write("# current\n")
            session = _complete_session("feature", "Login y usuarios")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            with self.assertRaises(RuntimeError):
                start_quick_session(tmpdir, raw_request="ajuste pequeño")

    def test_write_discovery_files_creates_refinement_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = write_discovery_files(
                tmpdir,
                raw_request=(
                    "Onboarding de usuario para una app SaaS B2B. "
                    "Quiero aterrizar invitacion, primer acceso y checklist inicial."
                ),
            )

            discovery_path = os.path.join(tmpdir, DISCOVERY_MD_RELATIVE_PATH)
            current_path = os.path.join(tmpdir, CURRENT_RELATIVE_PATH)

            self.assertTrue(os.path.isfile(discovery_path))
            self.assertTrue(os.path.isfile(current_path))
            self.assertEqual(result["recommended_command"], "feature")
            self.assertEqual(result["actor"], "usuario nuevo")

            with open(discovery_path, "r", encoding="utf-8") as fh:
                discovery_content = fh.read()
            with open(current_path, "r", encoding="utf-8") as fh:
                current_content = fh.read()

        self.assertIn("## Comando recomendado", discovery_content)
        self.assertIn("/alfred-dev:feature", discovery_content)
        self.assertIn("Estado: refinado previo preparado", current_content)

    def test_helper_first_commands_capture_richer_memory_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _enable_memory(tmpdir)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo", "scripts": {"test": "vitest"}}, fh)
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Demo\n\nProyecto para validar memoria helper-first.\n")

            write_codebase_map_files(tmpdir, raw_request="login")
            write_discovery_files(tmpdir, raw_request="Refinar login social")
            start_quick_session(tmpdir, raw_request="ajustar copy del login")

            db = MemoryDB(os.path.join(tmpdir, ".claude", "alfred-memory.db"))
            try:
                decisions = db.get_decisions(limit=10)
                helper_events = [
                    event
                    for event in db.get_events(limit=20)
                    if event.get("event_type") == "helper_seeded"
                ]
            finally:
                db.close()

            self.assertGreaterEqual(len(decisions), 3)
            self.assertGreaterEqual(len(helper_events), 3)
            titles = [item["title"] for item in decisions]
            self.assertIn("Arrancar por map-codebase antes de implementar", titles)
            self.assertTrue(any(title.startswith("Refinar antes de implementar:") for title in titles))
            self.assertTrue(any(title.startswith("Clasificar como quick:") for title in titles))

    def test_helper_first_commands_seed_operational_artifacts_for_ui(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _enable_memory(tmpdir)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo", "scripts": {"test": "vitest"}}, fh)
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Demo\n\nProyecto para validar artefactos helper-first.\n")

            write_codebase_map_files(tmpdir, raw_request="login")
            write_discovery_files(tmpdir, raw_request="Refinar login social")
            start_quick_session(tmpdir, raw_request="ajustar copy del login")

            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress_content = fh.read()
            with open(os.path.join(tmpdir, TRACEABILITY_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                traceability_content = fh.read()
            with open(os.path.join(tmpdir, KANBAN_BACKLOG_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                backlog_content = fh.read()
            with open(os.path.join(tmpdir, KANBAN_IN_PROGRESS_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                in_progress_content = fh.read()

        self.assertIn("Flujo operativo: `quick`.", progress_content)
        self.assertIn("Riesgo principal", traceability_content)
        self.assertIn("/alfred-dev:feature", backlog_content)
        self.assertIn("ajustar copy del login", in_progress_content)

    def test_start_quick_session_writes_current_and_progress_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)

            start_quick_session(tmpdir, raw_request="ajustar copy del login")

            with open(os.path.join(tmpdir, CURRENT_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                current_content = fh.read()
            with open(os.path.join(tmpdir, PROGRESS_MD_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                progress_content = fh.read()
            with open(os.path.join(tmpdir, KANBAN_IN_PROGRESS_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                in_progress_content = fh.read()
            with open(os.path.join(tmpdir, KANBAN_BACKLOG_RELATIVE_PATH), "r", encoding="utf-8") as fh:
                backlog_content = fh.read()

        self.assertIn("Estado: activo.", current_content)
        self.assertIn("/alfred-dev:resume", current_content)
        self.assertIn("Flujo operativo: `quick`.", progress_content)
        self.assertIn("ajustar copy del login", progress_content)
        self.assertIn("Kanban visible:", progress_content)
        self.assertIn("ajustar copy del login", in_progress_content)
        self.assertIn("/alfred-dev:verify", backlog_content)

    def test_write_codebase_map_files_creates_brownfield_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "name": "demo",
                        "scripts": {"test": "vitest", "build": "vite build"},
                    },
                    fh,
                )
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Demo\n\nAplicación de ejemplo para validar Alfred.\n")
            with open(os.path.join(tmpdir, "index.js"), "w", encoding="utf-8") as fh:
                fh.write("console.log('hola')\n")

            result = write_codebase_map_files(tmpdir, raw_request="autenticación")

            codebase_map_path = os.path.join(tmpdir, CODEBASE_MAP_RELATIVE_PATH)
            current_path = os.path.join(tmpdir, CURRENT_RELATIVE_PATH)

            self.assertTrue(os.path.isfile(codebase_map_path))
            self.assertTrue(os.path.isfile(current_path))
            self.assertEqual(result["recommended_command"], "discuss")

            with open(codebase_map_path, "r", encoding="utf-8") as fh:
                codebase_map_content = fh.read()
            with open(current_path, "r", encoding="utf-8") as fh:
                current_content = fh.read()

        self.assertIn("## Stack y runtime detectados", codebase_map_content)
        self.assertIn("Aplicación de ejemplo para validar Alfred.", codebase_map_content)
        self.assertIn("index.js", codebase_map_content)
        self.assertIn("/alfred-dev:discuss", current_content)

    def test_write_codebase_map_files_blocks_active_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            save_state(create_session("feature", "Alta de usuarios"), os.path.join(tmpdir, STATE_RELATIVE_PATH))

            with self.assertRaises(RuntimeError):
                write_codebase_map_files(tmpdir, raw_request="Refinar onboarding")

    def test_write_discovery_files_blocks_active_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            save_state(create_session("feature", "Alta de usuarios"), os.path.join(tmpdir, STATE_RELATIVE_PATH))

            with self.assertRaises(RuntimeError):
                write_discovery_files(tmpdir, raw_request="Refinar onboarding")

    def test_build_progress_snapshot_summarizes_kanban_without_side_effects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "docs", "project", "kanban"), exist_ok=True)
            save_state(create_session("quick", "Ajuste local"), os.path.join(tmpdir, STATE_RELATIVE_PATH))
            with open(os.path.join(tmpdir, "docs", "project", "progress.md"), "w", encoding="utf-8") as fh:
                fh.write("# Progreso\n\n- 1 tarea en curso\n")
            with open(os.path.join(tmpdir, "docs", "project", "traceability.md"), "w", encoding="utf-8") as fh:
                fh.write("# Traceability\n\n- CA-01 sin test asociado\n")
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"), "w", encoding="utf-8") as fh:
                fh.write("# Backlog\n\n- T-002 Pulir copy\n")
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"), "w", encoding="utf-8") as fh:
                fh.write("# In Progress\n\n- T-001 Ajustar login\n")
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "w", encoding="utf-8") as fh:
                fh.write("# Done\n\n- T-000 Setup\n")
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "w", encoding="utf-8") as fh:
                fh.write("# Blocked\n\n- Ninguna\n")

            snapshot = build_progress_snapshot(tmpdir)

        self.assertEqual(snapshot["kanban"]["done"], ["T-000 Setup"])
        self.assertEqual(snapshot["kanban"]["in_progress"], ["T-001 Ajustar login"])
        self.assertEqual(snapshot["kanban"]["backlog"], ["T-002 Pulir copy"])
        self.assertEqual(snapshot["kanban"]["progress_pct"], 33)
        self.assertIsNone(snapshot["bypass_path"])

    def test_build_progress_snapshot_derives_signals_when_artifacts_are_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)

            snapshot = build_progress_snapshot(tmpdir)

        self.assertTrue(snapshot["current_signals"])
        self.assertTrue(snapshot["progress_signals"])
        self.assertTrue(snapshot["traceability_signals"])
        self.assertIn("/alfred-dev:map-codebase", snapshot["current_signals"][-1])

    def test_build_progress_snapshot_counts_structured_kanban_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project", "kanban"), exist_ok=True)
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Backlog\n\n"
                    "### [T-010] Diseñar login\n\n"
                    "- **Agente:** architect\n"
                    "- **Criterios:** CA-01, CA-02\n"
                    "- **Notas:** Flujo base\n"
                )
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"), "w", encoding="utf-8") as fh:
                fh.write("# In Progress\n")
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Done\n\n"
                    "### [T-011] Preparar esquema\n\n"
                    "- **Agente:** data-engineer\n"
                    "- **Evidencia:** tests/test_users.py::test_schema\n"
                )
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "w", encoding="utf-8") as fh:
                fh.write("# Blocked\n")

            snapshot = build_progress_snapshot(tmpdir)

        self.assertEqual(snapshot["kanban"]["backlog"], ["[T-010] Diseñar login"])
        self.assertEqual(snapshot["kanban"]["done"], ["[T-011] Preparar esquema"])
        self.assertEqual(snapshot["kanban"]["total"], 2)
        self.assertEqual(snapshot["kanban"]["progress_pct"], 50)

    def test_build_progress_snapshot_ignores_internal_tasks_in_visible_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs", "project", "kanban"), exist_ok=True)
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "backlog.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Backlog\n\n"
                    "### [T-010] Validar 'Login' con /alfred-dev:verify.\n\n"
                    "- **Agente:** alfred:verify\n"
                )
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "in-progress.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# In Progress\n\n"
                    "### [T-011] Login\n\n"
                    "- **Agente:** alfred:feature\n\n"
                    "### [T-012] feature:producto — Login\n\n"
                    "- **Agente:** analyst\n"
                )
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "done.md"), "w", encoding="utf-8") as fh:
                fh.write("# Done\n")
            with open(os.path.join(tmpdir, "docs", "project", "kanban", "blocked.md"), "w", encoding="utf-8") as fh:
                fh.write("# Blocked\n")

            snapshot = build_progress_snapshot(tmpdir)

        self.assertEqual(snapshot["kanban"]["in_progress"], ["[T-011] Login"])
        self.assertEqual(snapshot["kanban"]["backlog"], [])
        self.assertEqual(snapshot["kanban"]["total"], 1)
        self.assertEqual(snapshot["kanban"]["internal_total"], 2)
        self.assertEqual(snapshot["kanban"]["phase_total"], 1)
        self.assertEqual(snapshot["kanban"]["verify_total"], 1)

    def test_build_progress_snapshot_overview_cards_prefer_handoff_for_paused_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Panel de usuarios")
            state["paused_at"] = datetime.now(timezone.utc).isoformat()
            state["paused_via"] = "/alfred-dev:pause"
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))
            write_handoff_files(tmpdir)

            snapshot = build_progress_snapshot(tmpdir)

        labels = [card["label"] for card in snapshot["overview_cards"]]
        self.assertIn("Handoff pendiente", labels)
        self.assertNotIn("Flujo activo", labels)
        self.assertEqual(snapshot["overview_cards"][0]["label"], "Handoff pendiente")

    def test_build_progress_snapshot_overview_cards_show_completed_session_not_active(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("feature", "Checkout nuevo")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            snapshot = build_progress_snapshot(tmpdir)

        labels = [card["label"] for card in snapshot["overview_cards"]]
        self.assertIn("Último flujo completado", labels)
        self.assertNotIn("Flujo activo", labels)
        self.assertEqual(snapshot["overview_cards"][0]["label"], "Último flujo completado")
        self.assertIn("UAT pendiente", snapshot["overview_cards"][0]["body"])

    def test_build_progress_snapshot_is_pure_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            save_state(
                create_session("feature", "Checkout nuevo"),
                os.path.join(tmpdir, STATE_RELATIVE_PATH),
            )

            snapshot = build_progress_snapshot(tmpdir)

        self.assertIsNone(snapshot["bypass_path"])
        self.assertFalse(os.path.exists(os.path.join(tmpdir, STOP_BYPASS_RELATIVE_PATH)))

    def test_build_progress_snapshot_project_signal_cards_prefer_handoff_for_paused_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Panel de usuarios")
            state["paused_at"] = datetime.now(timezone.utc).isoformat()
            state["paused_via"] = "/alfred-dev:pause"
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))
            write_handoff_files(tmpdir)

            snapshot = build_progress_snapshot(tmpdir)

        titles = [card["title"] for card in snapshot["project_signal_cards"]]
        self.assertNotIn("Current", titles)
        all_items = [item for card in snapshot["project_signal_cards"] for item in card["items"]]
        self.assertFalse(any(item.startswith("Flujo operativo:") for item in all_items))

    def test_build_progress_snapshot_project_signal_cards_do_not_repeat_completed_state_or_next_step(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("feature", "Checkout nuevo")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            snapshot = build_progress_snapshot(tmpdir)

        titles = [card["title"] for card in snapshot["project_signal_cards"]]
        self.assertNotIn("Current", titles)
        all_items = [item for card in snapshot["project_signal_cards"] for item in card["items"]]
        self.assertFalse(any(item.startswith("Trabajo en curso:") for item in all_items))

    def test_build_progress_snapshot_project_signal_cards_do_not_repeat_uat_from_overview(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            session = _complete_session("feature", "Checkout nuevo")
            save_state(session, os.path.join(tmpdir, STATE_RELATIVE_PATH))
            write_uat_files(tmpdir, raw_request="aprobado smoke manual correcto")

            snapshot = build_progress_snapshot(tmpdir)

        traceability_card = next(
            card for card in snapshot["project_signal_cards"] if card["title"] == "Trazabilidad"
        )
        self.assertFalse(any(item.startswith("UAT actual:") for item in traceability_card["items"]))
        self.assertFalse(any(item.startswith("Objetivo trazado:") for item in traceability_card["items"]))

    def test_build_progress_snapshot_project_signal_cards_use_spanish_lane_titles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Panel de usuarios")
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))
            with open(os.path.join(tmpdir, KANBAN_BLOCKED_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                fh.write("# Blocked\n\n### [T-090] Contrato legal\n")

            snapshot = build_progress_snapshot(tmpdir)

        titles = [card["title"] for card in snapshot["project_signal_cards"]]
        self.assertIn("En curso", titles)
        self.assertIn("Bloqueos", titles)
        self.assertNotIn("In progress", titles)
        self.assertNotIn("Blocked", titles)

    def test_build_progress_snapshot_exposes_runtime_team_card_for_persisted_on_demand_optionals(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(os.path.join(tmpdir, STATE_RELATIVE_PATH), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "comando": "fix",
                        "descripcion": "Regresión en checkout",
                        "fase_actual": "diagnostico",
                        "fase_numero": 0,
                        "fases_completadas": [],
                        "equipo_sesion": {
                            "opcionales_activos": {
                                "data-engineer": False,
                                "performance-engineer": True,
                                "github-manager": True,
                                "librarian": True,
                                "ux-reviewer": False,
                                "seo-specialist": True,
                                "copywriter": False,
                                "i18n-specialist": False,
                                "lucius": True,
                            },
                            "infra": {"memoria": False},
                            "fuente": "config_persistida",
                        },
                    },
                    fh,
                    ensure_ascii=False,
                )

            snapshot = build_progress_snapshot(tmpdir)

        team_card = next(
            card for card in snapshot["project_signal_cards"] if card["title"] == "Equipo runtime"
        )
        self.assertIn("Origen runtime: configuración persistida.", team_card["items"])
        self.assertIn(
            "Opcionales solo bajo demanda en este flujo: `github-manager`, `librarian`.",
            team_card["items"],
        )

    def test_build_status_snapshot_arms_bypass_for_status_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            save_state(
                create_session("fix", "Regresión en checkout"),
                os.path.join(tmpdir, STATE_RELATIVE_PATH),
            )

            snapshot = build_status_snapshot(tmpdir, arm_bypass=True)
            bypass = load_stop_hook_bypass(tmpdir)

        self.assertEqual(snapshot["bypass_path"], os.path.join(tmpdir, STOP_BYPASS_RELATIVE_PATH))
        self.assertIsNotNone(bypass)
        self.assertEqual(bypass["command"], "/alfred-dev:status")

    def test_render_progress_markdown_includes_next_step(self):
        snapshot = {
            "state": None,
            "handoff": None,
            "uat": None,
            "progress_signals": ["2 tareas completadas"],
            "current_signals": [],
            "traceability_signals": ["CA-01 cubierto"],
            "kanban": {
                "backlog": ["T-003 Ajustar copy"],
                "in_progress": [],
                "done": ["T-001 Login", "T-002 Logout"],
                "blocked": [],
                "total": 3,
                "progress_pct": 67,
            },
            "next_action": {
                "command": "quick",
                "reason": "La siguiente tarea es pequeña y acotada.",
            },
            "bypass_path": None,
        }

        content = render_progress_markdown(snapshot)

        self.assertIn("Resumen operativo del proyecto", content)
        self.assertIn("Comando: `/alfred-dev:quick`", content)
        self.assertIn("Foco:", content)
        self.assertIn("CA-01 cubierto", content)

    def test_render_progress_markdown_prefers_handoff_for_paused_session(self):
        state = create_session("feature", "Panel de usuarios")
        state["paused_at"] = datetime.now(timezone.utc).isoformat()
        state["paused_via"] = "/alfred-dev:pause"
        handoff = {
            "command": "feature",
            "phase": "producto",
            "resume_command": "/alfred-dev:resume",
            "resolved": False,
        }
        snapshot = {
            "state": state,
            "handoff": handoff,
            "uat": None,
            "progress_signals": [],
            "current_signals": [],
            "traceability_signals": [],
            "kanban": {
                "backlog": [],
                "in_progress": [],
                "done": [],
                "blocked": [],
                "total": 0,
                "progress_pct": None,
            },
            "next_action": {
                "command": "resume",
                "reason": "Hay un handoff pendiente.",
            },
            "bypass_path": None,
        }

        content = render_progress_markdown(snapshot)

        self.assertIn("### Handoff pendiente", content)
        self.assertNotIn("### Flujo activo", content)
        self.assertIn("Comando: `/alfred-dev:resume`", content)

    def test_render_next_markdown_uses_structured_guidance(self):
        content = render_next_markdown(
            {
                "command": "verify",
                "reason": "Falta cerrar la UAT.",
                "source": "verify",
                "source_label": "verificación/UAT",
                "focus": "Cerrar la verificación pendiente",
                "directive": "Registra la UAT antes de seguir.",
            }
        )

        self.assertIn("## Siguiente paso operativo", content)
        self.assertIn("Foco: Cerrar la verificación pendiente", content)
        self.assertIn("Fuente: verificación/UAT (`verify`)", content)
        self.assertIn("Comando: `/alfred-dev:verify`", content)
        self.assertIn("Qué hacer ahora: Registra la UAT antes de seguir.", content)

    def test_render_status_markdown_includes_structured_next_action_and_runtime_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            state = create_session("feature", "Checkout nuevo")
            save_state(state, os.path.join(tmpdir, STATE_RELATIVE_PATH))

            snapshot = build_status_snapshot(tmpdir)
            content = render_status_markdown(snapshot)

        self.assertIn("## Estado operativo de Alfred Dev", content)
        self.assertIn("### Sesión", content)
        self.assertIn("### Proyecto", content)
        self.assertIn("### Fases registradas", content)
        self.assertIn("Foco: Retomar el flujo en curso", content)
        self.assertIn("Comando: `/alfred-dev:resume`", content)


if __name__ == "__main__":
    unittest.main()
