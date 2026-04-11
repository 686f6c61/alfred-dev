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
        self.assertIn('data-label="Oscuro espacial"', html)
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

    def test_build_style_options_payload_accepts_palette_lists_and_typography_strings(self):
        with open(self.proposals_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "proposals": [
                        {
                            "choice": "A",
                            "name": "Enterprise clarity",
                            "concept": "Dashboard profesional de tono frío y neutral.",
                            "palette": ["#0F172A", "#1E3A5F", "#3B82F6", "#E2E8F0", "#FFFFFF"],
                            "typography": "Inter / DM Sans — sans-serif geométrica, alta legibilidad",
                            "tone": "corporativo, sobrio, confiable",
                            "spacing_density": "denso",
                            "sample_component": "Barra lateral oscura",
                        }
                    ]
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )

        payload = build_style_options_payload(self.state_dir)
        self.assertIn("#0F172A", payload["html"])
        self.assertIn("#3B82F6", payload["html"])
        self.assertIn("Titulares: Inter", payload["html"])
        self.assertIn("Cuerpo: DM Sans", payload["html"])
        self.assertIn("Notas: sans-serif geométrica, alta legibilidad", payload["html"])

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

    def test_render_style_options_html_diversifies_similar_dashboard_proposals(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "Enterprise clarity",
                    "concept": "Dashboard profesional de tono frío y neutral, orientado a directivos y analistas.",
                    "palette": [{"role": "surface", "value": "#0F172A"}, {"role": "accent", "value": "#3B82F6"}],
                    "typography": {"headings": "Inter", "body": "DM Sans"},
                    "tone": "corporativo, sobrio, confiable",
                    "spacing_density": "denso",
                    "sample_component": "Barra lateral oscura",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "B",
                    "name": "Data-dark pro",
                    "concept": "Modo oscuro total al estilo de Grafana o Datadog para monitorización en tiempo real.",
                    "palette": [{"role": "surface", "value": "#111827"}, {"role": "accent", "value": "#10B981"}],
                    "typography": {"headings": "JetBrains Mono", "body": "Geist"},
                    "tone": "técnico, preciso, urgente cuando hay alertas",
                    "spacing_density": "muy denso",
                    "sample_component": "Estados sin sombras",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": ["monitorización 24/7"],
                },
                {
                    "choice": "C",
                    "name": "Modern SaaS clean",
                    "concept": "La estética del SaaS moderno: fondo blanco, whitespace y acentos índigo.",
                    "palette": [{"role": "surface", "value": "#FFFFFF"}, {"role": "accent", "value": "#6366F1"}],
                    "typography": {"headings": "Geist", "body": "Satoshi"},
                    "tone": "moderno, limpio, amigable pero serio",
                    "spacing_density": "cómodo y aireado",
                    "sample_component": "Cards con shadow sutil",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": ["demos y screenshots de marketing"],
                },
            ]
        )
        self.assertIn("style-option--operational", html)
        self.assertIn("style-option--technical", html)
        self.assertIn("style-option--minimal", html)
        self.assertIn("preview-technical-chart", html)
        self.assertIn("preview-product-shell", html)

    def test_render_style_options_html_respects_explicit_preview_flavor(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "Firma expresiva",
                    "concept": "Versión protagonista del sistema.",
                    "style_family": "neo-brutalism",
                    "style_family_label": "Anti-diseno / Neo-brutalismo",
                    "palette": [{"role": "surface", "value": "#fff0b3"}, {"role": "accent", "value": "#111111"}],
                    "typography": {
                        "headings": "Archivo Black",
                        "body": "IBM Plex Mono",
                        "pairing_label": "Brutal Core",
                        "css_url": "https://fonts.googleapis.com/css2?family=Archivo+Black:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500;700&display=swap",
                    },
                    "tone": "Directo",
                    "spacing_density": "Media",
                    "sample_component": "Hero brutalista",
                    "preview_flavor": "expressive",
                    "variant_label": "Firma expresiva",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "B",
                    "name": "Producto operativo",
                    "concept": "Versión más utilizable del sistema.",
                    "style_family": "neo-brutalism",
                    "style_family_label": "Anti-diseno / Neo-brutalismo",
                    "palette": [{"role": "surface", "value": "#fff0b3"}, {"role": "accent", "value": "#111111"}],
                    "typography": {
                        "headings": "Archivo Black",
                        "body": "Space Grotesk",
                        "pairing_label": "Brutal legible",
                        "css_url": "https://fonts.googleapis.com/css2?family=Archivo+Black:wght@400;500;700&family=Space+Grotesk:wght@400;500;700&display=swap",
                    },
                    "tone": "Claro",
                    "spacing_density": "Media",
                    "sample_component": "Resumen operativo",
                    "preview_flavor": "operational",
                    "variant_label": "Producto operativo",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
            ]
        )
        self.assertIn("style-option--expressive", html)
        self.assertIn("style-option--operational", html)
        self.assertIn("Firma expresiva", html)
        self.assertIn("Producto operativo", html)
        self.assertIn("Pairing: Brutal Core", html)
        self.assertIn("data-label=\"Firma expresiva\"", html)
        self.assertIn("style-family--neo-brutalism", html)
        self.assertIn('data-style-family="neo-brutalism"', html)
        self.assertIn("fonts.googleapis.com/css2?family=Archivo+Black", html)
        self.assertIn("--option-heading-font:", html)
        self.assertIn("--option-body-font:", html)
        self.assertIn("--option-accent: #111111", html)
        self.assertIn('preview-brutal preview-brutal--expressive', html)
        self.assertIn('preview-brutal preview-brutal--operational', html)
        self.assertIn("<h4>Firma expresiva</h4>", html)
        self.assertIn("<p>Hero brutalista</p>", html)

    def test_render_style_options_html_uses_family_specific_preview_grammars(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "Anti-diseno / Neo-brutalismo — Firma expresiva",
                    "concept": "Bordes duros y cajas desplazadas.",
                    "style_family": "neo-brutalism",
                    "style_family_label": "Anti-diseno / Neo-brutalismo",
                    "palette": [{"role": "surface", "value": "#fff0b3"}, {"role": "accent", "value": "#111111"}],
                    "typography": {"headings": "Archivo Black", "body": "IBM Plex Mono"},
                    "tone": "Directo, ironico y no pulido",
                    "spacing_density": "Media",
                    "sample_component": "Hero brutalista",
                    "preview_flavor": "expressive",
                    "variant_label": "Firma expresiva",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "B",
                    "name": "Nature distilled / Organico — Equilibrio base",
                    "concept": "Curvas suaves y calor editorial.",
                    "style_family": "nature-distilled",
                    "style_family_label": "Nature distilled / Organico",
                    "palette": [{"role": "surface", "value": "#fbf7f1"}, {"role": "accent", "value": "#8c6a42"}],
                    "typography": {"headings": "Cormorant Garamond", "body": "Manrope"},
                    "tone": "Curado, calmado y organico",
                    "spacing_density": "Aireada",
                    "sample_component": "Hero organico",
                    "preview_flavor": "balanced",
                    "variant_label": "Equilibrio base",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "C",
                    "name": "Glassmorphism 2.0 — Producto limpio",
                    "concept": "Paneles translucidos y profundidad suave.",
                    "style_family": "glassmorphism-2",
                    "style_family_label": "Glassmorphism 2.0",
                    "palette": [{"role": "surface", "value": "#f4f6ff"}, {"role": "accent", "value": "#7c8cff"}],
                    "typography": {"headings": "Plus Jakarta Sans", "body": "Inter"},
                    "tone": "Suave y tecnologico",
                    "spacing_density": "Aireada",
                    "sample_component": "Panel glass",
                    "preview_flavor": "minimal",
                    "variant_label": "Producto limpio",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
            ]
        )
        self.assertIn("preview-brutal", html)
        self.assertIn("preview-organic", html)
        self.assertIn("style-glass-card", html)
        self.assertIn("preview-brutal-card--hero", html)
        self.assertIn("preview-organic-media", html)
        self.assertIn("style-glass-orb-large", html)

    def test_render_style_options_html_distinguishes_retro_dopamine_kinetic_and_journey(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "Maximalismo & Neo-retro — Firma expresiva",
                    "concept": "Capas y collage editorial.",
                    "style_family": "maximalism-neo-retro",
                    "style_family_label": "Maximalismo & Neo-retro",
                    "palette": [{"role": "surface", "value": "#f7cf44"}, {"role": "accent", "value": "#ff4268"}],
                    "typography": {"headings": "Bricolage Grotesque", "body": "Newsreader"},
                    "tone": "Cultural y visible",
                    "spacing_density": "Media alta",
                    "sample_component": "Hero apilado",
                    "preview_flavor": "expressive",
                    "variant_label": "Firma expresiva",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "B",
                    "name": "Colores dopamina — Equilibrio base",
                    "concept": "Color rapido y respuesta emocional.",
                    "style_family": "dopamine-colors",
                    "style_family_label": "Colores dopamina",
                    "palette": [{"role": "surface", "value": "#fff46c"}, {"role": "accent", "value": "#ff275e"}],
                    "typography": {"headings": "Archivo Black", "body": "DM Sans"},
                    "tone": "Energetico",
                    "spacing_density": "Media",
                    "sample_component": "Hero de impacto",
                    "preview_flavor": "balanced",
                    "variant_label": "Equilibrio base",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "C",
                    "name": "Scroll narrativo & Gamificacion — Equilibrio base",
                    "concept": "Historia por etapas y checkpoints.",
                    "style_family": "narrative-scroll-gamification",
                    "style_family_label": "Scroll narrativo & Gamificacion",
                    "palette": [{"role": "surface", "value": "#eef2ff"}, {"role": "accent", "value": "#2f6fed"}],
                    "typography": {"headings": "Space Grotesk", "body": "Inter"},
                    "tone": "Secuencial",
                    "spacing_density": "Media",
                    "sample_component": "Rail de pasos",
                    "preview_flavor": "balanced",
                    "variant_label": "Equilibrio base",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
            ]
        )
        self.assertIn("preview-retro", html)
        self.assertIn("preview-dopamine", html)
        self.assertIn("preview-journey", html)
        self.assertIn("preview-retro-poster", html)
        self.assertIn("preview-dopamine-bubble", html)
        self.assertIn("preview-journey-topline", html)

    def test_render_style_options_html_uses_full_card_renderer_for_kinetic_family(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "Tipografia cinetica — Narrativa editorial",
                    "concept": "Titular protagonista y ritmo tipografico.",
                    "style_family": "kinetic-typography",
                    "style_family_label": "Tipografia cinetica",
                    "palette_mode_label": "Solidos",
                    "palette": [{"role": "surface", "value": "#f8efe6"}, {"role": "accent", "value": "#ff4b2b"}],
                    "typography": {"headings": "Syne", "body": "IBM Plex Sans", "pairing_label": "Kinetic Editorial"},
                    "tone": "Directo y performativo",
                    "spacing_density": "Media",
                    "sample_component": "Hero tipografico con banda",
                    "preview_flavor": "editorial",
                    "variant_label": "Narrativa editorial",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                }
            ]
        )
        self.assertIn("style-option--kinetic-card", html)
        self.assertIn("style-kinetic-card", html)
        self.assertIn("style-kinetic-headline", html)
        self.assertIn("style-kinetic-specs", html)
        self.assertNotIn('<div class="style-meta">', html)

    def test_render_style_options_html_uses_full_card_renderers_for_lucid_glass_and_depth(self):
        html = render_style_options_html(
            [
                {
                    "choice": "A",
                    "name": "AI Hyperminimalismo — Producto limpio",
                    "concept": "Silencio visual y precision.",
                    "style_family": "ai-hyperminimalism",
                    "style_family_label": "AI Hyperminimalismo",
                    "palette_mode_label": "Recomendada",
                    "palette": [{"role": "surface", "value": "#f7f9fc"}, {"role": "accent", "value": "#7c8cff"}],
                    "typography": {"headings": "Manrope", "body": "Inter", "pairing_label": "Hyperminimal Core"},
                    "tone": "Preciso y elegante",
                    "spacing_density": "Aireada",
                    "sample_component": "Hero limpio",
                    "preview_flavor": "minimal",
                    "variant_label": "Producto limpio",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "B",
                    "name": "Glassmorphism 2.0 — Producto limpio",
                    "concept": "Capas translúcidas y profundidad suave.",
                    "style_family": "glassmorphism-2",
                    "style_family_label": "Glassmorphism 2.0",
                    "palette_mode_label": "Recomendada",
                    "palette": [{"role": "surface", "value": "#edf4ff"}, {"role": "accent", "value": "#c36bff"}],
                    "typography": {"headings": "Sora", "body": "Manrope", "pairing_label": "Liquid Premium"},
                    "tone": "Pulido y suave",
                    "spacing_density": "Equilibrada",
                    "sample_component": "Panel glass",
                    "preview_flavor": "minimal",
                    "variant_label": "Producto limpio",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
                {
                    "choice": "C",
                    "name": "3D interactivo & WebGL — Equilibrio base",
                    "concept": "Objeto protagonista y panel lateral.",
                    "style_family": "interactive-3d-webgl",
                    "style_family_label": "3D interactivo & WebGL",
                    "palette_mode_label": "Recomendada",
                    "palette": [{"role": "surface", "value": "#eef2ff"}, {"role": "accent", "value": "#4f46e5"}],
                    "typography": {"headings": "Sora", "body": "Inter", "pairing_label": "Immersive Sans"},
                    "tone": "Inmersivo",
                    "spacing_density": "Equilibrada",
                    "sample_component": "Escena heroica",
                    "preview_flavor": "balanced",
                    "variant_label": "Equilibrio base",
                    "rationale": "",
                    "not_this_direction": [],
                    "tokens": [],
                    "context_signals": [],
                },
            ]
        )
        self.assertIn("style-option--lucid-card", html)
        self.assertIn("style-option--glass-card", html)
        self.assertIn("style-option--depth-card", html)
        self.assertIn("style-lucid-card", html)
        self.assertIn("style-glass-card", html)
        self.assertIn("style-depth-card", html)
        self.assertIn("style-lucid-headline", html)
        self.assertIn("style-glass-orb-large", html)
        self.assertIn("style-depth-object-large", html)
        self.assertNotIn('<div class="style-meta">', html)

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
