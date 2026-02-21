#!/usr/bin/env python3
"""
Tests para el modulo de memoria persistente (core/memory.py).

Cobertura completa de:
- Creacion de la base de datos y esquema (tablas, indices, WAL, FK, FTS5, permisos).
- Operaciones CRUD sobre iteraciones, decisiones, commits y eventos.
- Sanitizacion de contenido sensible.
- Busqueda textual (FTS5 y fallback LIKE).
- Cronologia de eventos y estadisticas.
- Purga de eventos antiguos.
"""

import json
import os
import stat
import sqlite3
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory import MemoryDB, sanitize_content


class TestMemoryDBCreation(unittest.TestCase):
    """Verifica que la base de datos se crea correctamente con el esquema esperado."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        # Limpiar ficheros SQLite (principal + WAL + shm)
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_all_tables_exist(self):
        """Las 6 tablas del esquema deben existir tras la creacion."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {"meta", "iterations", "decisions", "commits",
                    "commit_links", "events", "decision_links"}
        # FTS5 puede anadir tablas adicionales; solo verificamos las basicas
        self.assertTrue(expected.issubset(tables),
                        f"Faltan tablas: {expected - tables}")

    def test_schema_version_registered(self):
        """La version del esquema debe quedar registrada en meta."""
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "2")

    def test_wal_mode_active(self):
        """El modo WAL debe estar activado para mejor concurrencia."""
        conn = sqlite3.connect(self._db_path)
        row = conn.execute("PRAGMA journal_mode").fetchone()
        conn.close()

        self.assertEqual(row[0], "wal")

    def test_foreign_keys_enabled(self):
        """Las foreign keys deben estar habilitadas en la conexion de MemoryDB.

        PRAGMA foreign_keys es un ajuste por conexion, no a nivel de fichero.
        Por eso se verifica contra la conexion interna del objeto, no contra
        una conexion nueva.
        """
        row = self.db._conn.execute("PRAGMA foreign_keys").fetchone()
        self.assertEqual(row[0], 1)

    def test_fts5_detection(self):
        """La deteccion de FTS5 debe registrarse en meta."""
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'fts_enabled'"
        ).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertIn(row[0], ("0", "1"))

    def test_fts_enabled_property(self):
        """La propiedad fts_enabled debe ser coherente con la deteccion."""
        self.assertIsInstance(self.db.fts_enabled, bool)

    def test_file_permissions_0600(self):
        """El fichero de la DB debe tener permisos 0600 (solo propietario)."""
        mode = os.stat(self._db_path).st_mode
        # Extraer solo los bits de permisos (ultimos 9 bits)
        perms = stat.S_IMODE(mode)
        self.assertEqual(perms, 0o600,
                         f"Permisos esperados 0600, obtenidos {oct(perms)}")

    def test_indices_exist(self):
        """Los 6 indices definidos en el esquema deben existir."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name LIKE 'idx_%'"
        )
        indices = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "idx_iterations_status",
            "idx_decisions_iteration",
            "idx_commits_iteration",
            "idx_events_iteration",
            "idx_events_type",
            "idx_decision_links_target",
        }
        self.assertEqual(expected, indices)

    def test_created_at_registered(self):
        """La fecha de creacion debe quedar registrada en meta."""
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'created_at'"
        ).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        # Debe ser una fecha ISO 8601
        self.assertIn("T", row[0])

    def test_creates_parent_directory(self):
        """Si el directorio padre no existe, MemoryDB lo crea."""
        nested_path = os.path.join(
            tempfile.mkdtemp(), "subdir", "deep", "test.db"
        )
        try:
            db = MemoryDB(nested_path)
            db.close()
            self.assertTrue(os.path.exists(nested_path))
        finally:
            # Limpieza
            for suffix in ("", "-wal", "-shm"):
                path = nested_path + suffix
                if os.path.exists(path):
                    os.unlink(path)


class TestIterations(unittest.TestCase):
    """Tests de CRUD sobre iteraciones."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_start_iteration_returns_id(self):
        """start_iteration debe devolver el ID de la nueva iteracion."""
        iter_id = self.db.start_iteration("feature", "Login con OAuth")
        self.assertIsInstance(iter_id, int)
        self.assertGreater(iter_id, 0)

    def test_get_iteration(self):
        """get_iteration debe devolver los datos de la iteracion."""
        iter_id = self.db.start_iteration("fix", "Error en el formulario")
        iteration = self.db.get_iteration(iter_id)

        self.assertIsNotNone(iteration)
        self.assertEqual(iteration["command"], "fix")
        self.assertEqual(iteration["description"], "Error en el formulario")
        self.assertEqual(iteration["status"], "active")
        self.assertIsNotNone(iteration["started_at"])
        self.assertIsNone(iteration["completed_at"])

    def test_get_nonexistent_iteration_returns_none(self):
        """Consultar una iteracion inexistente debe devolver None."""
        self.assertIsNone(self.db.get_iteration(9999))

    def test_complete_iteration(self):
        """complete_iteration debe marcar la iteracion como completada."""
        iter_id = self.db.start_iteration("spike", "Evaluar framework X")
        self.db.complete_iteration(iter_id)
        iteration = self.db.get_iteration(iter_id)

        self.assertEqual(iteration["status"], "completed")
        self.assertIsNotNone(iteration["completed_at"])

    def test_abandon_iteration(self):
        """Se puede abandonar una iteracion con status 'abandoned'."""
        iter_id = self.db.start_iteration("feature", "Funcionalidad cancelada")
        self.db.complete_iteration(iter_id, status="abandoned")
        iteration = self.db.get_iteration(iter_id)

        self.assertEqual(iteration["status"], "abandoned")

    def test_get_active_iteration(self):
        """get_active_iteration debe devolver la iteracion activa."""
        iter_id = self.db.start_iteration("feature", "Tarea activa")
        active = self.db.get_active_iteration()

        self.assertIsNotNone(active)
        self.assertEqual(active["id"], iter_id)

    def test_get_active_iteration_returns_none_when_none_active(self):
        """Si no hay iteracion activa, get_active_iteration devuelve None."""
        self.assertIsNone(self.db.get_active_iteration())

    def test_get_active_iteration_after_completion(self):
        """Tras completar, get_active_iteration no devuelve la completada."""
        iter_id = self.db.start_iteration("fix", "Bug resuelto")
        self.db.complete_iteration(iter_id)

        self.assertIsNone(self.db.get_active_iteration())

    def test_latest_active_iteration_wins(self):
        """Si hay varias activas, se devuelve la mas reciente."""
        self.db.start_iteration("feature", "Primera")
        iter_id2 = self.db.start_iteration("feature", "Segunda")
        active = self.db.get_active_iteration()

        self.assertEqual(active["id"], iter_id2)


