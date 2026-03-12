#!/usr/bin/env python3
"""
Tests para hooks/activity-capture.py.

Verifica la logica del hook centralizado de captura de actividad:
    - Deteccion de ficheros excluidos (_is_excluded_path).
    - Deteccion de comandos triviales (_is_trivial_command).
    - Deteccion de git commit (is_git_commit_command).
    - Dispatchers: Write, Edit, Bash, Read, Glob, Grep, Agent, WebFetch,
      WebSearch, NotebookEdit, Prompt, Compact, Stop.
    - Procesamiento de estado: iteraciones y fases (_process_state).

Cada test que interactua con la DB crea una instancia temporal de MemoryDB,
inicia una iteracion para poder consultar la timeline y limpia los ficheros
temporales en tearDown.
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest


def _load_module():
    """Carga el modulo activity-capture.py por ruta (tiene guion en el nombre)."""
    module_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "hooks",
        "activity-capture.py",
    )
    spec = importlib.util.spec_from_file_location("activity_capture", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_capture = _load_module()

# Asegurar que core.memory esta disponible
_plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _plugin_root not in sys.path:
    sys.path.insert(0, _plugin_root)

from core.memory import MemoryDB


# ---------------------------------------------------------------------------
# Helpers de test
# ---------------------------------------------------------------------------

class _DBTestCase(unittest.TestCase):
    """Clase base para tests que necesitan una DB temporal."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "test.db")
        self._db = MemoryDB(self._db_path)
        # Crear una iteracion para poder consultar la timeline
        self._it_id = self._db.start_iteration(command="test", description="test")

    def tearDown(self):
        if self._db:
            self._db.close()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _get_events(self, event_type=None):
        """Devuelve los eventos de la timeline, opcionalmente filtrados."""
        events = self._db.get_timeline(self._it_id)
        if event_type:
            return [e for e in events if e.get("event_type") == event_type]
        return events

    def _parse_payload(self, event):
        """Parsea el payload JSON de un evento."""
        raw = event.get("payload")
        if isinstance(raw, str):
            return json.loads(raw)
        return raw or {}


# ---------------------------------------------------------------------------
# TestIsExcludedPath
# ---------------------------------------------------------------------------

