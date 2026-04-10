#!/usr/bin/env python3
"""Tests para el hook memory-compact.py."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _PROJECT_ROOT)

from core.memory import MemoryDB

_hook_path = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "memory-compact.py"
)
_spec = importlib.util.spec_from_file_location("memory_compact", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_is_memory_enabled = _mod._is_memory_enabled
build_compact_context = _mod.build_compact_context


class TestBuildCompactContext(unittest.TestCase):
    """Verifica la construccion de contexto protegido para compactacion."""

    def test_empty_decisions_returns_empty(self):
        """Sin decisiones, debe devolver cadena vacia."""
        result = build_compact_context([])
        self.assertEqual(result, "")

    def test_includes_decision_title_and_chosen(self):
        """El contexto debe incluir titulo y opcion elegida."""
        decisions = [
            {"id": 1, "title": "Usar SQLite", "chosen": "SQLite",
             "decided_at": "2026-02-21T00:00:00"},
        ]
        result = build_compact_context(decisions)
        self.assertIn("Usar SQLite", result)
        self.assertIn("SQLite", result)
        self.assertIn("2026-02-21", result)


class TestMemoryCompactConfig(unittest.TestCase):
    """Comprueba que el hook consulta la config canónica de memoria."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._claude_dir = os.path.join(self._tmpdir, ".claude")
        os.makedirs(self._claude_dir, exist_ok=True)
        self._config_path = os.path.join(
            self._claude_dir,
            "alfred-dev.local.md",
        )

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_ignores_body_mentions_outside_frontmatter(self):
        with open(self._config_path, "w", encoding="utf-8") as fh:
            fh.write("# Notas\n\nmemoria:\n  enabled: true\n")

        self.assertFalse(_is_memory_enabled(self._tmpdir))

    def test_respects_valid_frontmatter_enable_flag(self):
        with open(self._config_path, "w", encoding="utf-8") as fh:
            fh.write("---\nmemoria:\n  enabled: true\n---\n")

        self.assertTrue(_is_memory_enabled(self._tmpdir))


class TestMemoryCompactRuntime(unittest.TestCase):
    def test_prefers_recent_project_decisions_when_active_iteration_has_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("---\nmemoria:\n  enabled: true\n---\n")

            db = MemoryDB(os.path.join(claude_dir, "alfred-memory.db"))
            feature_id = db.start_iteration("feature", "Decisión histórica")
            db.log_decision(
                title="Persistir con SQLite",
                chosen="SQLite local",
                iteration_id=feature_id,
            )
            db.complete_iteration(feature_id)
            db.start_iteration("session", "Sesión vacía")
            db.close()

            result = subprocess.run(
                [sys.executable, _hook_path],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Persistir con SQLite", context)
            self.assertIn("SQLite local", context)


if __name__ == "__main__":
    unittest.main()
