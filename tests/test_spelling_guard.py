#!/usr/bin/env python3
"""Tests para el hook de verificación ortográfica."""

import importlib.util
import json
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# El fichero del hook usa guión (spelling-guard.py), convención de los hooks
# de Alfred Dev. Python no permite importar módulos con guión directamente,
# así que usamos importlib para cargarlo por ruta.
_hook_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "spelling-guard.py")
_spec = importlib.util.spec_from_file_location("spelling_guard", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

find_accent_errors = _mod.find_accent_errors
prepare_text_for_spellcheck = _mod.prepare_text_for_spellcheck
should_inspect = _mod.should_inspect
ACCENT_WORDS = _mod.ACCENT_WORDS


class TestShouldInspect(unittest.TestCase):
    """Verifica que el filtro de ficheros funciona correctamente."""

    def test_inspects_markdown(self):
        self.assertTrue(should_inspect("/proyecto/docs/README.md"))

    def test_inspects_python(self):
        self.assertTrue(should_inspect("/proyecto/core/main.py"))

    def test_inspects_html(self):
        self.assertTrue(should_inspect("/proyecto/site/index.html"))

    def test_inspects_typescript(self):
        self.assertTrue(should_inspect("/proyecto/src/app.ts"))

    def test_ignores_json(self):
        self.assertFalse(should_inspect("/proyecto/package.json"))

    def test_ignores_lockfiles(self):
        self.assertFalse(should_inspect("/proyecto/package-lock.json"))

    def test_ignores_node_modules(self):
        self.assertFalse(should_inspect("/proyecto/node_modules/pkg/README.md"))

    def test_ignores_git(self):
        self.assertFalse(should_inspect("/proyecto/.git/HEAD"))

    def test_ignores_dist(self):
        self.assertFalse(should_inspect("/proyecto/dist/bundle.js"))

    def test_ignores_empty_path(self):
        self.assertFalse(should_inspect(""))

    def test_ignores_no_extension(self):
        self.assertFalse(should_inspect("/proyecto/Makefile"))


class TestFindAccentErrors(unittest.TestCase):
    """Verifica la detección de palabras sin tilde."""

    def test_detects_single_word(self):
        errors = find_accent_errors("La funcion devuelve un valor.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], ("funcion", "función"))

    def test_detects_multiple_words(self):
        text = "La configuracion del modulo es codigo basico."
        errors = find_accent_errors(text)
        found = {e[0].lower() for e in errors}
        self.assertIn("configuracion", found)
        self.assertIn("modulo", found)
        self.assertIn("basico", found)

    def test_no_duplicates(self):
        text = "La funcion principal llama a otra funcion auxiliar."
        errors = find_accent_errors(text)
        words = [e[0].lower() for e in errors]
        self.assertEqual(words.count("funcion"), 1)

    def test_case_insensitive(self):
        errors = find_accent_errors("FUNCION principal")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][1], "función")

    def test_no_errors_in_correct_text(self):
        errors = find_accent_errors("La función devuelve el código correcto.")
        self.assertEqual(errors, [])

    def test_empty_text(self):
        self.assertEqual(find_accent_errors(""), [])

    def test_none_text(self):
        self.assertEqual(find_accent_errors(None), [])

    def test_word_boundaries(self):
        """No detecta palabras parciales dentro de otras."""
        # 'version' dentro de 'subversion' no debería activar
        # Pero con \b sí lo detecta si 'version' es parte de 'subversion'
        # En este caso es correcto porque 'version' tiene límites de palabra propios
        errors = find_accent_errors("La version actual es estable.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], ("version", "versión"))

    def test_technical_context(self):
        """Detecta errores en contextos técnicos habituales."""
        text = "El metodo de autenticacion requiere validacion del parametro."
        errors = find_accent_errors(text)
        found = {e[0].lower() for e in errors}
        self.assertEqual(found, {"metodo", "autenticacion", "validacion", "parametro"})


class TestPrepareTextForSpellcheck(unittest.TestCase):
    """Verifica la reducción de ruido técnico antes de buscar errores."""

    def test_markdown_ignores_fenced_and_inline_code(self):
        text = (
            "Usa `modulo auth` y revisa la version.\n\n"
            "```bash\npython3 script.py --modulo auth --version v1\n```"
        )
        prepared = prepare_text_for_spellcheck(text, "/proyecto/README.md")
        errors = find_accent_errors(prepared)

        self.assertEqual(errors, [("version", "versión")])

    def test_javascript_ignores_route_like_paths(self):
        text = 'const route = "/api/version/publico";'
        prepared = prepare_text_for_spellcheck(text, "/proyecto/src/app.ts")

        self.assertEqual(find_accent_errors(prepared), [])

    def test_html_keeps_user_facing_attribute_text_but_not_attribute_names(self):
        text = '<div data-modulo="auth" aria-label="navegacion principal"></div>'
        prepared = prepare_text_for_spellcheck(text, "/proyecto/index.html")
        errors = find_accent_errors(prepared)

        found = {wrong.lower() for wrong, _ in errors}
        self.assertNotIn("modulo", found)
        self.assertIn("navegacion", found)

    def test_css_ignores_selectors_and_only_checks_comments(self):
        text = ".pagina-principal { color: red; }\n/* navegacion principal */"
        prepared = prepare_text_for_spellcheck(text, "/proyecto/site/app.css")
        errors = find_accent_errors(prepared)

        found = {wrong.lower() for wrong, _ in errors}
        self.assertNotIn("pagina", found)
        self.assertIn("navegacion", found)

    def test_toml_ignores_keys_but_checks_string_values(self):
        text = (
            'version = "1.0.0"\n'
            'description = "Modulo basico"\n'
            '# configuracion pendiente\n'
        )
        prepared = prepare_text_for_spellcheck(text, "/proyecto/pyproject.toml")
        errors = find_accent_errors(prepared)

        found = {wrong.lower() for wrong, _ in errors}
        self.assertNotIn("version", found)
        self.assertIn("modulo", found)
        self.assertIn("basico", found)
        self.assertIn("configuracion", found)


class TestAccentDictionary(unittest.TestCase):
    """Verifica la integridad del diccionario de tildes."""

    def test_no_self_referencing_entries(self):
        """No hay entradas donde la forma incorrecta sea igual a la correcta."""
        for wrong, correct in ACCENT_WORDS.items():
            self.assertNotEqual(
                wrong, correct,
                f"Entrada innecesaria: '{wrong}' ya es la forma correcta",
            )

    def test_all_corrections_have_accents(self):
        """Todas las formas correctas contienen al menos un carácter acentuado."""
        accented = set("áéíóúÁÉÍÓÚ")
        for wrong, correct in ACCENT_WORDS.items():
            has_accent = any(c in accented for c in correct)
            self.assertTrue(
                has_accent,
                f"La corrección de '{wrong}' -> '{correct}' no tiene tilde",
            )

    def test_minimum_dictionary_size(self):
        """El diccionario tiene al menos 50 entradas para ser útil."""
        self.assertGreaterEqual(len(ACCENT_WORDS), 50)


class TestMainFlow(unittest.TestCase):
    """Verifica el comportamiento del hook completo con payloads reales."""

    def _run_main(self, payload: dict) -> tuple[int, str]:
        stderr_capture = StringIO()
        exit_code = None

        with patch("sys.stdin", StringIO(json.dumps(payload))):
            with patch("sys.stderr", stderr_capture):
                try:
                    _mod.main()
                except SystemExit as exc:
                    exit_code = exc.code

        return exit_code, stderr_capture.getvalue()

    def test_markdown_code_examples_do_not_trigger_warning(self):
        code, stderr = self._run_main({
            "tool_input": {
                "file_path": "/proyecto/README.md",
                "content": "```bash\npython3 script.py --modulo auth --version v1\n```",
            }
        })

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

    def test_plain_spanish_text_still_triggers_warning(self):
        code, stderr = self._run_main({
            "tool_input": {
                "file_path": "/proyecto/README.md",
                "content": "La configuracion del modulo requiere revision.",
            }
        })

        self.assertEqual(code, 0)
        self.assertIn("Tildes ausentes", stderr)

    def test_javascript_route_path_does_not_trigger_warning(self):
        code, stderr = self._run_main({
            "tool_input": {
                "file_path": "/proyecto/src/routes.ts",
                "content": 'const route = "/api/version/publico";',
            }
        })

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
