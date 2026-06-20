#!/usr/bin/env python3
"""Tests del reporte asistido de revision manual."""

import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "scripts" / "manual_review_report.py"


def _load_report_module():
    spec = importlib.util.spec_from_file_location("manual_review_report", REPORT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestManualReviewReport(unittest.TestCase):
    def _evidence(self):
        return {
            "version": "0.6.0",
            "plugin_dir": str(ROOT),
            "plugin_source": "worktree",
            "plugin_surface": {"sha256": "abc123", "file_count": 1},
            "auth_preflight": {
                "status": "ok",
                "reason": "Claude CLI pudo completar una llamada minima.",
                "auth_status": {"claude_version": "2.1.183 (Claude Code)"},
            },
            "counts": {
                "total": 2,
                "needs_human_review": 1,
                "blocked_auth": 0,
                "failed": 1,
            },
            "cases": [
                {
                    "case_id": "quick-cta",
                    "status": "needs_human_review",
                    "duration_ms": 1200,
                    "returncode": 0,
                    "api_error_status": None,
                    "total_cost_usd": 0.25,
                    "response_preview": "Quick preparado sin sorpresas.",
                    "stderr_preview": "",
                },
                {
                    "case_id": "feature-login",
                    "status": "failed",
                    "duration_ms": 2000,
                    "returncode": 1,
                    "api_error_status": None,
                    "total_cost_usd": 1.51,
                    "response_preview": "Reached maximum budget sk-ant-" + ("a" * 24),
                    "stderr_preview": "Traceback de prueba",
                },
            ],
        }

    def test_report_is_a_review_aid_not_an_approval(self):
        report = _load_report_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            evidence_path.write_text(json.dumps(self._evidence()), encoding="utf-8")

            markdown = report.build_report(evidence_path)

        self.assertIn("# Reporte asistido de revision manual", markdown)
        self.assertIn("Este reporte no aprueba la release", markdown)
        self.assertIn("Review template: no suministrada", markdown)
        self.assertIn("`quick-cta`", markdown)
        self.assertIn("`feature-login`", markdown)
        self.assertIn("status=failed", markdown)
        self.assertIn("term:reached maximum budget", markdown)
        self.assertIn("secret:ANTHROPIC_KEY", markdown)
        self.assertIn("[REDACTED:ANTHROPIC_KEY]", markdown)
        self.assertNotIn("sk-ant-" + ("a" * 24), markdown)

    def test_report_flags_stale_plugin_surface(self):
        report = _load_report_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            evidence = self._evidence()
            evidence["plugin_surface"] = {
                "roots": ["commands"],
                "file_count": 1,
                "sha256": "0" * 64,
            }
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            markdown = report.build_report(evidence_path)

        self.assertIn("## Superficie Del Plugin", markdown)
        self.assertIn("evidence.plugin_surface.roots no coincide", markdown)
        self.assertIn("evidence.plugin_surface.file_count no coincide", markdown)
        self.assertIn("evidence.plugin_surface.sha256 no coincide", markdown)

    def test_report_reads_optional_review_state_without_mutating_it(self):
        report = _load_report_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            review = {"approved": False, "reviewer": "persona revisora"}
            evidence_path.write_text(json.dumps(self._evidence()), encoding="utf-8")
            review_path.write_text(json.dumps(review), encoding="utf-8")

            markdown = report.build_report(evidence_path, review_path)
            after = json.loads(review_path.read_text(encoding="utf-8"))

        self.assertEqual(after, review)
        self.assertIn("Review approved: `False`", markdown)
        self.assertIn("Reviewer: `persona revisora`", markdown)

    def test_report_flags_generic_and_repeated_human_notes(self):
        report = _load_report_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(self._evidence()), encoding="utf-8")
            review_path.write_text(
                json.dumps(
                    {
                        "approved": False,
                        "reviewer": "persona revisora",
                        "cases": {
                            "quick-cta": {"approved": True, "notes": "ok"},
                            "feature-login": {"approved": True, "notes": "ok"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            markdown = report.build_report(evidence_path, review_path)

        self.assertIn("## Calidad De Review Humana", markdown)
        self.assertIn("notes_low_quality", markdown)
        self.assertIn("notes_repeated", markdown)
        self.assertIn("`quick-cta`", markdown)
        self.assertIn("`feature-login`", markdown)

    def test_report_accepts_specific_unique_human_notes_without_note_flags(self):
        report = _load_report_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(self._evidence()), encoding="utf-8")
            review_path.write_text(
                json.dumps(
                    {
                        "approved": False,
                        "reviewer": "persona revisora",
                        "cases": {
                            "quick-cta": {
                                "approved": True,
                                "notes": "Quick CTA revisado: respuesta util, honesta y acotada al contrato.",
                            },
                            "feature-login": {
                                "approved": True,
                                "notes": "Feature login revisada: el fallo queda visible y bloquea publicacion.",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            markdown = report.build_report(evidence_path, review_path)

        self.assertIn("Sin flags automaticos de notas humanas", markdown)
        self.assertNotIn("notes_low_quality", markdown)
        self.assertNotIn("notes_repeated", markdown)

    def test_cli_writes_report_with_private_permissions(self):
        report = _load_report_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            output_path = Path(tmpdir) / "manual-report.md"
            evidence_path.write_text(json.dumps(self._evidence()), encoding="utf-8")

            exit_code = report.main(
                [str(evidence_path), "--output", str(output_path)]
            )
            mode = stat.S_IMODE(output_path.stat().st_mode)
            body = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(mode, 0o600)
        self.assertIn("# Reporte asistido de revision manual", body)


if __name__ == "__main__":
    unittest.main()
