#!/usr/bin/env python3
"""Tests del preflight externo seguro de release."""

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(ROOT, "scripts", "external_live_smoke.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("external_live_smoke", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestExternalLiveSmoke(unittest.TestCase):
    def test_default_preflight_writes_private_non_destructive_evidence(self):
        external = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "external-live-smoke.json"
            with mock.patch.object(
                external,
                "_github_preflight",
                return_value={"status": "ready", "write_attempted": False},
            ), mock.patch.object(
                external,
                "_docker_sonarqube_preflight",
                return_value={"status": "docker_ready", "live_attempted": False},
            ), mock.patch.object(
                external,
                "_codex_preflight",
                return_value={"status": "ready", "live_attempted": False},
            ), mock.patch.object(external, "_github_live_sync") as github_live, mock.patch.object(
                external,
                "_codex_live_exec",
            ) as codex_live:
                self.assertEqual(external.main(["--output", str(output)]), 0)

            github_live.assert_not_called()
            codex_live.assert_not_called()
            payload = json.loads(output.read_text(encoding="utf-8"))
            mode = output.stat().st_mode & 0o777

        self.assertEqual(payload["version"], "0.6.0")
        self.assertEqual(payload["mode"], "preflight")
        self.assertEqual(payload["counts"]["ready"], 3)
        self.assertEqual(payload["counts"]["blocked"], 0)
        self.assertEqual(payload["counts"]["live_attempted"], 0)
        self.assertEqual(mode, 0o600)

    def test_require_all_ready_returns_two_when_preflight_is_blocked(self):
        external = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "external-live-smoke.json"
            with mock.patch.object(
                external,
                "_github_preflight",
                return_value={"status": "auth_required", "write_attempted": False},
            ), mock.patch.object(
                external,
                "_docker_sonarqube_preflight",
                return_value={"status": "docker_ready", "live_attempted": False},
            ), mock.patch.object(
                external,
                "_codex_preflight",
                return_value={"status": "ready", "live_attempted": False},
            ):
                self.assertEqual(
                    external.main(["--require-all-ready", "--output", str(output)]),
                    2,
                )

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["counts"]["ready"], 2)
        self.assertEqual(payload["counts"]["blocked"], 1)

    def test_github_write_requires_repo(self):
        external = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "external-live-smoke.json"
            with mock.patch.object(
                external,
                "_github_preflight",
                return_value={"status": "ready", "write_attempted": False},
            ), mock.patch.object(
                external,
                "_docker_sonarqube_preflight",
                return_value={"status": "docker_ready", "live_attempted": False},
            ), mock.patch.object(
                external,
                "_codex_preflight",
                return_value={"status": "ready", "live_attempted": False},
            ), mock.patch.object(external, "sync_project_to_github") as sync:
                self.assertEqual(
                    external.main(["--allow-github-write", "--output", str(output)]),
                    1,
                )

            sync.assert_not_called()
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["github"]["status"], "skipped")
        self.assertFalse(payload["github"]["write_attempted"])

    def test_codex_preflight_requires_json_and_last_message_flags(self):
        external = _load_module()

        def fake_run(command, **_kwargs):
            if command == ["/usr/local/bin/codex", "--version"]:
                return {"returncode": 0, "stdout_preview": "codex-cli 0.137.0", "stderr_preview": ""}
            return {
                "returncode": 0,
                "stdout_preview": "--sandbox --ephemeral --json",
                "stderr_preview": "",
            }

        with mock.patch.object(external.shutil, "which", return_value="/usr/local/bin/codex"), mock.patch.object(
            external,
            "_run",
            side_effect=fake_run,
        ):
            payload = external._codex_preflight()

        self.assertEqual(payload["status"], "exec_help_missing_flags")
        self.assertEqual(payload["missing_flags"], ["--output-last-message"])

    def test_codex_live_exec_uses_jsonl_and_output_last_message(self):
        external = _load_module()
        calls = []

        def fake_run(command, **_kwargs):
            calls.append(command)
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text("OK_ALFRED_CODEX_EXTERNAL_060\n", encoding="utf-8")
            return {
                "returncode": 0,
                "stdout_preview": '{"type":"turn.completed"}',
                "stderr_preview": "",
            }

        with mock.patch.object(external.shutil, "which", return_value="/usr/local/bin/codex"), mock.patch.object(
            external,
            "_run",
            side_effect=fake_run,
        ):
            payload = external._codex_live_exec()

        command = calls[0]
        self.assertEqual(payload["status"], "ok")
        self.assertIn("--json", command)
        self.assertIn("--output-last-message", command)
        self.assertIn("OK_ALFRED_CODEX_EXTERNAL_060", payload["final_message_preview"])

    def test_safe_preview_sanitizes_secret_like_output(self):
        external = _load_module()

        preview = external._safe_preview("token='ghp_123456789012345678901234567890123456'")

        self.assertIn("[REDACTED:GITHUB_TOKEN]", preview)
        self.assertNotIn("ghp_1234567890", preview)


if __name__ == "__main__":
    unittest.main()