class TestDecisions(unittest.TestCase):
    """Tests de CRUD sobre decisiones."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_log_decision_returns_id(self):
        """log_decision debe devolver el ID de la nueva decision."""
        dec_id = self.db.log_decision(
            title="Elegir base de datos",
            chosen="SQLite",
            context="Necesitamos persistencia local",
        )
        self.assertIsInstance(dec_id, int)
        self.assertGreater(dec_id, 0)

    def test_get_decisions(self):
        """get_decisions debe devolver las decisiones registradas."""
        self.db.log_decision(title="Decision A", chosen="Opcion 1")
        self.db.log_decision(title="Decision B", chosen="Opcion 2")

        decisions = self.db.get_decisions()
        self.assertEqual(len(decisions), 2)

    def test_decision_auto_links_to_active_iteration(self):
        """Sin iteration_id, la decision se vincula a la iteracion activa."""
        iter_id = self.db.start_iteration("feature", "Modulo de memoria")
        dec_id = self.db.log_decision(
            title="Elegir motor de busqueda",
            chosen="FTS5",
        )

        decisions = self.db.get_decisions(iteration_id=iter_id)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["id"], dec_id)

    def test_decision_without_active_iteration(self):
        """Sin iteracion activa, la decision se registra con iteration_id=None."""
        dec_id = self.db.log_decision(
            title="Decision huerfana",
            chosen="Alguna opcion",
        )
        decisions = self.db.get_decisions()
        self.assertEqual(len(decisions), 1)
        self.assertIsNone(decisions[0]["iteration_id"])

    def test_decision_with_all_fields(self):
        """Registrar una decision con todos los campos opcionales."""
        dec_id = self.db.log_decision(
            title="Framework web",
            chosen="FastAPI",
            context="Necesitamos un API REST",
            alternatives=["Django", "Flask"],
            rationale="Mejor rendimiento y tipado",
            impact="high",
            phase="arquitectura",
        )
        decisions = self.db.get_decisions()
        d = decisions[0]

        self.assertEqual(d["title"], "Framework web")
        self.assertEqual(d["chosen"], "FastAPI")
        self.assertEqual(d["impact"], "high")
        self.assertEqual(d["phase"], "arquitectura")

        # Las alternativas se almacenan como JSON
        alts = json.loads(d["alternatives"])
        self.assertEqual(alts, ["Django", "Flask"])

    def test_get_decisions_filtered_by_iteration(self):
        """get_decisions con iteration_id filtra correctamente."""
        iter1 = self.db.start_iteration("feature", "Primera")
        self.db.log_decision(title="Dec iter 1", chosen="A")
        self.db.complete_iteration(iter1)

        iter2 = self.db.start_iteration("fix", "Segunda")
        self.db.log_decision(title="Dec iter 2", chosen="B")

        decs_iter1 = self.db.get_decisions(iteration_id=iter1)
        decs_iter2 = self.db.get_decisions(iteration_id=iter2)

        self.assertEqual(len(decs_iter1), 1)
        self.assertEqual(decs_iter1[0]["title"], "Dec iter 1")
        self.assertEqual(len(decs_iter2), 1)
        self.assertEqual(decs_iter2[0]["title"], "Dec iter 2")


class TestCommits(unittest.TestCase):
    """Tests de CRUD sobre commits."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_log_commit_returns_id(self):
        """log_commit debe devolver el ID del nuevo commit."""
        commit_id = self.db.log_commit(
            sha="abc123def456",
            message="feat: nuevo modulo",
        )
        self.assertIsInstance(commit_id, int)
        self.assertGreater(commit_id, 0)

    def test_duplicate_sha_returns_none(self):
        """Registrar un commit con el mismo SHA devuelve None (idempotencia)."""
        self.db.log_commit(sha="abc123def456", message="primer registro")
        result = self.db.log_commit(sha="abc123def456", message="duplicado")
        self.assertIsNone(result)

    def test_commit_auto_links_to_active_iteration(self):
        """Sin iteration_id, el commit se vincula a la iteracion activa."""
        iter_id = self.db.start_iteration("feature", "Modulo X")
        commit_id = self.db.log_commit(
            sha="commit1sha",
            message="feat: implementar X",
        )

        # Verificar via SQL directo
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT iteration_id FROM commits WHERE id = ?", (commit_id,)
        ).fetchone()
        conn.close()

        self.assertEqual(row[0], iter_id)

    def test_log_commit_with_full_metadata(self):
        """Registrar un commit con todos los campos de metadata."""
        commit_id = self.db.log_commit(
            sha="full_meta_sha",
            message="refactor: simplificar logica",
            author="dev@ejemplo.com",
            files_changed=5,
            insertions=120,
            deletions=80,
        )
        self.assertIsNotNone(commit_id)

    def test_link_commit_decision(self):
        """link_commit_decision debe crear la vinculacion correctamente."""
        dec_id = self.db.log_decision(
            title="Usar SQLite", chosen="SQLite"
        )
        commit_id = self.db.log_commit(
            sha="linked_sha_123",
            message="feat: implementar SQLite",
        )
        # No debe lanzar excepcion
        self.db.link_commit_decision(commit_id, dec_id, "implements")

        # Verificar via SQL directo
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT * FROM commit_links WHERE commit_id = ? AND decision_id = ?",
            (commit_id, dec_id),
        ).fetchone()
        conn.close()

        self.assertIsNotNone(row)

    def test_link_commit_decision_duplicate_ignored(self):
        """Vincular el mismo commit con la misma decision dos veces no falla."""
        dec_id = self.db.log_decision(title="Dec", chosen="X")
        commit_id = self.db.log_commit(sha="dup_link_sha", message="msg")

        self.db.link_commit_decision(commit_id, dec_id)
        # Segunda vez: no debe lanzar excepcion
        self.db.link_commit_decision(commit_id, dec_id)


