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
        self.assertGreaterEqual(len(proposal["reference_urls"]), 1)
        self.assertEqual(proposal["typography"]["source"], "google-fonts")
        self.assertIn("https://fonts.google.com/specimen/", proposal["typography"]["headings_url"])
        self.assertIn("https://fonts.googleapis.com/css2?", proposal["typography"]["css_url"])

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


if __name__ == "__main__":
    unittest.main()

