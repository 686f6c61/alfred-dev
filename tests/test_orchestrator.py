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
    load_state, save_state, get_effective_agents,
    run_flow, _validate_equipo_sesion, _KNOWN_OPTIONAL_AGENTS,
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
        session = create_session("feature", "Sistema de autenticación")
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
        """Las gates automáticas bloquean si los tests no pasan."""
        session = create_session("feature", "Test")
        # Avanzar a fase de desarrollo (gate automática)
        session = advance_phase(session)  # producto -> arquitectura
        session = advance_phase(session)  # arquitectura -> desarrollo
        result = check_gate(session, resultado="aprobado", tests_ok=False)
        self.assertFalse(result["passed"])
        self.assertIn("tests", result["reason"].lower())

    def test_automatic_gate_passes_when_tests_ok(self):
        """Las gates automáticas dejan pasar si tests y resultado OK."""
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
        # Fase de calidad: gate automático+seguridad
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
        session = create_session("spike", "Investigación")
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        session = advance_phase(session, resultado="aprobado", artefactos=[])
        self.assertEqual(session["fase_actual"], "completado")


# --- Fixture compartida para equipo_sesion ---
# Representa un equipo de sesión válido con composición dinámica.
# Se usa como referencia en los tests de validación y run_flow.
VALID_EQUIPO_SESION = {
    "opcionales_activos": {
        "data-engineer": True,
        "ux-reviewer": False,
        "performance-engineer": False,
        "github-manager": True,
        "seo-specialist": False,
        "copywriter": False,
        "librarian": False,
    },
    "infra": {
        "memoria": True,
        "gui": False,
    },
    "fuente": "composicion_dinamica",
}


class TestValidateEquipoSesion(unittest.TestCase):
    """Validación de la estructura del equipo de sesión."""

    def test_tc20_dict_valido_completo(self):
        """TC-20: un dict válido completo devuelve True."""
        self.assertTrue(_validate_equipo_sesion(VALID_EQUIPO_SESION))

    def test_tc21_dict_vacio(self):
        """TC-21: un dict vacío devuelve False."""
        self.assertFalse(_validate_equipo_sesion({}))

    def test_tc22_agente_extra_en_opcionales_acepta_con_aviso(self):
        """TC-22: un agente extra se acepta (True) pero emite aviso a stderr."""
        import copy
        import io
        malo = copy.deepcopy(VALID_EQUIPO_SESION)
        malo["opcionales_activos"]["agente-inventado"] = True
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            result = _validate_equipo_sesion(malo)
        finally:
            sys.stderr = old_stderr
        self.assertTrue(result)
        self.assertIn("agente-inventado", captured.getvalue())

    def test_tc22b_agente_faltante_en_opcionales_falla(self):
        """TC-22b: si falta un agente conocido, devuelve False."""
        import copy
        malo = copy.deepcopy(VALID_EQUIPO_SESION)
        del malo["opcionales_activos"]["data-engineer"]
        self.assertFalse(_validate_equipo_sesion(malo))

    def test_tc23_valor_no_bool_en_opcionales(self):
        """TC-23: un valor no booleano en opcionales devuelve False."""
        import copy
        malo = copy.deepcopy(VALID_EQUIPO_SESION)
        malo["opcionales_activos"]["data-engineer"] = "si"
        self.assertFalse(_validate_equipo_sesion(malo))


class TestRunFlow(unittest.TestCase):
    """Tests para la función run_flow de creación de sesión con equipo."""

    def test_tc15_sin_equipo_sesion(self):
        """TC-15: run_flow sin equipo_sesion crea sesión con equipo_sesion=None."""
        session = run_flow("feature", "Nueva funcionalidad")
        self.assertIn("equipo_sesion", session)
        self.assertIsNone(session["equipo_sesion"])
        self.assertIsNone(session["equipo_sesion_error"])

    def test_tc16_con_equipo_sesion_valido(self):
        """TC-16: run_flow con equipo_sesion válido lo inyecta en la sesión."""
        session = run_flow("feature", "Nueva funcionalidad", equipo_sesion=VALID_EQUIPO_SESION)
        self.assertEqual(session["equipo_sesion"], VALID_EQUIPO_SESION)
        self.assertIsNone(session["equipo_sesion_error"])

    def test_tc17_equipo_sesion_invalido_cae_a_none_con_error(self):
        """TC-17: run_flow con equipo_sesion inválido cae a None y registra motivo."""
        import io
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            session = run_flow("feature", "Test", equipo_sesion={"malo": True})
        finally:
            sys.stderr = old_stderr
        self.assertIsNone(session["equipo_sesion"])
        self.assertIn("Alfred Dev", captured.getvalue())
        # Verifica que el motivo del descarte se registra en la sesión
        self.assertIsNotNone(session["equipo_sesion_error"])
        self.assertIn("no pasó la validación", session["equipo_sesion_error"])

    def test_tc18_comando_desconocido_lanza_valueerror(self):
        """TC-18: run_flow con comando desconocido lanza ValueError."""
        with self.assertRaises(ValueError):
            run_flow("inventado", "No existe")

    def test_tc19_integracion_extremo_a_extremo(self):
        """TC-19: run_flow -> extraer opcionales -> get_effective_agents."""
        session = run_flow("feature", "Nuevo módulo", equipo_sesion=VALID_EQUIPO_SESION)
        opcionales = session["equipo_sesion"]["opcionales_activos"]
        effective = get_effective_agents("arquitectura", opcionales)
        # data-engineer está activo y participa en "arquitectura" en paralelo
        self.assertIn("data-engineer", effective["paralelo"])
        # github-manager está activo pero no participa en "arquitectura"
        self.assertNotIn("github-manager", effective["paralelo"])
        self.assertNotIn("github-manager", effective["secuencial"])

    def test_tc24_retrocompatibilidad_get_effective_agents_con_none(self):
        """TC-24: get_effective_agents(fase, None) sigue funcionando."""
        result = get_effective_agents("calidad", None)
        self.assertEqual(result, {"paralelo": [], "secuencial": []})


if __name__ == "__main__":
    unittest.main()
