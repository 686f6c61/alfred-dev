#!/usr/bin/env python3
"""Clasificación de prompts sin slash."""

import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.prompt_route import classify_prompt, render_route_hint


class TestPromptRoute(unittest.TestCase):
    def test_slash_commands_are_ignored(self):
        self.assertIsNone(classify_prompt("/alfred-dev:fix el login"))
        self.assertIsNone(classify_prompt("/compact"))

    def test_classifies_common_spanish_phrases(self):
        cases = {
            "sigue donde lo dejé": "retomar",
            "el login peta con eñes": "fix",
            "cambia el texto del botón": "quick",
            "esto va a producción": "ship",
            "qué decidimos de auth": "memory",
            "mapea este repo": "map-codebase",
            "audita la seguridad": "audit",
        }
        for prompt, route in cases.items():
            match = classify_prompt(prompt)
            self.assertIsNotNone(match, prompt)
            self.assertEqual(match["route"], route, prompt)

    def test_short_or_empty_is_silent(self):
        self.assertIsNone(classify_prompt("ok"))
        self.assertIsNone(classify_prompt("hola"))
        self.assertIsNone(classify_prompt("   "))

    def test_hint_mentions_command(self):
        match = classify_prompt("el endpoint falla con 500")
        self.assertIsNotNone(match)
        self.assertIn("/alfred-dev:fix", render_route_hint(match))

    def test_hook_emits_additional_context(self):
        script = os.path.join(os.path.dirname(__file__), "..", "hooks", "prompt-route.py")
        result = subprocess.run(
            [sys.executable, script],
            input=json.dumps({"prompt": "el login peta"}),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("/alfred-dev:fix", context)

    def test_hook_is_silent_without_signal(self):
        script = os.path.join(os.path.dirname(__file__), "..", "hooks", "prompt-route.py")
        result = subprocess.run(
            [sys.executable, script],
            input=json.dumps({"prompt": "hola"}),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
