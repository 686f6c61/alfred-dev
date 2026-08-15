#!/usr/bin/env python3
"""Higiene pre-dolor y cierre enseñable."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.hygiene import build_cierre, render_cierre_markdown, run_hygiene
from core.project_docs import FILLED_MARKER, SCAFFOLD_MARKER, ensure_project_docs


class TestHygiene(unittest.TestCase):
    def test_ship_blocks_pending_uat(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude = os.path.join(tmpdir, ".claude")
            os.makedirs(claude, exist_ok=True)
            with open(os.path.join(claude, "alfred-uat.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "status": "pending",
                        "target_id": "quick-1",
                        "updated_at": "2026-08-15T10:00:00+00:00",
                    },
                    handle,
                )
            # suggest_verify_action needs a completed session
            with open(os.path.join(claude, "alfred-dev-state.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "comando": "quick",
                        "descripcion": "CTA",
                        "fase_actual": "completado",
                        "fase_numero": 1,
                    },
                    handle,
                )
            result = run_hygiene(tmpdir, "ship")
            self.assertFalse(result["passed"])
            self.assertTrue(any("UAT" in item for item in result["blockers"]))

    def test_filled_architecture_with_scaffold_threat_model_blocks_ship(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_project_docs(tmpdir)
            architecture = os.path.join(tmpdir, "docs/project/architecture.md")
            with open(architecture, "w", encoding="utf-8") as handle:
                handle.write(f"# Arquitectura\n\n{FILLED_MARKER}\n\nCajas reales.\n")
            result = run_hygiene(tmpdir, "ship")
            self.assertFalse(result["passed"])
            self.assertTrue(any("threat-model" in item for item in result["blockers"]))

    def test_cierre_is_shareable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude = os.path.join(tmpdir, ".claude")
            os.makedirs(claude, exist_ok=True)
            with open(os.path.join(claude, "alfred-dev-state.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "comando": "quick",
                        "descripcion": "cambia el CTA",
                        "fase_actual": "validacion_rapida",
                        "fase_numero": 1,
                    },
                    handle,
                )
            with open(os.path.join(claude, "alfred-evidence.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "command": "pytest tests/test_cta.py",
                        "result": "pass",
                    },
                    handle,
                )
            cierre = build_cierre(tmpdir)
            text = render_cierre_markdown(cierre)
            self.assertIn("cambia el CTA", text)
            self.assertIn("pytest tests/test_cta.py", text)
            self.assertIn("Cierre Alfred", text)


if __name__ == "__main__":
    unittest.main()