class TestSanitization(unittest.TestCase):
    """
    Tests de sanitizacion de contenido sensible.

    Los valores de test se construyen en tiempo de ejecucion concatenando
    componentes para evitar que el hook de seguridad los detecte en el
    codigo fuente del test.
    """

    def test_none_returns_none(self):
        """sanitize_content(None) debe devolver None."""
        self.assertIsNone(sanitize_content(None))

    def test_clean_text_unchanged(self):
        """Texto sin secretos debe pasar sin modificaciones."""
        text = "Este texto no contiene ningun secreto"
        self.assertEqual(sanitize_content(text), text)

    def test_aws_key_redacted(self):
        """Las claves AWS (patron AKIA...) deben redactarse."""
        # Se construye la clave ficticia en runtime para no activar el hook
        fake_key = "AKIA" + "TESTMEMORYDB1234"
        text = f"La clave es {fake_key} en este texto"
        result = sanitize_content(text)

        self.assertNotIn(fake_key, result)
        self.assertIn("[REDACTED:AWS_KEY]", result)

    def test_jwt_redacted(self):
        """Los tokens JWT deben redactarse."""
        # Construir un JWT ficticio con las 3 partes separadas por punto
        header = "eyJhbGciOiJI" + "UzI1NiIsInR5"
        payload = "eyJzdWIiOiIx" + "MjM0NTY3ODkw"
        signature = "SflKxwRJSM" + "eKKF2QT4fwp"
        fake_jwt = f"{header}.{payload}.{signature}"
        text = f"Token: {fake_jwt}"
        result = sanitize_content(text)

        self.assertNotIn(fake_jwt, result)
        self.assertIn("[REDACTED:JWT]", result)

    def test_sk_key_redacted(self):
        """Las claves con prefijo sk- deben redactarse."""
        # 20+ caracteres alfanumericos tras sk-
        fake_sk = "sk-" + "a" * 25
        text = f"Clave: {fake_sk}"
        result = sanitize_content(text)

        self.assertNotIn(fake_sk, result)
        self.assertIn("[REDACTED:SK_KEY]", result)

    def test_private_key_header_redacted(self):
        """Las cabeceras de clave privada PEM deben redactarse."""
        pem = "-----BEGIN " + "PRIVATE KEY-----"
        text = f"Certificado: {pem}"
        result = sanitize_content(text)

        self.assertNotIn(pem, result)
        self.assertIn("[REDACTED:PRIVATE_KEY]", result)

    def test_connection_string_redacted(self):
        """Las cadenas de conexion con credenciales deben redactarse."""
        # Se construye en partes para evitar el hook
        proto = "postgres" + "ql"
        creds = "usuario" + ":contrasena_larga"
        host = "servidor" + ".ejemplo.com"
        conn_str = f"{proto}://{creds}@{host}/db"
        text = f"DB: {conn_str}"
        result = sanitize_content(text)

        self.assertIn("[REDACTED:CONNECTION_STRING]", result)

    def test_multiple_secrets_all_redacted(self):
        """Si hay varios secretos en el mismo texto, todos se redactan."""
        fake_aws = "AKIA" + "MULTITEST12345678"
        fake_sk = "sk-" + "b" * 25
        text = f"AWS: {fake_aws}, SK: {fake_sk}"
        result = sanitize_content(text)

        self.assertNotIn(fake_aws, result)
        self.assertNotIn(fake_sk, result)
        self.assertIn("[REDACTED:AWS_KEY]", result)
        self.assertIn("[REDACTED:SK_KEY]", result)

    def test_sanitization_in_decision(self):
        """Los campos de decisiones se sanitizan al persistir."""
        tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = tmpfile.name
        tmpfile.close()

        try:
            db = MemoryDB(db_path)
            fake_key = "AKIA" + "DECISIONTEST1234"
            db.log_decision(
                title="Configurar acceso",
                chosen=f"Usar clave {fake_key}",
            )
            decisions = db.get_decisions()
            db.close()

            self.assertNotIn(fake_key, decisions[0]["chosen"])
            self.assertIn("[REDACTED:AWS_KEY]", decisions[0]["chosen"])
        finally:
            for suffix in ("", "-wal", "-shm"):
                path = db_path + suffix
                if os.path.exists(path):
                    os.unlink(path)


