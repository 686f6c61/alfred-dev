#!/usr/bin/env python3
"""Tests para el hook de verificacion de evidencia."""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hooks.evidence_guard_lib import (
    is_test_command,
    detect_test_result,
    record_evidence,
    get_evidence,
    clear_evidence,
    EVIDENCE_MAX_AGE_SECONDS,
)


class TestIsTestCommand(unittest.TestCase):
    """Verifica la deteccion de comandos de tests."""

    def test_pytest(self):
        self.assertTrue(is_test_command("pytest tests/ -v"))

    def test_python_m_pytest(self):
        self.assertTrue(is_test_command("python3 -m pytest tests/ -v"))

    def test_npm_test(self):
        self.assertTrue(is_test_command("npm test"))

    def test_cargo_test(self):
        self.assertTrue(is_test_command("cargo test"))

    def test_jest(self):
        self.assertTrue(is_test_command("jest --coverage"))

    def test_vitest(self):
        self.assertTrue(is_test_command("vitest run"))

    def test_go_test(self):
        self.assertTrue(is_test_command("go test ./..."))

    def test_not_a_test_command(self):
        self.assertFalse(is_test_command("cat pytest.ini"))

    def test_grep_pytest(self):
        self.assertFalse(is_test_command("grep pytest requirements.txt"))

    def test_chained_pytest(self):
        self.assertTrue(is_test_command("cd project && pytest -v"))

    def test_empty_command(self):
        self.assertFalse(is_test_command(""))


class TestDetectTestResult(unittest.TestCase):
    """Verifica la deteccion de resultados de tests."""

    def test_pass_pytest(self):
        output = "====== 10 passed in 0.5s ======"
        self.assertEqual(detect_test_result(output), "pass")

    def test_fail_pytest(self):
        output = "FAILED tests/test_foo.py::test_bar - AssertionError"
        self.assertEqual(detect_test_result(output), "fail")

    def test_mixed_has_fail_priority(self):
        output = "3 passed, 1 failed"
        self.assertEqual(detect_test_result(output), "fail")

    def test_unknown_output(self):
        output = "Compiling project..."
        self.assertEqual(detect_test_result(output), "unknown")

    def test_jest_pass(self):
        output = "Tests: 5 passing"
        self.assertEqual(detect_test_result(output), "pass")

    def test_empty_output(self):
        self.assertEqual(detect_test_result(""), "unknown")

    def test_fail_safe_not_detected_as_failure(self):
        """La palabra 'fail-safe' no debe detectarse como fallo."""
        output = "System entered fail-safe mode. All checks passed."
        # Contiene "passed" como exito, "fail-safe" no debe contar como fallo
        self.assertEqual(detect_test_result(output), "pass")

    def test_failover_not_detected_as_failure(self):
        """La palabra 'failover' no debe detectarse como fallo."""
        output = "Failover completed successfully. 5 passed"
        self.assertEqual(detect_test_result(output), "pass")

    def test_zero_failures_not_detected_as_fail(self):
        """La salida '0 failures' no debe detectarse como fallo."""
        output = "Tests run: 10, 0 failures, 0 errors"
        self.assertEqual(detect_test_result(output), "pass")

    def test_zero_failed_not_detected_as_fail(self):
        """La salida '0 failed' no debe detectarse como fallo."""
        output = "10 passed, 0 failed in 1.5s"
        self.assertEqual(detect_test_result(output), "pass")

    def test_go_test_detected_as_pass(self):
        """La salida de go test se detecta como pass."""
        # Salida multilinea realista de go test
        output = "=== RUN   TestFoo\n--- PASS: TestFoo (0.00s)\nPASS\nok  \tgithub.com/foo/bar\t0.003s"
        self.assertEqual(detect_test_result(output), "pass")


class TestEvidenceStorage(unittest.TestCase):
    """Verifica el almacenamiento y consulta de evidencia."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.claude_dir = os.path.join(self.tmpdir, ".claude")
        os.makedirs(self.claude_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_and_get(self):
        record_evidence("pytest -v", "pass", project_dir=self.tmpdir)
        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertTrue(evidence["has_evidence"])
        self.assertTrue(evidence["all_passing"])
        self.assertEqual(evidence["count"], 1)

    def test_multiple_records(self):
        record_evidence("pytest tests/", "pass", project_dir=self.tmpdir)
        record_evidence("pytest tests/ -k foo", "pass", project_dir=self.tmpdir)
        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertEqual(evidence["count"], 2)
        self.assertTrue(evidence["all_passing"])

    def test_fail_record(self):
        record_evidence("pytest -v", "pass", project_dir=self.tmpdir)
        record_evidence("pytest -v", "fail", project_dir=self.tmpdir)
        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertFalse(evidence["all_passing"])
        self.assertEqual(evidence["last_result"], "fail")

    def test_no_evidence(self):
        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertFalse(evidence["has_evidence"])
        self.assertEqual(evidence["count"], 0)

    def test_clear_evidence(self):
        record_evidence("pytest -v", "pass", project_dir=self.tmpdir)
        clear_evidence(project_dir=self.tmpdir)
        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertFalse(evidence["has_evidence"])

    def test_old_evidence_excluded(self):
        """Evidencia antigua no se considera reciente."""
        # Escribir un registro con timestamp antiguo directamente
        path = os.path.join(self.claude_dir, "alfred-evidence.json")
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=EVIDENCE_MAX_AGE_SECONDS + 60)).isoformat()
        records = [{"timestamp": old_ts, "command": "pytest", "result": "pass"}]
        with open(path, "w") as f:
            json.dump(records, f)

        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertFalse(evidence["has_evidence"])

    def test_truncation_at_50(self):
        """El fichero se trunca a 50 registros."""
        for i in range(60):
            record_evidence(f"pytest test_{i}.py", "pass", project_dir=self.tmpdir)

        path = os.path.join(self.claude_dir, "alfred-evidence.json")
        with open(path, "r") as f:
            data = json.load(f)
        self.assertLessEqual(len(data), 50)

    def test_get_evidence_no_age_filter(self):
        """max_age_seconds=None devuelve todos los registros sin filtrar."""
        # Escribir un registro con timestamp antiguo
        path = os.path.join(self.claude_dir, "alfred-evidence.json")
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        records = [
            {"timestamp": old_ts, "command": "pytest", "result": "pass"},
        ]
        with open(path, "w") as f:
            json.dump(records, f)

        # Con ventana normal: no aparece
        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertFalse(evidence["has_evidence"])

        # Sin ventana: aparece
        evidence = get_evidence(max_age_seconds=None, project_dir=self.tmpdir)
        self.assertTrue(evidence["has_evidence"])
        self.assertEqual(evidence["count"], 1)

    def test_unknown_result_affects_all_passing(self):
        """Un resultado unknown hace que all_passing sea False."""
        record_evidence("pytest -v", "pass", project_dir=self.tmpdir)
        record_evidence("pytest -v", "unknown", project_dir=self.tmpdir)
        evidence = get_evidence(project_dir=self.tmpdir)
        self.assertTrue(evidence["has_evidence"])
        self.assertFalse(evidence["all_passing"])


if __name__ == "__main__":
    unittest.main()
