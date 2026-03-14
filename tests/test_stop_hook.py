#!/usr/bin/env python3
"""Tests para el hook stop-hook.py (patron ralph-loop).

Estos tests verifican la logica de decision del hook: cuando bloquea
la parada de Claude y cuando la permite. No ejecutan el hook como
proceso externo, sino que importan la logica de core/orchestrator.py
y simulan el estado de sesion.
"""

import json
import os
import sys
import tempfile
import unittest

# Anadir la raiz del plugin al path para importar core
_plugin_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _plugin_root)

from core.orchestrator import FLOWS, create_session, load_state, save_state

import importlib.util

_hooks_dir = os.path.join(_plugin_root, "hooks")
if _hooks_dir not in sys.path:
    sys.path.insert(0, _hooks_dir)

_stop_hook_path = os.path.join(_hooks_dir, "stop-hook.py")
_spec = importlib.util.spec_from_file_location("stop_hook", _stop_hook_path)
stop_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stop_hook)


class TestStopHookLogic(unittest.TestCase):
    """Verifica la logica de bloqueo del hook de Stop."""

    def setUp(self):
        """Crea un directorio temporal para los ficheros de estado."""
        self.tmpdir = tempfile.mkdtemp()
        self.state_path = os.path.join(self.tmpdir, "alfred-dev-state.json")

    def tearDown(self):
        """Limpia el directorio temporal."""
        if os.path.exists(self.state_path):
            os.unlink(self.state_path)
        os.rmdir(self.tmpdir)

    def test_no_state_file_allows_stop(self):
        """Sin fichero de estado, no hay sesion activa."""
        session = load_state(self.state_path)
        self.assertIsNone(session)

    def test_completed_session_allows_stop(self):
        """Una sesion completada no bloquea la parada."""
        session = create_session("feature", "Test feature")
        session["fase_actual"] = "completado"
        save_state(session, self.state_path)

        loaded = load_state(self.state_path)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["fase_actual"], "completado")

    def test_active_session_should_block(self):
        """Una sesion activa en una fase intermedia deberia bloquear."""
        session = create_session("feature", "Test feature")
        save_state(session, self.state_path)

        loaded = load_state(self.state_path)
        self.assertIsNotNone(loaded)
        self.assertNotEqual(loaded["fase_actual"], "completado")
        # Verificar que tiene informacion suficiente para construir el bloqueo
        self.assertIn(loaded["comando"], FLOWS)

    def test_fix_session_blocks_on_diagnostico(self):
        """Un fix en fase de diagnostico bloquea."""
        session = create_session("fix", "Bug critico")
        save_state(session, self.state_path)

        loaded = load_state(self.state_path)
        self.assertEqual(loaded["fase_actual"], "diagnostico")
        self.assertEqual(loaded["comando"], "fix")

    def test_spike_session_blocks_on_exploracion(self):
        """Un spike en fase de exploracion bloquea."""
        session = create_session("spike", "Investigar opciones")
        save_state(session, self.state_path)

        loaded = load_state(self.state_path)
        self.assertEqual(loaded["fase_actual"], "exploracion")

    def test_corrupted_state_allows_stop(self):
        """Un fichero de estado corrupto (JSON invalido) permite parar."""
        with open(self.state_path, "w") as f:
            f.write("{corrupted json!!")

        loaded = load_state(self.state_path)
        self.assertIsNone(loaded)

    def test_invalid_structure_allows_stop(self):
        """Un estado con estructura invalida (sin claves obligatorias) permite parar."""
        with open(self.state_path, "w") as f:
            json.dump({"random": "data"}, f)

        loaded = load_state(self.state_path)
        self.assertIsNone(loaded)

    def test_unknown_flow_allows_stop(self):
        """Un estado con un flujo desconocido no deberia causar excepcion."""
        session = {
            "comando": "flujo_inventado",
            "fase_actual": "fase_x",
            "fase_numero": 0,
            "fases_completadas": [],
            "artefactos": [],
        }
        save_state(session, self.state_path)

        loaded = load_state(self.state_path)
        self.assertIsNotNone(loaded)
        # El hook verificaria que el flujo existe en FLOWS y, al no existir,
        # permitiria la parada. Aqui verificamos que load_state no falla.
        self.assertNotIn(loaded["comando"], FLOWS)


