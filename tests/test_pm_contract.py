#!/usr/bin/env python3
"""Contratos para la capa PM 0.4.5 inspirada en CCPM."""

import json
import os
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestHelpListsPmCommands(unittest.TestCase):
    def test_help_includes_new_pm_commands(self):
        help_md = _read("commands/help.md")
        self.assertIn("/alfred-dev:standup", help_md)
        self.assertIn("/alfred-dev:blocked", help_md)
        self.assertIn("/alfred-dev:in-progress", help_md)
        self.assertIn("/alfred-dev:validate", help_md)
        self.assertIn("/alfred-dev:search", help_md)
        self.assertIn("/alfred-dev:sync-github", help_md)


class TestAlfredRoutingKnowsPmCommands(unittest.TestCase):
    def test_alfred_routes_standup_and_sync_explicitly(self):
        command = _read("commands/alfred.md")
        self.assertIn("resumen diario", command)
        self.assertIn("/alfred-dev:standup", command)
        self.assertIn("bloqueos", command)
        self.assertIn("/alfred-dev:blocked", command)
        self.assertIn("/alfred-dev:in-progress", command)
        self.assertIn("/alfred-dev:validate", command)
        self.assertIn("/alfred-dev:search", command)
        self.assertIn("/alfred-dev:sync-github", command)


class TestPmCommandWrappers(unittest.TestCase):
    def test_standup_uses_helper(self):
        command = _read("commands/standup.md")
        self.assertIn('allow-stop-once "$PWD" --command "/alfred-dev:standup"', command)
        self.assertIn('python3 .claude/alfred-continuity.py standup "$PWD"', command)
        self.assertIn("NO uses `AskUserQuestion`", command)

    def test_blocked_uses_helper(self):
        command = _read("commands/blocked.md")
        self.assertIn('allow-stop-once "$PWD" --command "/alfred-dev:blocked"', command)
        self.assertIn('python3 .claude/alfred-continuity.py blocked "$PWD"', command)
        self.assertIn("docs/project/kanban/blocked.md", command)

    def test_in_progress_uses_helper(self):
        command = _read("commands/in-progress.md")
        self.assertIn('allow-stop-once "$PWD" --command "/alfred-dev:in-progress"', command)
        self.assertIn('python3 .claude/alfred-continuity.py in-progress "$PWD"', command)
        self.assertIn("docs/project/kanban/in-progress.md", command)

    def test_validate_uses_helper(self):
        command = _read("commands/validate.md")
        self.assertIn('allow-stop-once "$PWD" --command "/alfred-dev:validate"', command)
        self.assertIn('python3 .claude/alfred-continuity.py validate "$PWD"', command)
        self.assertIn(".claude/alfred-github-sync.json", command)

    def test_search_uses_helper(self):
        command = _read("commands/search.md")
        self.assertIn('allow-stop-once "$PWD" --command "/alfred-dev:search"', command)
        self.assertIn('python3 .claude/alfred-continuity.py search "$PWD" --raw "$ARGUMENTS"', command)
        self.assertIn(".claude/alfred-memory.db", command)

    def test_sync_github_uses_helper(self):
        command = _read("commands/sync-github.md")
        self.assertIn('allow-stop-once "$PWD" --command "/alfred-dev:sync-github"', command)
        self.assertIn('python3 .claude/alfred-continuity.py sync-github "$PWD" --raw "$ARGUMENTS"', command)
        self.assertIn(".claude/alfred-github-sync.json", command)
        self.assertIn("docs/project/github-sync.md", command)
        self.assertIn("github-manager", command)


class TestPluginManifestIncludesPmCommands(unittest.TestCase):
    def test_plugin_json_references_new_commands(self):
        plugin = json.loads(_read(".claude-plugin/plugin.json"))
        commands = plugin["commands"]
        self.assertIn("./commands/standup.md", commands)
        self.assertIn("./commands/blocked.md", commands)
        self.assertIn("./commands/in-progress.md", commands)
        self.assertIn("./commands/validate.md", commands)
        self.assertIn("./commands/search.md", commands)
        self.assertIn("./commands/sync-github.md", commands)


if __name__ == "__main__":
    unittest.main()
