#!/usr/bin/env python3
"""Tests para el cargador de configuracion del plugin."""

import json
import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config_loader import load_config, detect_stack, DEFAULT_CONFIG


class TestLoadConfig(unittest.TestCase):
    def test_returns_defaults_when_no_file(self):
        config = load_config("/ruta/que/no/existe")
        self.assertEqual(config["autonomia"]["producto"], "interactivo")
        self.assertEqual(config["autonomia"]["seguridad"], "autonomo")
        self.assertEqual(config["personalidad"]["nivel_sarcasmo"], 3)

    def test_loads_yaml_frontmatter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nautonomia:\n  producto: autonomo\n---\n# Notas\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["autonomia"]["producto"], "autonomo")
        self.assertEqual(config["autonomia"]["seguridad"], "autonomo")

    def test_extracts_notes_section(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nautonomia:\n  producto: interactivo\n---\n## Notas\nPreferir Hono sobre Express.\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertIn("Preferir Hono", config["notas"])


class TestDetectStack(unittest.TestCase):
    def test_detects_node_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {"name": "test", "dependencies": {"next": "^14.0.0"}}
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(pkg, f)
            with open(os.path.join(tmpdir, "tsconfig.json"), "w") as f:
                json.dump({}, f)
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["runtime"], "node")
        self.assertEqual(stack["lenguaje"], "typescript")

    def test_detects_python_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
                f.write("[project]\nname = 'test'\n")
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["lenguaje"], "python")

    def test_returns_unknown_for_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["lenguaje"], "desconocido")


if __name__ == "__main__":
    unittest.main()
