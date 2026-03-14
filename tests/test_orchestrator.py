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
    should_retry_phase, reset_phase_iterations,
    is_autopilot_gate_passable, run_flow_autopilot,
    MAX_PHASE_ITERATIONS,
)


class TestFlows(unittest.TestCase):
    def test_feature_flow_has_6_phases(self):
        self.assertEqual(len(FLOWS["feature"]["fases"]), 6)

    def test_fix_flow_has_3_phases(self):
        self.assertEqual(len(FLOWS["fix"]["fases"]), 3)

    def test_all_flows_defined(self):
        expected = {"feature", "fix", "spike", "ship", "audit"}
        self.assertEqual(set(FLOWS.keys()), expected)

    def test_architecture_gate_is_usuario_seguridad(self):
        """La fase de arquitectura debe tener gate usuario+seguridad."""
        fase_arq = FLOWS["feature"]["fases"][1]
        self.assertEqual(fase_arq["nombre"], "arquitectura")
        self.assertEqual(fase_arq["gate_tipo"], "usuario+seguridad")


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
        "performance-engineer": False,
        "github-manager": True,
        "librarian": False,
        "ux-reviewer": False,
        "seo-specialist": False,
        "copywriter": False,
        "i18n-specialist": False,
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


class TestLoopIterativo(unittest.TestCase):
    """Tests para el loop iterativo dentro de fases (v0.4.0)."""

    def test_should_retry_when_gate_fails(self):
        """Si la gate falla y hay iteraciones, recomienda retry."""
        session = create_session("feature", "Test loop")
        # Fase 0 = producto, gate_tipo = usuario
        result = should_retry_phase(session, resultado="rechazado")
        self.assertEqual(result["action"], "retry")
        self.assertEqual(result["iteration"], 1)

    def test_should_advance_when_gate_passes(self):
        """Si la gate se supera, recomienda avanzar."""
        session = create_session("feature", "Test loop")
        result = should_retry_phase(session, resultado="aprobado")
        self.assertEqual(result["action"], "advance")

    def test_should_escalate_after_max_iterations(self):
        """Al agotar iteraciones, recomienda escalar al usuario."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = MAX_PHASE_ITERATIONS
        result = should_retry_phase(session, resultado="rechazado")
        self.assertEqual(result["action"], "escalate")

    def test_iteration_counter_increments(self):
        """El contador de iteraciones se incrementa con cada retry."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = 0
        should_retry_phase(session, resultado="rechazado")
        self.assertEqual(session["iteraciones_fase"], 1)
        should_retry_phase(session, resultado="rechazado")
        self.assertEqual(session["iteraciones_fase"], 2)

    def test_reset_phase_iterations(self):
        """El reset pone el contador a 0."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = 3
        reset_phase_iterations(session)
        self.assertEqual(session["iteraciones_fase"], 0)

    def test_advance_phase_resets_iterations(self):
        """Avanzar de fase reinicia el contador automaticamente."""
        session = create_session("feature", "Test loop")
        session["iteraciones_fase"] = 3
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session.get("iteraciones_fase", 0), 0)

    def test_advance_phase_preserves_iterations(self):
        """advance_phase guarda el contador de iteraciones en la fase completada."""
        session = create_session("feature", "Test iteraciones")
        session["iteraciones_fase"] = 3
        session = advance_phase(session, resultado="aprobado")
        fase_completada = session["fases_completadas"][-1]
        self.assertEqual(fase_completada["iteraciones"], 3)


class TestAutopilot(unittest.TestCase):
    """Tests para el modo autopilot (v0.4.0)."""

    def test_run_flow_autopilot_creates_session(self):
        """El modo autopilot crea una sesion con el flag activo."""
        session = run_flow_autopilot("feature", "Login automatico")
        self.assertTrue(session["autopilot"])
        self.assertEqual(session["iteraciones_fase"], 0)
        self.assertEqual(session["max_iteraciones_fase"], MAX_PHASE_ITERATIONS)

    def test_autopilot_approves_user_gates(self):
        """En autopilot, las gates de usuario se aprueban automaticamente."""
        session = create_session("feature", "Test autopilot")
        # Fase 0 = producto, gate_tipo = usuario
        result = is_autopilot_gate_passable(session)
        self.assertTrue(result["passed"])
        self.assertIn("autopilot", result["reason"])

    def test_autopilot_evaluates_automatic_gates(self):
        """En autopilot, las gates automaticas se evaluan normalmente."""
        session = create_session("feature", "Test autopilot")
        # Avanzar a fase 2 = desarrollo, gate_tipo = automatico
        session = advance_phase(session, resultado="aprobado")  # producto -> arquitectura
        session = advance_phase(session, resultado="aprobado")  # arquitectura -> desarrollo
        result = is_autopilot_gate_passable(session, tests_ok=False)
        self.assertFalse(result["passed"])

    def test_autopilot_evaluates_security_gates(self):
        """En autopilot, las gates de seguridad se evaluan normalmente."""
        session = create_session("feature", "Test autopilot")
        session = advance_phase(session, resultado="aprobado")  # producto -> arquitectura
        session = advance_phase(session, resultado="aprobado")  # arquitectura -> desarrollo
        session = advance_phase(session, resultado="aprobado", tests_ok=True)  # desarrollo -> calidad
        # Fase 3 = calidad, gate_tipo = automatico+seguridad
        result = is_autopilot_gate_passable(session, security_ok=False)
        self.assertFalse(result["passed"])

    def test_autopilot_invalid_command(self):
        """Autopilot con comando invalido lanza ValueError."""
        with self.assertRaises(ValueError):
            run_flow_autopilot("inexistente", "Test")

    def test_autopilot_gate_completed_session(self):
        """is_autopilot_gate_passable no falla con sesion completada."""
        session = create_session("spike", "Test")
        session = advance_phase(session, resultado="aprobado")
        session = advance_phase(session, resultado="aprobado")
        # Ahora fase_actual == "completado"
        result = is_autopilot_gate_passable(session)
        self.assertTrue(result["passed"])

    def test_autopilot_usuario_seguridad_auto_approves_user_part(self):
        """En autopilot, GATE_USUARIO_SEGURIDAD aprueba la parte de usuario
        pero evalua la de seguridad. Test de documentacion del comportamiento."""
        session = create_session("feature", "Test autopilot")
        session = advance_phase(session, resultado="aprobado")  # producto -> arquitectura
        # Ahora en fase arquitectura con gate GATE_USUARIO_SEGURIDAD
        # Con seguridad OK: debe pasar
        result = is_autopilot_gate_passable(session, security_ok=True)
        self.assertTrue(result["passed"])
        # Con seguridad KO: debe fallar
        result = is_autopilot_gate_passable(session, security_ok=False)
        self.assertFalse(result["passed"])


class TestCompletedSessionGuards(unittest.TestCase):
    """Verifica que check_gate no lanza IndexError con sesiones completadas."""

    def test_check_gate_completed_session(self):
        """check_gate devuelve passed=True para sesiones completadas."""
        session = create_session("spike", "Investigacion")
        session = advance_phase(session, resultado="aprobado")
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "completado")
        result = check_gate(session, resultado="aprobado")
        self.assertTrue(result["passed"])

    def test_check_gate_overflowed_fase_numero(self):
        """check_gate no falla si fase_numero excede el array de fases."""
        session = create_session("spike", "Test")
        session["fase_numero"] = 999
        result = check_gate(session, resultado="aprobado")
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