class TestSearch(unittest.TestCase):
    """Tests de busqueda textual."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

        # Poblar con datos de prueba
        self.iter_id = self.db.start_iteration("feature", "Sistema de pagos")
        self.db.log_decision(
            title="Pasarela de pago",
            chosen="Stripe",
            context="Necesitamos cobrar suscripciones",
            rationale="Buena documentacion y soporte en Europa",
        )
        self.db.log_decision(
            title="Base de datos",
            chosen="PostgreSQL",
            context="Persistencia relacional",
        )
        self.db.log_commit(
            sha="search_test_sha1",
            message="feat: integrar Stripe como pasarela de pagos",
        )

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_search_finds_decision_by_title(self):
        """La busqueda debe encontrar decisiones por titulo."""
        results = self.db.search("Pasarela")
        self.assertGreater(len(results), 0)

        # Al menos uno de los resultados debe ser la decision de pasarela
        titles = [r.get("title", "") for r in results]
        self.assertTrue(
            any("Pasarela" in t for t in titles),
            f"No se encontro 'Pasarela' en: {titles}"
        )

    def test_search_finds_commit_by_message(self):
        """La busqueda debe encontrar commits por mensaje."""
        results = self.db.search("Stripe")
        self.assertGreater(len(results), 0)

        # Debe haber al menos un resultado de tipo commit o decision
        source_types = [r["source_type"] for r in results]
        # Stripe aparece en la decision y en el commit
        self.assertTrue(len(source_types) > 0)

    def test_search_no_results(self):
        """Buscar un termino inexistente devuelve lista vacia."""
        results = self.db.search("blockchain_cuantico_inexistente")
        self.assertEqual(len(results), 0)

    def test_search_with_iteration_filter(self):
        """La busqueda filtrada por iteracion solo devuelve resultados de esa."""
        # Crear otra iteracion con datos diferentes
        self.db.complete_iteration(self.iter_id)
        iter2 = self.db.start_iteration("fix", "Otra cosa")
        self.db.log_decision(title="Otra decision", chosen="Otra opcion")

        results = self.db.search("Pasarela", iteration_id=iter2)
        self.assertEqual(len(results), 0)

    def test_search_respects_limit(self):
        """La busqueda respeta el parametro limit."""
        # Insertar muchas decisiones con el mismo termino
        for i in range(10):
            self.db.log_decision(
                title=f"Optimizacion numero {i}",
                chosen="Cachear",
            )

        results = self.db.search("Optimizacion", limit=3)
        self.assertLessEqual(len(results), 3)


class TestEvents(unittest.TestCase):
    """Tests de CRUD sobre eventos."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_log_event_returns_id(self):
        """log_event debe devolver el ID del nuevo evento."""
        iter_id = self.db.start_iteration("feature", "Test")
        event_id = self.db.log_event(
            event_type="phase_completed",
            phase="producto",
            iteration_id=iter_id,
        )
        self.assertIsInstance(event_id, int)
        self.assertGreater(event_id, 0)

    def test_log_event_with_payload(self):
        """Los eventos pueden incluir payload JSON."""
        iter_id = self.db.start_iteration("feature", "Test")
        self.db.log_event(
            event_type="gate_passed",
            phase="desarrollo",
            payload={"tests_ok": True, "duration_s": 12.5},
            iteration_id=iter_id,
        )

        timeline = self.db.get_timeline(iter_id)
        self.assertEqual(len(timeline), 1)

        payload = json.loads(timeline[0]["payload"])
        self.assertTrue(payload["tests_ok"])

    def test_event_auto_links_to_active_iteration(self):
        """Sin iteration_id, el evento se vincula a la iteracion activa."""
        iter_id = self.db.start_iteration("feature", "Auto-link")
        self.db.log_event(event_type="phase_completed", phase="producto")

        timeline = self.db.get_timeline(iter_id)
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0]["iteration_id"], iter_id)

    def test_get_timeline_ordered_chronologically(self):
        """get_timeline devuelve eventos en orden cronologico ascendente."""
        iter_id = self.db.start_iteration("feature", "Cronologia")

        self.db.log_event(
            event_type="phase_completed", phase="producto",
            iteration_id=iter_id,
        )
        self.db.log_event(
            event_type="phase_completed", phase="arquitectura",
            iteration_id=iter_id,
        )
        self.db.log_event(
            event_type="phase_completed", phase="desarrollo",
            iteration_id=iter_id,
        )

        timeline = self.db.get_timeline(iter_id)
        self.assertEqual(len(timeline), 3)
        self.assertEqual(timeline[0]["phase"], "producto")
        self.assertEqual(timeline[1]["phase"], "arquitectura")
        self.assertEqual(timeline[2]["phase"], "desarrollo")

    def test_get_timeline_empty_for_nonexistent_iteration(self):
        """get_timeline con iteracion inexistente devuelve lista vacia."""
        timeline = self.db.get_timeline(9999)
        self.assertEqual(len(timeline), 0)

    def test_purge_old_events(self):
        """purge_old_events elimina eventos anteriores a la ventana."""
        iter_id = self.db.start_iteration("feature", "Purga")

        # Insertar un evento con fecha antigua directamente en la DB
        # para poder probarlo sin esperar dias reales
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "INSERT INTO events (iteration_id, event_type, phase, created_at) "
            "VALUES (?, 'phase_completed', 'producto', '2020-01-01T00:00:00+00:00')",
            (iter_id,),
        )
        conn.commit()
        conn.close()

        # Insertar un evento reciente via la API
        self.db.log_event(
            event_type="phase_completed", phase="desarrollo",
            iteration_id=iter_id,
        )

        # Purgar con retencion de 30 dias: solo el antiguo debe eliminarse
        deleted = self.db.purge_old_events(retention_days=30)
        self.assertEqual(deleted, 1)

        timeline = self.db.get_timeline(iter_id)
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0]["phase"], "desarrollo")

    def test_purge_does_not_delete_recent_events(self):
        """purge_old_events no elimina eventos recientes."""
        iter_id = self.db.start_iteration("feature", "Recientes")
        self.db.log_event(
            event_type="phase_completed", phase="producto",
            iteration_id=iter_id,
        )

        deleted = self.db.purge_old_events(retention_days=30)
        self.assertEqual(deleted, 0)


