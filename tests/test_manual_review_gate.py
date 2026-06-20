#!/usr/bin/env python3
"""Tests del gate de revision humana de la matriz manual."""

from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest


ROOT = os.path.join(os.path.dirname(__file__), "..")
GATE_PATH = os.path.join(ROOT, "scripts", "manual_review_gate.py")
SMOKE_PATH = os.path.join(ROOT, "scripts", "manual_smoke.py")


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestManualReviewGate(unittest.TestCase):
    def _payloads(self):
        manual_smoke = _load_module(SMOKE_PATH, "manual_smoke_for_review_test")
        cases = [asdict(case) for case in manual_smoke.CASES]
        case_ids = [case["case_id"] for case in cases]
        plugin_dir = Path(ROOT).resolve()
        evidence = {
            "version": "0.6.0",
            "plugin_dir": str(plugin_dir),
            "plugin_source": "worktree",
            "plugin_surface": manual_smoke._plugin_surface_snapshot(plugin_dir),
            "counts": {
                "total": len(case_ids),
                "needs_human_review": len(case_ids),
                "blocked_auth": 0,
                "failed": 0,
            },
            "cases": [
                {
                    **case,
                    "status": "needs_human_review",
                    "response_preview": "respuesta revisable",
                }
                for case in cases
            ],
            "command_coverage": manual_smoke._case_command_coverage(),
            "option_coverage": manual_smoke._case_option_coverage(),
            "runtime_coverage": manual_smoke._case_runtime_coverage(),
        }
        review = {
            "version": "0.6.0",
            "evidence_file": "",
            "evidence_sha256": "",
            "approved": True,
            "reviewer": "release reviewer",
            "reviewed_at": "2026-06-19T00:00:00Z",
            "cases": {
                case["case_id"]: {
                    "approved": True,
                    "notes": (
                        f"Revisado {case['case_id']}: respuesta coherente, "
                        "honesta y ajustada al contrato probado."
                    ),
                    "prompt": case["prompt"],
                    "expected": case["expected"],
                    "setup": case["setup"],
                    "commands": case["commands"],
                    "suite": case["suite"],
                    "option_keys": case["option_keys"],
                    "runtime_keys": case["runtime_keys"],
                }
                for case in cases
            },
        }
        return evidence, review, case_ids

    def _assert_rejects_evidence(self, mutate, *needles):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        mutate(evidence, review, case_ids)

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        message = str(context.exception)
        for needle in needles:
            self.assertIn(needle, message)

    def test_review_gate_accepts_complete_human_review(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, _ = self._payloads()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            result = gate.validate_review(evidence_path, review_path)

        self.assertIn("plugin_source verificado: worktree", result[1])
        self.assertIn("revision humana", result[2])
        self.assertIn("review.evidence_sha256 coincide", result[3])
        self.assertIn("review.evidence_file coincide", result[4])
        self.assertIn("coverage maps coinciden", result[5])
        self.assertIn("review.cases coincide", result[6])
        self.assertIn("sin patrones de secretos reales", result[7])

    def test_review_gate_can_require_current_auth_preflight(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        manual_smoke = _load_module(SMOKE_PATH, "manual_smoke_for_current_auth_gate")
        evidence, review, _ = self._payloads()

        def fake_auth_preflight():
            return {
                "status": "blocked_auth",
                "reason": "Claude CLI devolvio 401 Invalid authentication credentials.",
                "diagnosis": {"code": "first_party_oauth_token_rejected"},
            }

        original_module_loader = gate._manual_smoke_module
        original_preflight = manual_smoke._auth_preflight
        manual_smoke._auth_preflight = fake_auth_preflight
        gate._manual_smoke_module = lambda: manual_smoke
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                evidence_path = Path(tmpdir) / "evidence.json"
                review_path = Path(tmpdir) / "review.json"
                evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
                review["evidence_file"] = str(evidence_path)
                review["evidence_sha256"] = gate._sha256(evidence_path)
                review_path.write_text(json.dumps(review), encoding="utf-8")

                with self.assertRaises(gate.ReviewGateError) as context:
                    gate.validate_review(
                        evidence_path,
                        review_path,
                        require_current_auth_preflight=True,
                    )
        finally:
            manual_smoke._auth_preflight = original_preflight
            gate._manual_smoke_module = original_module_loader

        self.assertIn("preflight actual de Claude CLI no esta ok", str(context.exception))
        self.assertIn("first_party_oauth_token_rejected", str(context.exception))

    def test_review_gate_rejects_stale_plugin_surface_roots(self):
        def mutate(evidence, review, case_ids):
            evidence["plugin_surface"]["roots"] = [
                root
                for root in evidence["plugin_surface"]["roots"]
                if root not in {"package.json", "README.md", "scripts"}
            ]

        self._assert_rejects_evidence(
            mutate,
            "evidence.plugin_surface.roots no coincide con el plugin actual",
        )

    def test_review_template_binds_cases_to_evidence_hash(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, _, case_ids = self._payloads()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            result = gate.write_review_template(evidence_path, review_path)
            template = json.loads(review_path.read_text(encoding="utf-8"))
            evidence_sha256 = gate._sha256(evidence_path)
            mode = stat.S_IMODE(review_path.stat().st_mode)

        self.assertIn("plantilla creada", result[0])
        self.assertEqual(template["evidence_sha256"], evidence_sha256)
        self.assertEqual(template["approved"], False)
        self.assertIn(case_ids[0], template["cases"])
        self.assertEqual(template["cases"][case_ids[0]]["approved"], False)
        self.assertEqual(mode, 0o600)

    def test_review_template_rejects_evidence_with_secrets(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, _, _ = self._payloads()
        anthropic_key = "sk-ant-" + ("b" * 24)
        evidence["cases"][0]["response_preview"] = f"token accidental {anthropic_key}"

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.write_review_template(evidence_path, review_path)

            self.assertFalse(review_path.exists())

        self.assertIn("No se crea plantilla", str(context.exception))
        self.assertIn("ANTHROPIC_KEY", str(context.exception))

    def test_review_gate_rejects_missing_case_approval(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        review["cases"][case_ids[0]]["approved"] = False

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("approved=true", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))

    def test_review_gate_rejects_missing_human_notes(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        review["cases"][case_ids[0]]["notes"] = ""

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("notes humanas", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))

    def test_review_gate_rejects_generic_human_notes(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        review["cases"][case_ids[0]]["notes"] = "ok"

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("demasiado genericas", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))

    def test_review_gate_rejects_repeated_human_notes(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        repeated = "Revisado manualmente: respuesta honesta y coherente con el contrato probado."
        review["cases"][case_ids[0]]["notes"] = repeated
        review["cases"][case_ids[1]]["notes"] = repeated

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("notes humanas repetidas", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))
        self.assertIn(case_ids[1], str(context.exception))

    def test_review_gate_rejects_failed_case_even_if_counts_are_clean(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        evidence["cases"][0]["status"] = "failed"

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("needs_human_review", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))

    def test_review_gate_rejects_review_for_different_evidence_hash(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, _ = self._payloads()
        review["evidence_sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("evidence_sha256", str(context.exception))

    def test_review_gate_rejects_missing_evidence_file_reference(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, _ = self._payloads()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = ""
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("review.evidence_file es obligatorio", str(context.exception))

    def test_review_gate_rejects_review_for_different_evidence_file(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, _ = self._payloads()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            other_evidence_path = Path(tmpdir) / "other-evidence.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            other_evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(other_evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("review.evidence_file", str(context.exception))
        self.assertIn("no coincide", str(context.exception))

    def test_review_gate_rejects_stale_plugin_surface_hash(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, _ = self._payloads()
        evidence["plugin_surface"]["sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("plugin_surface.sha256", str(context.exception))

    def test_review_gate_rejects_secrets_in_evidence(self):
        anthropic_key = "sk-ant-" + ("a" * 24)

        def mutate(evidence, _review, _case_ids):
            evidence["cases"][0]["response_preview"] = f"token accidental {anthropic_key}"

        self._assert_rejects_evidence(
            mutate,
            "evidence contiene posibles secretos reales",
            "ANTHROPIC_KEY",
            "response_preview",
        )

    def test_review_gate_rejects_secrets_in_human_notes(self):
        github_token = "ghp_" + ("A" * 36)

        def mutate(_evidence, review, case_ids):
            review["cases"][case_ids[0]]["notes"] = f"probado con {github_token}"

        self._assert_rejects_evidence(
            mutate,
            "review contiene posibles secretos reales",
            "GITHUB_TOKEN",
            "notes",
        )

    def test_review_gate_rejects_wrong_expected_plugin_source(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, _ = self._payloads()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(
                    evidence_path,
                    review_path,
                    expected_plugin_source="installed-cache",
                )

        self.assertIn("plugin_source", str(context.exception))
        self.assertIn("installed-cache", str(context.exception))

    def test_review_gate_rejects_stale_manual_case_prompt(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        evidence["cases"][0]["prompt"] = "/alfred-dev:help"

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("evidence.cases desalineados", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))
        self.assertIn("prompt", str(context.exception))

    def test_review_gate_rejects_missing_manual_case_metadata(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        del evidence["cases"][0]["expected"]

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("evidence.cases desalineados", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))
        self.assertIn("expected", str(context.exception))

    def test_review_gate_rejects_stale_review_case_metadata(self):
        gate = _load_module(GATE_PATH, "manual_review_gate")
        evidence, review, case_ids = self._payloads()
        review["cases"][case_ids[0]]["expected"] = "Criterio viejo que no toca"

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "evidence.json"
            review_path = Path(tmpdir) / "review.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review["evidence_file"] = str(evidence_path)
            review["evidence_sha256"] = gate._sha256(evidence_path)
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(gate.ReviewGateError) as context:
                gate.validate_review(evidence_path, review_path)

        self.assertIn("review.cases desalineados", str(context.exception))
        self.assertIn(case_ids[0], str(context.exception))
        self.assertIn("expected", str(context.exception))

    def test_review_gate_rejects_missing_option_coverage_key(self):
        def mutate(evidence, _review, _case_ids):
            del evidence["option_coverage"]["audit:sonarqube-docker-install-menu"]

        self._assert_rejects_evidence(
            mutate,
            "option_coverage",
            "no incluye claves actuales",
            "audit:sonarqube-docker-install-menu",
        )

    def test_review_gate_rejects_stale_option_coverage_case_ids(self):
        def mutate(evidence, _review, _case_ids):
            evidence["option_coverage"]["update:confirm-update-menu"] = ["help"]

        self._assert_rejects_evidence(
            mutate,
            "option_coverage",
            "no coincide con matriz actual",
            "update:confirm-update-menu",
        )

    def test_review_gate_rejects_obsolete_runtime_coverage_key(self):
        def mutate(evidence, _review, _case_ids):
            evidence["runtime_coverage"]["update:scope-global"] = ["update-user"]

        self._assert_rejects_evidence(
            mutate,
            "runtime_coverage",
            "claves obsoletas/desconocidas",
            "update:scope-global",
        )


if __name__ == "__main__":
    unittest.main()
