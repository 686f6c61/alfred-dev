#!/usr/bin/env python3
"""Tests para la generacion canónica de style-options.html."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from core.selina_style_options import (
    build_style_options_payload,
    render_style_options_html,
    write_style_options_html,
)


WRITE_STYLE_OPTIONS_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visual",
    "scripts",
    "write-style-options.py",
)


class TestSelinaStyleOptions(unittest.TestCase):
    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="alfred-selina-options-")
        self.session_dir = os.path.join(self.project_dir, ".alfred-dev", "visual", "session-1")
        self.state_dir = os.path.join(self.session_dir, "state")
        self.content_dir = os.path.join(self.session_dir, "content")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
        self.proposals_path = os.path.join(self.content_dir, "style-options.json")

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    def _write_proposals(self):
        proposals = {
            "proposals": [
                {
                    "choice": "A",
                    "name": "Oscuro espacial",
                    "concept": "Direccion dramatica con foco tecnologico.",
                    "palette": {"primario": "#1a1a2e", "acento": "#e94560"},
                    "typography": {"headings": "Space Grotesk", "body": "Inter"},
                    "tone": "Intenso y preciso",
                    "spacing_density": "Media, con bloques compactos.",
                    "sample_component": "Dashboard hero con cards de estado.",
                },
                {
                    "choice": "B",
                    "name": "Editorial calido",
                    "description": "Jerarquia editorial y tono premium.",
                    "palette": {"primario": "#f5f0e8", "texto": "#2c2c2c"},
                    "mood": "Calido y curado",
                    "layout_density": "Aireada",
                    "component_example": "Hero editorial con CTA sobrio.",
                },
            ]
        }
        with open(self.proposals_path, "w", encoding="utf-8") as fh:
            json.dump(proposals, fh, ensure_ascii=False, indent=2)

    def test_render_style_options_html_outputs_fragment_cards(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "Oscuro espacial",
                    "concept": "Direccion dramatica.",
                    "palette": [{"role": "primario", "value": "#1a1a2e"}],
                    "typography": {"headings": "Space Grotesk"},
                    "tone": "Intenso",
                    "spacing_density": "Media",
                    "sample_component": "Dashboard hero",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                }
            ]
        )
        self.assertIn('<div class="style-grid">', html)
        self.assertIn('data-choice="A"', html)
        self.assertIn("Oscuro espacial", html)
        self.assertNotIn("<!DOCTYPE", html)
        self.assertNotIn("style-viewer.css", html)
        self.assertNotIn("style-viewer.js", html)

    def test_build_style_options_payload_normalizes_sidecar_aliases(self):
        self._write_proposals()

        payload = build_style_options_payload(self.state_dir)
        self.assertEqual(payload["choices"], ["A", "B"])
        self.assertIn("Jerarquia editorial y tono premium.", payload["html"])
        self.assertIn("Calido y curado", payload["html"])
        self.assertIn("Hero editorial con CTA sobrio.", payload["html"])

    def test_render_style_options_html_uses_flavor_specific_cards(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "Editorial calido",
                    "concept": "Jerarquia editorial y tono premium.",
                    "palette": [{"role": "primario", "value": "#f5f0e8"}],
                    "typography": {"headings": "Fraunces"},
                    "tone": "Calido y curado",
                    "spacing_density": "Aireada",
                    "sample_component": "Hero editorial",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "B",
                    "name": "Panel operativo",
                    "concept": "Dashboard de control y metricas.",
                    "palette": [{"role": "primario", "value": "#dfeef3"}],
                    "typography": {"headings": "IBM Plex Sans"},
                    "tone": "Preciso",
                    "spacing_density": "Media",
                    "sample_component": "Panel de resumen",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "C",
                    "name": "Oscuro espacial",
                    "concept": "Direccion futurista de alto contraste.",
                    "palette": [{"role": "primario", "value": "#1a1a2e"}],
                    "typography": {"headings": "Space Grotesk"},
                    "tone": "Intenso",
                    "spacing_density": "Media",
                    "sample_component": "Hero de impacto",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
            ]
        )
        self.assertIn("style-option--editorial", html)
        self.assertIn("style-option--operational", html)
        self.assertIn("style-option--expressive", html)
        self.assertIn("preview-dashboard", html)
        self.assertIn("preview-badge", html)
        self.assertIn("--option-accent:", html)

    def test_write_style_options_html_writes_fragment_to_content_dir(self):
        self._write_proposals()

        result = write_style_options_html(self.state_dir)
        self.assertEqual(result["status"], "ok")
        html_path = os.path.join(self.content_dir, "style-options.html")
        self.assertEqual(result["html_path"], html_path)
        self.assertTrue(os.path.isfile(html_path))
        with open(html_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("Selecciona una direccion visual", content)
        self.assertIn("data-choice=\"B\"", content)

    def test_write_style_options_script_returns_pending_without_sidecar(self):
        result = subprocess.run(
            ["python3", WRITE_STYLE_OPTIONS_SCRIPT, "--visual-path", self.state_dir],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pending")

    def test_write_style_options_script_writes_html(self):
        self._write_proposals()

        result = subprocess.run(
            [
                "python3",
                WRITE_STYLE_OPTIONS_SCRIPT,
                "--visual-path",
                self.state_dir,
                "--title",
                "Elige una direccion",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        with open(payload["html_path"], "r", encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("Elige una direccion", content)


if __name__ == "__main__":
    unittest.main()
