#!/usr/bin/env python3
"""Tests para el servidor GUI de Alfred Dev.

Verifica el correcto funcionamiento del servidor HTTP estatico, el watcher
de SQLite que detecta cambios incrementales y el procesamiento de acciones
del dashboard. Cada test crea una base de datos temporal para garantizar
aislamiento total entre pruebas.
"""

import asyncio
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory import MemoryDB


class TestGUIServerHTTP(unittest.TestCase):
    """Tests del servidor HTTP estatico."""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.db = MemoryDB(self.tmp_db.name)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp_db.name)

    def test_import_server_module(self):
        """El modulo gui.server se puede importar sin errores."""
        from gui.server import GUIServer
        server = GUIServer(self.tmp_db.name, http_port=0, ws_port=0)
        self.assertIsNotNone(server)

    def test_server_finds_dashboard(self):
        """El servidor localiza dashboard.html relativo a su ubicacion."""
        from gui.server import GUIServer
        server = GUIServer(self.tmp_db.name, http_port=0, ws_port=0)
        self.assertTrue(os.path.isfile(server.dashboard_path))


class TestGUIServerWatcher(unittest.TestCase):
    """Tests del SQLite watcher."""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.db = MemoryDB(self.tmp_db.name)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp_db.name)

    def test_detect_new_events(self):
        """El watcher detecta eventos nuevos desde un checkpoint."""
        from gui.server import GUIServer
        server = GUIServer(self.tmp_db.name, http_port=0, ws_port=0)

        iter_id = self.db.start_iteration("feature", "Test")
        self.db.log_event("phase_started", payload={"fase": "analisis"}, iteration_id=iter_id)

        new_events = server.poll_new_events()
        self.assertGreater(len(new_events), 0)

    def test_checkpoint_advances(self):
        """Despues de poll, el checkpoint avanza y no repite eventos."""
        from gui.server import GUIServer
        server = GUIServer(self.tmp_db.name, http_port=0, ws_port=0)

        iter_id = self.db.start_iteration("feature", "Test")
        self.db.log_event("test_event", payload={}, iteration_id=iter_id)

        first = server.poll_new_events()
        second = server.poll_new_events()
        self.assertGreater(len(first), 0)
        self.assertEqual(len(second), 0)

    def test_get_full_state(self):
        """get_full_state devuelve el estado completo para init."""
        from gui.server import GUIServer
        server = GUIServer(self.tmp_db.name, http_port=0, ws_port=0)

        iter_id = self.db.start_iteration("feature", "Dashboard")
        self.db.log_decision(
            title="Test decision",
            chosen="Opcion A",
            iteration_id=iter_id,
        )

        state = server.get_full_state()
        self.assertIn("iteration", state)
        self.assertIn("decisions", state)
        self.assertIn("events", state)
        self.assertIn("pinned", state)

    def test_process_gui_action(self):
        """Las acciones de la GUI se escriben en SQLite."""
        from gui.server import GUIServer
        server = GUIServer(self.tmp_db.name, http_port=0, ws_port=0)

        server.process_gui_action({
            "type": "pin_item",
            "item_type": "decision",
            "item_id": 1,
            "note": "Importante"
        })

        pinned = self.db.get_pinned_items()
        self.assertEqual(len(pinned), 1)
        self.assertEqual(pinned[0]["note"], "Importante")


if __name__ == "__main__":
    unittest.main()
