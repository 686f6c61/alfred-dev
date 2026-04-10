#!/usr/bin/env python3
"""Tests para la generación canónica de docs/style-direction.md."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from core.selina_style_direction import (
    discover_proposals_file,
    render_style_direction_markdown,
    write_style_direction_artifact,
)


WRITE_STYLE_DIRECTION_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visual",
    "scripts",
    "write-style-direction.py",
)


class TestSelinaStyleDirection(unittest.TestCase):
    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="alfred-selina-style-")
        self.session_dir = os.path.join(self.project_dir, ".alfred-dev", "visual", "session-1")
        self.state_dir = os.path.join(self.session_dir, "state")
        self.content_dir = os.path.join(self.session_dir, "content")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
        self.events_path = os.path.join(self.state_dir, "events")
        self.proposals_path = os.path.join(self.content_dir, "style-options.json")

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    def _write_fixture_files(self):
        with open(self.events_path, "w", encoding="utf-8") as fh:
            fh.write(
                '{"type":"click","choice":"B","label":"Editorial cálido","ts":"2026-04-07T10:00:02Z"}\n'
            )

        proposals = {
            "proposals": [
                {
                    "choice": "A",
                    "name": "Oscuro espacial",
                    "concept": "Alta densidad visual con foco tecnológico.",
                },
                {
                    "choice": "B",
                    "name": "Editorial cálido",
                    "concept": "Una interfaz con jerarquía editorial y tono premium.",
                    "palette": {
                        "primario": "#f5f0e8",
                        "secundario": "#c8a96e",
                        "texto": "#2c2c2c",
                    },
                    "typography": {
                        "headings": "Fraunces",
                        "body": "Source Sans 3",
                        "scale": "16 / 20 / 28 / 40",
                    },
                    "spacing_density": "Aireada, con bloques respirables y ritmo editorial.",
                    "tone": "Editorial cálido",
                    "sample_component": "Tarjeta de resumen con titular serif, métricas cortas y CTA sobrio.",
                    "rationale": "Encaja con un producto que necesita transmitir criterio y confianza.",
                    "not_this_direction": [
                        "No es una UI dashboard densa ni hiper-técnica.",
                        "No busca estética startup genérica.",
                    ],
                    "tokens": {
                        "color.bg.canvas": "#f5f0e8",
                        "color.text.primary": "#2c2c2c",
                    },
                    "context_signals": [
                        "Audiencia profesional no técnica.",
                        "Necesidad de transmitir calma y credibilidad.",
                    ],
                },
            ]
        }
        with open(self.proposals_path, "w", encoding="utf-8") as fh:
            json.dump(proposals, fh, ensure_ascii=False, indent=2)

    def test_discover_proposals_file_prefers_content_style_options_json(self):
        self._write_fixture_files()
        self.assertEqual(discover_proposals_file(self.state_dir), self.proposals_path)

    def test_write_style_direction_artifact_renders_selected_proposal(self):
        self._write_fixture_files()

        result = write_style_direction_artifact(self.project_dir, self.state_dir)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["choice"], "B")

        artifact_path = os.path.join(self.project_dir, "docs", "style-direction.md")
        with open(artifact_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn(
            "Selina recomienda `B` — Editorial cálido como sistema de diseño base para esta fase.",
            content,
        )
        self.assertIn("## Por qué gana esta opción", content)
        self.assertIn("Fraunces", content)
        self.assertIn("No es una UI dashboard densa ni hiper-técnica.", content)
        self.assertIn("color.bg.canvas", content)
        self.assertIn("Propuestas fuente: `content/style-options.json`", content)

    def test_render_style_direction_markdown_has_required_sections(self):
        record = {
            "generated_at": "2026-04-07T10:00:02Z",
            "choice": "C",
            "selected_label": "Minimalismo vibrante",
            "selected_at": "2026-04-07T10:00:02Z",
            "proposals_file": "/tmp/style-options.json",
            "proposal": {
                "choice": "C",
                "name": "Minimalismo vibrante",
                "concept": "Sistema limpio con acento energético.",
                "palette": [{"role": "primario", "value": "#0d7377"}],
                "typography": {"headings": "Sora", "body": "Inter"},
                "spacing_density": "Aireada",
                "tone": "Moderno y ligero",
                "sample_component": "Dashboard de cards con foco en highlights.",
                "rationale": "Conviene a un producto claro y visual.",
                "not_this_direction": ["No es sobrio corporativo."],
                "tokens": [{"name": "color.brand.primary", "value": "#0d7377"}],
                "context_signals": ["Producto orientado a descubrimiento visual."],
            },
        }
        content = render_style_direction_markdown(record)
        self.assertIn("## Sistema de diseño elegido", content)
        self.assertIn("## Por qué gana esta opción", content)
        self.assertIn("## Qué NO es este sistema", content)
        self.assertIn("## Tokens iniciales sugeridos", content)
        self.assertIn("Producto orientado a descubrimiento visual.", content)

    def test_render_style_direction_markdown_uses_basename_when_project_context_missing(self):
        record = {
            "generated_at": "2026-04-07T10:00:02Z",
            "choice": "A",
            "selected_label": "Oscuro espacial",
            "selected_at": "",
            "proposals_file": "/tmp/nested/style-options.json",
            "proposal": {
                "choice": "A",
                "name": "Oscuro espacial",
                "concept": "",
                "palette": [],
                "typography": {},
                "spacing_density": "",
                "tone": "",
                "sample_component": "",
                "rationale": "",
                "not_this_direction": [],
                "tokens": [],
                "context_signals": [],
            },
        }

        content = render_style_direction_markdown(record)
        self.assertIn("Propuestas fuente: `style-options.json`", content)
        self.assertNotIn("../../", content)

    def test_sparse_proposal_gets_semantic_defaults(self):
        with open(self.events_path, "w", encoding="utf-8") as fh:
            fh.write(
                '{"type":"click","choice":"A","label":"Editorial cálido","ts":"2026-04-07T10:00:02Z"}\n'
            )
        with open(self.proposals_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "proposals": [
                        {
                            "choice": "A",
                            "name": "Editorial cálido",
                            "palette": {"primario": "#f5f0e8"},
                            "typography": {"headings": "Fraunces"},
                        }
                    ]
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )

        result = write_style_direction_artifact(self.project_dir, self.state_dir)
        self.assertEqual(result["status"], "ok")

        artifact_path = os.path.join(self.project_dir, "docs", "style-direction.md")
        with open(artifact_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("Lenguaje editorial con jerarquía clara", content)
        self.assertIn("Funciona bien cuando el producto necesita transmitir criterio", content)
        self.assertIn("Hero editorial con titular protagonista", content)
        self.assertIn("No es una UI de dashboard densa", content)
        self.assertIn("Necesidad de transmitir criterio, calma y sensación de cuidado.", content)

    def test_sidecar_alias_fields_are_normalized(self):
        with open(self.events_path, "w", encoding="utf-8") as fh:
            fh.write(
                '{"type":"click","choice":"C","label":"Minimalismo vibrante","ts":"2026-04-07T10:00:02Z"}\n'
            )
        with open(self.proposals_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "proposals": [
                        {
                            "choice": "C",
                            "title": "Minimalismo vibrante",
                            "description": "Sistema limpio con acento energético.",
                            "mood": "Ligero y nítido",
                            "layout_density": "Muy aireada",
                            "component_example": "Hero con claim corto y CTA dominante.",
                            "why": "Ayuda a reducir ruido visual desde el primer pantallazo.",
                            "anti_patterns": ["No es una interfaz ornamental."],
                            "audience": "Equipo de producto con poco tiempo de lectura",
                        }
                    ]
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )

        result = write_style_direction_artifact(self.project_dir, self.state_dir)
        self.assertEqual(result["status"], "ok")

        artifact_path = os.path.join(self.project_dir, "docs", "style-direction.md")
        with open(artifact_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("Sistema limpio con acento energético.", content)
        self.assertIn("Ligero y nítido", content)
        self.assertIn("Muy aireada", content)
        self.assertIn("Hero con claim corto y CTA dominante.", content)
        self.assertIn("Ayuda a reducir ruido visual desde el primer pantallazo.", content)
        self.assertIn("No es una interfaz ornamental.", content)
        self.assertIn("Equipo de producto con poco tiempo de lectura", content)

    def test_write_style_direction_script_returns_pending_without_choice(self):
        with open(self.proposals_path, "w", encoding="utf-8") as fh:
            json.dump({"A": {"name": "Oscuro espacial"}}, fh)

        result = subprocess.run(
            [
                "python3",
                WRITE_STYLE_DIRECTION_SCRIPT,
                "--project-dir",
                self.project_dir,
                "--visual-path",
                self.state_dir,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pending")

    def test_write_style_direction_script_writes_artifact(self):
        self._write_fixture_files()

        result = subprocess.run(
            [
                "python3",
                WRITE_STYLE_DIRECTION_SCRIPT,
                "--project-dir",
                self.project_dir,
                "--visual-path",
                self.state_dir,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(os.path.isfile(payload["artifact_path"]))


if __name__ == "__main__":
    unittest.main()
