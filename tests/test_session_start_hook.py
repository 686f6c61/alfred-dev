#!/usr/bin/env python3
"""Tests de contrato para el hook de SessionStart.

Protegen el contexto operativo que Alfred inyecta al arrancar en Claude Code.
"""

import json
import os
import subprocess
import tempfile
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


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
        self.assertIn("autonomia:", self.bootstrap)
        self.assertIn("producto: autonomo", self.bootstrap)
        self.assertIn("arquitectura: autonomo", self.bootstrap)
        self.assertIn("desarrollo: autonomo", self.bootstrap)
        self.assertIn("documentacion: autonomo", self.bootstrap)
        self.assertIn("entrega: autonomo", self.bootstrap)

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

            for settings_path in (settings_local, settings_shared):
                with open(settings_path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)

                self.assertEqual(payload["defaultMode"], "acceptEdits")
                self.assertIn("Bash(python3 .claude/alfred-continuity.py *)", payload["permissions"]["allow"])


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


if __name__ == "__main__":
    unittest.main()
