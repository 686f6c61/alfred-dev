#!/usr/bin/env python3
"""Tests E2E del prototipo de Memory UI."""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.continuity import launch_memory_ui, stop_memory_ui
from core.memory import MemoryDB


class TestMemoryUI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".claude"), exist_ok=True)
        os.makedirs(os.path.join(self.tmpdir, "docs", "project"), exist_ok=True)

        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        iteration_id = db.start_iteration("feature", "Sistema de login social")
        dec1 = db.log_decision(
            title="Usar OAuth 2.1",
            chosen="GitHub + Google con backend centralizado",
            rationale="Evita flujos duplicados y simplifica auditoría",
            tags=["auth", "security"],
            iteration_id=iteration_id,
        )
        dec2 = db.log_decision(
            title="Persistir sesiones en SQLite",
            chosen="SQLite por simplicidad y trazabilidad local",
            rationale="Encaja con la memoria persistente del proyecto",
            tags=["storage"],
            iteration_id=iteration_id,
        )
        db.link_decisions(dec1, dec2, "depends_on")
        db.log_commit(
            sha="abc1234567890",
            message="feat: implementar callback OAuth",
            author="Alfred",
            iteration_id=iteration_id,
            files=["src/auth/callback.ts", "tests/auth/callback.test.ts"],
        )
        db.log_event(
            event_type="phase_completed",
            phase="arquitectura",
            summary="Arquitectura completada",
            content="ADR aprobada para OAuth y persistencia local.",
            iteration_id=iteration_id,
        )
        db.close()
        self._launched = []

    def tearDown(self):
        try:
            result = stop_memory_ui(self.tmpdir)
            pid = int(result.get("pid", 0) or 0)
            if pid > 0:
                deadline = time.time() + 3
                while time.time() < deadline:
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        break
                    time.sleep(0.1)
                else:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
        finally:
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _get_json(self, url: str):
        with urllib.request.urlopen(url, timeout=3) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_launch_memory_ui_exposes_live_endpoints(self):
        result = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4511,
        )

        self.assertIn("url", result)
        overview = self._get_json(f"{result['url']}/api/overview")
        self.assertEqual(overview["plugin_name"], "Alfred Dev")
        self.assertEqual(overview["ui_version"], "0.0.2")
        self.assertEqual(overview["stats"]["total_decisions"], 2)
        self.assertEqual(overview["stats"]["total_commits"], 1)
        self.assertEqual(overview["health"]["status"], "healthy")

        decisions = self._get_json(f"{result['url']}/api/decisions")
        self.assertEqual(len(decisions["items"]), 2)
        self.assertEqual(decisions["items"][0]["title"], "Persistir sesiones en SQLite")

        graph = self._get_json(f"{result['url']}/api/graph")
        self.assertGreaterEqual(len(graph["nodes"]), 2)
        self.assertGreaterEqual(len(graph["edges"]), 1)

        commits = self._get_json(f"{result['url']}/api/commits")
        self.assertEqual(commits["items"][0]["sha_short"], "abc12345")

        activity = self._get_json(f"{result['url']}/api/activity")
        self.assertTrue(activity["recent_events"])
        self.assertTrue(activity["event_counts"])
        self.assertIn("display_title", activity["recent_events"][0])
        self.assertIn("display_body", activity["recent_events"][0])

        query = urllib.parse.quote("OAuth")
        search = self._get_json(f"{result['url']}/api/search?q={query}")
        self.assertTrue(search["memory"])

    def test_activity_humanizes_task_notification_events(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        active = db.get_active_iteration()
        iteration_id = int(active["id"])
        db.log_event(
            event_type="user_prompt",
            summary="Prompt: <task-notification>...",
            content=(
                "<task-notification>\n"
                "<task-id>abc123</task-id>\n"
                "<tool-use-id>toolu_01</tool-use-id>\n"
                "<output-file>/tmp/abc123.output</output-file>\n"
                "<status>killed</status>\n"
                "<summary>Agent \"Auditoría QA del proyecto\" was stopped</summary>\n"
                "<result>Tengo suficiente material.</result>\n"
                "</task-notification>\n"
                "Full transcript available at: /tmp/abc123.output\n"
            ),
            iteration_id=iteration_id,
        )
        db.close()

        result = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4541,
        )
        activity = self._get_json(f"{result['url']}/api/activity")
        first = activity["recent_events"][0]
        self.assertEqual(first["kind_label"], "Subagente")
        self.assertEqual(first["status_label"], "killed")
        self.assertIn("Auditoría QA del proyecto", first["display_title"])
        self.assertIn("Tengo suficiente material", first["display_body"])

    def test_activity_humanizes_helper_seeded_events(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        active = db.get_active_iteration()
        iteration_id = int(active["id"])
        db.log_event(
            event_type="helper_seeded",
            phase="discovery",
            summary="Refinado preparado para /alfred-dev:feature",
            content=(
                "Refinado previo listo para 'Login social'. "
                "Siguiente comando recomendado: /alfred-dev:feature."
            ),
            payload={
                "helper": "discuss",
                "recommended_command": "feature",
                "artifacts": [
                    "docs/project/discovery.md",
                    "docs/project/current.md",
                ],
            },
            iteration_id=iteration_id,
        )
        db.close()

        result = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4542,
        )
        activity = self._get_json(f"{result['url']}/api/activity")
        first = activity["recent_events"][0]
        self.assertEqual(first["kind_label"], "Helper")
        self.assertIn("Refinado preparado", first["display_title"])
        self.assertIn("Login social", first["display_body"])
        self.assertTrue(any("Siguiente paso" in line for line in first["detail_lines"]))

    def test_launch_memory_ui_reuses_existing_process(self):
        first = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4531,
        )
        second = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4531,
        )

        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        self.assertEqual(first["url"], second["url"])
        self.assertEqual(first["pid"], second["pid"])

    def test_cli_memory_ui_script_mode_supports_direct_execution(self):
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
                "memory-ui",
                self.tmpdir,
                "--json",
                "--no-open",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("url", payload)
        self.assertTrue(payload["url"].startswith("http://127.0.0.1:"))

    def test_memory_ui_imports_recent_git_history_when_commits_are_missing(self):
        repo = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        os.makedirs(os.path.join(repo, ".claude"), exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Alfred"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "alfred@example.com"], cwd=repo, check=True)
        with open(os.path.join(repo, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("# Demo\n")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "feat: crear demo base"], cwd=repo, check=True)

        result = launch_memory_ui(
            repo,
            open_browser_window=False,
            preferred_port=4543,
        )
        self.addCleanup(lambda: stop_memory_ui(repo))

        overview = self._get_json(f"{result['url']}/api/overview")
        commits = self._get_json(f"{result['url']}/api/commits")

        self.assertGreaterEqual(overview["stats"]["total_commits"], 1)
        self.assertEqual(commits["items"][0]["message"], "feat: crear demo base")

    def test_overview_describes_empty_non_git_workspace(self):
        empty_repo = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(empty_repo, ignore_errors=True))
        os.makedirs(os.path.join(empty_repo, ".claude"), exist_ok=True)

        result = launch_memory_ui(
            empty_repo,
            open_browser_window=False,
            preferred_port=4544,
        )
        self.addCleanup(lambda: stop_memory_ui(empty_repo))

        overview = self._get_json(f"{result['url']}/api/overview")
        self.assertFalse(overview["workspace"]["is_git_repo"])
        self.assertFalse(overview["workspace"]["has_codebase"])
