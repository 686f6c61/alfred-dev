#!/usr/bin/env python3
"""Tests para el parser ligero de configuracion de memoria."""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory_config import is_memory_enabled, load_memory_config


class TestMemoryConfig(unittest.TestCase):
    """Verifica defaults y parseo del bloque memoria."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._claude_dir = os.path.join(self._tmpdir, ".claude")
        os.makedirs(self._claude_dir, exist_ok=True)
        self._config_path = os.path.join(
            self._claude_dir, "alfred-dev.local.md"
        )

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_defaults_if_config_missing(self):
        """Sin fichero debe devolver defaults seguros."""
        config = load_memory_config(self._tmpdir)
        self.assertFalse(config["enabled"])
        self.assertTrue(config["sync_to_native"])
        self.assertEqual(config["sync_commits_limit"], 10)
        self.assertEqual(config["retention_days"], 365)

    def test_reads_memory_block_from_frontmatter(self):
        """Debe parsear bools e ints del bloque memoria."""
        with open(self._config_path, "w", encoding="utf-8") as handle:
            handle.write(
                "---\n"
                "equipo:\n"
                "  librarian: true\n"
                "memoria:\n"
                "  enabled: true\n"
                "  sync_to_native: false\n"
                "  sync_commits_limit: 25\n"
                "  capture_decisions: false\n"
                "  capture_commits: true\n"
                "  retention_days: 14\n"
                "---\n"
            )

        config = load_memory_config(self._tmpdir)
        self.assertTrue(config["enabled"])
        self.assertFalse(config["sync_to_native"])
        self.assertEqual(config["sync_commits_limit"], 25)
        self.assertFalse(config["capture_decisions"])
        self.assertTrue(config["capture_commits"])
        self.assertEqual(config["retention_days"], 14)
        self.assertTrue(is_memory_enabled(self._tmpdir))
