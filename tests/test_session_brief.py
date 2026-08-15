#!/usr/bin/env python3
"""Briefing de sesión y protocolo de conversación."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory import MemoryDB
from core.session_brief import (
    build_session_brief,
    render_session_start_context,
)


class TestSessionBrief(unittest.TestCase):
    def test_empty_project_asks_what_to_do(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            brief = build_session_brief(tmpdir)
            self.assertFalse(brief["active"])
            text = render_session_start_context(tmpdir)
            self.assertIn("/alfred-dev:alfred", text)
            self.assertIn("/alfred-dev:feature", text)
            self.assertIn("Agent Teams", text)
            self.assertIn("slash command", text.lower())
            self.assertIn("No hay sesión abierta", text)

    def test_active_session_points_to_retomar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude = os.path.join(tmpdir, ".claude")
            os.makedirs(claude, exist_ok=True)
            with open(os.path.join(claude, "alfred-dev-state.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "comando": "feature",
                        "descripcion": "login con email",
                        "fase_actual": "calidad",
                        "fase_numero": 4,
                    },
                    handle,
                )
            brief = build_session_brief(tmpdir)
            self.assertTrue(brief["active"])
            self.assertEqual(brief["next_step"], "/alfred-dev:retomar")
            text = render_session_start_context(tmpdir)
            self.assertIn("calidad", text)
            self.assertIn("/alfred-dev:retomar", text)

    def test_includes_last_decision_when_memory_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude = os.path.join(tmpdir, ".claude")
            os.makedirs(claude, exist_ok=True)
            with open(os.path.join(claude, "alfred-dev.local.md"), "w", encoding="utf-8") as handle:
                handle.write("---\nmemoria:\n  enabled: true\n---\n")
            db = MemoryDB(os.path.join(claude, "alfred-memory.db"))
            db.start_iteration("feature", "auth")
            db.log_decision(title="Auth con JWT", chosen="JWT, no sesiones")
            db.close()
            text = render_session_start_context(tmpdir)
            self.assertIn("Auth con JWT", text)
            self.assertIn("JWT, no sesiones", text)

    def test_session_start_hook_emits_briefing(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        script = os.path.join(root, "hooks", "session-start.sh")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [script],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("/alfred-dev:alfred", context)
            self.assertIn("Briefing", context)


if __name__ == "__main__":
    unittest.main()