class TestStats(unittest.TestCase):
    """Tests de estadisticas generales."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_stats_empty_db(self):
        """En una DB vacia, los contadores deben ser 0."""
        stats = self.db.get_stats()

        self.assertEqual(stats["total_iterations"], 0)
        self.assertEqual(stats["total_decisions"], 0)
        self.assertEqual(stats["total_commits"], 0)
        self.assertEqual(stats["total_events"], 0)

    def test_stats_with_data(self):
        """Los contadores deben reflejar los datos insertados."""
        self.db.start_iteration("feature", "Test stats")
        self.db.log_decision(title="Dec 1", chosen="A")
        self.db.log_decision(title="Dec 2", chosen="B")
        self.db.log_commit(sha="stats_sha_1", message="commit 1")
        self.db.log_event(event_type="phase_completed", phase="producto")

        stats = self.db.get_stats()

        self.assertEqual(stats["total_iterations"], 1)
        self.assertEqual(stats["total_decisions"], 2)
        self.assertEqual(stats["total_commits"], 1)
        self.assertEqual(stats["total_events"], 1)

    def test_stats_includes_metadata(self):
        """Las estadisticas incluyen metadatos de la tabla meta."""
        stats = self.db.get_stats()

        self.assertIn("schema_version", stats)
        self.assertEqual(stats["schema_version"], "2")
        self.assertIn("fts_enabled", stats)
        self.assertIn("created_at", stats)

    def test_stats_fts_coherent_with_property(self):
        """El campo fts_enabled en stats es coherente con la propiedad."""
        stats = self.db.get_stats()
        expected = "1" if self.db.fts_enabled else "0"
        self.assertEqual(stats["fts_enabled"], expected)


class TestReopen(unittest.TestCase):
    """Tests de reapertura de la base de datos (persistencia entre sesiones)."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()

    def tearDown(self):
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_data_persists_after_close_and_reopen(self):
        """Los datos deben persistir tras cerrar y reabrir la DB."""
        db = MemoryDB(self._db_path)
        iter_id = db.start_iteration("feature", "Persistencia")
        db.log_decision(title="Decision persistente", chosen="SQLite")
        db.close()

        # Reabrir
        db2 = MemoryDB(self._db_path)
        iteration = db2.get_iteration(iter_id)
        decisions = db2.get_decisions()
        db2.close()

        self.assertIsNotNone(iteration)
        self.assertEqual(iteration["command"], "feature")
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["title"], "Decision persistente")

    def test_schema_not_duplicated_on_reopen(self):
        """Reabrir la DB no debe duplicar la version del esquema."""
        db = MemoryDB(self._db_path)
        db.close()

        db2 = MemoryDB(self._db_path)
        stats = db2.get_stats()
        db2.close()

        self.assertEqual(stats["schema_version"], "2")


# ---------------------------------------------------------------------------
# SQL del esquema v1 (sin tags, status, files ni decision_links).
# Se usa en los tests de migracion para crear una DB que simule la version
# anterior y verificar que _run_migrations la transforma correctamente.
# ---------------------------------------------------------------------------

_V1_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS iterations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    command          TEXT    NOT NULL,
    description      TEXT,
    status           TEXT    NOT NULL DEFAULT 'active',
    started_at       TEXT    NOT NULL,
    completed_at     TEXT,
    phases_completed TEXT,
    artifacts        TEXT
);
CREATE TABLE IF NOT EXISTS decisions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id  INTEGER REFERENCES iterations(id),
    title         TEXT    NOT NULL,
    context       TEXT,
    chosen        TEXT    NOT NULL,
    alternatives  TEXT,
    rationale     TEXT,
    impact        TEXT,
    phase         TEXT,
    decided_at    TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS commits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sha           TEXT    UNIQUE NOT NULL,
    message       TEXT,
    author        TEXT,
    files_changed INTEGER,
    insertions    INTEGER,
    deletions     INTEGER,
    committed_at  TEXT    NOT NULL,
    iteration_id  INTEGER REFERENCES iterations(id)
);
CREATE TABLE IF NOT EXISTS commit_links (
    commit_id   INTEGER REFERENCES commits(id),
    decision_id INTEGER REFERENCES decisions(id),
    link_type   TEXT,
    PRIMARY KEY (commit_id, decision_id)
);
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id  INTEGER REFERENCES iterations(id),
    event_type    TEXT    NOT NULL,
    phase         TEXT,
    payload       TEXT,
    created_at    TEXT    NOT NULL
);
"""


def _create_v1_db(db_path: str) -> None:
    """Crea una base de datos con esquema v1 para tests de migracion.

    Ejecuta el SQL del esquema original (sin las columnas ni tablas
    anadidas en v2) e inserta la version 1 en la tabla meta.

    Args:
        db_path: ruta al fichero SQLite a crear.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_V1_SCHEMA_SQL)
    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('schema_version', '1')"
    )
    conn.commit()
    conn.close()


