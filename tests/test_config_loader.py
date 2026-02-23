#!/usr/bin/env python3
"""Tests para el cargador de configuración del plugin."""

import json
import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config_loader import (
    load_config,
    detect_stack,
    suggest_optional_agents,
    match_task_keywords,
    DEFAULT_CONFIG,
    TASK_KEYWORDS,
)


class TestLoadConfig(unittest.TestCase):
    def test_returns_defaults_when_no_file(self):
        config = load_config("/ruta/que/no/existe")
        self.assertEqual(config["autonomia"]["producto"], "interactivo")
        self.assertEqual(config["autonomia"]["seguridad"], "autónomo")
        self.assertEqual(config["personalidad"]["nivel_sarcasmo"], 3)

    def test_loads_yaml_frontmatter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nautonomia:\n  producto: autónomo\n---\n# Notas\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["autonomia"]["producto"], "autónomo")
        self.assertEqual(config["autonomia"]["seguridad"], "autónomo")

    def test_extracts_notes_section(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nautonomia:\n  producto: interactivo\n---\n## Notas\nPreferir Hono sobre Express.\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertIn("Preferir Hono", config["notas"])


class TestDetectStack(unittest.TestCase):
    def test_detects_node_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {"name": "test", "dependencies": {"next": "^14.0.0"}}
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(pkg, f)
            with open(os.path.join(tmpdir, "tsconfig.json"), "w") as f:
                json.dump({}, f)
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["runtime"], "node")
        self.assertEqual(stack["lenguaje"], "typescript")

    def test_detects_python_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
                f.write("[project]\nname = 'test'\n")
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["lenguaje"], "python")

    def test_returns_unknown_for_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["lenguaje"], "desconocido")


class TestOptionalAgents(unittest.TestCase):
    """Tests para la configuración y descubrimiento de agentes opcionales."""

    def test_default_config_has_optional_agents(self):
        """La configuración por defecto incluye la sección de agentes opcionales."""
        self.assertIn("agentes_opcionales", DEFAULT_CONFIG)
        agents = DEFAULT_CONFIG["agentes_opcionales"]
        expected = {
            "data-engineer", "ux-reviewer", "performance-engineer",
            "github-manager", "seo-specialist", "copywriter", "librarian",
        }
        self.assertEqual(set(agents.keys()), expected)

    def test_all_optional_agents_disabled_by_default(self):
        """Todos los agentes opcionales están desactivados por defecto."""
        for name, active in DEFAULT_CONFIG["agentes_opcionales"].items():
            self.assertFalse(active, f"'{name}' debería estar desactivado por defecto")

    def test_config_loads_optional_agents(self):
        """La configuración del fichero .local.md se fusiona con los defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nagentes_opcionales:\n  data-engineer: true\n  github-manager: true\n---\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertTrue(config["agentes_opcionales"]["data-engineer"])
        self.assertTrue(config["agentes_opcionales"]["github-manager"])
        # Los no especificados mantienen el default (false)
        self.assertFalse(config["agentes_opcionales"]["ux-reviewer"])

    def test_suggest_for_node_project_with_orm(self):
        """Un proyecto Node con ORM sugiere data-engineer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {
                "name": "test",
                "dependencies": {"next": "^14.0.0", "@prisma/client": "^5.0.0"},
            }
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(pkg, f)
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("data-engineer", agent_names)
        self.assertIn("ux-reviewer", agent_names)

    def test_suggest_for_project_with_html(self):
        """Un proyecto con contenido web público sugiere seo-specialist y copywriter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "index.html"), "w") as f:
                f.write("<html></html>")
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("seo-specialist", agent_names)
        self.assertIn("copywriter", agent_names)

    def test_suggest_skips_already_active(self):
        """No sugiere agentes que ya están activos en la configuración."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "index.html"), "w") as f:
                f.write("<html></html>")
            config = load_config("/ruta/que/no/existe")
            config["agentes_opcionales"]["seo-specialist"] = True
            suggestions = suggest_optional_agents(tmpdir, config)
        agent_names = [s[0] for s in suggestions]
        self.assertNotIn("seo-specialist", agent_names)
        self.assertIn("copywriter", agent_names)

    def test_suggest_empty_for_minimal_project(self):
        """Un proyecto vacío no sugiere ningún agente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            suggestions = suggest_optional_agents(tmpdir)
        self.assertEqual(suggestions, [])

    def test_suggest_github_manager_with_remote(self):
        """Un proyecto con remote Git sugiere github-manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as f:
                f.write('[remote "origin"]\n\turl = git@github.com:user/repo.git\n')
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("github-manager", agent_names)


