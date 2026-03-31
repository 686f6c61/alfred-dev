#!/usr/bin/env python3
"""
Tests para la capa de sincronizacion SQLite -> memoria nativa de Claude Code.

Cobertura:
- Resolucion de memory_dir.
- Proyeccion de decisiones activas y archivadas.
- Generacion de iteracion activa, commits y resumen.
- Gestion de la seccion delimitada en MEMORY.md.
- Limpieza de ficheros huerfanos.
- Flujo end-to-end completo.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.memory import MemoryDB


class TestResolveMemoryDir(unittest.TestCase):
    """Verifica la resolucion del directorio de memoria nativa."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        # Simular estructura ~/.claude/projects/<hash>/memory/
        self._projects_base = os.path.join(self._tmpdir, "projects")
        self._project_dir = os.path.join(self._tmpdir, "mi-proyecto")
        os.makedirs(self._project_dir)

        # Convencion de Claude Code: path con / -> -
        mangled = self._project_dir.replace(os.sep, "-")
        if not mangled.startswith("-"):
            mangled = "-" + mangled
        self._memory_dir = os.path.join(self._projects_base, mangled, "memory")
        os.makedirs(self._memory_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_encuentra_directorio_existente(self):
        """Localiza el directorio de memoria cuando existe."""
        from core.memory_sync import resolve_memory_dir

        result = resolve_memory_dir(self._project_dir, self._projects_base)
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("memory"))
        self.assertTrue(os.path.isdir(result))

    def test_crea_directorio_si_no_existe(self):
        """Crea el directorio de memoria si no existe previamente."""
        from core.memory_sync import resolve_memory_dir

        base = os.path.join(self._tmpdir, "nuevo-base")
        result = resolve_memory_dir(
            os.path.join(self._tmpdir, "fantasma"),
            base,
        )
        self.assertIsNotNone(result)
        self.assertTrue(os.path.isdir(result))
        self.assertTrue(result.endswith("memory"))

    def test_devuelve_none_si_no_puede_crear(self):
        """Devuelve None si el directorio no se puede crear (permisos)."""
        from core.memory_sync import resolve_memory_dir
        from unittest.mock import patch

        with patch("os.makedirs", side_effect=OSError("permiso denegado")):
            result = resolve_memory_dir(
                os.path.join(self._tmpdir, "fantasma"),
                os.path.join(self._tmpdir, "bloqueado"),
            )
        self.assertIsNone(result)


