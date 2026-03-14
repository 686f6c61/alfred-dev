#!/usr/bin/env python3
"""
Tests para el hook quality-gate.py.

La logica de deteccion de comandos y resultados esta cubierta por
``test_evidence_guard.py``. Aqui se verifica unicamente que el hook
importa correctamente desde ``evidence_guard_lib`` (fuente unica de verdad)
y que su logica de flujo principal funciona como se espera.
"""

import importlib.util
import json
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Rutas base para importar modulos con guion en el nombre
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_HOOKS_DIR = os.path.join(_TESTS_DIR, "..", "hooks")
_HOOK_PATH = os.path.join(_HOOKS_DIR, "quality-gate.py")


def _load_quality_gate():
    """Carga el modulo quality-gate.py mediante importlib."""
    spec = importlib.util.spec_from_file_location("quality_gate", _HOOK_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestQualityGateImports(unittest.TestCase):
    """Verifica que quality-gate reutiliza las funciones de evidence_guard_lib."""

    def test_quality_gate_uses_evidence_guard_lib(self):
        """quality-gate debe usar las funciones de evidence_guard_lib."""
        qg = _load_quality_gate()
        # Debe usar la misma funcion que evidence_guard_lib
        sys.path.insert(0, _HOOKS_DIR)
        from evidence_guard_lib import is_test_command as lib_fn
        self.assertIs(qg.is_test_command, lib_fn)


class TestQualityGateMain(unittest.TestCase):
    """Verifica el flujo de main() ante distintas entradas."""

    def _run_main(self, payload: dict) -> tuple[int, str]:
        """Ejecuta main() con el payload dado y devuelve (exit_code, stderr)."""
        qg = _load_quality_gate()
        stdin_data = json.dumps(payload)
        stderr_capture = StringIO()

        exit_code = None
        with patch("sys.stdin", StringIO(stdin_data)):
            with patch("sys.stderr", stderr_capture):
                try:
                    qg.main()
                except SystemExit as exc:
                    exit_code = exc.code

        return exit_code, stderr_capture.getvalue()

    def test_non_test_command_exits_0_silently(self):
        """Comandos que no son runners de tests no emiten nada por stderr."""
        payload = {
            "tool_input": {"command": "ls -la"},
            "tool_output": {"stdout": "", "stderr": ""},
        }
        code, stderr = self._run_main(payload)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

    def test_passing_tests_exits_0_silently(self):
        """Tests que pasan no emiten aviso."""
        payload = {
            "tool_input": {"command": "pytest tests/"},
            "tool_output": {"stdout": "5 passed in 0.12s", "stderr": ""},
        }
        code, stderr = self._run_main(payload)
        self.assertEqual(code, 0)
        self.assertNotIn("Rompe-cosas", stderr)

    def test_failing_tests_emits_warning(self):
        """Tests fallidos emiten el aviso de El Rompe-cosas por stderr."""
        payload = {
            "tool_input": {"command": "pytest tests/"},
            "tool_output": {"stdout": "1 failed, 4 passed in 0.15s", "stderr": ""},
        }
        code, stderr = self._run_main(payload)
        self.assertEqual(code, 0)
        self.assertIn("Rompe-cosas", stderr)

    def test_invalid_json_exits_0_with_warning(self):
        """Entrada JSON invalida emite aviso pero no bloquea (exit 0)."""
        qg = _load_quality_gate()
        stderr_capture = StringIO()
        exit_code = None
        with patch("sys.stdin", StringIO("esto no es json")):
            with patch("sys.stderr", stderr_capture):
                try:
                    qg.main()
                except SystemExit as exc:
                    exit_code = exc.code
        self.assertEqual(exit_code, 0)
        self.assertIn("quality-gate", stderr_capture.getvalue())


if __name__ == "__main__":
    unittest.main()
