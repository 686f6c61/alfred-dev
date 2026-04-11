#!/usr/bin/env python3
"""Tests para la generación guiada de variantes finales de Selina."""

import json
import os
import shutil
import tempfile
import unittest

from core.selina_style_variants import (
    build_guided_style_variants,
    write_guided_style_options,
)


class TestSelinaStyleVariants(unittest.TestCase):
    def setUp(self):
        self.session_dir = tempfile.mkdtemp(prefix="alfred-selina-variants-")
        self.state_dir = os.path.join(self.session_dir, "state")
        self.content_dir = os.path.join(self.session_dir, "content")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
        self.events_path = os.path.join(self.state_dir, "events")

    def tearDown(self):
        shutil.rmtree(self.session_dir, ignore_errors=True)

    def test_build_guided_style_variants_keeps_family_palette_and_pairing(self):
        proposals = build_guided_style_variants(
            style_id="neo-brutalism",
            font_pairing_id="brutal-readable",
            palette_mode="solid",
        )

        self.assertEqual([proposal["choice"] for proposal in proposals], ["A", "B", "C"])
        self.assertEqual(
            {proposal["style_family"] for proposal in proposals},
            {"neo-brutalism"},
        )
        self.assertEqual(
            {proposal["palette_mode"] for proposal in proposals},
            {"solid"},
        )
        self.assertEqual(
            {proposal["typography"]["pairing_label"] for proposal in proposals},
            {"Brutal legible"},
        )
        self.assertEqual(len({proposal["preview_flavor"] for proposal in proposals}), 3)
        self.assertEqual(
            [proposal["preview_title"] for proposal in proposals],
            ["Firma expresiva", "Producto operativo", "Producto limpio"],
        )
        self.assertTrue(all(proposal["prompt_seed"] for proposal in proposals))
        self.assertTrue(all(proposal["layout_grammar"] for proposal in proposals))
        self.assertTrue(all(proposal["signature_elements"] for proposal in proposals))
        self.assertTrue(
            all("neo-brutalismo real" in proposal["prompt_seed"].lower() for proposal in proposals)
        )

    def test_write_guided_style_options_uses_latest_brief_choice(self):
        with open(self.events_path, "w", encoding="utf-8") as fh:
            fh.write(
                '{"type":"click","choice":"brief::neo-brutalism::brutal-readable::solid","label":"Brutal legible · Solidos","ts":"2026-04-11T10:00:00Z"}\n'
            )

        result = write_guided_style_options(self.state_dir)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(os.path.isfile(result["proposals_file"]))
        self.assertTrue(os.path.isfile(result["html_path"]))
        self.assertEqual(result["choices"], ["A", "B", "C"])

        with open(result["proposals_file"], "r", encoding="utf-8") as fh:
            payload = json.load(fh)

        self.assertEqual(payload["guided_selection"]["style_id"], "neo-brutalism")
        self.assertEqual(payload["guided_selection"]["font_pairing_id"], "brutal-readable")
        self.assertEqual(payload["guided_selection"]["palette_mode"], "solid")
        self.assertEqual(len(payload["proposals"]), 3)
        self.assertEqual(payload["proposals"][0]["typography"]["pairing_label"], "Brutal legible")
        self.assertEqual(payload["proposals"][1]["preview_note"], "Producto operativo")

        with open(result["html_path"], "r", encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("Elige la versión final de Anti-diseno / Neo-brutalismo", html)
        self.assertIn("Brutal legible", html)
        self.assertIn("Variante:", html)
        self.assertIn("style-family--neo-brutalism", html)
        self.assertIn('data-style-family="neo-brutalism"', html)
        self.assertIn("preview-brutal", html)


if __name__ == "__main__":
    unittest.main()
