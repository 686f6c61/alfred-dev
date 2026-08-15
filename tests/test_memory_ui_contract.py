#!/usr/bin/env python3
"""Contratos textuales de /alfred-dev:memory-ui."""

import json
import os
import unittest


ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    with open(os.path.join(ROOT, relative_path), "r", encoding="utf-8") as fh:
        return fh.read()


class TestMemoryUIContract(unittest.TestCase):
    def test_help_lists_memory_ui(self):
        alfred_md = _read("commands/alfred.md")
        self.assertIn("/alfred-dev:memory-ui", alfred_md)

    def test_alfred_context_routes_memory_ui_requests(self):
        command = _read("commands/alfred.md")
        self.assertIn("/alfred-dev:memory-ui", command)
        self.assertIn("UI de memoria", command)

    def test_memory_ui_command_uses_helper_first_protocol(self):
        command = _read("commands/memory-ui.md")
        self.assertIn('consume-prefetch "$PWD" --expected memory-ui', command)
        self.assertNotIn("allow-stop-once", command)
        self.assertIn('python3 .claude/alfred-continuity.py memory-ui "$PWD" --raw "$ARGUMENTS"', command)
        self.assertIn("úsala tal cual como respuesta final", command)
        self.assertIn("NO añadas una segunda explicación", command)
        self.assertIn(".claude/alfred-memory.db", command)
        self.assertIn("/alfred-dev:memory-ui stop", command)
        self.assertIn("$ARGUMENTS", command)

    def test_alfred_does_not_delegate_memory_to_removed_librarian(self):
        alfred = _read("agents/alfred.md")
        self.assertIn("/alfred-dev:memory-ui", alfred)
        self.assertIn("alfred-memory", alfred)
        self.assertIn("ese agente ya no existe", alfred)
        self.assertNotIn("invocando al subagente `librarian`", alfred)

    def test_memory_skill_points_to_ui_and_mcp(self):
        skill = _read("skills/memory/SKILL.md")
        self.assertIn("/alfred-dev:memory-ui", skill)
        self.assertIn("memory_search", skill)
        self.assertIn("No existe el agente `librarian`", skill)

    def test_plugin_json_references_memory_ui_command(self):
        plugin = json.loads(_read(".claude-plugin/plugin.json"))
        self.assertIn("./commands/memory-ui.md", plugin["commands"])

    def test_readme_mentions_memory_ui(self):
        readme = _read("README.md")
        self.assertIn("/alfred-dev:memory-ui", readme)
        self.assertIn("memoria SQLite", readme)

    def test_memory_ui_server_declares_ui_version(self):
        server = _read("core/memory_ui_server.py")
        self.assertIn('UI_VERSION = "0.0.4"', server)
        self.assertIn("Alfred Dev Memory UI", server)
        self.assertIn("helper_seeded", server)
        self.assertIn("togglePanel", server)

    def test_memory_ui_server_localizes_dates_and_statuses(self):
        server = _read("core/memory_ui_server.py")
        self.assertIn('Intl.DateTimeFormat("es-ES"', server)
        self.assertIn('healthy: "saludable"', server)
        self.assertIn("function statusLabel(status", server)

    def test_memory_ui_prioritizes_active_iteration_in_selector(self):
        server = _read("core/memory_ui_server.py")
        self.assertIn("const preferred = items.find((item) => item.is_active) || items[0];", server)
        self.assertIn("selectedStillExists", server)
