#!/usr/bin/env python3
"""Tests para el catalogo visual canónico de Selina."""

import unittest

from core.selina_style_catalog import (
    DEFAULT_STYLE_ID,
    build_style_catalog_proposal,
    get_palette_modes,
    get_style_catalog,
    resolve_font_pairing,
)


class TestSelinaStyleCatalog(unittest.TestCase):
    def test_catalog_exposes_nine_trends_plus_free_mode(self):
        catalog = get_style_catalog()
        self.assertEqual(len(catalog), 10)

        ids = {entry["id"] for entry in catalog}
        self.assertIn(DEFAULT_STYLE_ID, ids)
        self.assertIn("neo-brutalism", ids)
        self.assertIn("glassmorphism-2", ids)
        self.assertIn("ai-hyperminimalism", ids)

    def test_palette_mode_catalog_includes_requested_modes(self):
        mode_ids = {entry["id"] for entry in get_palette_modes()}
        self.assertIn("recommended", mode_ids)
        self.assertIn("pastel", mode_ids)
        self.assertIn("solid", mode_ids)
        self.assertIn("monochrome", mode_ids)

    def test_build_style_catalog_proposal_carries_references_palette_and_font_urls(self):
        proposal = build_style_catalog_proposal(
            "neo-brutalism",
            choice="A",
            palette_mode="pastel",
        )

        self.assertEqual(proposal["style_family"], "neo-brutalism")
        self.assertEqual(proposal["palette_mode"], "pastel")
        self.assertEqual(proposal["palette_mode_label"], "Pastel")
        self.assertGreaterEqual(len(proposal["reference_urls"]), 1)
        self.assertEqual(proposal["typography"]["pairing_id"], "brutal-core")
        self.assertEqual(proposal["typography"]["pairing_label"], "Brutal Core")
        self.assertEqual(proposal["typography"]["source"], "google-fonts")
        self.assertIn("https://fonts.google.com/specimen/", proposal["typography"]["headings_url"])
        self.assertIn("https://fonts.googleapis.com/css2?", proposal["typography"]["css_url"])
        self.assertGreaterEqual(len(proposal["visual_principles"]), 2)
        self.assertIn("bordes negros", proposal["prompt_seed"].lower())
        self.assertIn("cajas desplazadas", proposal["layout_grammar"].lower())
        self.assertIn("CTA con sombra brutal", proposal["signature_elements"])
        self.assertGreaterEqual(len(proposal["implementation_guardrails"]), 1)

    def test_custom_google_fonts_url_overrides_default_pairing(self):
        pairing = resolve_font_pairing(
            "free-default",
            custom_google_fonts_url="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&display=swap",
            custom_headings="IBM Plex Mono",
            custom_body="IBM Plex Mono",
        )
        self.assertEqual(pairing["source"], "custom-google-fonts")
        self.assertEqual(pairing["headings"], "IBM Plex Mono")
        self.assertIn("fonts.googleapis.com", pairing["css_url"])

    def test_catalog_entries_expose_structured_style_cues_for_each_family(self):
        for entry in get_style_catalog():
            self.assertIn("visual_principles", entry)
            self.assertGreaterEqual(len(entry["visual_principles"]), 2)
            self.assertTrue(entry["layout_grammar"])
            self.assertTrue(entry["surface_treatment"])
            self.assertTrue(entry["shape_language"])
            self.assertTrue(entry["motion_language"])
            self.assertGreaterEqual(len(entry["signature_elements"]), 1)
            self.assertGreaterEqual(len(entry["implementation_guardrails"]), 1)
            self.assertTrue(entry["prompt_seed"])


if __name__ == "__main__":
    unittest.main()
