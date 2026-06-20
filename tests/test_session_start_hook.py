#!/usr/bin/env python3
"""Tests de contrato para el hook de SessionStart.

Protegen el contexto operativo que Alfred inyecta al arrancar en Claude Code.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _PROJECT_ROOT)

from core.memory import MemoryDB
from core.memory_config import load_memory_config
from core.memory_sync import resolve_memory_dir


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestSessionStartHookContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hook = _read("hooks/session-start.sh")
        cls.bootstrap = _read("hooks/session-bootstrap.sh")
        cls.hooks_json = _read("hooks/hooks.json")

    def test_hook_announces_current_command_prefix(self):
        self.assertIn("/alfred-dev:feature", self.hook)
        self.assertIn("/alfred-dev:discuss", self.hook)
        self.assertIn("/alfred-dev:audit", self.hook)
        self.assertIn("/alfred-dev:map-codebase", self.hook)
        self.assertIn("/alfred-dev:next", self.hook)
        self.assertIn("/alfred-dev:pause", self.hook)
        self.assertIn("/alfred-dev:progress", self.hook)
        self.assertIn("/alfred-dev:quick", self.hook)
        self.assertIn("/alfred-dev:resume", self.hook)
        self.assertIn("/alfred-dev:verify", self.hook)
        self.assertIn("/alfred-dev:help", self.hook)
        self.assertIn("consume-prefetch", self.hook)
        self.assertIn(".claude/alfred-prefetch.json", self.hook)
        self.assertNotIn("- /alfred audit -", self.hook)

    def test_hook_uses_current_update_command_and_semver_ordering(self):
        self.assertIn("/alfred-dev:update", self.hook)
        self.assertIn("UPDATE_AVAILABLE=$(python3 -c", self.hook)
        self.assertNotIn('"$LATEST_RELEASE" != "$CURRENT_VERSION"', self.hook)

    def test_hook_injects_next_step_recommendation(self):
        self.assertIn("### Siguiente paso recomendado", self.hook)
        self.assertIn("from core.continuity import suggest_next_action", self.hook)

    def test_session_start_registers_sync_bootstrap_before_async_context(self):
        self.assertIn("session-bootstrap.sh", self.hooks_json)
        self.assertIn("session-start.sh", self.hooks_json)
        self.assertIn("prefetch-finish-guard.py", self.hooks_json)
        self.assertIn('"async": true', self.hooks_json)

    def test_bootstrap_hook_ensures_cli_first_autonomy(self):
        self.assertIn("ensure_bootstrap_local_config", self.bootstrap)
        self.assertIn("from core.config_loader import ensure_bootstrap_local_config", self.bootstrap)

    def test_bootstrap_hook_prepares_local_permissions_and_wrapper(self):
        self.assertIn('.claude/settings.local.json', self.bootstrap)
        self.assertIn('.claude/settings.json', self.bootstrap)
        self.assertIn('"defaultMode"', self.bootstrap)
        self.assertIn('"acceptEdits"', self.bootstrap)
        self.assertIn('Read(**)', self.bootstrap)
        self.assertIn('Edit(docs/project/**)', self.bootstrap)
        self.assertIn('Write(docs/project/**)', self.bootstrap)
        self.assertIn('Write(.claude/alfred-*.json)', self.bootstrap)
        self.assertIn('Bash(python3 *)', self.bootstrap)
        self.assertIn('Bash(python3 .claude/alfred-continuity.py *)', self.bootstrap)
        self.assertIn('alfred-continuity.py', self.bootstrap)

    def test_bootstrap_hook_initializes_project_memory(self):
        self.assertIn("alfred-memory.db", self.bootstrap)
        self.assertIn("session-bootstrap.sh", self.bootstrap)
        self.assertIn("db.start_iteration(", self.bootstrap)

class TestSessionBootstrapRuntime(unittest.TestCase):
    def test_bootstrap_script_prepares_project_locals(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-bootstrap.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)

            local_config = os.path.join(tmpdir, ".claude", "alfred-dev.local.md")
            settings_local = os.path.join(tmpdir, ".claude", "settings.local.json")
            settings_shared = os.path.join(tmpdir, ".claude", "settings.json")
            wrapper = os.path.join(tmpdir, ".claude", "alfred-continuity.py")
            memory_db = os.path.join(tmpdir, ".claude", "alfred-memory.db")

            self.assertTrue(os.path.isfile(local_config))
            self.assertTrue(os.path.isfile(settings_local))
            self.assertTrue(os.path.isfile(settings_shared))
            self.assertTrue(os.path.isfile(wrapper))
            self.assertTrue(os.path.isfile(memory_db))
            with open(wrapper, "r", encoding="utf-8") as fh:
                wrapper_source = fh.read()
            self.assertIn("CLAUDE_PLUGIN_ROOT", wrapper_source)
            self.assertIn("EMBEDDED_PLUGIN_ROOT", wrapper_source)
            self.assertIn("_cache_candidates", wrapper_source)

            for settings_path in (settings_local, settings_shared):
                with open(settings_path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)

                self.assertEqual(payload["defaultMode"], "acceptEdits")
                self.assertIn("Bash(python3 .claude/alfred-continuity.py *)", payload["permissions"]["allow"])

    def test_continuity_wrapper_recovers_from_stale_embedded_plugin_root(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-bootstrap.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            wrapper = os.path.join(tmpdir, ".claude", "alfred-continuity.py")
            with open(wrapper, "r", encoding="utf-8") as fh:
                wrapper_source = fh.read()
            wrapper_source = "\n".join(
                "EMBEDDED_PLUGIN_ROOT = '/tmp/alfred-dev-stale-cache'"
                if line.startswith("EMBEDDED_PLUGIN_ROOT = ")
                else line
                for line in wrapper_source.splitlines()
            ) + "\n"
            with open(wrapper, "w", encoding="utf-8") as fh:
                fh.write(wrapper_source)

            env = os.environ.copy()
            env["CLAUDE_PLUGIN_ROOT"] = os.path.realpath(_PROJECT_ROOT)
            wrapper_result = subprocess.run(
                [sys.executable, wrapper, "status", tmpdir, "--json"],
                cwd=tmpdir,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(wrapper_result.returncode, 0, msg=wrapper_result.stderr)
            payload = json.loads(wrapper_result.stdout)
            self.assertIn("next_action", payload)
            self.assertIn("kanban", payload)
            self.assertIn("session_status_label", payload)

    def test_bootstrap_injects_valid_frontmatter_when_body_only_mentions_memory(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-bootstrap.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            local_config = os.path.join(claude_dir, "alfred-dev.local.md")
            with open(local_config, "w", encoding="utf-8") as fh:
                fh.write("# Notas\n\nmemoria:\n  enabled: true\n")

            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(load_memory_config(tmpdir)["enabled"])
            with open(local_config, "r", encoding="utf-8") as fh:
                self.assertTrue(fh.read().startswith("---\n"))

    def test_bootstrap_preserves_explicit_memory_disable(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-bootstrap.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            local_config = os.path.join(claude_dir, "alfred-dev.local.md")
            with open(local_config, "w", encoding="utf-8") as fh:
                fh.write(
                    "---\n"
                    "autonomia:\n"
                    "  producto: autonomo\n"
                    "memoria:\n"
                    "  enabled: false\n"
                    "---\n"
                )

            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertFalse(load_memory_config(tmpdir)["enabled"])

    def test_bootstrap_does_not_create_memory_db_when_explicitly_disabled(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-bootstrap.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("---\nmemoria:\n  enabled: false\n---\n")

            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertFalse(
                os.path.exists(os.path.join(claude_dir, "alfred-memory.db"))
            )


class TestSessionStartRuntime(unittest.TestCase):
    def test_session_start_emits_context_without_shell_substitution_errors(self):
        bootstrap_path = os.path.join(_PROJECT_ROOT, "hooks", "session-bootstrap.sh")
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-start.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            bootstrap = subprocess.run(
                [bootstrap_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stderr)

            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn("command not found", result.stderr)
            self.assertNotIn("consume-prefetch: error", result.stderr)

            payload = json.loads(result.stdout)
            hook_output = payload["hookSpecificOutput"]["hookEventName"]
            self.assertEqual(hook_output, "SessionStart")
            additional_context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("consume-prefetch <project_dir> --expected <comando>", additional_context)

    def test_session_start_emits_effective_config_summary(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-start.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "---\n"
                    "autonomia:\n"
                    "  producto: autonomo\n"
                    "  arquitectura: autonomo\n"
                    "  desarrollo: autonomo\n"
                    "  calidad: interactivo\n"
                    "  documentacion: autonomo\n"
                    "  entrega: autonomo\n"
                    "agentes_opcionales:\n"
                    "  lucius: true\n"
                    "  seo-specialist: true\n"
                    "memoria:\n"
                    "  enabled: false\n"
                    "personalidad:\n"
                    "  nivel_sarcasmo: 5\n"
                    "  idioma: en\n"
                    "  verbosidad: alta\n"
                    "  celebrar_victorias: false\n"
                    "  insultar_malas_practicas: false\n"
                    "---\n"
                )

            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            additional_context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("### Configuración efectiva", additional_context)
            self.assertIn("Autopilot por configuración: no", additional_context)
            self.assertIn("Autopilot efectivo (config/estado): no", additional_context)
            self.assertIn("Memoria persistente: inactiva", additional_context)
            self.assertIn("Personalidad: sarcasmo=5, idioma=en, verbosidad=alta", additional_context)
            self.assertIn("celebrar_victorias=no", additional_context)
            self.assertIn("insultar_malas_practicas=no", additional_context)
            self.assertIn("Agentes opcionales activos: seo-specialist, lucius", additional_context)

    def test_session_start_preserves_explicit_memory_disable(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-start.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "---\n"
                    "autonomia:\n"
                    "  producto: autonomo\n"
                    "memoria:\n"
                    "  enabled: false\n"
                    "---\n"
                )

            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertFalse(load_memory_config(tmpdir)["enabled"])
            self.assertFalse(
                os.path.exists(os.path.join(claude_dir, "alfred-memory.db"))
            )

    def test_session_start_uses_canonical_sync_to_native_config(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-start.sh")

        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as home_dir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "---\n"
                    "memoria:\n"
                    "  enabled: true\n"
                    "  sync_to_native: true\n"
                    "---\n\n"
                    "# Notas\n\n"
                    "sync_to_native: false\n"
                )

            db = MemoryDB(os.path.join(claude_dir, "alfred-memory.db"))
            iteration_id = db.start_iteration("feature", "Contexto sync")
            db.log_decision(
                title="Mantener sync nativa",
                chosen="Sí",
                iteration_id=iteration_id,
            )
            db.complete_iteration(iteration_id)
            db.close()

            env = os.environ.copy()
            env["HOME"] = home_dir
            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            memory_dir = resolve_memory_dir(
                os.path.realpath(tmpdir),
                projects_base=os.path.join(home_dir, ".claude", "projects"),
            )
            self.assertIsNotNone(memory_dir)
            self.assertTrue(
                any(name.endswith(".md") for name in os.listdir(memory_dir)),
                msg=f"No se generaron memorias nativas en {memory_dir}",
            )

    def test_session_start_falls_back_to_project_decisions_when_active_iteration_is_empty(self):
        script_path = os.path.join(_PROJECT_ROOT, "hooks", "session-start.sh")

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("---\nmemoria:\n  enabled: true\n---\n")

            db = MemoryDB(os.path.join(claude_dir, "alfred-memory.db"))
            feature_id = db.start_iteration("feature", "Decisión histórica")
            db.log_decision(
                title="Usar API estable",
                chosen="Responses API",
                iteration_id=feature_id,
            )
            db.complete_iteration(feature_id)
            db.start_iteration("session", "Sesión vacía actual")
            db.close()

            result = subprocess.run(
                [script_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            additional_context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("La iteracion activa aun no tiene decisiones", additional_context)
            self.assertIn("Usar API estable", additional_context)


if __name__ == "__main__":
    unittest.main()
