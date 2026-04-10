#!/usr/bin/env python3
"""Tests del punto de entrada hooks/evidence-guard.py."""

import importlib.util
import json
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch


_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_HOOKS_DIR = os.path.join(_TESTS_DIR, "..", "hooks")
_HOOK_PATH = os.path.join(_HOOKS_DIR, "evidence-guard.py")


def _load_evidence_guard():
    spec = importlib.util.spec_from_file_location("evidence_guard_hook", _HOOK_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestEvidenceGuardMain(unittest.TestCase):
    """Verifica el comportamiento del hook PostToolUse."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".claude"), exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run_main(self, payload: dict) -> tuple[int, str, list]:
        mod = _load_evidence_guard()
        stderr_capture = StringIO()
        exit_code = None
        evidence_calls = []

        def _record(command, result):
            evidence_calls.append((command, result))

        with patch("sys.stdin", StringIO(json.dumps(payload))):
            with patch("sys.stderr", stderr_capture):
                with patch.object(mod, "record_evidence", side_effect=_record):
                    try:
                        mod.main()
                    except SystemExit as exc:
                        exit_code = exc.code

        return exit_code, stderr_capture.getvalue(), evidence_calls

    def test_nonzero_exit_code_is_recorded_as_failure(self):
        payload = {
            "tool_input": {"command": "pytest tests/"},
            "tool_output": {"stdout": "", "stderr": "", "exit_code": 1},
        }
        code, stderr, calls = self._run_main(payload)

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(calls, [("pytest tests/", "fail")])

    def test_tool_result_payload_is_supported(self):
        payload = {
            "tool_input": {"command": "pytest tests/"},
            "tool_result": {"stdout": "5 passed", "stderr": "", "exit_code": 0},
        }
        code, stderr, calls = self._run_main(payload)

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(calls, [("pytest tests/", "pass")])


if __name__ == "__main__":
    unittest.main()
