#!/usr/bin/env python3
"""Tests para la tabla gui_actions de la memoria persistente."""

import json
import os
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory import MemoryDB


class TestGUIActions(unittest.TestCase):
    """Tests del CRUD de acciones de la GUI."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = MemoryDB(self.tmp.name)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_create_gui_action(self):
        """Crear una accion y verificar que se persiste."""
        action_id = self.db.create_gui_action(
            "activate_agent", {"agent_name": "tech-writer", "phase": "documentacion"}
        )
        self.assertIsInstance(action_id, int)
        self.assertGreater(action_id, 0)

    def test_get_pending_actions(self):
        """Las acciones creadas se devuelven como pendientes."""
        self.db.create_gui_action("activate_agent", {"agent_name": "tech-writer"})
        self.db.create_gui_action("approve_gate", {"gate_name": "security"})

        pending = self.db.get_pending_actions()
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]["action_type"], "activate_agent")
        self.assertEqual(pending[1]["action_type"], "approve_gate")

    def test_mark_action_processed(self):
        """Una accion procesada ya no aparece como pendiente."""
        action_id = self.db.create_gui_action("activate_agent", {"agent_name": "qa"})
        self.db.mark_action_processed(action_id, "memory-compact.py")

        pending = self.db.get_pending_actions()
        self.assertEqual(len(pending), 0)

    def test_processed_action_has_metadata(self):
        """La accion procesada guarda quien la proceso y cuando."""
        action_id = self.db.create_gui_action("approve_gate", {"gate": "tests"})
        self.db.mark_action_processed(action_id, "stop-hook.py")

        row = self.db._conn.execute(
            "SELECT status, processed_at, processed_by FROM gui_actions WHERE id = ?",
            (action_id,),
        ).fetchone()
        self.assertEqual(row["status"], "processed")
        self.assertIsNotNone(row["processed_at"])
        self.assertEqual(row["processed_by"], "stop-hook.py")

    def test_pending_actions_ordered_by_creation(self):
        """Las acciones pendientes se devuelven en orden FIFO."""
        id1 = self.db.create_gui_action("action_a", {"data": "first"})
        id2 = self.db.create_gui_action("action_b", {"data": "second"})

        pending = self.db.get_pending_actions()
        self.assertEqual(pending[0]["id"], id1)
        self.assertEqual(pending[1]["id"], id2)

    def test_payload_stored_as_json(self):
        """El payload se serializa como JSON y se puede recuperar."""
        payload = {"agent_name": "senior-dev", "options": {"tdd": True}}
        action_id = self.db.create_gui_action("activate_agent", payload)

        pending = self.db.get_pending_actions()
        recovered = json.loads(pending[0]["payload"])
        self.assertEqual(recovered["agent_name"], "senior-dev")
        self.assertTrue(recovered["options"]["tdd"])


if __name__ == "__main__":
    unittest.main()