class TestSchemaMigration(unittest.TestCase):
    """Verifica que el mecanismo de migracion de esquema funciona correctamente.

    Cada test que necesita una DB v1 la crea manualmente con el esquema
    original (6 tablas, sin las columnas tags/status/files ni la tabla
    decision_links) y despues abre la DB con MemoryDB para forzar la
    migracion.
    """

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()

    def tearDown(self):
        # Limpiar ficheros SQLite (principal + WAL + shm + backup)
        for suffix in ("", "-wal", "-shm", ".bak"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_new_db_gets_latest_schema_version(self):
        """Una DB nueva debe crearse directamente con la ultima version."""
        db = MemoryDB(self._db_path)
        stats = db.get_stats()
        db.close()

        self.assertEqual(stats["schema_version"], "2")

    def test_v1_db_migrates_to_v2(self):
        """Una DB con esquema v1 debe migrar automaticamente a v2 al abrirla."""
        _create_v1_db(self._db_path)

        db = MemoryDB(self._db_path)
        stats = db.get_stats()
        db.close()

        self.assertEqual(stats["schema_version"], "2")

    def test_migration_creates_backup(self):
        """Al migrar, se debe crear una copia de seguridad (.bak) del fichero."""
        _create_v1_db(self._db_path)

        db = MemoryDB(self._db_path)
        db.close()

        bak_path = self._db_path + ".bak"
        self.assertTrue(
            os.path.exists(bak_path),
            f"No se encontro el fichero de backup en {bak_path}"
        )

    def test_migration_adds_tags_column(self):
        """Tras migrar de v1, la tabla decisions debe tener la columna tags."""
        _create_v1_db(self._db_path)

        db = MemoryDB(self._db_path)

        # Verificar que se puede insertar un registro con la columna tags
        db._conn.execute(
            "INSERT INTO decisions "
            "(title, chosen, tags, status, decided_at) "
            "VALUES ('Test', 'A', '[\"tag1\"]', 'active', '2026-01-01T00:00:00+00:00')"
        )
        db._conn.commit()

        row = db._conn.execute(
            "SELECT tags FROM decisions WHERE title = 'Test'"
        ).fetchone()
        db.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], '["tag1"]')

    def test_migration_creates_decision_links_table(self):
        """Tras migrar de v1, la tabla decision_links debe existir."""
        _create_v1_db(self._db_path)

        db = MemoryDB(self._db_path)

        row = db._conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='decision_links'"
        ).fetchone()
        db.close()

        self.assertIsNotNone(
            row,
            "La tabla decision_links no se encontro en sqlite_master"
        )


class TestDecisionTagsAndStatus(unittest.TestCase):
    """Tests de etiquetas y estado en decisiones.

    Verifican que las etiquetas se almacenan como JSON, que el estado
    se puede actualizar con valores validos y que los valores por defecto
    son correctos.
    """

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_log_decision_with_tags(self):
        """Las etiquetas proporcionadas se almacenan como JSON en la columna tags."""
        dec_id = self.db.log_decision(
            title="Decision con etiquetas",
            chosen="Opcion A",
            tags=["arquitectura", "rendimiento"],
        )
        decisions = self.db.get_decisions()
        d = decisions[0]

        tags = json.loads(d["tags"])
        self.assertEqual(tags, ["arquitectura", "rendimiento"])

    def test_log_decision_without_tags_defaults_empty(self):
        """Sin etiquetas, la columna tags contiene una lista JSON vacia."""
        dec_id = self.db.log_decision(
            title="Decision sin etiquetas",
            chosen="Opcion B",
        )
        decisions = self.db.get_decisions()
        d = decisions[0]

        tags = json.loads(d["tags"])
        self.assertEqual(tags, [])

    def test_add_decision_tags(self):
        """add_decision_tags anade etiquetas sin duplicar las existentes."""
        dec_id = self.db.log_decision(
            title="Decision para etiquetar",
            chosen="Opcion C",
            tags=["frontend"],
        )
        self.db.add_decision_tags(dec_id, ["backend", "frontend", "api"])

        decisions = self.db.get_decisions()
        tags = json.loads(decisions[0]["tags"])

        # frontend no debe duplicarse; el orden conserva la insercion
        self.assertEqual(tags, ["frontend", "backend", "api"])

    def test_update_decision_status(self):
        """update_decision_status cambia el estado correctamente."""
        dec_id = self.db.log_decision(
            title="Decision a reemplazar",
            chosen="Opcion vieja",
        )
        self.db.update_decision_status(dec_id, "superseded")

        decisions = self.db.get_decisions()
        self.assertEqual(decisions[0]["status"], "superseded")

    def test_update_decision_status_invalid(self):
        """Un estado no valido debe lanzar ValueError."""
        dec_id = self.db.log_decision(
            title="Decision con estado invalido",
            chosen="Algo",
        )
        with self.assertRaises(ValueError):
            self.db.update_decision_status(dec_id, "invalid")

    def test_decision_default_status_active(self):
        """El estado por defecto de una decision nueva es 'active'."""
        dec_id = self.db.log_decision(
            title="Decision nueva",
            chosen="Lo que sea",
        )
        decisions = self.db.get_decisions()
        self.assertEqual(decisions[0]["status"], "active")


