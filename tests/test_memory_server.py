#!/usr/bin/env python3
"""
Tests para las herramientas MCP del servidor de memoria.

Cada test verifica que los handlers del servidor MCP producen resultados
correctos al invocar las operaciones sobre una base de datos temporal.
Se comprueba tanto el comportamiento exitoso como los casos de validacion.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory import MemoryDB
from mcp.memory_server import MemoryMCPServer, _TOOLS


class TestMCPTools(unittest.TestCase):
    """Verifica que los handlers MCP producen resultados correctos."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.server = MemoryMCPServer(db_path=self._db_path)
        self.db = self.server._ensure_db()

    def tearDown(self):
        if self.server._db:
            self.server._db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    # --- Tests de herramientas nuevas --------------------------------------

    def test_memory_update_decision_changes_status(self):
        """memory_update_decision cambia el estado de una decision."""
        dec_id = self.db.log_decision(
            title="Decision para actualizar",
            chosen="Opcion A",
        )
        result = self.server._call_memory_update_decision(
            self.db, {"id": dec_id, "status": "superseded"},
        )

        self.assertNotIn("error", result)
        self.assertEqual(result["id"], dec_id)

        # Comprobar que el estado se ha aplicado realmente
        decisions = self.db.get_decisions()
        self.assertEqual(decisions[0]["status"], "superseded")

    def test_memory_update_decision_adds_tags(self):
        """memory_update_decision anade etiquetas sin duplicar."""
        dec_id = self.db.log_decision(
            title="Decision para etiquetar",
            chosen="Opcion B",
            tags=["existente"],
        )
        result = self.server._call_memory_update_decision(
            self.db, {"id": dec_id, "tags": ["nueva", "existente"]},
        )

        self.assertNotIn("error", result)

        decisions = self.db.get_decisions()
        tags = json.loads(decisions[0]["tags"])
        # La etiqueta "existente" no debe duplicarse
        self.assertEqual(tags, ["existente", "nueva"])

    def test_memory_link_decisions_creates_link(self):
        """memory_link_decisions crea la relacion entre decisiones."""
        dec1 = self.db.log_decision(title="Origen", chosen="A")
        dec2 = self.db.log_decision(title="Destino", chosen="B")

        result = self.server._call_memory_link_decisions(
            self.db,
            {"source_id": dec1, "target_id": dec2, "link_type": "supersedes"},
        )

        self.assertNotIn("error", result)
        self.assertEqual(result["source_id"], dec1)
        self.assertEqual(result["target_id"], dec2)
        self.assertEqual(result["link_type"], "supersedes")

        # Verificar que la relacion existe en la BD
        links = self.db.get_decision_links(dec1)
        self.assertEqual(len(links), 1)

    def test_memory_health_returns_status(self):
        """memory_health devuelve un informe con status y schema_version."""
        result = self.server._call_memory_health(self.db, {})

        self.assertIn("status", result)
        self.assertIn("schema_version", result)
        self.assertIn("fts_enabled", result)
        self.assertIn("size_bytes", result)
        # Una BD recien creada debe estar saludable
        self.assertEqual(result["status"], "healthy")

    def test_memory_export_returns_count(self):
        """memory_export exporta las decisiones y devuelve el conteo."""
        self.db.log_decision(title="Decision A", chosen="Opcion 1")
        self.db.log_decision(title="Decision B", chosen="Opcion 2")

        export_path = os.path.join(
            tempfile.mkdtemp(), "test_export.md",
        )
        try:
            result = self.server._call_memory_export(
                self.db,
                {"format": "markdown", "path": export_path},
            )

            self.assertNotIn("error", result)
            self.assertEqual(result["exported"], 2)
            self.assertEqual(result["format"], "markdown")
            self.assertTrue(os.path.exists(export_path))
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    # --- Tests de herramientas modificadas ---------------------------------

    def test_memory_search_with_filters(self):
        """memory_search pasa correctamente los filtros de tags y status."""
        self.db.log_decision(
            title="Politica de seguridad",
            chosen="OAuth2",
            tags=["security"],
        )
        self.db.log_decision(
            title="Politica de rendimiento",
            chosen="Redis",
            tags=["performance"],
        )

        result = self.server._call_memory_search(
            self.db,
            {"query": "Politica", "tags": ["security"]},
        )

        self.assertGreater(result["total"], 0)
        # Solo debe aparecer la decision de seguridad
        titles = [r.get("title", "") for r in result["results"]]
        self.assertTrue(any("seguridad" in t for t in titles))
        self.assertFalse(any("rendimiento" in t for t in titles))

    def test_memory_log_decision_with_tags(self):
        """memory_log_decision registra las etiquetas correctamente."""
        result = self.server._call_memory_log_decision(
            self.db,
            {
                "title": "Decision con tags",
                "chosen": "Opcion Z",
                "tags": ["api", "backend"],
            },
        )

        self.assertNotIn("error", result)
        dec_id = result["decision_id"]

        decisions = self.db.get_decisions()
        d = [dec for dec in decisions if dec["id"] == dec_id][0]
        tags = json.loads(d["tags"])
        self.assertEqual(tags, ["api", "backend"])

    def test_memory_log_commit_with_files(self):
        """memory_log_commit registra la lista de ficheros correctamente."""
        result = self.server._call_memory_log_commit(
            self.db,
            {
                "sha": "test_files_sha_001",
                "message": "feat: nuevo componente",
                "files": ["src/app.py", "tests/test_app.py"],
            },
        )

        self.assertNotIn("error", result)
        commit_id = result["commit_id"]
        self.assertIsNotNone(commit_id)

        # Verificar via SQL directo que los ficheros se guardaron
        import sqlite3
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT files FROM commits WHERE id = ?", (commit_id,)
        ).fetchone()
        conn.close()

        files = json.loads(row[0])
        self.assertEqual(files, ["src/app.py", "tests/test_app.py"])

    # --- Test de conteo total de herramientas ------------------------------

    def test_tool_count_is_15(self):
        """El catalogo _TOOLS debe contener exactamente 15 herramientas."""
        self.assertEqual(len(_TOOLS), 15)


if __name__ == "__main__":
    unittest.main()
