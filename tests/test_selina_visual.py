#!/usr/bin/env python3
"""Tests para la lectura canónica de elecciones visuales de Selina."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from core.selina_visual import (
    events_file_for,
    read_latest_style_choice,
    resolve_state_dir,
)


READ_CHOICE_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visual",
    "scripts",
    "read-choice.py",
)


class TestSelinaVisual(unittest.TestCase):
    def setUp(self):
        self.session_dir = tempfile.mkdtemp(prefix="alfred-selina-visual-")
        self.state_dir = os.path.join(self.session_dir, "state")
        os.makedirs(self.state_dir, exist_ok=True)
        self.events_path = os.path.join(self.state_dir, "events")

    def tearDown(self):
        shutil.rmtree(self.session_dir, ignore_errors=True)

    def test_read_latest_style_choice_uses_last_valid_click(self):
        with open(self.events_path, "w", encoding="utf-8") as fh:
            fh.write('{"type":"hover","choice":"A"}\n')
            fh.write("no es json\n")
            fh.write('{"type":"click","choice":"A","element":".style-option","ts":"2026-04-07T10:00:00Z"}\n')
            fh.write('{"source":"user-event","type":"click","choice":"B","label":"Editorial","timestamp":"2026-04-07T10:00:01Z"}\n')

        choice = read_latest_style_choice(self.state_dir)
        self.assertEqual(
            choice,
            {
                "choice": "B",
                "label": "Editorial",
                "timestamp": "2026-04-07T10:00:01Z",
                "element": ".style-option",
            },
        )

    def test_read_latest_style_choice_ignores_non_style_targets(self):
        with open(self.events_path, "w", encoding="utf-8") as fh:
            fh.write('{"type":"click","choice":"A","element":".other"}\n')

        self.assertIsNone(read_latest_style_choice(self.session_dir))

    def test_resolve_state_dir_accepts_session_or_state_dir(self):
        self.assertEqual(resolve_state_dir(self.session_dir), self.state_dir)
        self.assertEqual(resolve_state_dir(self.state_dir), self.state_dir)
        self.assertEqual(events_file_for(self.session_dir), self.events_path)

    def test_read_choice_cli_returns_pending_without_valid_choice(self):
        result = subprocess.run(
            ["python3", READ_CHOICE_SCRIPT, self.session_dir],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["state_dir"], self.state_dir)

    def test_read_choice_cli_returns_latest_choice(self):
        with open(self.events_path, "w", encoding="utf-8") as fh:
            fh.write('{"type":"click","choice":"C","label":"Minimalismo vibrante","ts":"2026-04-07T10:00:02Z"}\n')

        result = subprocess.run(
            ["python3", READ_CHOICE_SCRIPT, self.state_dir],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["choice"], "C")
        self.assertEqual(payload["label"], "Minimalismo vibrante")
        self.assertEqual(payload["timestamp"], "2026-04-07T10:00:02Z")


if __name__ == "__main__":
    unittest.main()
