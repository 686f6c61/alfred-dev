#!/usr/bin/env python3
"""Tests para hooks/secret-guard.sh."""

import json
import os
import subprocess
import unittest


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
HOOK_PATH = os.path.join(PROJECT_ROOT, "hooks", "secret-guard.sh")


class TestSecretGuard(unittest.TestCase):
    """Verifica el comportamiento end-to-end del guard de secretos."""

    def _run_hook(self, tool_input=None, raw_input=None):
        if raw_input is None:
            raw_input = json.dumps({"tool_input": tool_input or {}})

        return subprocess.run(
            ["bash", HOOK_PATH],
            input=raw_input,
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=False,
        )

    def test_env_file_is_allowed(self):
        """Un .env real es un contenedor legitimo y no debe bloquearse."""
        fake_key = "sk-" + "a" * 24
        result = self._run_hook({
            "file_path": "/tmp/.env",
            "content": f'OPENAI_API_KEY="{fake_key}"',
        })

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_env_file_is_allowed(self):
        """local.env tambien debe permitirse."""
        fake_key = "sk-" + "b" * 24
        result = self._run_hook({
            "file_path": "/tmp/local.env",
            "content": f'OPENAI_API_KEY="{fake_key}"',
        })

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_env_example_blocks_real_secret(self):
        """.env.example no debe actuar como whitelist para secretos reales."""
        fake_key = "sk-" + "c" * 24
        result = self._run_hook({
            "file_path": "/tmp/.env.example",
            "content": f'OPENAI_API_KEY="{fake_key}"',
        })

        self.assertEqual(result.returncode, 2)
        self.assertIn("ALERTA DE SEGURIDAD", result.stderr)

    def test_edit_new_string_blocks_secret(self):
        """Edit usa new_string y debe bloquear igual que Write."""
        fake_key = "sk-" + "d" * 24
        result = self._run_hook({
            "file_path": "/tmp/config.py",
            "new_string": f'OPENAI_API_KEY = "{fake_key}"',
        })

        self.assertEqual(result.returncode, 2)
        self.assertIn("prefijo sk-", result.stderr)

    def test_short_connection_string_with_credentials_is_blocked(self):
        """Las DSN con user:pass cortos tambien deben bloquearse."""
        conn_str = "postgres://user:pass@example.com/app"
        result = self._run_hook({
            "file_path": "/tmp/settings.py",
            "content": f'DATABASE_URL = "{conn_str}"',
        })

        self.assertEqual(result.returncode, 2)
        self.assertIn("Connection string", result.stderr)

    def test_private_key_header_blocks_without_grep_noise(self):
        """Una cabecera PEM debe bloquear sin errores espurios de grep."""
        pem_header = "-----BEGIN " + "PRIVATE KEY-----"
        result = self._run_hook({
            "file_path": "/tmp/credentials.py",
            "content": pem_header,
        })

        self.assertEqual(result.returncode, 2)
        self.assertIn("Clave privada", result.stderr)
        self.assertNotIn("grep:", result.stderr)

    def test_bash_command_blocks_secret(self):
        fake_key = "sk-" + "e" * 24
        result = self._run_hook(raw_input=json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": f'echo "{fake_key}" > /tmp/key.txt'},
        }))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("ALERTA DE SEGURIDAD", result.stderr)

    def test_mcp_write_payload_blocks_secret(self):
        fake_key = "sk-ant-" + "f" * 24
        result = self._run_hook(raw_input=json.dumps({
            "tool_name": "mcp__other__write_file",
            "tool_input": {"content": fake_key},
        }))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("ALERTA DE SEGURIDAD", result.stderr)

    def test_invalid_json_blocks_fail_closed(self):
        """Si no puede parsear la entrada debe bloquear por precaucion."""
        result = self._run_hook(raw_input="{esto no es json")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Operación bloqueada por precaución", result.stderr)


if __name__ == "__main__":
    unittest.main()