class TestMatchTaskKeywords(unittest.TestCase):
    """Tests para la composición dinámica de equipo basada en palabras clave."""

    # TC-01: keyword "pagos" activa data-engineer
    def test_keyword_pagos_activa_data_engineer(self):
        """Una tarea que menciona 'pagos' sugiere data-engineer con score >= 0.5."""
        result = match_task_keywords("Necesitamos integrar pagos con Stripe")
        agent = result["data-engineer"]
        self.assertTrue(agent["sugerido"])
        self.assertGreaterEqual(agent["score"], 0.5)

    # TC-02: dos keywords aplican bonus 0.1
    def test_dos_keywords_aplican_bonus(self):
        """Dos keywords del mismo agente suman peso_base + 0.1."""
        result = match_task_keywords("migracion de base de datos")
        agent = result["data-engineer"]
        # peso_base (0.6) + bonus 2+ keywords (0.1) = 0.7
        self.assertAlmostEqual(agent["score"], 0.7, places=2)

    # TC-03: solo proyecto no supera umbral
    def test_solo_proyecto_no_supera_umbral(self):
        """Un agente mencionado solo por project_suggestions (+0.4) no llega a 0.5."""
        result = match_task_keywords(
            "algo irrelevante",
            project_suggestions=[("data-engineer", "Usas Prisma")],
        )
        agent = result["data-engineer"]
        self.assertFalse(agent["sugerido"])
        self.assertAlmostEqual(agent["score"], 0.4, places=2)

    # TC-04: proyecto + keyword = 1.0, sugerido
    def test_proyecto_mas_keyword_sugiere(self):
        """Proyecto (+0.4) + keyword (+0.6) = 1.0, sugerido=True."""
        result = match_task_keywords(
            "Necesito migrar la base de datos",
            project_suggestions=[("data-engineer", "Usas Prisma")],
        )
        agent = result["data-engineer"]
        self.assertTrue(agent["sugerido"])
        self.assertAlmostEqual(agent["score"], 1.0, places=2)

    # TC-05: config activa sola no supera umbral
    def test_config_activa_sola_no_supera_umbral(self):
        """Un agente con config activa (+0.3) pero sin keywords no llega a 0.5."""
        result = match_task_keywords(
            "algo irrelevante",
            active_config={"data-engineer": True},
        )
        agent = result["data-engineer"]
        self.assertFalse(agent["sugerido"])
        self.assertAlmostEqual(agent["score"], 0.3, places=2)

    # TC-06: config + proyecto = 0.7, sugerido
    def test_config_mas_proyecto_sugiere(self):
        """Config activa (+0.3) + proyecto (+0.4) = 0.7, sugerido=True."""
        result = match_task_keywords(
            "algo irrelevante",
            project_suggestions=[("data-engineer", "Usas Prisma")],
            active_config={"data-engineer": True},
        )
        agent = result["data-engineer"]
        self.assertTrue(agent["sugerido"])
        self.assertAlmostEqual(agent["score"], 0.7, places=2)

    # TC-07: tarea vacía devuelve todos con score 0.0
    def test_tarea_vacia_score_cero(self):
        """Una tarea vacía devuelve todos los agentes con score 0.0."""
        result = match_task_keywords("")
        for name, info in result.items():
            self.assertAlmostEqual(info["score"], 0.0, places=2,
                                   msg=f"{name} debería tener score 0.0")
            self.assertFalse(info["sugerido"],
                             msg=f"{name} no debería estar sugerido")

    # TC-08: texto irrelevante no activa ninguno
    def test_texto_irrelevante_no_activa(self):
        """Un texto sin keywords relevantes no activa ningún agente."""
        result = match_task_keywords("El gato se sentó en la alfombra")
        for name, info in result.items():
            self.assertFalse(info["sugerido"],
                             msg=f"{name} no debería estar sugerido con texto irrelevante")

    # TC-09: retorno tiene exactamente 7 agentes
    def test_retorno_tiene_siete_agentes(self):
        """El resultado contiene exactamente las 7 claves de TASK_KEYWORDS."""
        result = match_task_keywords("cualquier cosa")
        self.assertEqual(set(result.keys()), set(TASK_KEYWORDS.keys()))
        self.assertEqual(len(result), 7)

    # TC-10: razones no vacías cuando sugerido=True
    def test_razones_no_vacias_cuando_sugerido(self):
        """Cuando un agente está sugerido, su lista de razones no está vacía."""
        result = match_task_keywords("Necesitamos integrar pagos con Stripe")
        for name, info in result.items():
            if info["sugerido"]:
                self.assertTrue(
                    len(info["razones"]) > 0,
                    msg=f"{name} sugerido pero sin razones",
                )

    # TC-11: razones vacías cuando score=0.0
    def test_razones_vacias_cuando_score_cero(self):
        """Cuando el score es 0.0, la lista de razones está vacía."""
        result = match_task_keywords("")
        for name, info in result.items():
            if info["score"] == 0.0:
                self.assertEqual(
                    info["razones"], [],
                    msg=f"{name} con score 0.0 debería tener razones vacías",
                )

    # TC-12: TASK_KEYWORDS tiene mismas claves que DEFAULT_CONFIG["agentes_opcionales"]
    def test_task_keywords_coincide_con_agentes_opcionales(self):
        """TASK_KEYWORDS define exactamente los mismos agentes que DEFAULT_CONFIG."""
        self.assertEqual(
            set(TASK_KEYWORDS.keys()),
            set(DEFAULT_CONFIG["agentes_opcionales"].keys()),
        )

    # TC-13: normalización case-insensitive
    def test_normalizacion_case_insensitive(self):
        """Las keywords se detectan independientemente de mayúsculas/minúsculas."""
        result_lower = match_task_keywords("pagos")
        result_upper = match_task_keywords("PAGOS")
        result_mixed = match_task_keywords("PaGoS")
        self.assertEqual(result_lower["data-engineer"]["score"],
                         result_upper["data-engineer"]["score"])
        self.assertEqual(result_lower["data-engineer"]["score"],
                         result_mixed["data-engineer"]["score"])

    # TC-14: task_description=None no lanza excepción
    def test_none_no_lanza_excepcion(self):
        """Pasar None como descripción no lanza excepción."""
        try:
            result = match_task_keywords(None)
        except Exception as e:
            self.fail(f"match_task_keywords(None) lanzó {type(e).__name__}: {e}")
        # Además, debe devolver los 7 agentes con score 0.0
        self.assertEqual(len(result), 7)
        for info in result.values():
            self.assertAlmostEqual(info["score"], 0.0, places=2)

    # TC-15b: keywords cortas no causan falsos positivos por subcadena
    def test_keywords_cortas_no_falsos_positivos(self):
        """Keywords como 'ui', 'ci', 'pr' no se activan dentro de palabras más largas."""
        # "circuito" contiene "ui" como subcadena, pero no debe activar ux-reviewer
        result = match_task_keywords("Diseñar el circuito de aprobación")
        self.assertFalse(result["ux-reviewer"]["sugerido"],
                         "'circuito' no debe activar ux-reviewer por 'ui'")

        # "ciencia" contiene "ci" como subcadena, no debe activar github-manager
        result = match_task_keywords("Aplicar ciencia de datos al proyecto")
        self.assertFalse(result["github-manager"]["sugerido"],
                         "'ciencia' no debe activar github-manager por 'ci'")

        # "precio" contiene "pr" como subcadena, no debe activar github-manager
        result = match_task_keywords("Calcular el precio del producto")
        self.assertFalse(result["github-manager"]["sugerido"],
                         "'precio' no debe activar github-manager por 'pr'")

    # TC-15c: keywords cortas sí se activan como palabras completas
    def test_keywords_cortas_activan_como_palabras(self):
        """Keywords como 'ui' y 'pr' se activan cuando aparecen como palabras completas."""
        result = match_task_keywords("Mejorar la ui del formulario de registro")
        self.assertTrue(result["ux-reviewer"]["sugerido"],
                        "'ui' como palabra completa debe activar ux-reviewer")

        result = match_task_keywords("Crear un pr con los cambios")
        self.assertTrue(result["github-manager"]["sugerido"],
                        "'pr' como palabra completa debe activar github-manager")

    # TC-15d: truncamiento emite aviso a stderr
    def test_truncamiento_emite_aviso(self):
        """Una descripción que supera 10.000 caracteres emite aviso a stderr."""
        import io
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            # Texto largo donde la keyword está al final (se perderá)
            texto = "a " * 6000 + "pagos"
            match_task_keywords(texto)
        finally:
            sys.stderr = old_stderr
        self.assertIn("truncará", captured.getvalue())

    # TC-15e: tipo no-str emite aviso a stderr
    def test_tipo_no_str_emite_aviso(self):
        """Pasar un tipo no-str emite aviso a stderr y devuelve scores 0.0."""
        import io
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            result = match_task_keywords(42)
        finally:
            sys.stderr = old_stderr
        self.assertIn("tipo int", captured.getvalue())
        for info in result.values():
            self.assertAlmostEqual(info["score"], 0.0, places=2)


if __name__ == "__main__":
    unittest.main()
