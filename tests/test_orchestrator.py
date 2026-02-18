#!/usr/bin/env python3
"""Tests para el orquestador de flujos."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.orchestrator import (
    FLOWS, create_session, advance_phase, check_gate,
    load_state, save_state,
)


class TestFlows(unittest.TestCase):
    def test_feature_flow_has_6_phases(self):
        self.assertEqual(len(FLOWS["feature"]["fases"]), 6)

    def test_fix_flow_has_3_phases(self):
        self.assertEqual(len(FLOWS["fix"]["fases"]), 3)

    def test_all_flows_defined(self):
        expected = {"feature", "fix", "spike", "ship", "audit"}
        self.assertEqual(set(FLOWS.keys()), expected)


class TestSession(unittest.TestCase):
    def test_create_session(self):
        session = create_session("feature", "Sistema de autenticacion")
        self.assertEqual(session["comando"], "feature")
        self.assertEqual(session["fase_actual"], "producto")
        self.assertEqual(session["fase_numero"], 0)
        self.assertEqual(len(session["fases_completadas"]), 0)

    def test_save_and_load_state(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_path = f.name
        try:
            session = create_session("fix", "Bug en login")
            save_state(session, state_path)
            loaded = load_state(state_path)
            self.assertEqual(loaded["comando"], "fix")
            self.assertEqual(loaded["descripcion"], "Bug en login")
        finally:
            os.unlink(state_path)


class TestGates(unittest.TestCase):
    def test_gate_passes_with_correct_result(self):
        session = create_session("feature", "Test feature")
        result = check_gate(session, resultado="aprobado")
        self.assertTrue(result["passed"])

    def test_gate_fails_with_incorrect_result(self):
        session = create_session("feature", "Test feature")
        result = check_gate(session, resultado="rechazado")
        self.assertFalse(result["passed"])

    def test_automatic_gate_fails_when_tests_fail(self):
        """Las gates automaticas bloquean si los tests no pasan."""
        session = create_session("feature", "Test")
        # Avanzar a fase de desarrollo (gate automatica)
        session = advance_phase(session)  # producto -> arquitectura
        session = advance_phase(session)  # arquitectura -> desarrollo
        result = check_gate(session, resultado="aprobado", tests_ok=False)
        self.assertFalse(result["passed"])
        self.assertIn("tests", result["reason"].lower())

    def test_automatic_gate_passes_when_tests_ok(self):
        """Las gates automaticas dejan pasar si tests y resultado OK."""
        session = create_session("feature", "Test")
        session = advance_phase(session)  # producto
        session = advance_phase(session)  # arquitectura
        result = check_gate(session, resultado="aprobado", tests_ok=True)
        self.assertTrue(result["passed"])

    def test_security_gate_fails_when_security_fails(self):
        """Las gates con seguridad bloquean si security_ok es False."""
        session = create_session("feature", "Test")
        session = advance_phase(session)  # producto
        session = advance_phase(session)  # arquitectura
        session = advance_phase(session)  # desarrollo
        # Fase de calidad: gate automatico+seguridad
        result = check_gate(session, resultado="aprobado", security_ok=False)
        self.assertFalse(result["passed"])
        self.assertIn("seguridad", result["reason"].lower())

    def test_advance_phase_propagates_tests_ok(self):
        """advance_phase propaga tests_ok a check_gate."""
        session = create_session("feature", "Test")
        session = advance_phase(session)  # producto
        session = advance_phase(session)  # arquitectura
        # Intentar avanzar desarrollo con tests rojos
        with self.assertRaises(RuntimeError):
            advance_phase(session, resultado="aprobado", tests_ok=False)


class TestAdvancePhase(unittest.TestCase):
    def test_advance_moves_to_next_phase(self):
        session = create_session("feature", "Test")
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        self.assertEqual(session["fase_actual"], "arquitectura")
        self.assertEqual(session["fase_numero"], 1)
        self.assertEqual(len(session["fases_completadas"]), 1)

    def test_cannot_advance_past_last_phase(self):
        session = create_session("spike", "Investigacion")
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        self.assertEqual(session["fase_actual"], "completado")


if __name__ == "__main__":
    unittest.main()
