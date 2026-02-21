#!/usr/bin/env python3
"""Tests para el hook memory-compact.py."""

import importlib.util
import os
import unittest

_hook_path = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "memory-compact.py"
)
_spec = importlib.util.spec_from_file_location("memory_compact", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

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


if __name__ == "__main__":
    unittest.main()
