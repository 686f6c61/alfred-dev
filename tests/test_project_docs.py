#!/usr/bin/env python3
"""Contrato de documentación viva del proyecto."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.project_docs import (
    FILLED_MARKER,
    SCAFFOLD_MARKER,
    check_project_docs,
    doc_status,
    ensure_project_docs,
    next_adr_number,
    required_docs,
    scaffold_adr,
)


class TestProjectDocs(unittest.TestCase):
    def test_scaffold_creates_living_docs_and_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_project_docs(tmpdir)
            self.assertIn("docs/project/architecture.md", result["created"])
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "docs/project/README.md")))
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, "docs/adr")))
            architecture = open(
                os.path.join(tmpdir, "docs/project/architecture.md"),
                encoding="utf-8",
            ).read()
            self.assertIn(SCAFFOLD_MARKER, architecture)
            self.assertEqual(doc_status(architecture), "scaffold")

    def test_architecture_gate_requires_filled_docs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_project_docs(tmpdir)
            failed = check_project_docs(tmpdir, "feature", "arquitectura")
            self.assertFalse(failed["passed"])
            self.assertIn("docs/project/architecture.md", failed["empty"])

            path = os.path.join(tmpdir, "docs/project/architecture.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(f"# Arquitectura\n\n{FILLED_MARKER}\n\nDiagrama real.\n")
            threat = os.path.join(tmpdir, "docs/project/threat-model.md")
            with open(threat, "w", encoding="utf-8") as handle:
                handle.write(f"# Modelo\n\n{FILLED_MARKER}\n\nSTRIDE del login.\n")

            passed = check_project_docs(tmpdir, "feature", "arquitectura")
            self.assertTrue(passed["passed"], passed)

    def test_map_codebase_accepts_architecture_skeleton(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_project_docs(tmpdir)
            result = check_project_docs(tmpdir, "map-codebase")
            self.assertTrue(result["passed"], result)

    def test_next_adr_increments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            first = scaffold_adr(tmpdir, "Elegir SQLite")
            self.assertTrue(first["created"])
            self.assertEqual(first["number"], 1)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, first["path"])))
            self.assertEqual(next_adr_number(tmpdir), 2)
            second = scaffold_adr(tmpdir, "Auth por sesión")
            self.assertEqual(second["number"], 2)

    def test_existing_user_docs_count_as_filled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "docs/project"), exist_ok=True)
            with open(
                os.path.join(tmpdir, "docs/project/compliance.md"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("# Compliance\n\nRGPD no aplica: CLI sin datos personales.\n")
            ensure_project_docs(tmpdir)
            result = check_project_docs(tmpdir, "feature", "calidad")
            self.assertTrue(result["passed"], result)

    def test_required_docs_known_for_core_flows(self):
        self.assertTrue(required_docs("feature", "calidad"))
        self.assertTrue(required_docs("audit"))
        self.assertFalse(required_docs("progress"))


if __name__ == "__main__":
    unittest.main()
