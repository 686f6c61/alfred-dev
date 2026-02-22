#!/usr/bin/env python3
"""Tests para la tabla pinned_items de la memoria persistente."""

import os
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory import MemoryDB


class TestPinnedItems(unittest.TestCase):
    """Tests del CRUD de elementos marcados."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = MemoryDB(self.tmp.name)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_pin_item(self):
        """Marcar un elemento y verificar que se persiste."""
        pin_id = self.db.pin_item("decision", item_id=42, note="Critica para la arquitectura")
        self.assertIsInstance(pin_id, int)
        self.assertGreater(pin_id, 0)

    def test_get_pinned_items(self):
        """Los elementos marcados se devuelven correctamente."""
        self.db.pin_item("decision", item_id=1, note="Nota A")
        self.db.pin_item("event", item_id=5, note="Nota B")

        pinned = self.db.get_pinned_items()
        self.assertEqual(len(pinned), 2)

    def test_filter_by_type(self):
        """Se puede filtrar por tipo de elemento."""
        self.db.pin_item("decision", item_id=1, note="D1")
        self.db.pin_item("event", item_id=2, note="E1")
        self.db.pin_item("decision", item_id=3, note="D2")

        decisions = self.db.get_pinned_items(item_type="decision")
        self.assertEqual(len(decisions), 2)

        events = self.db.get_pinned_items(item_type="event")
        self.assertEqual(len(events), 1)

    def test_unpin_item(self):
        """Desmarcar un elemento lo elimina de la lista."""
        pin_id = self.db.pin_item("gate", item_ref="security_review", note="OK")
        self.db.unpin_item(pin_id)

        pinned = self.db.get_pinned_items()
        self.assertEqual(len(pinned), 0)

    def test_auto_pinned_flag(self):
        """Los elementos auto-marcados se distinguen de los manuales."""
        self.db.pin_item("decision", item_id=1, note="Manual", auto=False)
        self.db.pin_item("decision", item_id=2, note="Auto", auto=True)

        pinned = self.db.get_pinned_items()
        manual = [p for p in pinned if not p["auto_pinned"]]
        auto = [p for p in pinned if p["auto_pinned"]]
        self.assertEqual(len(manual), 1)
        self.assertEqual(len(auto), 1)

    def test_pin_with_item_ref(self):
        """Se puede marcar un elemento con referencia textual en vez de ID."""
        pin_id = self.db.pin_item("gate", item_ref="security_review", note="Aprobado con condicion X")
        pinned = self.db.get_pinned_items()
        self.assertEqual(pinned[0]["item_ref"], "security_review")

    def test_priority_ordering(self):
        """Los elementos se devuelven ordenados por prioridad descendente."""
        self.db.pin_item("decision", item_id=1, note="Baja", priority=1)
        self.db.pin_item("decision", item_id=2, note="Alta", priority=10)
        self.db.pin_item("decision", item_id=3, note="Media", priority=5)

        pinned = self.db.get_pinned_items()
        priorities = [p["priority"] for p in pinned]
        self.assertEqual(priorities, [10, 5, 1])

    def test_get_session_context(self):
        """get_session_context devuelve contexto estructurado con pinned items."""
        iter_id = self.db.start_iteration("feature", "Test feature")
        self.db.log_decision(
            title="Usar WebSocket",
            chosen="WebSocket manual RFC 6455",
            iteration_id=iter_id,
        )
        self.db.pin_item("decision", item_id=1, note="Clave arquitectonica", priority=10)
        self.db.create_gui_action("activate_agent", {"agent_name": "tech-writer"})

        context = self.db.get_session_context()
        self.assertIn("iteration", context)
        self.assertIn("pinned_items", context)
        self.assertIn("pending_actions", context)
        self.assertEqual(len(context["pinned_items"]), 1)
        self.assertEqual(len(context["pending_actions"]), 1)


if __name__ == "__main__":
    unittest.main()
