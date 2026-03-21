#!/usr/bin/env python3
"""Tests de contrato para el hook de SessionStart.

Protegen el contexto operativo que Alfred inyecta al arrancar en Claude Code.
"""

import os
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestSessionStartHookContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hook = _read("hooks/session-start.sh")

    def test_hook_announces_current_command_prefix(self):
        self.assertIn("/alfred-dev:feature", self.hook)
        self.assertIn("/alfred-dev:audit", self.hook)
        self.assertIn("/alfred-dev:help", self.hook)
        self.assertNotIn("- /alfred audit -", self.hook)

    def test_hook_uses_current_update_command_and_semver_ordering(self):
        self.assertIn("/alfred-dev:update", self.hook)
        self.assertIn("UPDATE_AVAILABLE=$(python3 -c", self.hook)
        self.assertNotIn('"$LATEST_RELEASE" != "$CURRENT_VERSION"', self.hook)


if __name__ == "__main__":
    unittest.main()
