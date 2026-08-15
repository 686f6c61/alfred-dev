#!/usr/bin/env python3
"""SessionEnd escribe el cierre si hubo trabajo."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.hygiene import write_session_cierre


class TestSessionEndCierre(unittest.TestCase):
    def test_skips_empty_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsNone(write_session_cierre(tmpdir))
            self.assertFalse(
                os.path.exists(os.path.join(tmpdir, ".claude", "alfred-last-cierre.md"))
            )

    def test_writes_cierre_when_session_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude = os.path.join(tmpdir, ".claude")
            os.makedirs(claude, exist_ok=True)
            with open(os.path.join(claude, "alfred-dev-state.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "comando": "quick",
                        "descripcion": "cambia el CTA",
                        "fase_actual": "validacion_rapida",
                        "fase_numero": 1,
                    },
                    handle,
                )
            path = write_session_cierre(tmpdir)
            self.assertIsNotNone(path)
            text = open(path, encoding="utf-8").read()
            self.assertIn("Cierre Alfred", text)
            self.assertIn("cambia el CTA", text)

    def test_hook_exits_zero(self):
        script = os.path.join(os.path.dirname(__file__), "..", "hooks", "session-end.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, script],
                cwd=tmpdir,
                input="{}",
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
