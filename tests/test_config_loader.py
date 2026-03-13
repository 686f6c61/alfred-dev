#!/usr/bin/env python3
"""Tests para el cargador de configuración del plugin."""

import json
import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config_loader import (
    load_config,
    detect_stack,
    suggest_optional_agents,
    DEFAULT_CONFIG,
)


class TestLoadConfig(unittest.TestCase):
    def test_returns_defaults_when_no_file(self):
        config = load_config("/ruta/que/no/existe")
        self.assertEqual(config["autonomia"]["producto"], "interactivo")
        self.assertEqual(config["autonomia"]["seguridad"], "autónomo")
        self.assertEqual(config["personalidad"]["nivel_sarcasmo"], 3)

    def test_loads_yaml_frontmatter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nautonomia:\n  producto: autónomo\n---\n# Notas\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["autonomia"]["producto"], "autónomo")
        self.assertEqual(config["autonomia"]["seguridad"], "autónomo")

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


class TestOptionalAgents(unittest.TestCase):
    """Tests para la configuración y descubrimiento de agentes opcionales."""

    def test_default_config_has_optional_agents(self):
        """La configuración por defecto incluye la sección de agentes opcionales."""
        self.assertIn("agentes_opcionales", DEFAULT_CONFIG)
        agents = DEFAULT_CONFIG["agentes_opcionales"]
        expected = {
            "data-engineer", "performance-engineer", "github-manager",
            "librarian", "ux-reviewer", "seo-specialist", "copywriter",
            "i18n-specialist",
        }
        self.assertEqual(set(agents.keys()), expected)

    def test_all_optional_agents_disabled_by_default(self):
        """Todos los agentes opcionales están desactivados por defecto."""
        for name, active in DEFAULT_CONFIG["agentes_opcionales"].items():
            self.assertFalse(active, f"'{name}' debería estar desactivado por defecto")

    def test_config_loads_optional_agents(self):
        """La configuración del fichero .local.md se fusiona con los defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nagentes_opcionales:\n  data-engineer: true\n  github-manager: true\n---\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertTrue(config["agentes_opcionales"]["data-engineer"])
        self.assertTrue(config["agentes_opcionales"]["github-manager"])
        # Los no especificados mantienen el default (false)
        self.assertFalse(config["agentes_opcionales"]["ux-reviewer"])

    def test_suggest_for_node_project_with_orm(self):
        """Un proyecto Node con ORM sugiere data-engineer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {
                "name": "test",
                "dependencies": {"next": "^14.0.0", "@prisma/client": "^5.0.0"},
            }
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(pkg, f)
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("data-engineer", agent_names)
        self.assertIn("ux-reviewer", agent_names)

    def test_suggest_for_project_with_html(self):
        """Un proyecto con contenido web público sugiere seo-specialist y copywriter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "index.html"), "w") as f:
                f.write("<html></html>")
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("seo-specialist", agent_names)
        self.assertIn("copywriter", agent_names)

    def test_suggest_skips_already_active(self):
        """No sugiere agentes que ya están activos en la configuración."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "index.html"), "w") as f:
                f.write("<html></html>")
            config = load_config("/ruta/que/no/existe")
            config["agentes_opcionales"]["seo-specialist"] = True
            suggestions = suggest_optional_agents(tmpdir, config)
        agent_names = [s[0] for s in suggestions]
        self.assertNotIn("seo-specialist", agent_names)
        self.assertIn("copywriter", agent_names)

    def test_suggest_empty_for_minimal_project(self):
        """Un proyecto vacío no sugiere ningún agente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            suggestions = suggest_optional_agents(tmpdir)
        self.assertEqual(suggestions, [])

    def test_suggest_github_manager_with_remote(self):
        """Un proyecto con remote Git sugiere github-manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as f:
                f.write('[remote "origin"]\n\turl = git@github.com:user/repo.git\n')
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("github-manager", agent_names)



if __name__ == "__main__":
    unittest.main()
