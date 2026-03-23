#!/usr/bin/env python3
"""Tests para la capa de continuidad inspirada en GSD."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.continuity import (
    CODEBASE_MAP_RELATIVE_PATH,
    CURRENT_RELATIVE_PATH,
    DISCOVERY_MD_RELATIVE_PATH,
    HANDOFF_JSON_RELATIVE_PATH,
    HANDOFF_MD_RELATIVE_PATH,
    KANBAN_BACKLOG_RELATIVE_PATH,
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
    render_quick_setup_summary,
    render_progress_markdown,
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
        self.assertEqual(suggestion["source"], "project")

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

        self.assertIn("Flujo activo: `quick`.", progress_content)
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

        self.assertIn("Estado: quick activo", current_content)
        self.assertIn("/alfred-dev:resume", current_content)
        self.assertIn("Flujo activo: `quick`.", progress_content)
        self.assertIn("/alfred-dev:verify", progress_content)
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

    def test_build_progress_snapshot_summarizes_kanban_and_arms_bypass(self):
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
        self.assertIsNotNone(snapshot["bypass_path"])

    def test_build_progress_snapshot_derives_signals_when_artifacts_are_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": "demo"}, fh)

            snapshot = build_progress_snapshot(tmpdir)

        self.assertTrue(snapshot["current_signals"])
        self.assertTrue(snapshot["progress_signals"])
        self.assertTrue(snapshot["traceability_signals"])
        self.assertIn("/alfred-dev:map-codebase", snapshot["current_signals"][-1])

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
        self.assertIn("/alfred-dev:quick", content)
        self.assertIn("CA-01 cubierto", content)


if __name__ == "__main__":
    unittest.main()