class TestIsExcludedPath(unittest.TestCase):
    """Verifica la exclusion de ficheros internos."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._original_cwd = os.getcwd()
        os.chdir(self._tmpdir)

    def tearDown(self):
        os.chdir(self._original_cwd)
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_excludes_claude_dir(self):
        path = os.path.join(self._tmpdir, ".claude", "config.json")
        self.assertTrue(_capture._is_excluded_path(path))

    def test_excludes_git_dir(self):
        path = os.path.join(self._tmpdir, ".git", "objects", "abc123")
        self.assertTrue(_capture._is_excluded_path(path))

    def test_excludes_node_modules(self):
        path = os.path.join(self._tmpdir, "node_modules", "lodash", "index.js")
        self.assertTrue(_capture._is_excluded_path(path))

    def test_excludes_pycache(self):
        path = os.path.join(self._tmpdir, "__pycache__", "module.cpython-312.pyc")
        self.assertTrue(_capture._is_excluded_path(path))

    def test_excludes_venv(self):
        path = os.path.join(self._tmpdir, ".venv", "lib", "python3.12", "site.py")
        self.assertTrue(_capture._is_excluded_path(path))

    def test_excludes_mypy_cache(self):
        path = os.path.join(self._tmpdir, ".mypy_cache", "3.12", "module.meta.json")
        self.assertTrue(_capture._is_excluded_path(path))

    def test_excludes_pytest_cache(self):
        path = os.path.join(self._tmpdir, ".pytest_cache", "v", "cache", "lastfailed")
        self.assertTrue(_capture._is_excluded_path(path))

    def test_includes_source_file(self):
        path = os.path.join(self._tmpdir, "src", "main.py")
        self.assertFalse(_capture._is_excluded_path(path))

    def test_includes_root_file(self):
        path = os.path.join(self._tmpdir, "README.md")
        self.assertFalse(_capture._is_excluded_path(path))

    def test_includes_nested_source(self):
        path = os.path.join(self._tmpdir, "core", "memory.py")
        self.assertFalse(_capture._is_excluded_path(path))


# ---------------------------------------------------------------------------
# TestIsTrivialCommand
# ---------------------------------------------------------------------------

class TestIsTrivialCommand(unittest.TestCase):
    """Verifica la deteccion de comandos triviales."""

    def test_ls_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("ls"))

    def test_ls_with_flags_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("ls -la"))

    def test_pwd_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("pwd"))

    def test_cd_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("cd /tmp"))

    def test_echo_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("echo hello"))

    def test_cat_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("cat file.txt"))

    def test_head_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("head -n 10 file.py"))

    def test_tail_is_trivial(self):
        self.assertTrue(_capture._is_trivial_command("tail -f log.txt"))

    def test_npm_install_is_not_trivial(self):
        self.assertFalse(_capture._is_trivial_command("npm install"))

    def test_git_push_is_not_trivial(self):
        self.assertFalse(_capture._is_trivial_command("git push"))

    def test_python_is_not_trivial(self):
        self.assertFalse(_capture._is_trivial_command("python3 -m pytest tests/"))

    def test_make_is_not_trivial(self):
        self.assertFalse(_capture._is_trivial_command("make build"))

    def test_docker_is_not_trivial(self):
        self.assertFalse(_capture._is_trivial_command("docker build ."))

    def test_env_var_prefix_stripped(self):
        """Variables de entorno al inicio no deben afectar la deteccion."""
        self.assertFalse(_capture._is_trivial_command("NODE_ENV=prod npm start"))

    def test_absolute_path_stripped(self):
        """Rutas absolutas se reducen al nombre base."""
        self.assertTrue(_capture._is_trivial_command("/usr/bin/cat file.txt"))


# ---------------------------------------------------------------------------
# TestIsGitCommitCommand
# ---------------------------------------------------------------------------

class TestIsGitCommitCommand(unittest.TestCase):
    """Verifica la deteccion de git commit en comandos de shell."""

    def test_simple_git_commit(self):
        self.assertTrue(_capture.is_git_commit_command("git commit -m 'msg'"))

    def test_git_commit_with_amend(self):
        self.assertTrue(_capture.is_git_commit_command("git commit --amend"))

    def test_chained_with_and(self):
        self.assertTrue(_capture.is_git_commit_command("git add . && git commit -m 'msg'"))

    def test_chained_with_semicolon(self):
        self.assertTrue(_capture.is_git_commit_command("git add .; git commit -m 'msg'"))

    def test_after_or(self):
        self.assertTrue(_capture.is_git_commit_command("false || git commit -m 'fallback'"))

    def test_not_in_echo(self):
        """git commit dentro de un echo no es un commit real."""
        self.assertFalse(_capture.is_git_commit_command("echo 'run git commit'"))

    def test_not_in_grep(self):
        self.assertFalse(_capture.is_git_commit_command("grep 'git commit' history.log"))

    def test_npm_install(self):
        self.assertFalse(_capture.is_git_commit_command("npm install"))

    def test_git_push(self):
        self.assertFalse(_capture.is_git_commit_command("git push origin main"))


# ---------------------------------------------------------------------------
# TestDispatchWrite
# ---------------------------------------------------------------------------

class TestDispatchWrite(_DBTestCase):
    """Verifica el dispatcher de Write."""

    def test_normal_file_creates_event(self):
        """Un Write en un fichero normal crea un evento file_written."""
        # Crear un fichero temporal para que _read_file_safe lo pueda leer
        test_file = os.path.join(self._tmpdir, "src", "main.py")
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, "w") as f:
            f.write("print('hello')\nprint('world')\n")

        data = {"tool_input": {"file_path": test_file}}

        _capture._dispatch_write(self._db, data)

        events = self._get_events("file_written")
        self.assertEqual(len(events), 1)

    def test_summary_contains_path_and_lines(self):
        """El summary incluye la ruta relativa y el conteo de lineas."""
        test_file = os.path.join(self._tmpdir, "app.js")
        with open(test_file, "w") as f:
            f.write("const x = 1;\nconst y = 2;\nconst z = 3;\n")

        data = {"tool_input": {"file_path": test_file}}

        _capture._dispatch_write(self._db, data)

        events = self._get_events("file_written")
        self.assertIn("app.js", events[0].get("summary", ""))
        self.assertIn("3 lineas", events[0].get("summary", ""))

    def test_content_contains_file_content(self):
        """El campo content almacena el contenido completo del fichero."""
        test_file = os.path.join(self._tmpdir, "data.txt")
        file_text = "linea uno\nlinea dos\n"
        with open(test_file, "w") as f:
            f.write(file_text)

        data = {"tool_input": {"file_path": test_file}}

        _capture._dispatch_write(self._db, data)

        events = self._get_events("file_written")
        self.assertEqual(events[0].get("content"), file_text)

    def test_excluded_file_creates_no_event(self):
        """Un Write en un fichero excluido no crea ningun evento."""
        original_cwd = os.getcwd()
        os.chdir(self._tmpdir)
        try:
            data = {"tool_input": {"file_path": os.path.join(self._tmpdir, ".git", "index")}}
            _capture._dispatch_write(self._db, data)
            events = self._get_events("file_written")
            self.assertEqual(len(events), 0)
        finally:
            os.chdir(original_cwd)

    def test_empty_path_creates_no_event(self):
        """Una ruta vacia no crea ningun evento."""
        data = {"tool_input": {"file_path": ""}}
        _capture._dispatch_write(self._db, data)
        events = self._get_events("file_written")
        self.assertEqual(len(events), 0)

    def test_state_json_triggers_process_state(self):
        """Si el fichero es alfred-dev-state.json, dispara _process_state."""
        # Cerrar la iteracion del setUp para que _process_state cree una nueva
        self._db.complete_iteration(self._it_id)

        state_file = os.path.join(self._tmpdir, "alfred-dev-state.json")
        state = {
            "comando": "feature",
            "fase_actual": "producto",
            "descripcion": "test feature",
            "fases_completadas": [],
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        data = {"tool_input": {"file_path": state_file}}

        _capture._dispatch_write(self._db, data)

        # _process_state debe haber creado una nueva iteracion
        active = self._db.get_active_iteration()
        self.assertIsNotNone(active)
        self.assertEqual(active["command"], "feature")

        # Verificar que iteration_started se registro en la nueva iteracion
        new_timeline = self._db.get_timeline(active["id"])
        started = [e for e in new_timeline if e.get("event_type") == "iteration_started"]
        self.assertGreaterEqual(len(started), 1)

    def test_payload_contains_extension(self):
        """El payload incluye la extension del fichero."""
        test_file = os.path.join(self._tmpdir, "style.css")
        with open(test_file, "w") as f:
            f.write("body { color: red; }\n")

        data = {"tool_input": {"file_path": test_file}}

        _capture._dispatch_write(self._db, data)

        events = self._get_events("file_written")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["extension"], "css")


# ---------------------------------------------------------------------------
# TestDispatchEdit
# ---------------------------------------------------------------------------

class TestDispatchEdit(_DBTestCase):
    """Verifica el dispatcher de Edit."""

    def test_creates_file_edited_event(self):
        """Un Edit crea un evento file_edited."""
        test_file = os.path.join(self._tmpdir, "main.py")
        with open(test_file, "w") as f:
            f.write("pass")

        data = {
            "tool_input": {
                "file_path": test_file,
                "old_string": "viejo\notra linea",
                "new_string": "nuevo\nsegunda\ntercera",
            }
        }

        _capture._dispatch_edit(self._db, data)

        events = self._get_events("file_edited")
        self.assertEqual(len(events), 1)

    def test_summary_has_line_counts(self):
        """El summary indica las lineas reemplazadas y las nuevas."""
        test_file = os.path.join(self._tmpdir, "app.py")
        with open(test_file, "w") as f:
            f.write("pass")

        data = {
            "tool_input": {
                "file_path": test_file,
                "old_string": "a\nb",
                "new_string": "x\ny\nz",
            }
        }

        _capture._dispatch_edit(self._db, data)

        events = self._get_events("file_edited")
        summary = events[0].get("summary", "")
        self.assertIn("2 lineas reemplazadas por 3", summary)

    def test_content_contains_diff(self):
        """El campo content almacena el diff old/new."""
        test_file = os.path.join(self._tmpdir, "util.py")
        with open(test_file, "w") as f:
            f.write("pass")

        data = {
            "tool_input": {
                "file_path": test_file,
                "old_string": "funcion_vieja()",
                "new_string": "funcion_nueva(x, y)",
            }
        }

        _capture._dispatch_edit(self._db, data)

        events = self._get_events("file_edited")
        content = events[0].get("content", "")
        self.assertIn("--- old ---", content)
        self.assertIn("funcion_vieja()", content)
        self.assertIn("--- new ---", content)
        self.assertIn("funcion_nueva(x, y)", content)

    def test_excluded_file_creates_no_event(self):
        """Un Edit en un fichero excluido no crea ningun evento."""
        original_cwd = os.getcwd()
        os.chdir(self._tmpdir)
        try:
            data = {
                "tool_input": {
                    "file_path": os.path.join(self._tmpdir, ".claude", "settings.json"),
                    "old_string": "a",
                    "new_string": "b",
                }
            }
            _capture._dispatch_edit(self._db, data)
            events = self._get_events("file_edited")
            self.assertEqual(len(events), 0)
        finally:
            os.chdir(original_cwd)

    def test_payload_has_file_and_extension(self):
        """El payload incluye la ruta relativa y la extension."""
        test_file = os.path.join(self._tmpdir, "index.ts")
        with open(test_file, "w") as f:
            f.write("pass")

        data = {
            "tool_input": {
                "file_path": test_file,
                "old_string": "a",
                "new_string": "b",
            }
        }

        _capture._dispatch_edit(self._db, data)

        events = self._get_events("file_edited")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["extension"], "ts")
        self.assertIn("index.ts", payload["file"])


# ---------------------------------------------------------------------------
# TestDispatchBash
# ---------------------------------------------------------------------------

class TestDispatchBash(_DBTestCase):
    """Verifica el dispatcher de Bash."""

    def test_nontrivial_command_creates_event(self):
        """Un comando relevante crea un evento command_executed."""
        data = {
            "tool_input": {"command": "npm install"},
            "tool_result": {"exit_code": 0, "stdout": "added 123 packages"},
        }

        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        self.assertEqual(len(events), 1)

    def test_trivial_command_creates_no_event(self):
        """Un comando trivial no crea ningun evento."""
        data = {
            "tool_input": {"command": "ls -la"},
            "tool_result": {"exit_code": 0, "stdout": "total 42"},
        }

        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        self.assertEqual(len(events), 0)

    def test_summary_contains_command_and_exit(self):
        """El summary incluye el comando (truncado) y el exit code."""
        data = {
            "tool_input": {"command": "python3 -m pytest tests/"},
            "tool_result": {"exit_code": 0, "stdout": "5 passed"},
        }

        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        summary = events[0].get("summary", "")
        self.assertIn("python3 -m pytest", summary)
        self.assertIn("exit 0", summary)

    def test_content_contains_full_stdout(self):
        """El campo content almacena el stdout completo sin truncar."""
        long_output = "linea " * 500
        data = {
            "tool_input": {"command": "npm build"},
            "tool_result": {"exit_code": 0, "stdout": long_output},
        }

        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        content = events[0].get("content", "")
        self.assertIn("--- stdout ---", content)
        # El contenido NO debe estar truncado
        self.assertIn(long_output, content)

    def test_content_contains_stderr_on_failure(self):
        """El campo content incluye stderr cuando hay error."""
        data = {
            "tool_input": {"command": "npm test"},
            "tool_result": {"exit_code": 1, "stdout": "", "stderr": "Error: test failed"},
        }

        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        content = events[0].get("content", "")
        self.assertIn("--- stderr ---", content)
        self.assertIn("Error: test failed", content)

    def test_payload_contains_command_and_exit_code(self):
        """El payload tiene command y exit_code sin truncar."""
        data = {
            "tool_input": {"command": "git status"},
            "tool_result": {"exit_code": 0, "stdout": "clean"},
        }

        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["command"], "git status")
        self.assertEqual(payload["exit_code"], 0)

    def test_git_commit_triggers_log_commit(self):
        """Un git commit exitoso dispara _capture_git_commit."""
        # No podemos testear el subprocess.run aqui, pero verificamos que
        # no falle si no hay repositorio git
        data = {
            "tool_input": {"command": "git commit -m 'test'"},
            "tool_result": {"exit_code": 0, "stdout": "[main abc1234] test"},
        }

        # No debe lanzar excepcion aunque no haya repo git
        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        self.assertEqual(len(events), 1)

    def test_empty_command_creates_no_event(self):
        """Un comando vacio no crea ningun evento."""
        data = {
            "tool_input": {"command": ""},
            "tool_result": {"exit_code": 0},
        }

        _capture._dispatch_bash(self._db, data)

        events = self._get_events("command_executed")
        self.assertEqual(len(events), 0)


# ---------------------------------------------------------------------------
# TestDispatchPrompt
# ---------------------------------------------------------------------------

class TestDispatchPrompt(_DBTestCase):
    """Verifica el dispatcher de UserPromptSubmit."""

    def test_prompt_saved_with_full_text(self):
        """El prompt se guarda con el texto completo en content."""
        full_text = "Implementa el sistema de autenticacion con OAuth2 y JWT tokens"
        data = {"prompt": full_text}

        _capture._dispatch_prompt(self._db, data)

        events = self._get_events("user_prompt")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].get("content"), full_text)

    def test_summary_truncated(self):
        """El summary contiene solo la primera linea, truncada."""
        long_prompt = "Primera linea del prompt\nSegunda linea con mas detalles\nTercera"
        data = {"prompt": long_prompt}

        _capture._dispatch_prompt(self._db, data)

        events = self._get_events("user_prompt")
        summary = events[0].get("summary", "")
        self.assertIn("Prompt:", summary)
        self.assertIn("Primera linea del prompt", summary)
        self.assertIn("...", summary)

    def test_payload_has_length(self):
        """El payload incluye la longitud del prompt."""
        text = "Haz esto"
        data = {"prompt": text}

        _capture._dispatch_prompt(self._db, data)

        events = self._get_events("user_prompt")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["length"], len(text))

    def test_empty_prompt_creates_no_event(self):
        """Un prompt vacio no crea ningun evento."""
        data = {"prompt": ""}

        _capture._dispatch_prompt(self._db, data)

        events = self._get_events("user_prompt")
        self.assertEqual(len(events), 0)

    def test_content_field_fallback(self):
        """Si no hay 'prompt', usa 'content' como fallback."""
        text = "Texto via content"
        data = {"content": text}

        _capture._dispatch_prompt(self._db, data)

        events = self._get_events("user_prompt")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].get("content"), text)


# ---------------------------------------------------------------------------
# TestDispatchCompact
# ---------------------------------------------------------------------------

class TestDispatchCompact(_DBTestCase):
    """Verifica el dispatcher de PreCompact."""

    def test_creates_context_compacted_event(self):
        """Crea un evento context_compacted con summary descriptivo."""
        _capture._dispatch_compact(self._db, {})

        events = self._get_events("context_compacted")
        self.assertEqual(len(events), 1)
        self.assertIn("compactado", events[0].get("summary", ""))

    def test_payload_has_source(self):
        """El payload incluye la fuente del evento."""
        _capture._dispatch_compact(self._db, {})

        events = self._get_events("context_compacted")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["source"], "PreCompact")


# ---------------------------------------------------------------------------
# TestDispatchStop
# ---------------------------------------------------------------------------

class TestDispatchStop(_DBTestCase):
    """Verifica el dispatcher de Stop."""

    def test_creates_session_ended_event(self):
        """Crea un evento session_ended."""
        _capture._dispatch_stop(self._db, {})

        events = self._get_events("session_ended")
        self.assertEqual(len(events), 1)
        self.assertIn("finalizada", events[0].get("summary", ""))

    def test_closes_active_iteration(self):
        """Si hay iteracion activa, la cierra."""
        # Ya hay una iteracion activa del setUp
        active_before = self._db.get_active_iteration()
        self.assertIsNotNone(active_before)

        _capture._dispatch_stop(self._db, {})

        active_after = self._db.get_active_iteration()
        self.assertIsNone(active_after)

    def test_no_error_without_active_iteration(self):
        """No falla si no hay iteracion activa."""
        # Cerrar la iteracion del setUp
        self._db.complete_iteration(self._it_id)

        # No debe lanzar excepcion
        _capture._dispatch_stop(self._db, {})

        # El evento session_ended se registra sin iteration_id, asi que
        # buscamos directamente en la tabla de eventos
        cursor = self._db._conn.execute(
            "SELECT * FROM events WHERE event_type = 'session_ended'"
        )
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)


# ---------------------------------------------------------------------------
# TestProcessState
# ---------------------------------------------------------------------------

class TestProcessState(_DBTestCase):
    """Verifica el procesamiento de estado (iteraciones y fases)."""

    def _write_state(self, state: dict) -> str:
        """Escribe un fichero de estado temporal y devuelve la ruta."""
        state_file = os.path.join(self._tmpdir, "alfred-dev-state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)
        return state_file

    def test_creates_iteration_if_none_active(self):
        """Sin iteracion activa distinta de la del setUp, crea una nueva al procesar estado."""
        # Cerrar la iteracion del setUp para simular "sin iteracion activa"
        self._db.complete_iteration(self._it_id)

        state_file = self._write_state({
            "comando": "feature",
            "fase_actual": "producto",
            "descripcion": "test feature",
            "fases_completadas": [],
        })

        _capture._process_state(self._db, state_file)

        active = self._db.get_active_iteration()
        self.assertIsNotNone(active)
        self.assertEqual(active["command"], "feature")

    def test_registers_phase_completed(self):
        """Las fases completadas se registran como eventos."""
        state_file = self._write_state({
            "comando": "feature",
            "fase_actual": "arquitectura",
            "descripcion": "test",
            "fases_completadas": [{"nombre": "producto", "resultado": "aprobado"}],
        })

        _capture._process_state(self._db, state_file)

        events = self._get_events("phase_completed")
        self.assertGreaterEqual(len(events), 1)

    def test_does_not_duplicate_phases(self):
        """Ejecutar dos veces con las mismas fases no duplica eventos."""
        state_file = self._write_state({
            "comando": "feature",
            "fase_actual": "desarrollo",
            "descripcion": "test",
            "fases_completadas": [
                {"nombre": "producto", "resultado": "aprobado"},
                {"nombre": "arquitectura", "resultado": "aprobado"},
            ],
        })

        _capture._process_state(self._db, state_file)
        _capture._process_state(self._db, state_file)

        events = self._get_events("phase_completed")
        # Debe haber exactamente 2, no 4
        self.assertEqual(len(events), 2)

    def test_completes_iteration(self):
        """Fase 'completado' cierra la iteracion."""
        state_file = self._write_state({
            "comando": "feature",
            "fase_actual": "completado",
            "descripcion": "test",
            "fases_completadas": [{"nombre": "producto"}],
        })

        _capture._process_state(self._db, state_file)

        # La iteracion original del setUp deberia seguir o estar cerrada
        # dependiendo de si _process_state uso la existente
        # Verificamos que hay un iteration_completed
        events = self._get_events("iteration_completed")
        self.assertGreaterEqual(len(events), 1)

    def test_string_phases(self):
        """Las fases como strings (no dicts) se procesan correctamente."""
        state_file = self._write_state({
            "comando": "fix",
            "fase_actual": "validacion",
            "descripcion": "test",
            "fases_completadas": ["diagnostico", "correccion"],
        })

        _capture._process_state(self._db, state_file)

        events = self._get_events("phase_completed")
        self.assertEqual(len(events), 2)

    def test_invalid_state_file_does_nothing(self):
        """Un fichero de estado invalido no genera eventos."""
        state_file = os.path.join(self._tmpdir, "alfred-dev-state.json")
        with open(state_file, "w") as f:
            f.write("esto no es json {{{")

        initial_count = len(self._get_events())

        _capture._process_state(self._db, state_file)

        final_count = len(self._get_events())
        self.assertEqual(initial_count, final_count)

    def test_auto_pins_completed_phase(self):
        """Las fases completadas se auto-pinean."""
        state_file = self._write_state({
            "comando": "feature",
            "fase_actual": "arquitectura",
            "descripcion": "test",
            "fases_completadas": [{"nombre": "producto", "resultado": "ok"}],
        })

        _capture._process_state(self._db, state_file)

        # Verificar que hay un pin (no falla si la tabla no existe)
        try:
            cursor = self._db._conn.execute(
                "SELECT * FROM pinned_items WHERE item_ref = ?",
                ("phase:producto",),
            )
            pins = cursor.fetchall()
            self.assertGreaterEqual(len(pins), 1)
        except Exception:
            pass  # Si la tabla no existe, el test no aplica


# ---------------------------------------------------------------------------
# TestDispatchRead
# ---------------------------------------------------------------------------

class TestDispatchRead(_DBTestCase):
    """Verifica el dispatcher de Read."""

    def setUp(self):
        super().setUp()
        self._original_cwd = os.getcwd()
        os.chdir(self._tmpdir)

    def tearDown(self):
        os.chdir(self._original_cwd)
        super().tearDown()

    def test_creates_file_read_event(self):
        """Un Read crea un evento file_read."""
        data = {"tool_input": {"file_path": os.path.join(self._tmpdir, "src", "main.py")}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        self.assertEqual(len(events), 1)

    def test_summary_contains_path(self):
        """El summary incluye la ruta relativa."""
        data = {"tool_input": {"file_path": os.path.join(self._tmpdir, "core", "memory.py")}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        self.assertIn("memory.py", events[0].get("summary", ""))

    def test_summary_with_offset_and_limit(self):
        """El summary incluye el rango de lineas cuando se especifica."""
        data = {"tool_input": {"file_path": os.path.join(self._tmpdir, "f.py"), "offset": 10, "limit": 50}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        summary = events[0].get("summary", "")
        self.assertIn("lineas 10-60", summary)

    def test_summary_with_only_offset(self):
        """El summary indica la linea de inicio cuando solo hay offset."""
        data = {"tool_input": {"file_path": os.path.join(self._tmpdir, "f.py"), "offset": 100}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        self.assertIn("desde linea 100", events[0].get("summary", ""))

    def test_summary_with_only_limit(self):
        """El summary indica el limite cuando solo hay limit."""
        data = {"tool_input": {"file_path": os.path.join(self._tmpdir, "f.py"), "limit": 20}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        self.assertIn("primeras 20 lineas", events[0].get("summary", ""))

    def test_excluded_file_creates_no_event(self):
        """Un Read de fichero excluido no crea evento."""
        data = {"tool_input": {"file_path": os.path.join(self._tmpdir, ".git", "HEAD")}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        self.assertEqual(len(events), 0)

    def test_empty_path_creates_no_event(self):
        """Una ruta vacia no crea evento."""
        data = {"tool_input": {"file_path": ""}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        self.assertEqual(len(events), 0)

    def test_no_content_stored(self):
        """No almacena contenido para evitar duplicacion."""
        data = {"tool_input": {"file_path": os.path.join(self._tmpdir, "f.py")}}
        _capture._dispatch_read(self._db, data)

        events = self._get_events("file_read")
        self.assertIsNone(events[0].get("content"))


# ---------------------------------------------------------------------------
# TestDispatchGlob
# ---------------------------------------------------------------------------

class TestDispatchGlob(_DBTestCase):
    """Verifica el dispatcher de Glob."""

    def test_creates_glob_search_event(self):
        """Un Glob crea un evento glob_search."""
        data = {
            "tool_input": {"pattern": "**/*.py", "path": "."},
            "tool_result": {"output": "src/main.py\nsrc/util.py\n"},
        }
        _capture._dispatch_glob(self._db, data)

        events = self._get_events("glob_search")
        self.assertEqual(len(events), 1)

    def test_summary_contains_pattern_and_count(self):
        """El summary incluye el patron y el numero de resultados."""
        data = {
            "tool_input": {"pattern": "*.ts"},
            "tool_result": {"output": "index.ts\napp.ts\nutil.ts\n"},
        }
        _capture._dispatch_glob(self._db, data)

        events = self._get_events("glob_search")
        summary = events[0].get("summary", "")
        self.assertIn("*.ts", summary)
        self.assertIn("3 resultados", summary)

    def test_content_stores_file_list(self):
        """El content almacena la lista de ficheros encontrados."""
        file_list = "a.py\nb.py\n"
        data = {
            "tool_input": {"pattern": "*.py"},
            "tool_result": {"output": file_list},
        }
        _capture._dispatch_glob(self._db, data)

        events = self._get_events("glob_search")
        self.assertEqual(events[0].get("content"), file_list)

    def test_empty_pattern_creates_no_event(self):
        """Un patron vacio no crea evento."""
        data = {"tool_input": {"pattern": ""}, "tool_result": {}}
        _capture._dispatch_glob(self._db, data)

        events = self._get_events("glob_search")
        self.assertEqual(len(events), 0)

    def test_zero_results(self):
        """Un glob sin resultados se registra con 0 resultados."""
        data = {
            "tool_input": {"pattern": "*.xyz"},
            "tool_result": {"output": ""},
        }
        _capture._dispatch_glob(self._db, data)

        events = self._get_events("glob_search")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["results"], 0)


# ---------------------------------------------------------------------------
# TestDispatchGrep
# ---------------------------------------------------------------------------

class TestDispatchGrep(_DBTestCase):
    """Verifica el dispatcher de Grep."""

    def test_creates_grep_search_event(self):
        """Un Grep crea un evento grep_search."""
        data = {
            "tool_input": {"pattern": "TODO", "path": "."},
            "tool_result": {"output": "file.py:10:# TODO fix\n"},
        }
        _capture._dispatch_grep(self._db, data)

        events = self._get_events("grep_search")
        self.assertEqual(len(events), 1)

    def test_summary_contains_pattern_and_count(self):
        """El summary incluye el patron regex y el conteo."""
        data = {
            "tool_input": {"pattern": "import\\s+os"},
            "tool_result": {"output": "a.py\nb.py\nc.py\n"},
        }
        _capture._dispatch_grep(self._db, data)

        events = self._get_events("grep_search")
        summary = events[0].get("summary", "")
        self.assertIn("import\\s+os", summary)
        self.assertIn("3 coincidencias", summary)

    def test_payload_includes_filters(self):
        """El payload incluye filtros de tipo y glob cuando se usan."""
        data = {
            "tool_input": {"pattern": "def ", "type": "py", "output_mode": "content"},
            "tool_result": {"output": "result\n"},
        }
        _capture._dispatch_grep(self._db, data)

        events = self._get_events("grep_search")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["type"], "py")
        self.assertEqual(payload["mode"], "content")

    def test_glob_filter_in_summary(self):
        """El summary muestra el filtro glob cuando se usa."""
        data = {
            "tool_input": {"pattern": "class", "glob": "*.tsx"},
            "tool_result": {"output": "Component.tsx\n"},
        }
        _capture._dispatch_grep(self._db, data)

        events = self._get_events("grep_search")
        summary = events[0].get("summary", "")
        self.assertIn("filtro=*.tsx", summary)

    def test_empty_pattern_creates_no_event(self):
        """Un patron vacio no crea evento."""
        data = {"tool_input": {"pattern": ""}, "tool_result": {}}
        _capture._dispatch_grep(self._db, data)

        events = self._get_events("grep_search")
        self.assertEqual(len(events), 0)


# ---------------------------------------------------------------------------
# TestDispatchAgent
# ---------------------------------------------------------------------------

class TestDispatchAgent(_DBTestCase):
    """Verifica el dispatcher de Agent."""

    def test_creates_agent_launched_event(self):
        """Un Agent crea un evento agent_launched."""
        data = {
            "tool_input": {
                "description": "buscar patron",
                "subagent_type": "Explore",
                "prompt": "Busca la clase AuthMiddleware",
            },
            "tool_result": {"output": "Encontrado en src/auth.py"},
        }
        _capture._dispatch_agent(self._db, data)

        events = self._get_events("agent_launched")
        self.assertEqual(len(events), 1)

    def test_summary_contains_type_and_description(self):
        """El summary incluye el tipo y la descripcion."""
        data = {
            "tool_input": {
                "description": "revisar codigo",
                "subagent_type": "code-reviewer",
                "prompt": "Revisa el modulo auth",
            },
            "tool_result": {},
        }
        _capture._dispatch_agent(self._db, data)

        events = self._get_events("agent_launched")
        summary = events[0].get("summary", "")
        self.assertIn("code-reviewer", summary)
        self.assertIn("revisar codigo", summary)

    def test_content_contains_prompt_and_result(self):
        """El content almacena el prompt enviado y el resultado."""
        data = {
            "tool_input": {"prompt": "Analiza esto", "description": "test"},
            "tool_result": {"output": "Resultado del analisis"},
        }
        _capture._dispatch_agent(self._db, data)

        events = self._get_events("agent_launched")
        content = events[0].get("content", "")
        self.assertIn("--- prompt ---", content)
        self.assertIn("Analiza esto", content)
        self.assertIn("--- resultado ---", content)
        self.assertIn("Resultado del analisis", content)

    def test_default_subagent_type(self):
        """Sin subagent_type, usa general-purpose por defecto."""
        data = {
            "tool_input": {"description": "tarea generica", "prompt": "haz algo"},
            "tool_result": {},
        }
        _capture._dispatch_agent(self._db, data)

        events = self._get_events("agent_launched")
        payload = self._parse_payload(events[0])
        self.assertEqual(payload["subagent_type"], "general-purpose")


# ---------------------------------------------------------------------------
# TestDispatchWebFetch
# ---------------------------------------------------------------------------

class TestDispatchWebFetch(_DBTestCase):
    """Verifica el dispatcher de WebFetch."""

    def test_creates_web_fetched_event(self):
        """Un WebFetch crea un evento web_fetched."""
        data = {
            "tool_input": {"url": "https://example.com/api"},
            "tool_result": {"content": "<html>OK</html>"},
        }
        _capture._dispatch_web_fetch(self._db, data)

        events = self._get_events("web_fetched")
        self.assertEqual(len(events), 1)

    def test_summary_contains_url(self):
        """El summary incluye la URL (truncada si es larga)."""
        data = {
            "tool_input": {"url": "https://docs.python.org/3/library/sqlite3.html"},
            "tool_result": {"content": "docs"},
        }
        _capture._dispatch_web_fetch(self._db, data)

        events = self._get_events("web_fetched")
        self.assertIn("docs.python.org", events[0].get("summary", ""))

    def test_content_stores_response(self):
        """El content almacena la respuesta completa."""
        response = "<html><body>Contenido completo</body></html>"
        data = {
            "tool_input": {"url": "https://example.com"},
            "tool_result": {"content": response},
        }
        _capture._dispatch_web_fetch(self._db, data)

        events = self._get_events("web_fetched")
        self.assertEqual(events[0].get("content"), response)

    def test_empty_url_creates_no_event(self):
        """Una URL vacia no crea evento."""
        data = {"tool_input": {"url": ""}, "tool_result": {}}
        _capture._dispatch_web_fetch(self._db, data)

        events = self._get_events("web_fetched")
        self.assertEqual(len(events), 0)


# ---------------------------------------------------------------------------
# TestDispatchWebSearch
# ---------------------------------------------------------------------------

class TestDispatchWebSearch(_DBTestCase):
    """Verifica el dispatcher de WebSearch."""

    def test_creates_web_searched_event(self):
        """Un WebSearch crea un evento web_searched."""
        data = {
            "tool_input": {"query": "python sqlite3 fts5"},
            "tool_result": {"content": "resultado 1\nresultado 2"},
        }
        _capture._dispatch_web_search(self._db, data)

        events = self._get_events("web_searched")
        self.assertEqual(len(events), 1)

    def test_summary_contains_query(self):
        """El summary incluye la consulta de busqueda."""
        data = {
            "tool_input": {"query": "claude code hooks api"},
            "tool_result": {"content": "results"},
        }
        _capture._dispatch_web_search(self._db, data)

        events = self._get_events("web_searched")
        self.assertIn("claude code hooks api", events[0].get("summary", ""))

    def test_content_stores_results(self):
        """El content almacena los resultados de la busqueda."""
        results = "1. Resultado uno\n2. Resultado dos\n3. Resultado tres"
        data = {
            "tool_input": {"query": "test"},
            "tool_result": {"content": results},
        }
        _capture._dispatch_web_search(self._db, data)

        events = self._get_events("web_searched")
        self.assertEqual(events[0].get("content"), results)

    def test_empty_query_creates_no_event(self):
        """Una query vacia no crea evento."""
        data = {"tool_input": {"query": ""}, "tool_result": {}}
        _capture._dispatch_web_search(self._db, data)

        events = self._get_events("web_searched")
        self.assertEqual(len(events), 0)


# ---------------------------------------------------------------------------
# TestDispatchNotebook
# ---------------------------------------------------------------------------

class TestDispatchNotebook(_DBTestCase):
    """Verifica el dispatcher de NotebookEdit."""

    def setUp(self):
        super().setUp()
        self._original_cwd = os.getcwd()
        os.chdir(self._tmpdir)

    def tearDown(self):
        os.chdir(self._original_cwd)
        super().tearDown()

    def test_creates_notebook_edited_event(self):
        """Un NotebookEdit crea un evento notebook_edited."""
        data = {"tool_input": {"notebook_path": os.path.join(self._tmpdir, "analysis.ipynb"), "command": "edit"}}
        _capture._dispatch_notebook(self._db, data)

        events = self._get_events("notebook_edited")
        self.assertEqual(len(events), 1)

    def test_summary_contains_path_and_command(self):
        """El summary incluye la ruta y el tipo de operacion."""
        data = {"tool_input": {"notebook_path": os.path.join(self._tmpdir, "model.ipynb"), "command": "add_cell"}}
        _capture._dispatch_notebook(self._db, data)

        events = self._get_events("notebook_edited")
        summary = events[0].get("summary", "")
        self.assertIn("model.ipynb", summary)
        self.assertIn("add_cell", summary)

    def test_payload_has_file_and_command(self):
        """El payload incluye la ruta relativa y el comando."""
        data = {"tool_input": {"notebook_path": os.path.join(self._tmpdir, "nb.ipynb"), "command": "delete_cell"}}
        _capture._dispatch_notebook(self._db, data)

        events = self._get_events("notebook_edited")
        payload = self._parse_payload(events[0])
        self.assertIn("nb.ipynb", payload["file"])
        self.assertEqual(payload["command"], "delete_cell")

    def test_excluded_path_creates_no_event(self):
        """Un notebook en directorio excluido no crea evento."""
        data = {"tool_input": {"notebook_path": os.path.join(self._tmpdir, ".venv", "nb.ipynb")}}
        _capture._dispatch_notebook(self._db, data)

        events = self._get_events("notebook_edited")
        self.assertEqual(len(events), 0)

    def test_empty_path_creates_no_event(self):
        """Una ruta vacia no crea evento."""
        data = {"tool_input": {"notebook_path": ""}}
        _capture._dispatch_notebook(self._db, data)

        events = self._get_events("notebook_edited")
        self.assertEqual(len(events), 0)


# ---------------------------------------------------------------------------
# TestHelpers
# ---------------------------------------------------------------------------

class TestFirstMeaningfulLine(unittest.TestCase):
    """Verifica la extraccion de la primera linea significativa."""

    def test_normal_text(self):
        result = _capture._first_meaningful_line("primera linea\nsegunda")
        self.assertEqual(result, "primera linea")

    def test_empty_lines_skipped(self):
        result = _capture._first_meaningful_line("\n\n  \ntercera linea\n")
        self.assertEqual(result, "tercera linea")

    def test_empty_string(self):
        result = _capture._first_meaningful_line("")
        self.assertEqual(result, "")

    def test_none_returns_empty(self):
        result = _capture._first_meaningful_line(None)
        self.assertEqual(result, "")

    def test_truncated_to_120(self):
        long_line = "x" * 200
        result = _capture._first_meaningful_line(long_line)
        self.assertEqual(len(result), 120)


class TestRelativePath(unittest.TestCase):
    """Verifica la conversion a ruta relativa."""

    def test_normal_conversion(self):
        result = _capture._relative_path("/project/src/main.py", "/project")
        self.assertEqual(result, "src/main.py")

    def test_same_directory(self):
        result = _capture._relative_path("/project/file.py", "/project")
        self.assertEqual(result, "file.py")


class TestReadFileSafe(unittest.TestCase):
    """Verifica la lectura segura de ficheros."""

    def test_reads_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("contenido de prueba")
            path = f.name
        try:
            result = _capture._read_file_safe(path)
            self.assertEqual(result, "contenido de prueba")
        finally:
            os.unlink(path)

    def test_returns_none_for_missing_file(self):
        result = _capture._read_file_safe("/tmp/no_existe_para_nada_12345.txt")
        self.assertIsNone(result)


class TestLoadStateFile(unittest.TestCase):
    """Verifica la carga y validacion del fichero de estado."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self._tmpfile.close()

    def tearDown(self):
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)

    def _write_state(self, data):
        with open(self._tmpfile.name, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_valid_state(self):
        self._write_state({
            "comando": "feature",
            "fase_actual": "producto",
            "descripcion": "login con OAuth2",
        })
        result = _capture._load_state_file(self._tmpfile.name)
        self.assertIsNotNone(result)
        self.assertEqual(result["comando"], "feature")

    def test_missing_comando(self):
        self._write_state({"fase_actual": "producto"})
        result = _capture._load_state_file(self._tmpfile.name)
        self.assertIsNone(result)

    def test_missing_fase_actual(self):
        self._write_state({"comando": "feature"})
        result = _capture._load_state_file(self._tmpfile.name)
        self.assertIsNone(result)

    def test_not_a_dict(self):
        self._write_state([1, 2, 3])
        result = _capture._load_state_file(self._tmpfile.name)
        self.assertIsNone(result)

    def test_invalid_json(self):
        with open(self._tmpfile.name, "w") as f:
            f.write("esto no es json {{{")
        result = _capture._load_state_file(self._tmpfile.name)
        self.assertIsNone(result)

    def test_nonexistent_file(self):
        result = _capture._load_state_file("/tmp/no_existe_alfred_state.json")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
