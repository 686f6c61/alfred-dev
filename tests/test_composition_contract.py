#!/usr/bin/env python3
"""Contrato del protocolo de composicion dinamica."""

import os
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestCompositionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = _read("commands/_composicion.md")

    def test_missing_autonomy_bootstraps_cli_defaults(self):
        self.assertIn("NO uses `AskUserQuestion` en este bootstrap inicial", self.command)
        self.assertIn("producto: autonomo", self.command)
        self.assertIn("arquitectura: autonomo", self.command)
        self.assertIn("desarrollo: autonomo", self.command)
        self.assertIn("calidad: autonomo", self.command)
        self.assertIn("documentacion: autonomo", self.command)
        self.assertIn("entrega: autonomo", self.command)

    def test_bootstrap_points_to_current_config_command(self):
        self.assertIn("/alfred-dev:ajustes", self.command)
        self.assertIn("/alfred-dev:quick", self.command)
        self.assertNotIn("/alfred config", self.command)


if __name__ == "__main__":
    unittest.main()