class SyncTestBase(unittest.TestCase):
    """Clase base con entorno completo: DB poblada + MemorySync."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, ".claude", "alfred-memory.db")
        os.makedirs(os.path.dirname(self._db_path))
        self._memory_dir = os.path.join(self._tmpdir, "memory")
        os.makedirs(self._memory_dir)

        self.db = MemoryDB(self._db_path)
        from core.memory_sync import MemorySync
        self.sync = MemorySync(self.db, self._memory_dir)

        # Crear datos de prueba
        self.iter_id = self.db.start_iteration(
            command="feature", description="Sistema de cache"
        )
        self.d1_id = self.db.log_decision(
            title="Cache con Redis",
            chosen="Redis por latencia sub-ms",
            context="Necesitamos cache para reducir latencia",
            alternatives=["Memcached", "Cache en memoria"],
            rationale="Redis ofrece TTL nativo y persistencia opcional",
            impact="high",
            phase="arquitectura",
            tags=["cache", "infra"],
            iteration_id=self.iter_id,
        )
        self.d2_id = self.db.log_decision(
            title="Autenticacion con sesiones",
            chosen="Sesiones server-side",
            context="Requisitos de compliance",
            alternatives=["JWT"],
            rationale="Compliance exige revocacion inmediata",
            impact="critical",
            phase="arquitectura",
            tags=["auth", "security"],
            iteration_id=self.iter_id,
        )

    def tearDown(self):
        self.db.close()
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)


class TestSyncDecisions(SyncTestBase):
    """Verifica la proyeccion de decisiones a ficheros .md."""

    def test_genera_fichero_decision_activa(self):
        """sync_decision genera un fichero con frontmatter correcto."""
        self.sync.sync_decision(self.d1_id)

        path = os.path.join(self._memory_dir, f"alfred-decision-{self.d1_id}.md")
        self.assertTrue(os.path.isfile(path))

        with open(path, "r") as f:
            content = f.read()

        self.assertIn("source: alfred-memory", content)
        self.assertIn(f"source_id: {self.d1_id}", content)
        self.assertIn("Cache con Redis", content)
        self.assertIn("Redis por latencia sub-ms", content)
        self.assertIn("Memcached", content)
        self.assertIn("TTL nativo", content)

    def test_decision_archivada_no_genera_fichero_individual(self):
        """Una decision supersedida no genera fichero individual."""
        self.db.update_decision_status(self.d1_id, "superseded")
        self.sync.sync_decision(self.d1_id)

        individual = os.path.join(
            self._memory_dir, f"alfred-decision-{self.d1_id}.md"
        )
        self.assertFalse(os.path.isfile(individual))

        # Pero debe estar en el archivo consolidado
        archived = os.path.join(self._memory_dir, "alfred-decisions-archived.md")
        self.assertTrue(os.path.isfile(archived))
        with open(archived, "r") as f:
            content = f.read()
        self.assertIn(f"D#{self.d1_id}", content)
        self.assertIn("superseded", content)

    def test_decision_archivada_borra_fichero_previo(self):
        """Si una decision tenia fichero y se archiva, el fichero se borra."""
        # Primero generar el fichero como activa
        self.sync.sync_decision(self.d1_id)
        path = os.path.join(self._memory_dir, f"alfred-decision-{self.d1_id}.md")
        self.assertTrue(os.path.isfile(path))

        # Archivar y re-sync
        self.db.update_decision_status(self.d1_id, "superseded")
        self.sync.sync_decision(self.d1_id)
        self.assertFalse(os.path.isfile(path))


class TestSyncAll(SyncTestBase):
    """Verifica la sincronizacion completa."""

    def test_genera_todos_los_ficheros(self):
        """sync_all genera resumen, iteracion, decisiones."""
        result = self.sync.sync_all()

        self.assertEqual(result["errors"], 0)
        self.assertGreater(result["synced"], 0)

        self.assertTrue(os.path.isfile(
            os.path.join(self._memory_dir, "alfred-summary.md")
        ))
        self.assertTrue(os.path.isfile(
            os.path.join(self._memory_dir, "alfred-iteration-active.md")
        ))
        self.assertTrue(os.path.isfile(
            os.path.join(self._memory_dir, f"alfred-decision-{self.d1_id}.md")
        ))
        self.assertTrue(os.path.isfile(
            os.path.join(self._memory_dir, f"alfred-decision-{self.d2_id}.md")
        ))

    def test_resumen_contiene_estadisticas(self):
        """El resumen narrativo incluye contadores y decisiones clave."""
        self.sync.sync_all()

        with open(os.path.join(self._memory_dir, "alfred-summary.md"), "r") as f:
            content = f.read()

        self.assertIn("2 decisiones activas", content)
        self.assertIn("Cache con Redis", content)
        self.assertIn("Autenticacion con sesiones", content)
        self.assertIn("source: alfred-memory", content)

    def test_iteracion_activa_con_datos(self):
        """El fichero de iteracion activa contiene comando y descripcion."""
        self.sync.sync_all()

        with open(
            os.path.join(self._memory_dir, "alfred-iteration-active.md"), "r"
        ) as f:
            content = f.read()

        self.assertIn("feature", content)
        self.assertIn("Sistema de cache", content)
        self.assertIn("source: alfred-memory", content)


class TestUpdateIndex(SyncTestBase):
    """Verifica la gestion de MEMORY.md con marcadores."""

    def test_crea_seccion_en_memory_md_existente(self):
        """Anade la seccion delimitada a un MEMORY.md con contenido previo."""
        memory_md = os.path.join(self._memory_dir, "MEMORY.md")
        with open(memory_md, "w") as f:
            f.write("# Mi proyecto\n\nContenido manual.\n")

        self.sync.sync_all()

        with open(memory_md, "r") as f:
            content = f.read()

        self.assertIn("Contenido manual.", content)
        self.assertIn("<!-- ALFRED-SYNC:START -->", content)
        self.assertIn("<!-- ALFRED-SYNC:END -->", content)
        self.assertIn("alfred-summary.md", content)

    def test_no_duplica_bloque_en_segunda_sync(self):
        """Dos sync seguidos no duplican los marcadores."""
        self.sync.sync_all()
        self.sync.sync_all()

        memory_md = os.path.join(self._memory_dir, "MEMORY.md")
        with open(memory_md, "r") as f:
            content = f.read()

        self.assertEqual(content.count("<!-- ALFRED-SYNC:START -->"), 1)
        self.assertEqual(content.count("<!-- ALFRED-SYNC:END -->"), 1)

    def test_crea_memory_md_si_no_existe(self):
        """Si MEMORY.md no existe, lo crea con la seccion de Alfred."""
        memory_md = os.path.join(self._memory_dir, "MEMORY.md")
        self.assertFalse(os.path.isfile(memory_md))

        self.sync.sync_all()

        self.assertTrue(os.path.isfile(memory_md))
        with open(memory_md, "r") as f:
            content = f.read()
        self.assertIn("<!-- ALFRED-SYNC:START -->", content)


class TestCleanupStale(SyncTestBase):
    """Verifica la limpieza de ficheros huerfanos."""

    def test_borra_decision_ya_no_activa(self):
        """Ficheros de decisiones archivadas se eliminan."""
        self.sync.sync_all()
        path = os.path.join(self._memory_dir, f"alfred-decision-{self.d1_id}.md")
        self.assertTrue(os.path.isfile(path))

        self.db.update_decision_status(self.d1_id, "superseded")
        deleted = self.sync.cleanup_stale()

        self.assertFalse(os.path.isfile(path))
        self.assertEqual(len(deleted), 1)

    def test_no_toca_ficheros_manuales(self):
        """Ficheros sin source: alfred-memory no se borran."""
        manual = os.path.join(self._memory_dir, "alfred-notas.md")
        with open(manual, "w") as f:
            f.write("Mis notas personales.\n")

        deleted = self.sync.cleanup_stale()
        self.assertTrue(os.path.isfile(manual))
        self.assertNotIn(manual, deleted)

    def test_borra_iteracion_sin_activa(self):
        """Fichero de iteracion se borra si no hay iteracion activa."""
        self.sync.sync_all()
        iter_path = os.path.join(self._memory_dir, "alfred-iteration-active.md")
        self.assertTrue(os.path.isfile(iter_path))

        self.db.complete_iteration(self.iter_id)
        deleted = self.sync.cleanup_stale()

        self.assertFalse(os.path.isfile(iter_path))


class TestCommitsSync(SyncTestBase):
    """Verifica la proyeccion de commits."""

    def test_genera_fichero_commits(self):
        """sync_commits genera tabla con commits recientes."""
        self.db.log_commit(
            sha="abc1234567890",
            message="feat: setup inicial",
            author="dev",
            files_changed=3,
        )
        self.sync.sync_commits()

        path = os.path.join(self._memory_dir, "alfred-commits-recent.md")
        self.assertTrue(os.path.isfile(path))

        with open(path, "r") as f:
            content = f.read()

        self.assertIn("abc1234", content)
        self.assertIn("feat: setup inicial", content)
        self.assertIn("source: alfred-memory", content)

    def test_sin_commits_no_genera_fichero(self):
        """Si no hay commits, no se genera fichero."""
        self.sync.sync_commits()

        path = os.path.join(self._memory_dir, "alfred-commits-recent.md")
        self.assertFalse(os.path.isfile(path))


class TestEdgeCases(unittest.TestCase):
    """Tests para casos de borde no cubiertos en las clases anteriores."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, ".claude", "alfred-memory.db")
        os.makedirs(os.path.dirname(self._db_path))
        self._memory_dir = os.path.join(self._tmpdir, "memory")
        os.makedirs(self._memory_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_sync_all_db_vacia(self):
        """sync_all con DB sin datos no genera ficheros de decision."""
        db = MemoryDB(self._db_path)
        from core.memory_sync import MemorySync
        sync = MemorySync(db, self._memory_dir)

        result = sync.sync_all()
        self.assertEqual(result["errors"], 0)

        # Resumen debe existir pero con 0 decisiones
        summary = os.path.join(self._memory_dir, "alfred-summary.md")
        self.assertTrue(os.path.isfile(summary))
        with open(summary, "r") as f:
            content = f.read()
        self.assertIn("0 decisiones activas", content)

        # No debe haber ficheros de decision individual
        for entry in os.listdir(self._memory_dir):
            if entry.startswith("alfred-decision-") and entry != "alfred-decisions-archived.md":
                self.fail(f"Fichero de decision inesperado: {entry}")

        db.close()

    def test_marcador_start_sin_end(self):
        """Si MEMORY.md tiene START sin END, se limpia y recrea."""
        db = MemoryDB(self._db_path)
        from core.memory_sync import MemorySync
        sync = MemorySync(db, self._memory_dir)

        memory_md = os.path.join(self._memory_dir, "MEMORY.md")
        with open(memory_md, "w") as f:
            f.write("# Notas\n\n<!-- ALFRED-SYNC:START -->\nContenido roto\n")

        sync.sync_all()

        with open(memory_md, "r") as f:
            content = f.read()

        # Debe haber exactamente un par de marcadores validos
        self.assertEqual(content.count("<!-- ALFRED-SYNC:START -->"), 1)
        self.assertEqual(content.count("<!-- ALFRED-SYNC:END -->"), 1)
        # El contenido original debe conservarse
        self.assertIn("# Notas", content)

        db.close()

    def test_marcadores_en_orden_invertido(self):
        """Si los marcadores estan invertidos, se limpia y recrea."""
        db = MemoryDB(self._db_path)
        from core.memory_sync import MemorySync
        sync = MemorySync(db, self._memory_dir)

        memory_md = os.path.join(self._memory_dir, "MEMORY.md")
        with open(memory_md, "w") as f:
            f.write(
                "# Notas\n\n"
                "<!-- ALFRED-SYNC:END -->\nBasura\n"
                "<!-- ALFRED-SYNC:START -->\n"
            )

        sync.sync_all()

        with open(memory_md, "r") as f:
            content = f.read()

        self.assertEqual(content.count("<!-- ALFRED-SYNC:START -->"), 1)
        self.assertEqual(content.count("<!-- ALFRED-SYNC:END -->"), 1)
        # Verificar que START aparece antes que END
        self.assertLess(
            content.index("<!-- ALFRED-SYNC:START -->"),
            content.index("<!-- ALFRED-SYNC:END -->"),
        )

        db.close()

    def test_decision_con_campos_none(self):
        """Decisiones con campos opcionales a None no rompen la proyeccion."""
        db = MemoryDB(self._db_path)
        from core.memory_sync import MemorySync
        sync = MemorySync(db, self._memory_dir)

        db.start_iteration(command="test", description=None)
        d_id = db.log_decision(
            title="Minima",
            chosen="Opcion unica",
            # context, alternatives, rationale, impact, phase, tags: todo None
        )

        sync.sync_decision(d_id)

        path = os.path.join(self._memory_dir, f"alfred-decision-{d_id}.md")
        self.assertTrue(os.path.isfile(path))
        with open(path, "r") as f:
            content = f.read()
        self.assertIn("Minima", content)
        self.assertIn("Opcion unica", content)
        self.assertIn("source: alfred-memory", content)

        db.close()

    def test_sync_decision_funciona_mas_alla_de_1000_registros(self):
        """sync_decision debe recuperar una decision fuera del primer batch."""
        db = MemoryDB(self._db_path)
        from core.memory_sync import MemorySync
        sync = MemorySync(db, self._memory_dir)

        db.start_iteration(command="test", description="volumen")
        last_id = None
        for index in range(1005):
            last_id = db.log_decision(
                title=f"Decision {index}",
                chosen=f"Opcion {index}",
            )

        sync.sync_decision(last_id)

        path = os.path.join(self._memory_dir, f"alfred-decision-{last_id}.md")
        self.assertTrue(os.path.isfile(path))
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("Decision 1004", content)

        db.close()


class TestE2E(unittest.TestCase):
    """Test end-to-end del flujo completo."""

    def test_flujo_completo(self):
        """Crea datos, sincroniza, archiva, re-sincroniza."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmpdir, ".claude", "alfred-memory.db")
            os.makedirs(os.path.dirname(db_path))
            memory_dir = os.path.join(tmpdir, "memory")
            os.makedirs(memory_dir)

            # MEMORY.md preexistente
            memory_md = os.path.join(memory_dir, "MEMORY.md")
            with open(memory_md, "w") as f:
                f.write("# Proyecto de prueba\n\nNotas manuales del usuario.\n")

            db = MemoryDB(db_path)
            from core.memory_sync import MemorySync
            sync = MemorySync(db, memory_dir)

            # 1. Crear iteracion con decisiones y commit
            db.start_iteration(command="feature", description="E2E test")
            d1 = db.log_decision(
                title="Framework web",
                chosen="FastAPI",
                alternatives=["Flask", "Django"],
                rationale="Rendimiento y tipado nativo",
                impact="high",
                phase="arquitectura",
                tags=["backend"],
            )
            d2 = db.log_decision(
                title="Base de datos",
                chosen="PostgreSQL",
                impact="critical",
                phase="arquitectura",
            )
            db.log_commit(
                sha="abc1234567890",
                message="feat: setup inicial",
                author="dev",
            )

            # 2. Sync completo
            result = sync.sync_all()
            self.assertEqual(result["errors"], 0)

            # 3. Verificar ficheros
            self.assertTrue(os.path.isfile(
                os.path.join(memory_dir, f"alfred-decision-{d1}.md")
            ))
            self.assertTrue(os.path.isfile(
                os.path.join(memory_dir, f"alfred-decision-{d2}.md")
            ))
            self.assertTrue(os.path.isfile(
                os.path.join(memory_dir, "alfred-summary.md")
            ))
            self.assertTrue(os.path.isfile(
                os.path.join(memory_dir, "alfred-iteration-active.md")
            ))
            self.assertTrue(os.path.isfile(
                os.path.join(memory_dir, "alfred-commits-recent.md")
            ))

            # 4. MEMORY.md mantiene contenido manual
            with open(memory_md, "r") as f:
                index = f.read()
            self.assertIn("Notas manuales del usuario.", index)
            self.assertIn("<!-- ALFRED-SYNC:START -->", index)
            self.assertIn("alfred-summary.md", index)

            # 5. Resumen con datos correctos
            with open(os.path.join(memory_dir, "alfred-summary.md"), "r") as f:
                summary = f.read()
            self.assertIn("2 decisiones activas", summary)
            self.assertIn("Framework web", summary)

            # 6. Archivar y re-sync
            db.update_decision_status(d1, "superseded")
            sync.sync_decision(d1)
            sync.sync_summary()
            sync.update_index()

            self.assertFalse(os.path.isfile(
                os.path.join(memory_dir, f"alfred-decision-{d1}.md")
            ))
            archived = os.path.join(memory_dir, "alfred-decisions-archived.md")
            self.assertTrue(os.path.isfile(archived))
            with open(archived, "r") as f:
                arch = f.read()
            self.assertIn("Framework web", arch)
            self.assertIn("superseded", arch)

            # 7. Resumen actualizado
            with open(os.path.join(memory_dir, "alfred-summary.md"), "r") as f:
                summary2 = f.read()
            self.assertIn("1 decisiones activas", summary2)

            db.close()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
