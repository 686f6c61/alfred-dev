#!/usr/bin/env python3
"""Tests E2E del prototipo de Memory UI."""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.continuity import (
    assert_memory_ui_loopback_host,
    is_memory_ui_stop_request,
    launch_memory_ui,
    render_memory_ui_markdown,
    stop_memory_ui,
    _save_memory_ui_state,
)
from core.memory import MemoryDB
from core.memory_ui_server import (
    build_activity_payload,
    build_commits_payload,
    build_graph_payload,
    build_iterations_payload,
    build_overview_payload,
    build_snapshot_payload,
    build_timeline_payload,
)


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
        self.assertEqual(overview["ui_version"], "0.0.4")
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

    def test_build_activity_payload_counts_recent_window_instead_of_full_history(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        iteration_id = int(db.get_active_iteration()["id"])
        for index in range(6):
            db.log_event(
                event_type="helper_seeded",
                summary=f"helper viejo {index}",
                iteration_id=iteration_id,
            )
        for index in range(3):
            db.log_event(
                event_type="command_executed",
                summary=f"comando reciente {index}",
                iteration_id=iteration_id,
            )
        db.close()

        payload = build_activity_payload(db_path, limit=3)
        self.assertEqual(len(payload["recent_events"]), 3)
        self.assertEqual(
            payload["event_counts"],
            [
                {
                    "event_type": "command_executed",
                    "label": "Comando",
                    "total": 3,
                }
            ],
        )
        self.assertEqual(payload["total_event_counts"][0]["event_type"], "helper_seeded")

    def test_build_overview_payload_ignores_bootstrap_only_events_for_workspace_notice(self):
        empty_repo = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(empty_repo, ignore_errors=True))
        os.makedirs(os.path.join(empty_repo, ".claude"), exist_ok=True)
        db_path = os.path.join(empty_repo, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        db.log_event(
            event_type="session_started",
            summary="Sesión abierta por bootstrap",
            content="Memoria lista.",
        )
        db.close()

        overview = build_overview_payload(
            empty_repo,
            db_path,
            host="127.0.0.1",
            port=4551,
        )
        self.assertEqual(overview["stats"]["total_events"], 1)
        self.assertEqual(overview["workspace"]["bootstrap_event_count"], 1)
        self.assertEqual(overview["workspace"]["meaningful_event_count"], 0)
        self.assertFalse(overview["workspace"]["has_meaningful_memory"])

    def test_build_overview_payload_exposes_canonical_project_signal_cards(self):
        state_path = os.path.join(self.tmpdir, ".claude", "alfred-dev-state.json")
        with open(
            state_path,
            "w",
            encoding="utf-8",
        ) as fh:
            json.dump(
                {
                    "comando": "feature",
                    "descripcion": "Checkout nuevo",
                    "fase_actual": "completado",
                    "objetivo": "Checkout nuevo",
                    "fases_completadas": ["producto", "arquitectura", "desarrollo"],
                },
                fh,
                ensure_ascii=False,
            )

        overview = build_overview_payload(
            self.tmpdir,
            os.path.join(self.tmpdir, ".claude", "alfred-memory.db"),
            host="127.0.0.1",
            port=4552,
        )
        cards = overview["progress"]["project_signal_cards"]
        titles = [card["title"] for card in cards]
        self.assertNotIn("Current", titles)
        self.assertIn("Progreso", titles)

    def test_build_overview_payload_exposes_structured_next_action_guidance(self):
        overview = build_overview_payload(
            self.tmpdir,
            os.path.join(self.tmpdir, ".claude", "alfred-memory.db"),
            host="127.0.0.1",
            port=4554,
        )

        next_action = overview["progress"]["next_action"]
        self.assertIn("focus", next_action)
        self.assertIn("directive", next_action)
        self.assertIn("source_label", next_action)
        self.assertIn("urgency", next_action)

    def test_build_overview_payload_exposes_runtime_team_card(self):
        state_path = os.path.join(self.tmpdir, ".claude", "alfred-dev-state.json")
        with open(
            state_path,
            "w",
            encoding="utf-8",
        ) as fh:
            json.dump(
                {
                    "comando": "spike",
                    "descripcion": "Checkout roto",
                    "fase_actual": "exploracion",
                    "fase_numero": 0,
                    "fases_completadas": [],
                    "equipo_sesion": {
                        "opcionales_activos": {
                            "lucius": True,
                        },
                        "infra": {"memoria": False},
                        "fuente": "config_persistida",
                    },
                },
                fh,
                ensure_ascii=False,
            )

        overview = build_overview_payload(
            self.tmpdir,
            os.path.join(self.tmpdir, ".claude", "alfred-memory.db"),
            host="127.0.0.1",
            port=4553,
        )
        team_card = next(
            card for card in overview["progress"]["project_signal_cards"] if card["title"] == "Equipo runtime"
        )
        self.assertIn("Origen runtime: configuración persistida.", team_card["items"])
        self.assertIn(
            "Opcionales solo bajo demanda en este flujo: `lucius`.",
            team_card["items"],
        )

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

    def test_stop_memory_ui_terminates_matching_server(self):
        result = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4532,
        )

        pid = int(result["pid"])
        state_path = os.path.join(self.tmpdir, ".claude", "alfred-memory-ui.json")
        self.assertTrue(os.path.exists(state_path))

        stopped = stop_memory_ui(self.tmpdir)

        self.assertTrue(stopped["stopped"])
        self.assertEqual(stopped["pid"], pid)
        deadline = time.time() + 3
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"{result['url']}/api/healthz", timeout=0.3)
            except Exception:
                break
            time.sleep(0.05)
        else:
            self.fail("La Memory UI siguió respondiendo tras enviar SIGTERM.")

        self.assertFalse(os.path.exists(state_path))

    def test_stop_memory_ui_does_not_kill_unrelated_process_from_stale_state(self):
        dummy = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        def _cleanup_dummy():
            if dummy.poll() is None:
                dummy.terminate()
                try:
                    dummy.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    dummy.kill()
                    dummy.wait(timeout=5)

        self.addCleanup(_cleanup_dummy)

        _save_memory_ui_state(
            self.tmpdir,
            {
                "pid": dummy.pid,
                "url": "http://127.0.0.1:4599",
                "host": "127.0.0.1",
                "port": 4599,
                "project_dir": self.tmpdir,
                "db_path": os.path.join(self.tmpdir, ".claude", "alfred-memory.db"),
            },
        )

        state_path = os.path.join(self.tmpdir, ".claude", "alfred-memory-ui.json")
        stopped = stop_memory_ui(self.tmpdir)

        self.assertFalse(stopped["stopped"])
        self.assertEqual(stopped["reason"], "stale-state")
        self.assertEqual(stopped["pid"], dummy.pid)
        self.assertFalse(os.path.exists(state_path))
        os.kill(dummy.pid, 0)

    def test_launch_memory_ui_rejects_reachable_server_from_other_project(self):
        fake_script = textwrap.dedent(
            """
            import json
            from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

            class FakeHealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == "/api/healthz":
                        body = json.dumps(
                            {
                                "ok": True,
                                "project_dir": "/tmp/otro-proyecto",
                                "db_path": "/tmp/otra-memory.db",
                            }
                        ).encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        return
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()

                def log_message(self, format, *args):
                    return

            ThreadingHTTPServer(("127.0.0.1", 4550), FakeHealthHandler).serve_forever()
            """
        )
        fake_server = subprocess.Popen([sys.executable, "-c", fake_script])
        def _cleanup_fake_server():
            if fake_server.poll() is None:
                fake_server.terminate()
                fake_server.wait(timeout=5)

        self.addCleanup(_cleanup_fake_server)
        deadline = time.time() + 3
        while time.time() < deadline:
            try:
                self._get_json("http://127.0.0.1:4550/api/healthz")
                break
            except Exception:
                time.sleep(0.05)
        else:
            self.fail("El servidor fake de healthz no arrancó a tiempo.")

        _save_memory_ui_state(
            self.tmpdir,
            {
                "pid": fake_server.pid,
                "url": "http://127.0.0.1:4550",
                "host": "127.0.0.1",
                "port": 4550,
                "project_dir": "/tmp/otro-proyecto",
                "db_path": "/tmp/otra-memory.db",
            },
        )

        result = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4550,
        )

        self.assertFalse(result["reused"])
        self.assertNotEqual(result["url"], "http://127.0.0.1:4550")
        overview = self._get_json(f"{result['url']}/api/overview")
        self.assertEqual(overview["project_dir"], self.tmpdir)

    def test_build_iterations_payload_reports_full_event_count(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        active = db.get_active_iteration()
        iteration_id = int(active["id"])
        for index in range(1004):
            db.log_event(
                event_type="command_executed",
                summary=f"evento {index}",
                iteration_id=iteration_id,
            )
        db.close()

        payload = build_iterations_payload(db_path)
        self.assertEqual(payload["items"][0]["event_count"], 1005)

    def test_build_iterations_payload_uses_latest_recent_event_for_summary(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        active = db.get_active_iteration()
        iteration_id = int(active["id"])
        for index in range(4):
            db.log_event(
                event_type="command_executed",
                summary=f"evento antiguo {index}",
                content=f"detalle antiguo {index}",
                iteration_id=iteration_id,
            )
        db.log_event(
            event_type="command_executed",
            summary="evento más reciente",
            content="detalle final de la iteración",
            iteration_id=iteration_id,
        )
        db.close()

        payload = build_iterations_payload(db_path)
        item = payload["items"][0]
        self.assertEqual(item["last_summary"], "evento más reciente")
        self.assertEqual(item["last_title"], "evento más reciente")
        self.assertEqual(item["last_body"], "detalle final de la iteración")

    def test_timeline_endpoint_returns_full_iteration_when_limit_is_omitted(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        active = db.get_active_iteration()
        iteration_id = int(active["id"])
        for index in range(140):
            db.log_event(
                event_type="command_executed",
                summary=f"timeline {index}",
                iteration_id=iteration_id,
            )
        db.close()

        result = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4545,
        )
        timeline = self._get_json(f"{result['url']}/api/timeline?iteration_id={iteration_id}")

        self.assertEqual(timeline["event_count"], 141)
        self.assertEqual(timeline["returned_count"], 141)
        self.assertFalse(timeline["truncated"])
        self.assertEqual(len(timeline["events"]), 141)

    def test_build_timeline_payload_marks_explicit_truncation(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        active = db.get_active_iteration()
        iteration_id = int(active["id"])
        for index in range(12):
            db.log_event(
                event_type="command_executed",
                summary=f"evento {index}",
                iteration_id=iteration_id,
            )
        db.close()

        payload = build_timeline_payload(db_path, iteration_id, limit=5)
        self.assertEqual(payload["event_count"], 13)
        self.assertEqual(payload["returned_count"], 5)
        self.assertTrue(payload["truncated"])
        self.assertEqual(len(payload["events"]), 5)

    def test_build_commits_payload_resolves_iteration_labels_beyond_recent_window(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        first_iteration_id = int(db.get_active_iteration()["id"])
        for index in range(201):
            iteration_id = db.start_iteration("feature", f"iteración {index}")
            db.complete_iteration(iteration_id)
        db.log_commit(
            sha="def1234567890",
            message="feat: mantener contexto de iteración antigua",
            author="Alfred",
            iteration_id=first_iteration_id,
            committed_at="2099-01-01T00:00:00+00:00",
            files=["src/legacy-context.ts"],
        )
        db.close()

        payload = build_commits_payload(db_path, self.tmpdir, limit=5)
        labels = {
            item["sha_short"]: item["iteration_label"]
            for item in payload["items"]
        }
        self.assertEqual(labels["def12345"], "#1 · feature")

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

    def test_memory_ui_does_not_import_git_history_into_sqlite(self):
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

        self.assertEqual(overview["stats"]["total_commits"], 0)
        self.assertTrue(overview["memory_empty"])
        self.assertEqual(overview["progress"], {})
        self.assertEqual(commits["items"], [])

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
        self.assertTrue(overview["memory_empty"])
        self.assertEqual(overview["progress"], {})
        self.assertEqual(overview["stats"]["total_commits"], 0)

    def test_snapshot_filters_by_iteration_and_uses_active_graph_status(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        db = MemoryDB(db_path)
        first_id = int(db.get_active_iteration()["id"])
        second_id = db.start_iteration("fix", "Regresión de checkout")
        db.log_decision(
            title="Aislar el checkout",
            chosen="Reproducir en fixture local",
            rationale="Evita ruido de otros flujos",
            iteration_id=second_id,
        )
        db.close()

        snapshot = build_snapshot_payload(
            self.tmpdir,
            db_path,
            host="127.0.0.1",
            port=4560,
            iteration_id=second_id,
        )
        titles = [item["title"] for item in snapshot["decisions"]["items"]]
        graph_titles = [node["title"] for node in snapshot["graph"]["nodes"]]
        self.assertEqual(snapshot["selected_iteration_id"], second_id)
        self.assertIn("Aislar el checkout", titles)
        self.assertNotIn("Usar OAuth 2.1", titles)
        self.assertIn("Aislar el checkout", graph_titles)
        self.assertTrue(all(node["status"] == "active" for node in snapshot["graph"]["nodes"]))
        self.assertEqual(snapshot["timeline"]["iteration"]["id"], second_id)

        first_snapshot = build_snapshot_payload(
            self.tmpdir,
            db_path,
            host="127.0.0.1",
            port=4560,
            iteration_id=first_id,
        )
        first_titles = [item["title"] for item in first_snapshot["decisions"]["items"]]
        self.assertIn("Usar OAuth 2.1", first_titles)
        self.assertNotIn("Aislar el checkout", first_titles)

    def test_graph_payload_defaults_to_active_status(self):
        db_path = os.path.join(self.tmpdir, ".claude", "alfred-memory.db")
        payload = build_graph_payload(db_path)
        self.assertGreaterEqual(len(payload["nodes"]), 2)
        self.assertTrue(all(node["status"] == "active" for node in payload["nodes"]))
        self.assertIn("decision_id", payload["nodes"][0])
        self.assertIn("chosen", payload["nodes"][0])

    def test_loopback_host_is_required(self):
        with self.assertRaises(RuntimeError):
            assert_memory_ui_loopback_host("0.0.0.0")
        with self.assertRaises(RuntimeError):
            launch_memory_ui(
                self.tmpdir,
                open_browser_window=False,
                host="0.0.0.0",
                preferred_port=4570,
            )
        self.assertEqual(assert_memory_ui_loopback_host("127.0.0.1"), "127.0.0.1")

    def test_stop_request_tokens_and_cli_raw_stop(self):
        self.assertTrue(is_memory_ui_stop_request("stop"))
        self.assertTrue(is_memory_ui_stop_request("cerrar ahora"))
        self.assertFalse(is_memory_ui_stop_request(""))
        self.assertFalse(is_memory_ui_stop_request("abrir"))

        launched = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4571,
        )
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
                "--raw",
                "cerrar",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload.get("stopped"))
        self.assertIn("detenida", render_memory_ui_markdown(payload).lower())
        self.assertFalse(
            os.path.exists(os.path.join(self.tmpdir, ".claude", "alfred-memory-ui.json"))
        )
        deadline = time.time() + 3
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"{launched['url']}/api/healthz", timeout=0.3)
            except Exception:
                break
            time.sleep(0.05)
        else:
            self.fail("La Memory UI siguió respondiendo tras /memory-ui cerrar.")

    def test_snapshot_endpoint_is_exposed(self):
        result = launch_memory_ui(
            self.tmpdir,
            open_browser_window=False,
            preferred_port=4572,
        )
        snapshot = self._get_json(f"{result['url']}/api/snapshot")
        self.assertEqual(snapshot["overview"]["ui_version"], "0.0.4")
        self.assertIn("items", snapshot["iterations"])
        self.assertIn("nodes", snapshot["graph"])
        self.assertIn("events", snapshot["timeline"])
        self.assertTrue(snapshot["selected_iteration_id"])
