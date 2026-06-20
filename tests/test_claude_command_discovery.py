#!/usr/bin/env python3
"""Tests del smoke interactivo de descubrimiento de /alfred."""

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "claude_command_discovery.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("claude_command_discovery", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestClaudeCommandDiscovery(unittest.TestCase):
    def test_analysis_accepts_alfred_selector_output(self):
        discovery = _load_module()
        raw_output = (
            "\x1b[?25l/alfred\r\n"
            "/alfred        (Alfred Dev) Alias global /alfred para abrir el asistente contextual\r\n"
            "/alfred-dev:fix        (Alfred Dev) Correccion de bugs\r\n"
            "/alfred-dev:help       (Alfred Dev) Muestra los comandos disponibles\r\n"
        )

        analysis = discovery.analyze_discovery_output(raw_output)

        self.assertTrue(analysis.ok)
        self.assertTrue(analysis.alias_visible)
        self.assertEqual(analysis.alias_entry_count, 1)
        self.assertTrue(analysis.namespaced_visible)
        self.assertFalse(analysis.no_match_visible)

    def test_analysis_rejects_duplicate_alfred_alias_entries(self):
        discovery = _load_module()
        raw_output = (
            "/alfred\r\n"
            "/alfred        (Alfred Dev) Alias global /alfred para abrir el asistente contextual\r\n"
            "/alfred        Alias global /alfred para abrir el asistente contextual\r\n"
            "/alfred-dev:help       (Alfred Dev) Muestra los comandos disponibles\r\n"
        )

        analysis = discovery.analyze_discovery_output(raw_output)

        self.assertFalse(analysis.ok)
        self.assertEqual(analysis.alias_entry_count, 2)
        self.assertIn("mas de una entrada /alfred", " ".join(analysis.problems))

    def test_analysis_rejects_no_commands_match(self):
        discovery = _load_module()

        analysis = discovery.analyze_discovery_output('No commands match "/alfred"')

        self.assertFalse(analysis.ok)
        self.assertTrue(analysis.no_match_visible)
        self.assertIn('Claude muestra "No commands match"', analysis.problems[0])

    def test_strip_terminal_control_removes_ansi_without_losing_text(self):
        discovery = _load_module()

        cleaned = discovery.strip_terminal_control(
            "\x1b]0;Claude\x07\x1b[31m/alfred\x1b[0m Alias global"
        )

        self.assertEqual(cleaned, "/alfred Alias global")


if __name__ == "__main__":
    unittest.main()
