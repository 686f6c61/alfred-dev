#!/usr/bin/env python3
"""Tests de consistencia de version.

Verifica que todos los ficheros que declaran la version del plugin
coincidan entre si y tengan formato semver valido. La fuente de verdad
es .claude-plugin/plugin.json; el resto de ficheros deben reflejar
el mismo valor.

Ficheros cubiertos:
  - .claude-plugin/plugin.json   (JSON, campo "version")
  - .claude-plugin/marketplace.json (JSON, plugins[0].version)
  - package.json                 (JSON, campo "version")
  - install.sh                   (bash, variable VERSION="...")
  - install.ps1                  (PowerShell, variable $Version = "...")
"""

import json
import os
import re
import unittest

# Raiz del proyecto (un nivel por encima de tests/)
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")

# Patron semver simplificado: MAJOR.MINOR.PATCH con pre-release opcional
_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*))?$"
)


def _read_file(relative_path: str) -> str:
    """Lee un fichero del proyecto y devuelve su contenido."""
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _get_plugin_json_version() -> str:
    """Extrae la version de .claude-plugin/plugin.json (fuente de verdad)."""
    data = json.loads(_read_file(".claude-plugin/plugin.json"))
    return data["version"]


def _get_marketplace_json_version() -> str:
    """Extrae la version del primer plugin en marketplace.json."""
    data = json.loads(_read_file(".claude-plugin/marketplace.json"))
    return data["plugins"][0]["version"]


def _get_package_json_version() -> str:
    """Extrae la version de package.json."""
    data = json.loads(_read_file("package.json"))
    return data["version"]


def _get_install_sh_version() -> str:
    """Extrae la variable VERSION de install.sh."""
    content = _read_file("install.sh")
    match = re.search(r'^VERSION="([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("No se encontro VERSION=\"...\" en install.sh")
    return match.group(1)


def _get_install_ps1_version() -> str:
    """Extrae la variable $Version de install.ps1."""
    content = _read_file("install.ps1")
    match = re.search(r'^\$Version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError('No se encontro $Version = "..." en install.ps1')
    return match.group(1)


class TestVersionConsistency(unittest.TestCase):
    """Verifica que la version es consistente en todos los ficheros."""

    @classmethod
    def setUpClass(cls):
        """Carga la version canonica una sola vez."""
        cls.canonical = _get_plugin_json_version()

    def test_canonical_version_is_semver(self):
        """La version canonica debe tener formato semver valido."""
        self.assertIsNotNone(
            _SEMVER_RE.match(self.canonical),
            f"La version '{self.canonical}' en plugin.json no es semver valida",
        )

    def test_marketplace_json_matches(self):
        """marketplace.json debe coincidir con plugin.json."""
        self.assertEqual(
            _get_marketplace_json_version(),
            self.canonical,
            "La version en marketplace.json no coincide con plugin.json",
        )

    def test_package_json_matches(self):
        """package.json debe coincidir con plugin.json."""
        self.assertEqual(
            _get_package_json_version(),
            self.canonical,
            "La version en package.json no coincide con plugin.json",
        )

    def test_install_sh_matches(self):
        """install.sh debe coincidir con plugin.json."""
        self.assertEqual(
            _get_install_sh_version(),
            self.canonical,
            "La version en install.sh no coincide con plugin.json",
        )

    def test_install_ps1_matches(self):
        """install.ps1 debe coincidir con plugin.json."""
        self.assertEqual(
            _get_install_ps1_version(),
            self.canonical,
            "La version en install.ps1 no coincide con plugin.json",
        )


if __name__ == "__main__":
    unittest.main()
