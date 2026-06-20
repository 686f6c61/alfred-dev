#!/usr/bin/env python3
"""Tests del diagnostico humano de auth de Claude CLI."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "claude_auth_recovery.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("claude_auth_recovery", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _blocked_oauth_preflight():
    return {
        "status": "blocked_auth",
        "reason": "Claude CLI devolvio 401 Invalid authentication credentials.",
        "returncode": 1,
        "api_error_status": 401,
        "auth_status": {
            "credential_env": {
                "ANTHROPIC_API_KEY": False,
                "CLAUDE_CODE_OAUTH_TOKEN": False,
            },
            "claude_version": "2.1.183 (Claude Code)",
            "loggedIn": True,
            "authMethod": "claude.ai",
            "apiProvider": "firstParty",
            "subscriptionType": "max",
        },
        "diagnosis": {
            "code": "first_party_oauth_token_rejected",
            "summary": "OAuth first-party rechazado.",
        },
    }


class TestClaudeAuthRecovery(unittest.TestCase):
    def test_payload_recommends_interactive_relogin_for_rejected_oauth(self):
        recovery = _load_module()

        payload = recovery.build_recovery_payload(_blocked_oauth_preflight(), system_name="Darwin")
        formatted = recovery.format_guidance(payload)

        self.assertEqual(payload["diagnosis_code"], "first_party_oauth_token_rejected")
        self.assertIn("claude doctor", payload["recovery_commands"])
        self.assertIn(
            "security unlock-keychain ~/Library/Keychains/login.keychain-db",
            payload["recovery_commands"],
        )
        self.assertIn("claude auth logout", payload["recovery_commands"])
        self.assertIn("claude auth login", payload["recovery_commands"])
        self.assertIn("npm run release:audit:prepublish:prepare", payload["recovery_commands"])
        self.assertIn("claude setup-token", payload["fallback_commands"])
        self.assertIn("CLAUDE_CODE_OAUTH_TOKEN", " ".join(payload["fallback_commands"]))
        self.assertIn("debug-file", " ".join(payload["debug_commands"]))
        self.assertIn("doctor no emite salida", " ".join(payload["notes"]))
        self.assertIn("ANTHROPIC_API_KEY", payload["credential_precedence"])
        self.assertIn("Credential env: none", formatted)
        self.assertIn("Platform: Darwin", formatted)
        self.assertIn("Fallback for scripted/manual evidence", formatted)
        self.assertIn("Optional debug for support", formatted)
        self.assertIn("Do not publish", formatted)

    def test_payload_does_not_show_macos_keychain_command_on_linux(self):
        recovery = _load_module()

        payload = recovery.build_recovery_payload(_blocked_oauth_preflight(), system_name="Linux")

        self.assertIn("claude doctor", payload["recovery_commands"])
        self.assertNotIn(
            "security unlock-keychain ~/Library/Keychains/login.keychain-db",
            payload["recovery_commands"],
        )

    def test_payload_prioritizes_environment_credentials_when_present(self):
        recovery = _load_module()
        preflight = _blocked_oauth_preflight()
        preflight["auth_status"]["credential_env"]["ANTHROPIC_API_KEY"] = True

        payload = recovery.build_recovery_payload(preflight, system_name="Darwin")

        self.assertEqual(payload["active_credential_env"], ["ANTHROPIC_API_KEY"])
        self.assertNotIn("claude auth logout", payload["recovery_commands"])
        self.assertIn("terminal limpia", " ".join(payload["notes"]))

    def test_main_writes_private_report_and_strict_fails_on_blocked_auth(self):
        recovery = _load_module()

        class FakeManualSmoke:
            @staticmethod
            def _auth_preflight(timeout=45):
                return _blocked_oauth_preflight()

        original_loader = recovery._manual_smoke_module
        recovery._manual_smoke_module = lambda: FakeManualSmoke
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output = Path(tmpdir) / "auth.json"
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = recovery.main(["--strict", "--output", str(output)])

                self.assertEqual(result, 2)
                payload = json.loads(output.read_text(encoding="utf-8"))
                mode = output.stat().st_mode & 0o777
                self.assertEqual(mode, 0o600)
                self.assertEqual(payload["status"], "blocked_auth")
                self.assertIn("Recovery commands:", stdout.getvalue())
        finally:
            recovery._manual_smoke_module = original_loader

    def test_main_json_mode_returns_zero_without_strict_for_diagnostics(self):
        recovery = _load_module()

        class FakeManualSmoke:
            @staticmethod
            def _auth_preflight(timeout=45):
                return _blocked_oauth_preflight()

        original_loader = recovery._manual_smoke_module
        recovery._manual_smoke_module = lambda: FakeManualSmoke
        try:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = recovery.main(["--json"])

            self.assertEqual(result, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["api_error_status"], 401)
        finally:
            recovery._manual_smoke_module = original_loader


if __name__ == "__main__":
    unittest.main()
