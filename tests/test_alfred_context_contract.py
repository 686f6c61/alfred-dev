#!/usr/bin/env python3
"""Contrato del asistente contextual de Alfred Dev."""

import os
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestAlfredContextContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = _read("commands/alfred.md")

    def test_reads_continuity_artifacts_before_routing(self):
        self.assertIn('python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected alfred', self.command)
        self.assertIn(".claude/alfred-dev-state.json", self.command)
        self.assertIn(".claude/alfred-handoff.json", self.command)
        self.assertIn(".claude/alfred-uat.json", self.command)
        self.assertIn("docs/project/discovery.md", self.command)
        self.assertIn("docs/project/current.md", self.command)
        self.assertIn("docs/project/codebase-map.md", self.command)
        self.assertIn("docs/project/uat.md", self.command)
        self.assertIn('python3 .claude/alfred-continuity.py next "$PWD" --json', self.command)

    def test_routes_to_operational_commands_first(self):
        self.assertIn("actúa como `/alfred-dev:status`", self.command)
        self.assertIn("actúa como `/alfred-dev:next`", self.command)
        self.assertIn("actúa como `/alfred-dev:pause`", self.command)
        self.assertIn("actúa como `/alfred-dev:progress`", self.command)
        self.assertIn("actúa como `/alfred-dev:verify`", self.command)
        self.assertIn("actúa como `/alfred-dev:update`", self.command)
        self.assertIn("actúa como `/alfred-dev:lucius`", self.command)
        self.assertIn("actúa como `/alfred-dev:discuss`", self.command)
        self.assertIn("actúa como `/alfred-dev:quick`", self.command)
        self.assertIn("actúa como `/alfred-dev:map-codebase`", self.command)
        self.assertIn("prioriza también", self.command)
        self.assertIn("no arranque un equipo multiagente “a ciegas”", self.command)

    def test_routes_new_work_to_core_flows(self):
        self.assertIn("/alfred-dev:feature", self.command)
        self.assertIn("/alfred-dev:discuss", self.command)
        self.assertIn("/alfred-dev:quick", self.command)
        self.assertIn("/alfred-dev:fix", self.command)
        self.assertIn("/alfred-dev:spike", self.command)
        self.assertIn("/alfred-dev:audit", self.command)
        self.assertIn("/alfred-dev:verify", self.command)
        self.assertIn("/alfred-dev:ship", self.command)
        self.assertIn("/alfred-dev:lucius", self.command)
        self.assertIn("/alfred-dev:update", self.command)
        self.assertIn("NO lo dejes en una redirección muda", self.command)
        self.assertIn("NO reintentes `Bash`", self.command)

    def test_avoids_old_command_prefix_and_default_menu(self):
        self.assertIn("NO uses nombres viejos del plugin sin prefijo `-dev`", self.command)
        self.assertNotIn("`/alfred feature`", self.command)
        self.assertIn("NO ofrezcas un menú genérico si el siguiente paso es evidente", self.command)
        self.assertIn("AskUserQuestion", self.command)
        self.assertIn("menú seleccionable real", self.command)


if __name__ == "__main__":
    unittest.main()
