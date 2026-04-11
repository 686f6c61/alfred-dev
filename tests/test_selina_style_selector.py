#!/usr/bin/env python3
"""Tests para las pantallas guiadas del selector de Selina."""

import os
import shutil
import tempfile
import unittest

from core.selina_style_selector import (
    encode_style_brief_choice,
    encode_style_choice,
    parse_guided_choice,
    write_style_selector_html,
)


class TestSelinaStyleSelector(unittest.TestCase):
    def setUp(self):
        self.session_dir = tempfile.mkdtemp(prefix="alfred-selina-selector-")
        self.state_dir = os.path.join(self.session_dir, "state")
        self.content_dir = os.path.join(self.session_dir, "content")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.session_dir, ignore_errors=True)

    def test_parse_guided_choice_decodes_style_family(self):
        payload = parse_guided_choice(encode_style_choice("neo-brutalism"))
        self.assertEqual(
            payload,
            {
                "stage": "style-family",
                "style_id": "neo-brutalism",
            },
        )

    def test_parse_guided_choice_decodes_style_brief(self):
        payload = parse_guided_choice(
            encode_style_brief_choice("neo-brutalism", "brutal-readable", "solid")
        )
        self.assertEqual(
            payload,
            {
                "stage": "style-brief",
                "style_id": "neo-brutalism",
                "font_pairing_id": "brutal-readable",
                "palette_mode": "solid",
            },
        )

    def test_write_style_selector_html_writes_family_stage(self):
        result = write_style_selector_html(self.state_dir)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stage"], "style-family")
        self.assertTrue(os.path.isfile(result["html_path"]))

        with open(result["html_path"], "r", encoding="utf-8") as fh:
            html = fh.read()

        self.assertIn("Elige el sistema de diseño base", html)
        self.assertIn("Anti-diseno / Neo-brutalismo", html)
        self.assertIn("style::neo-brutalism", html)
        self.assertIn("Brutal Core", html)

    def test_write_style_selector_html_writes_brief_stage(self):
        result = write_style_selector_html(self.state_dir, style_id="neo-brutalism")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stage"], "style-brief")
        self.assertTrue(os.path.isfile(result["html_path"]))

        with open(result["html_path"], "r", encoding="utf-8") as fh:
            html = fh.read()

        self.assertIn("Elige tipografía y paleta para Anti-diseno / Neo-brutalismo", html)
        self.assertIn("brief::neo-brutalism::brutal-core::recommended", html)
        self.assertIn("Brutal legible", html)
        self.assertIn("Solidos", html)


if __name__ == "__main__":
    unittest.main()