class TestShouldBlock(unittest.TestCase):
    """Verifica la funcion should_block."""

    def test_completed_session_does_not_block(self):
        session = create_session("feature", "Test")
        session["fase_actual"] = "completado"
        flow = FLOWS["feature"]
        self.assertFalse(stop_hook.should_block(session, flow))

    def test_active_session_blocks(self):
        session = create_session("feature", "Test")
        flow = FLOWS["feature"]
        self.assertTrue(stop_hook.should_block(session, flow))

    def test_incoherent_fase_numero_does_not_block(self):
        session = create_session("feature", "Test")
        session["fase_numero"] = 999
        flow = FLOWS["feature"]
        self.assertFalse(stop_hook.should_block(session, flow))


class TestBuildBlockMessage(unittest.TestCase):
    """Verifica la construccion del mensaje de bloqueo."""

    def _make_fase(self, gate_tipo="usuario"):
        return {
            "nombre": "producto",
            "agentes": ["product-owner"],
            "descripcion": "Fase de prueba",
            "gate_tipo": gate_tipo,
        }

    def test_interactive_user_gate_asks_for_approval(self):
        """En modo interactivo, la gate de usuario pide confirmacion."""
        session = create_session("feature", "Test")
        fase = self._make_fase("usuario")
        msg = stop_hook.build_block_message(session, fase, "usuario")
        self.assertIn("aprobacion del usuario", msg.lower())
        self.assertNotIn("autopilot", msg.lower())

    def test_autopilot_user_gate_does_not_ask_for_approval(self):
        """En autopilot, la gate de usuario no pide confirmacion."""
        session = create_session("feature", "Test")
        session["autopilot"] = True
        fase = self._make_fase("usuario")
        msg = stop_hook.build_block_message(session, fase, "usuario")
        self.assertIn("autopilot", msg.lower())
        self.assertNotIn("aprobacion del usuario", msg.lower())

    def test_automatic_gate_mentions_tests(self):
        """La gate automatica menciona tests."""
        session = create_session("feature", "Test")
        fase = self._make_fase("automatico")
        msg = stop_hook.build_block_message(session, fase, "automatico")
        self.assertIn("tests", msg.lower())


class TestHandleSessionReport(unittest.TestCase):
    """Verifica la generacion de informes desde el stop-hook."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generates_complete_report(self):
        """Una sesion completada genera informe normal."""
        session = {
            "comando": "feature",
            "descripcion": "Login",
            "fase_actual": "completado",
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado"},
            ],
            "artefactos": [],
            "creado_en": "2026-03-14T10:00:00+00:00",
            "actualizado_en": "2026-03-14T10:30:00+00:00",
        }
        stop_hook.handle_session_report(session, self.tmpdir, completed=True)
        report_dir = os.path.join(self.tmpdir, "docs", "alfred-reports")
        self.assertTrue(os.path.isdir(report_dir))
        reports = os.listdir(report_dir)
        self.assertEqual(len(reports), 1)
        with open(os.path.join(report_dir, reports[0])) as f:
            content = f.read()
        self.assertIn("Informe de sesion", content)

    def test_generates_partial_report(self):
        """Una sesion parcial genera informe."""
        session = {
            "comando": "feature",
            "descripcion": "Login",
            "fase_actual": "desarrollo",
            "fase_numero": 2,
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado"},
            ],
            "artefactos": [],
            "creado_en": "2026-03-14T10:00:00+00:00",
            "actualizado_en": "2026-03-14T10:30:00+00:00",
        }
        stop_hook.handle_session_report(session, self.tmpdir, completed=False)
        report_dir = os.path.join(self.tmpdir, "docs", "alfred-reports")
        self.assertTrue(os.path.isdir(report_dir))
        reports = os.listdir(report_dir)
        self.assertEqual(len(reports), 1)


if __name__ == "__main__":
    unittest.main()
