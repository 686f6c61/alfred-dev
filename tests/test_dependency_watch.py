#!/usr/bin/env python3
"""Tests para el hook dependency-watch.py."""

import importlib.util
import json
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Importar el hook usando importlib (el nombre tiene guion)
_hook_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "dependency-watch.py")
_spec = importlib.util.spec_from_file_location("dependency_watch", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

is_dependency_file = _mod.is_dependency_file
has_dependency_signal = _mod.has_dependency_signal


class TestIsDependencyFile(unittest.TestCase):
    """Verifica que los ficheros de dependencias se detectan correctamente."""

    # --- Casos positivos: ficheros de dependencias ---

    def test_package_json(self):
        self.assertTrue(is_dependency_file("/proyecto/package.json"))

    def test_package_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/package-lock.json"))

    def test_yarn_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/yarn.lock"))

    def test_pnpm_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/pnpm-lock.yaml"))

    def test_pyproject_toml(self):
        self.assertTrue(is_dependency_file("/proyecto/pyproject.toml"))

    def test_requirements_txt(self):
        self.assertTrue(is_dependency_file("/proyecto/requirements.txt"))

    def test_requirements_dev(self):
        self.assertTrue(is_dependency_file("/proyecto/requirements-dev.txt"))

    def test_requirements_ci(self):
        self.assertTrue(is_dependency_file("/proyecto/requirements-ci.txt"))

    def test_requirements_in(self):
        self.assertTrue(is_dependency_file("/proyecto/requirements.in"))

    def test_constraints_txt(self):
        self.assertTrue(is_dependency_file("/proyecto/constraints.txt"))

    def test_cargo_toml(self):
        self.assertTrue(is_dependency_file("/proyecto/Cargo.toml"))

    def test_cargo_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/Cargo.lock"))

    def test_go_mod(self):
        self.assertTrue(is_dependency_file("/proyecto/go.mod"))

    def test_go_sum(self):
        self.assertTrue(is_dependency_file("/proyecto/go.sum"))

    def test_gemfile(self):
        self.assertTrue(is_dependency_file("/proyecto/Gemfile"))

    def test_gemfile_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/Gemfile.lock"))

    def test_pom_xml(self):
        self.assertTrue(is_dependency_file("/proyecto/pom.xml"))

    def test_build_gradle(self):
        self.assertTrue(is_dependency_file("/proyecto/build.gradle"))

    def test_csproj(self):
        self.assertTrue(is_dependency_file("/proyecto/MiApp.csproj"))

    def test_fsproj(self):
        self.assertTrue(is_dependency_file("/proyecto/MiApp.fsproj"))

    def test_vbproj(self):
        self.assertTrue(is_dependency_file("/proyecto/MiApp.vbproj"))

    def test_composer_json(self):
        self.assertTrue(is_dependency_file("/proyecto/composer.json"))

    def test_mix_exs(self):
        self.assertTrue(is_dependency_file("/proyecto/mix.exs"))

    def test_pipfile(self):
        self.assertTrue(is_dependency_file("/proyecto/Pipfile"))

    def test_poetry_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/poetry.lock"))

    def test_uv_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/uv.lock"))

    def test_pnpm_workspace(self):
        self.assertTrue(is_dependency_file("/proyecto/pnpm-workspace.yaml"))

    def test_directory_packages_props(self):
        self.assertTrue(is_dependency_file("/proyecto/Directory.Packages.props"))

    def test_packages_lock_json(self):
        self.assertTrue(is_dependency_file("/proyecto/packages.lock.json"))

    # --- Casos negativos: ficheros normales ---

    def test_readme(self):
        self.assertFalse(is_dependency_file("/proyecto/README.md"))

    def test_source_file(self):
        self.assertFalse(is_dependency_file("/proyecto/src/main.py"))

    def test_config_file(self):
        self.assertFalse(is_dependency_file("/proyecto/.eslintrc.json"))

    def test_tsconfig(self):
        self.assertFalse(is_dependency_file("/proyecto/tsconfig.json"))

    def test_gitignore(self):
        self.assertFalse(is_dependency_file("/proyecto/.gitignore"))


class TestDependencySignal(unittest.TestCase):
    """Verifica que los manifests mixtos no avisen por ruido lateral."""

    def test_package_json_scripts_edit_does_not_count_as_dependency_change(self):
        self.assertFalse(has_dependency_signal(
            "/proyecto/package.json",
            {"old_string": '"scripts": {"test": "vitest"}', "new_string": '"scripts": {"test": "vitest run"}'},
        ))

    def test_package_json_dependencies_edit_counts(self):
        self.assertTrue(has_dependency_signal(
            "/proyecto/package.json",
            {"old_string": '"dependencies": {"react": "^18.2.0"}', "new_string": '"dependencies": {"react": "^19.0.0"}'},
        ))

    def test_pyproject_version_edit_does_not_count(self):
        self.assertFalse(has_dependency_signal(
            "/proyecto/pyproject.toml",
            {"old_string": 'version = "0.1.0"', "new_string": 'version = "0.2.0"'},
        ))

    def test_constraints_file_always_counts(self):
        self.assertTrue(has_dependency_signal(
            "/proyecto/constraints.txt",
            {"old_string": "django==5.0.0", "new_string": "django==5.1.0"},
        ))


class TestDependencyWatchMain(unittest.TestCase):
    """Verifica el flujo principal del hook."""

    def _run_main(self, payload: dict) -> tuple[int, str]:
        stderr_capture = StringIO()
        exit_code = None

        with patch("sys.stdin", StringIO(json.dumps(payload))):
            with patch("sys.stderr", stderr_capture):
                try:
                    _mod.main()
                except SystemExit as exc:
                    exit_code = exc.code

        return exit_code, stderr_capture.getvalue()

    def test_dependency_edit_emits_warning(self):
        code, stderr = self._run_main({
            "tool_input": {
                "file_path": "/proyecto/package.json",
                "old_string": '"dependencies": {"react": "^18"}',
                "new_string": '"dependencies": {"react": "^19"}',
            }
        })

        self.assertEqual(code, 0)
        self.assertIn("Cambio en dependencias detectado", stderr)

    def test_scripts_only_edit_is_silent(self):
        code, stderr = self._run_main({
            "tool_input": {
                "file_path": "/proyecto/package.json",
                "old_string": '"scripts": {"test": "vitest"}',
                "new_string": '"scripts": {"test": "vitest run"}',
            }
        })

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