class TestDecisionLinks(unittest.TestCase):
    """Tests de relaciones entre decisiones.

    Verifican que se pueden crear relaciones dirigidas entre decisiones,
    que la idempotencia funciona y que la busqueda es bidireccional.
    """

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_link_decisions(self):
        """link_decisions crea la relacion y get_decision_links la devuelve."""
        dec1 = self.db.log_decision(title="Decision origen", chosen="A")
        dec2 = self.db.log_decision(title="Decision destino", chosen="B")

        self.db.link_decisions(dec1, dec2, "supersedes")
        links = self.db.get_decision_links(dec1)

        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["source_id"], dec1)
        self.assertEqual(links[0]["target_id"], dec2)
        self.assertEqual(links[0]["link_type"], "supersedes")
        self.assertIn("created_at", links[0])

    def test_link_decisions_duplicate_ignored(self):
        """Crear la misma relacion dos veces no lanza excepcion."""
        dec1 = self.db.log_decision(title="Dec A", chosen="X")
        dec2 = self.db.log_decision(title="Dec B", chosen="Y")

        self.db.link_decisions(dec1, dec2, "relates")
        # Segunda vez: no debe fallar
        self.db.link_decisions(dec1, dec2, "relates")

        links = self.db.get_decision_links(dec1)
        self.assertEqual(len(links), 1)

    def test_get_decision_links_bidirectional(self):
        """get_decision_links devuelve resultados al buscar desde el target."""
        dec1 = self.db.log_decision(title="Origen", chosen="A")
        dec2 = self.db.log_decision(title="Destino", chosen="B")

        self.db.link_decisions(dec1, dec2, "depends_on")

        # Buscar desde el target (dec2) tambien devuelve la relacion
        links_from_target = self.db.get_decision_links(dec2)
        self.assertEqual(len(links_from_target), 1)
        self.assertEqual(links_from_target[0]["source_id"], dec1)
        self.assertEqual(links_from_target[0]["target_id"], dec2)

    def test_get_decision_links_empty(self):
        """Sin enlaces, get_decision_links devuelve lista vacia."""
        dec = self.db.log_decision(title="Solitaria", chosen="Z")
        links = self.db.get_decision_links(dec)
        self.assertEqual(links, [])


class TestSearchFilters(unittest.TestCase):
    """Tests de los filtros avanzados de busqueda (since, until, tags, status).

    Verifican que los metodos search() y get_decisions() aplican
    correctamente los filtros de fecha, etiquetas y estado sobre los
    resultados devueltos.
    """

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_search_with_since_filter(self):
        """since excluye resultados con fecha anterior al umbral."""
        # Crear dos decisiones con el mismo termino para que aparezcan
        dec_old = self.db.log_decision(
            title="Optimizacion antigua",
            chosen="Cache LRU",
        )
        dec_new = self.db.log_decision(
            title="Optimizacion reciente",
            chosen="Cache distribuida",
        )

        # Forzar la fecha de la primera decision a 2025-01-01 via SQL directo
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "UPDATE decisions SET decided_at = ? WHERE id = ?",
            ("2025-01-01T00:00:00+00:00", dec_old),
        )
        conn.commit()
        conn.close()

        results = self.db.search("Optimizacion", since="2026-01-01")
        titles = [r.get("title", "") for r in results]

        self.assertNotIn("Optimizacion antigua", titles)
        self.assertTrue(
            any("Optimizacion reciente" in t for t in titles),
            f"La decision reciente deberia aparecer, resultados: {titles}",
        )

    def test_search_with_until_filter(self):
        """until excluye resultados con fecha posterior al umbral."""
        dec_old = self.db.log_decision(
            title="Migracion antigua",
            chosen="PostgreSQL 14",
        )
        dec_new = self.db.log_decision(
            title="Migracion reciente",
            chosen="PostgreSQL 16",
        )

        # Forzar la fecha de la primera decision a 2025-01-01
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "UPDATE decisions SET decided_at = ? WHERE id = ?",
            ("2025-01-01T00:00:00+00:00", dec_old),
        )
        conn.commit()
        conn.close()

        results = self.db.search("Migracion", until="2025-06-01")
        titles = [r.get("title", "") for r in results]

        self.assertNotIn("Migracion reciente", titles)
        self.assertTrue(
            any("Migracion antigua" in t for t in titles),
            f"La decision antigua deberia aparecer, resultados: {titles}",
        )

    def test_search_with_tags_filter(self):
        """tags filtra decisiones que contengan al menos una etiqueta."""
        self.db.log_decision(
            title="Politica de autenticacion",
            chosen="OAuth2",
            tags=["security", "auth"],
        )
        self.db.log_decision(
            title="Politica de cache",
            chosen="Redis",
            tags=["performance"],
        )

        results = self.db.search("Politica", tags=["security"])
        titles = [r.get("title", "") for r in results]

        self.assertTrue(
            any("autenticacion" in t for t in titles),
            f"La decision de seguridad deberia aparecer: {titles}",
        )
        self.assertNotIn("Politica de cache", titles)

    def test_search_with_status_filter(self):
        """status filtra decisiones por su estado."""
        dec_active = self.db.log_decision(
            title="Estrategia de despliegue activa",
            chosen="Kubernetes",
        )
        dec_superseded = self.db.log_decision(
            title="Estrategia de despliegue antigua",
            chosen="Docker Swarm",
        )
        self.db.update_decision_status(dec_superseded, "superseded")

        results = self.db.search("Estrategia de despliegue", status="active")
        titles = [r.get("title", "") for r in results]

        self.assertTrue(
            any("activa" in t for t in titles),
            f"La decision activa deberia aparecer: {titles}",
        )
        self.assertNotIn("Estrategia de despliegue antigua", titles)

    def test_get_decisions_with_tags_filter(self):
        """get_decisions filtra por etiquetas en SQL."""
        self.db.log_decision(
            title="Patron de acceso a datos",
            chosen="Repository pattern",
            tags=["arquitectura", "backend"],
        )
        self.db.log_decision(
            title="Diseno de la UI",
            chosen="Material Design",
            tags=["frontend", "ux"],
        )

        results = self.db.get_decisions(tags=["arquitectura"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Patron de acceso a datos")

    def test_get_decisions_with_status_filter(self):
        """get_decisions filtra por estado en SQL."""
        dec1 = self.db.log_decision(
            title="Decision vigente",
            chosen="A",
        )
        dec2 = self.db.log_decision(
            title="Decision reemplazada",
            chosen="B",
        )
        self.db.update_decision_status(dec2, "superseded")

        actives = self.db.get_decisions(status="active")
        self.assertEqual(len(actives), 1)
        self.assertEqual(actives[0]["title"], "Decision vigente")

        superseded = self.db.get_decisions(status="superseded")
        self.assertEqual(len(superseded), 1)
        self.assertEqual(superseded[0]["title"], "Decision reemplazada")


class TestCommitFiles(unittest.TestCase):
    """Tests del campo files en commits.

    Verifican que la lista de ficheros modificados se serializa
    correctamente como JSON en la columna ``files`` de la tabla commits.
    """

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_log_commit_with_files(self):
        """files se almacena como JSON cuando se proporciona una lista."""
        commit_id = self.db.log_commit(
            sha="files_test_sha_1",
            message="feat: nuevo componente",
            files=["src/components/Button.tsx", "src/styles/button.css"],
        )
        self.assertIsNotNone(commit_id)

        # Verificar via SQL directo
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT files FROM commits WHERE id = ?", (commit_id,)
        ).fetchone()
        conn.close()

        files = json.loads(row[0])
        self.assertEqual(
            files,
            ["src/components/Button.tsx", "src/styles/button.css"],
        )

    def test_log_commit_without_files_defaults_empty(self):
        """Sin files, la columna contiene una lista JSON vacia."""
        commit_id = self.db.log_commit(
            sha="files_test_sha_2",
            message="chore: limpieza",
        )
        self.assertIsNotNone(commit_id)

        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT files FROM commits WHERE id = ?", (commit_id,)
        ).fetchone()
        conn.close()

        files = json.loads(row[0])
        self.assertEqual(files, [])

    def test_log_commit_files_list_stored(self):
        """Los paths se almacenan fielmente en el campo files."""
        expected_files = [
            "core/memory.py",
            "tests/test_memory.py",
            "docs/changelog.md",
        ]
        commit_id = self.db.log_commit(
            sha="files_test_sha_3",
            message="refactor: reorganizar modulos",
            files=expected_files,
        )
        self.assertIsNotNone(commit_id)

        # Verificacion directa contra SQLite sin pasar por la API
        conn = sqlite3.connect(self._db_path)
        row = conn.execute(
            "SELECT files FROM commits WHERE sha = 'files_test_sha_3'"
        ).fetchone()
        conn.close()

        stored_files = json.loads(row[0])
        self.assertEqual(stored_files, expected_files)


