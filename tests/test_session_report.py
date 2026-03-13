#!/usr/bin/env python3
"""Tests para el generador de informes de sesion."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.session_report import (
    generate_report,
    _section_phases,
    _section_evidence,
    _section_team,
    _section_artifacts,
    _estimate_duration,
)


class TestSectionPhases(unittest.TestCase):
    """Verifica la generacion de la seccion de fases."""

    def test_no_phases(self):
        session = {"fases_completadas": []}
        result = _section_phases(session)
        self.assertIn("No se completaron", result)

    def test_with_phases(self):
        session = {
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado", "artefactos": ["prd.md"]},
                {"nombre": "arquitectura", "resultado": "aprobado", "artefactos": []},
            ],
            "fase_actual": "desarrollo",
        }
        result = _section_phases(session)
        self.assertIn("producto", result)
        self.assertIn("arquitectura", result)
        self.assertIn("prd.md", result)
        self.assertIn("detenido en fase **desarrollo**", result)

    def test_completed_flow(self):
        session = {
            "fases_completadas": [{"nombre": "unica", "resultado": "aprobado"}],
            "fase_actual": "completado",
        }
        result = _section_phases(session)
        self.assertIn("flujo completado", result)


class TestSectionEvidence(unittest.TestCase):
    """Verifica la generacion de la seccion de evidencia."""

    def test_no_evidence_data(self):
        result = _section_evidence(None)
        self.assertEqual(result, "")

    def test_no_tests_run(self):
        evidence = {"has_evidence": False, "records": []}
        result = _section_evidence(evidence)
        self.assertIn("No se ejecutaron tests", result)

    def test_with_evidence(self):
        evidence = {
            "has_evidence": True,
            "all_passing": True,
            "count": 2,
            "records": [
                {"timestamp": "2026-03-13T10:00:00+00:00", "command": "pytest -v", "result": "pass"},
                {"timestamp": "2026-03-13T10:05:00+00:00", "command": "pytest -v", "result": "pass"},
            ],
        }
        result = _section_evidence(evidence)
        self.assertIn("2 rondas de tests", result)
        self.assertIn("todos verdes", result)

    def test_with_failures(self):
        evidence = {
            "has_evidence": True,
            "all_passing": False,
            "count": 1,
            "records": [
                {"timestamp": "2026-03-13T10:00:00+00:00", "command": "pytest", "result": "fail"},
            ],
        }
        result = _section_evidence(evidence)
        self.assertIn("con fallos", result)
        self.assertIn("FALLO", result)


class TestSectionTeam(unittest.TestCase):
    """Verifica la generacion de la seccion de equipo."""

    def test_no_team(self):
        session = {}
        result = _section_team(session)
        self.assertEqual(result, "")

    def test_with_optionals(self):
        session = {
            "equipo_sesion": {
                "opcionales_activos": {
                    "data-engineer": True,
                    "ux-reviewer": False,
                    "performance-engineer": True,
                },
            },
        }
        result = _section_team(session)
        self.assertIn("data-engineer", result)
        self.assertIn("performance-engineer", result)
        self.assertNotIn("ux-reviewer", result)


class TestSectionArtifacts(unittest.TestCase):
    """Verifica la generacion de la seccion de artefactos."""

    def test_no_artifacts(self):
        result = _section_artifacts({"artefactos": []})
        self.assertEqual(result, "")

    def test_with_artifacts(self):
        result = _section_artifacts({"artefactos": ["prd.md", "adr-001.md"]})
        self.assertIn("prd.md", result)
        self.assertIn("adr-001.md", result)


class TestEstimateDuration(unittest.TestCase):
    """Verifica la estimacion de duracion."""

    def test_missing_timestamps(self):
        result = _estimate_duration({})
        self.assertEqual(result, "no disponible")

    def test_short_duration(self):
        session = {
            "creado_en": "2026-03-13T10:00:00+00:00",
            "actualizado_en": "2026-03-13T10:00:30+00:00",
        }
        result = _estimate_duration(session)
        self.assertIn("30 segundos", result)

    def test_minutes_duration(self):
        session = {
            "creado_en": "2026-03-13T10:00:00+00:00",
            "actualizado_en": "2026-03-13T10:15:00+00:00",
        }
        result = _estimate_duration(session)
        self.assertIn("15 minutos", result)

    def test_hours_duration(self):
        session = {
            "creado_en": "2026-03-13T10:00:00+00:00",
            "actualizado_en": "2026-03-13T12:30:00+00:00",
        }
        result = _estimate_duration(session)
        self.assertIn("2h 30m", result)


class TestGenerateReport(unittest.TestCase):
    """Verifica la generacion completa del informe."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generates_file(self):
        session = {
            "comando": "feature",
            "descripcion": "Login con OAuth",
            "fase_actual": "completado",
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado"},
            ],
            "artefactos": ["prd.md"],
            "creado_en": "2026-03-13T10:00:00+00:00",
            "actualizado_en": "2026-03-13T10:30:00+00:00",
        }
        report_path = generate_report(session, project_dir=self.tmpdir)
        self.assertTrue(os.path.isfile(report_path))

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("feature", content)
        self.assertIn("Login con OAuth", content)
        self.assertIn("producto", content)
        self.assertIn("prd.md", content)

    def test_report_in_correct_directory(self):
        session = {
            "comando": "fix",
            "descripcion": "Bug critico",
            "fase_actual": "completado",
            "fases_completadas": [],
            "artefactos": [],
            "creado_en": "2026-03-13T10:00:00+00:00",
            "actualizado_en": "2026-03-13T10:05:00+00:00",
        }
        report_path = generate_report(session, project_dir=self.tmpdir)
        self.assertIn("docs/alfred-reports", report_path)
        self.assertTrue(report_path.endswith("-fix.md"))


class TestFilenameSanitization(unittest.TestCase):
    """Verifica que el nombre del comando se sanitiza en el fichero."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_path_traversal_sanitized(self):
        """Un comando con caracteres de path traversal no escapa del directorio."""
        session = {
            "comando": "../../etc/passwd",
            "descripcion": "Intento de path traversal",
            "fase_actual": "completado",
            "fases_completadas": [],
            "artefactos": [],
            "creado_en": "2026-03-13T10:00:00+00:00",
            "actualizado_en": "2026-03-13T10:05:00+00:00",
        }
        report_path = generate_report(session, project_dir=self.tmpdir)
        # El fichero debe estar dentro de docs/alfred-reports/
        self.assertIn("docs/alfred-reports", report_path)
        # No debe contener ".." en el nombre del fichero
        filename = os.path.basename(report_path)
        self.assertNotIn("..", filename)
        self.assertTrue(os.path.isfile(report_path))

    def test_special_chars_sanitized(self):
        """Los caracteres especiales en el comando se reemplazan por _."""
        session = {
            "comando": "feat/login & rm -rf",
            "descripcion": "Comando con chars raros",
            "fase_actual": "completado",
            "fases_completadas": [],
            "artefactos": [],
            "creado_en": "2026-03-13T10:00:00+00:00",
            "actualizado_en": "2026-03-13T10:05:00+00:00",
        }
        report_path = generate_report(session, project_dir=self.tmpdir)
        filename = os.path.basename(report_path)
        self.assertNotIn("/", filename)
        self.assertNotIn("&", filename)
        self.assertTrue(os.path.isfile(report_path))


if __name__ == "__main__":
    unittest.main()
