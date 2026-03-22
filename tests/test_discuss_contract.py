#!/usr/bin/env python3
"""Contratos del comando de refinado previo a feature."""

import os
import unittest


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestDiscussCommandContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = _read("commands/discuss.md")
        cls.feature = _read("commands/feature.md")
        cls.plugin = _read(".claude-plugin/plugin.json")

    def test_discuss_is_registered_and_visible(self):
        self.assertIn("./commands/discuss.md", self.plugin)
        self.assertIn("/alfred-dev:discuss", self.command)
        self.assertIn("docs/project/discovery.md", self.command)
        self.assertIn("docs/project/current.md", self.command)
        self.assertIn('python3 .claude/alfred-continuity.py discuss "$PWD" --raw "$ARGUMENTS"', self.command)
        self.assertIn("NO uses `Read`, `Glob`, `Grep`", self.command)
        self.assertIn("NO lo reintentes", self.command)

    def test_discuss_uses_product_owner_and_recommends_next_flow(self):
        self.assertIn("product-owner", self.command)
        self.assertIn("pregunta corta", self.command)
        self.assertIn("tú mismo por defecto", self.command)
        self.assertIn("NO lances subagentes por inercia", self.command)
        self.assertIn("`Bash` fue denegado", self.command)
        self.assertIn("YA ha persistido", self.command)
        self.assertIn("NO vuelvas a usar `Write` ni `Edit`", self.command)
        self.assertIn("Solo en modo manual", self.command)
        self.assertIn("/alfred-dev:feature", self.command)
        self.assertIn("/alfred-dev:quick", self.command)
        self.assertIn("/alfred-dev:fix", self.command)
        self.assertIn("/alfred-dev:spike", self.command)

    def test_feature_reuses_discovery_artifact(self):
        self.assertIn("docs/project/discovery.md", self.feature)
        self.assertIn("PRD", self.feature)
        self.assertIn("refinado previo", self.feature)
        self.assertIn("/alfred-dev:quick", self.feature)
        self.assertIn("/alfred-dev:spike", self.feature)


if __name__ == "__main__":
    unittest.main()