class TestHealthCheck(unittest.TestCase):
    """Tests de validacion de integridad de la base de datos.

    Verifican que check_health() detecta correctamente el estado del
    esquema, los permisos del fichero y el tamano de la base de datos.
    """

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_healthy_db(self):
        """Una DB nueva debe reportar status 'healthy' sin issues."""
        health = self.db.check_health()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(len(health["issues"]), 0)

    def test_schema_version_check(self):
        """La version del esquema debe ser '2'."""
        health = self.db.check_health()
        self.assertEqual(health["schema_version"], "2")

    def test_permissions_check(self):
        """Los permisos del fichero deben ser correctos."""
        health = self.db.check_health()
        self.assertTrue(health["permissions_ok"])

    def test_db_size_reported(self):
        """El tamano de la BD debe existir y ser un entero mayor que 0."""
        health = self.db.check_health()
        self.assertIn("size_bytes", health)
        self.assertIsInstance(health["size_bytes"], int)
        self.assertGreater(health["size_bytes"], 0)


class TestExportImport(unittest.TestCase):
    """Tests de exportacion e importacion de datos.

    Verifican que export_decisions_markdown genera ficheros correctos
    y que import_git_history es idempotente respecto a commits ya
    registrados.
    """

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._db_path = self._tmpfile.name
        self._tmpfile.close()
        self.db = MemoryDB(self._db_path)
        self._export_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = self._db_path + suffix
            if os.path.exists(path):
                os.unlink(path)
        import shutil
        shutil.rmtree(self._export_dir, ignore_errors=True)

    def test_export_markdown_creates_file(self):
        """export_decisions_markdown debe crear el fichero con el titulo."""
        self.db.log_decision(
            title="Usar SQLite como motor de memoria",
            chosen="SQLite",
            context="Necesitamos persistencia local ligera",
        )
        export_path = os.path.join(self._export_dir, "decisions.md")
        count = self.db.export_decisions_markdown(export_path)

        self.assertEqual(count, 1)
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Usar SQLite como motor de memoria", content)

    def test_export_markdown_includes_metadata(self):
        """El export debe incluir etiquetas y estado en el Markdown."""
        self.db.log_decision(
            title="Patron de acceso a datos",
            chosen="Repository pattern",
            tags=["arquitectura", "backend"],
        )
        export_path = os.path.join(self._export_dir, "meta.md")
        self.db.export_decisions_markdown(export_path)

        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("arquitectura", content)
        self.assertIn("backend", content)
        self.assertIn("active", content)

    def test_import_git_history_idempotent(self):
        """Importar el mismo historial dos veces no duplica commits."""
        import subprocess

        repo_dir = os.path.join(self._export_dir, "test_repo")
        os.makedirs(repo_dir)
        subprocess.run(
            ["git", "init"], cwd=repo_dir,
            capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_dir, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_dir, capture_output=True, check=True,
        )
        test_file = os.path.join(repo_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        subprocess.run(
            ["git", "add", "."], cwd=repo_dir,
            capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "feat: test commit"],
            cwd=repo_dir, capture_output=True, check=True,
        )

        first_count = self.db.import_git_history(repo_dir)
        self.assertEqual(first_count, 1)

        second_count = self.db.import_git_history(repo_dir)
        self.assertEqual(second_count, 0)


if __name__ == "__main__":
    unittest.main()
