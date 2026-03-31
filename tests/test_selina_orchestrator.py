#!/usr/bin/env python3
"""Tests para las funciones del orquestador de Selina (la estilista)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config_loader import has_frontend
from core.orchestrator import (
    FLOWS, create_session, advance_phase, check_gate,
)


class TestHasFrontend(unittest.TestCase):
    """Verifica que has_frontend identifique correctamente frameworks con UI."""

    # --- Frameworks con interfaz de usuario (deben devolver True) ---

    def test_next(self):
        stack = {"framework": "next", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    def test_react(self):
        stack = {"framework": "react", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    def test_vue(self):
        stack = {"framework": "vue", "runtime": "node", "lenguaje": "javascript"}
        self.assertTrue(has_frontend(stack))

    def test_svelte(self):
        stack = {"framework": "svelte", "runtime": "node", "lenguaje": "javascript"}
        self.assertTrue(has_frontend(stack))

    def test_astro(self):
        stack = {"framework": "astro", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    def test_angular(self):
        stack = {"framework": "angular", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    def test_remix(self):
        stack = {"framework": "remix", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    def test_gatsby(self):
        stack = {"framework": "gatsby", "runtime": "node", "lenguaje": "javascript"}
        self.assertTrue(has_frontend(stack))

    def test_nuxt(self):
        stack = {"framework": "nuxt", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    def test_solid_js(self):
        stack = {"framework": "solid-js", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    def test_qwik(self):
        stack = {"framework": "qwik", "runtime": "node", "lenguaje": "typescript"}
        self.assertTrue(has_frontend(stack))

    # --- Frameworks sin interfaz de usuario (deben devolver False) ---

    def test_fastapi(self):
        stack = {"framework": "fastapi", "runtime": "python", "lenguaje": "python"}
        self.assertFalse(has_frontend(stack))

    def test_express(self):
        stack = {"framework": "express", "runtime": "node", "lenguaje": "javascript"}
        self.assertFalse(has_frontend(stack))

    def test_django(self):
        stack = {"framework": "django", "runtime": "python", "lenguaje": "python"}
        self.assertFalse(has_frontend(stack))

    def test_desconocido(self):
        stack = {"framework": "desconocido", "runtime": "node", "lenguaje": "javascript"}
        self.assertFalse(has_frontend(stack))

    def test_sin_framework(self):
        """Un stack sin clave 'framework' debe devolver False (valor por defecto)."""
        stack = {"runtime": "node", "lenguaje": "javascript"}
        self.assertFalse(has_frontend(stack))


class TestSelinaPhase(unittest.TestCase):
    """Verifica que la fase estilo_visual esta correctamente integrada."""

    def test_feature_flow_has_7_phases(self):
        self.assertEqual(len(FLOWS["feature"]["fases"]), 7)

    def test_estilo_visual_is_phase_1(self):
        fase = FLOWS["feature"]["fases"][1]
        self.assertEqual(fase["nombre"], "estilo_visual")

    def test_estilo_visual_uses_selina(self):
        fase = FLOWS["feature"]["fases"][1]
        self.assertEqual(fase["agentes"], ["selina"])

    def test_estilo_visual_gate_is_usuario(self):
        fase = FLOWS["feature"]["fases"][1]
        self.assertEqual(fase["gate_tipo"], "usuario")

    def test_estilo_visual_has_condicion(self):
        fase = FLOWS["feature"]["fases"][1]
        self.assertEqual(fase.get("condicion"), "tiene_frontend")

    def test_arquitectura_is_now_phase_2(self):
        fase = FLOWS["feature"]["fases"][2]
        self.assertEqual(fase["nombre"], "arquitectura")

    def test_fix_flow_unchanged(self):
        self.assertEqual(len(FLOWS["fix"]["fases"]), 3)

    def test_quick_flow_unchanged(self):
        self.assertEqual(len(FLOWS["quick"]["fases"]), 2)

    def test_session_starts_at_producto(self):
        session = create_session("feature", "App con frontend")
        self.assertEqual(session["fase_actual"], "producto")

    def test_advance_from_producto_goes_to_estilo_visual(self):
        session = create_session("feature", "App con frontend")
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "estilo_visual")

    def test_advance_from_estilo_visual_goes_to_arquitectura(self):
        session = create_session("feature", "App con frontend")
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "estilo_visual")
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "arquitectura")


class TestSelinaFullFlow(unittest.TestCase):
    """Verifica el flujo completo feature con Selina."""

    def test_full_feature_flow_with_selina(self):
        """Recorrer las 7 fases del flujo feature."""
        session = create_session("feature", "App con dashboard")

        # Fase 0: producto
        self.assertEqual(session["fase_actual"], "producto")
        session = advance_phase(session, resultado="aprobado")

        # Fase 1: estilo_visual
        self.assertEqual(session["fase_actual"], "estilo_visual")
        session = advance_phase(session, resultado="aprobado")

        # Fase 2: arquitectura
        self.assertEqual(session["fase_actual"], "arquitectura")
        session = advance_phase(session, resultado="aprobado", security_ok=True)

        # Fase 3: desarrollo
        self.assertEqual(session["fase_actual"], "desarrollo")
        session = advance_phase(session, resultado="aprobado", tests_ok=True)

        # Fase 4: calidad
        self.assertEqual(session["fase_actual"], "calidad")
        session = advance_phase(
            session, resultado="aprobado", security_ok=True, tests_ok=True,
        )

        # Fase 5: documentacion
        self.assertEqual(session["fase_actual"], "documentacion")
        session = advance_phase(session, resultado="aprobado")

        # Fase 6: entrega
        self.assertEqual(session["fase_actual"], "entrega")
        session = advance_phase(session, resultado="aprobado", security_ok=True)

        # Completado
        self.assertEqual(session["fase_actual"], "completado")
        self.assertEqual(len(session["fases_completadas"]), 7)

    def test_estilo_visual_gate_rejects_without_approval(self):
        """La gate de estilo_visual rechaza sin aprobacion."""
        session = create_session("feature", "App con UI")
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "estilo_visual")

        result = check_gate(session, resultado="rechazado")
        self.assertFalse(result["passed"])


class TestSelinaSkippedWhenNoFrontend(unittest.TestCase):
    """Verifica que estilo_visual se salta en proyectos sin frontend."""

    def test_skip_estilo_visual_when_no_frontend(self):
        """Con stack sin frontend, estilo_visual se salta."""
        session = create_session("feature", "API backend")
        session["stack"] = {"framework": "fastapi", "runtime": "python", "lenguaje": "python"}
        session = advance_phase(session, resultado="aprobado")  # producto -> debe saltar estilo_visual
        self.assertEqual(session["fase_actual"], "arquitectura")
        # Verificar que estilo_visual se registro como saltada
        skipped = [f for f in session["fases_completadas"] if f["nombre"] == "estilo_visual"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["resultado"], "saltada")

    def test_estilo_visual_executes_when_frontend(self):
        """Con stack con frontend, estilo_visual se ejecuta normalmente."""
        session = create_session("feature", "App Next.js")
        session["stack"] = {"framework": "next", "runtime": "node", "lenguaje": "typescript"}
        session = advance_phase(session, resultado="aprobado")  # producto -> estilo_visual
        self.assertEqual(session["fase_actual"], "estilo_visual")

    def test_skip_when_no_stack_in_session(self):
        """Sin stack en sesion, la condicion no se evalua y la fase se ejecuta."""
        session = create_session("feature", "Proyecto nuevo")
        # Sin stack: la condicion no puede evaluarse, asi que la fase se ejecuta
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "estilo_visual")


if __name__ == "__main__":
    unittest.main()
