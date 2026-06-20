#!/usr/bin/env python3
"""Tests de integración para start-server.sh y stop-server.sh."""

import json
import os
import shutil
import signal
import stat
import subprocess
import tempfile
import unittest


SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visual",
    "scripts",
)
START_SERVER = os.path.join(SCRIPTS_DIR, "start-server.sh")
STOP_SERVER = os.path.join(SCRIPTS_DIR, "stop-server.sh")


class TestVisualScripts(unittest.TestCase):
    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="alfred-visual-project-")

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    def test_start_server_background_returns_metadata_and_stop_server_stops_it(self):
        result = subprocess.run(
            ["bash", START_SERVER, "--project-dir", self.project_dir, "--background"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        payload = json.loads(result.stdout)
        self.assertEqual(payload["type"], "server-started")
        self.assertTrue(payload["session_dir"].startswith(self.project_dir))
        self.assertTrue(os.path.isfile(payload["pid_file"]))
        self.assertGreater(payload["server_pid"], 0)
        for path in (
            payload["session_dir"],
            os.path.join(payload["session_dir"], "content"),
            os.path.join(payload["session_dir"], "state"),
        ):
            mode = stat.S_IMODE(os.stat(path).st_mode)
            self.assertEqual(mode & 0o077, 0, msg=f"{path} no es privado: {oct(mode)}")

        info_path = os.path.join(payload["session_dir"], "state", "server-info")
        self.assertTrue(os.path.isfile(info_path))
        with open(info_path, "r", encoding="utf-8") as fh:
            info = json.load(fh)
        self.assertEqual(info["session_dir"], payload["session_dir"])
        self.assertEqual(info["server_pid"], payload["server_pid"])

        stop = subprocess.run(
            ["bash", STOP_SERVER, payload["session_dir"]],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(stop.returncode, 0, msg=stop.stderr)
        self.assertEqual(json.loads(stop.stdout)["status"], "stopped")

    def test_stop_server_does_not_kill_unrelated_process_from_stale_pid_file(self):
        session_dir = os.path.join(self.project_dir, ".alfred-dev", "visual", "stale")
        state_dir = os.path.join(session_dir, "state")
        os.makedirs(state_dir, exist_ok=True)

        sleeper = subprocess.Popen(["sleep", "30"])
        try:
            with open(os.path.join(state_dir, "server.pid"), "w", encoding="utf-8") as fh:
                fh.write(str(sleeper.pid))

            result = subprocess.run(
                ["bash", STOP_SERVER, session_dir],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "not_running")
            self.assertIsNone(sleeper.poll())
        finally:
            if sleeper.poll() is None:
                sleeper.send_signal(signal.SIGTERM)
                sleeper.wait(timeout=5)

    def test_start_server_cleans_pid_file_when_node_fails_before_start(self):
        env = os.environ.copy()
        env["ALFRED_VISUAL_PORT"] = "not-a-number"

        result = subprocess.run(
            ["bash", START_SERVER, "--project-dir", self.project_dir, "--background"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertNotEqual(result.returncode, 0)

        payload = json.loads(result.stdout)
        self.assertEqual(payload["type"], "error")
        session_dir = payload["session_dir"]
        self.assertTrue(os.path.isdir(session_dir))
        self.assertFalse(os.path.exists(os.path.join(session_dir, "state", "server.pid")))

    def test_start_server_reports_missing_option_value_as_json(self):
        result = subprocess.run(
            ["bash", START_SERVER, "--project-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["type"], "error")
        self.assertIn("Falta valor para --project-dir", payload["message"])

    def test_start_server_escapes_unknown_argument_json(self):
        result = subprocess.run(
            ["bash", START_SERVER, 'bad"arg'],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["type"], "error")
        self.assertIn('bad"arg', payload["message"])


if __name__ == "__main__":
    unittest.main()
