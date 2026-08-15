#!/usr/bin/env python3
"""Contratos para exponer el estado operativo de SonIA en CLI."""

import os
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestProgressCommandContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = _read("commands/progress.md")

    def test_progress_reads_sonia_artifacts(self):
        self.assertIn("docs/project/progress.md", self.command)
        self.assertIn("docs/project/traceability.md", self.command)
        self.assertIn("docs/project/kanban/backlog.md", self.command)
        self.assertIn("docs/project/kanban/in-progress.md", self.command)
        self.assertIn("docs/project/kanban/blocked.md", self.command)

    def test_progress_stays_operational(self):
        self.assertIn("/alfred-dev:map-codebase", self.command)
        self.assertIn("/alfred-dev:quick", self.command)
        self.assertIn("/alfred-dev:feature", self.command)
        self.assertIn('python3 .claude/alfred-continuity.py progress "$PWD"', self.command)
        self.assertIn("NO uses `AskUserQuestion` como paso obligatorio", self.command)


class TestStatusCommandContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = _read("commands/progress.md")

    def test_status_mentions_sonia_sources(self):
        self.assertIn("docs/project/discovery.md", self.command)
        self.assertIn("docs/project/progress.md", self.command)
        self.assertIn("docs/project/traceability.md", self.command)
        self.assertIn("docs/project/kanban/in-progress.md", self.command)
        self.assertIn("docs/project/kanban/blocked.md", self.command)
        self.assertIn('python3 .claude/alfred-continuity.py progress "$PWD"', self.command)
        self.assertIn("docs/project/kanban", self.command)


if __name__ == "__main__":
    unittest.main()
