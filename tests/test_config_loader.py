#!/usr/bin/env python3
"""Tests para el cargador de configuración del plugin."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config_loader import (
    apply_config_section_update,
    build_config_section_change_preview,
    build_config_section_menu,
    build_config_section_summaries,
    build_equipo_sesion_from_config,
    build_project_equipo_sesion,
    DEFAULT_CONFIG,
    detect_stack,
    ensure_bootstrap_local_config,
    get_active_optional_agents,
    has_frontend,
    is_autopilot_configured,
    is_autopilot_enabled_for_project,
    load_config,
    load_project_config,
    render_config_markdown,
    save_config,
    save_project_config,
    suggest_optional_agents,
    update_config_section,
    update_project_config_section,
)
from core.optional_agents import (
    build_optional_agent_menu_option,
    build_optional_agent_group_menu,
    build_optional_agent_group_menus,
    get_optional_integrations,
    get_optional_agent_names,
    get_optional_agents_by_group,
    get_optional_agent_display_label,
    get_optional_agent_specialty,
    get_static_suggestible_agent_names,
)


class TestLoadConfig(unittest.TestCase):
    def test_returns_defaults_when_no_file(self):
        config = load_config("/ruta/que/no/existe")
        self.assertEqual(
            config["autonomia"],
            {
                "producto": "autonomo",
                "arquitectura": "autonomo",
                "desarrollo": "autonomo",
                "calidad": "autonomo",
                "documentacion": "autonomo",
                "entrega": "autonomo",
            },
        )
        self.assertEqual(config["personalidad"]["nivel_sarcasmo"], 3)
        self.assertTrue(config["personalidad"]["celebrar_victorias"])
        self.assertTrue(config["personalidad"]["insultar_malas_practicas"])
        self.assertEqual(config["memoria"]["sync_commits_limit"], 10)
        self.assertFalse(config["memoria"]["enabled"])

    def test_loads_yaml_frontmatter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nautonomia:\n  producto: autónomo\n---\n# Notas\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["autonomia"]["producto"], "autonomo")
        self.assertEqual(config["autonomia"]["arquitectura"], "autonomo")

    def test_extracts_notes_section(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nautonomia:\n  producto: interactivo\n---\n## Notas\nPreferir Hono sobre Express.\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertIn("Preferir Hono", config["notas"])

    def test_accepts_accented_autonomia_section_name(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("---\nautonomía:\n  producto: autónomo\n---\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["autonomia"]["producto"], "autonomo")
        self.assertNotIn("autonomía", config)

    def test_maps_legacy_autonomy_domains_to_current_phases(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(
                "---\n"
                "autonomia:\n"
                "  seguridad: semi-autónomo\n"
                "  refactor: interactivo\n"
                "  docs: interactivo\n"
                "  devops: semi-autonomo\n"
                "  tests: interactivo\n"
                "---\n"
            )
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["autonomia"]["desarrollo"], "interactivo")
        self.assertEqual(config["autonomia"]["documentacion"], "interactivo")
        self.assertEqual(config["autonomia"]["entrega"], "semi-autonomo")
        self.assertEqual(config["autonomia"]["calidad"], "interactivo")
        self.assertEqual(config["autonomia"]["arquitectura"], "semi-autonomo")

    def test_parses_frontmatter_after_leading_blank_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("\n\n---\npersonalidad:\n  nivel_sarcasmo: 4\n---\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["personalidad"]["nivel_sarcasmo"], 4)

    def test_load_project_config_applies_detected_stack_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as f:
                json.dump({"name": "demo", "dependencies": {"next": "^15.0.0"}}, f)
            config = load_project_config(tmpdir)
        self.assertEqual(config["proyecto"]["runtime"], "node")
        self.assertEqual(config["proyecto"]["framework"], "next")

    def test_load_project_config_preserves_explicit_project_overrides(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as f:
                json.dump({"name": "demo", "dependencies": {"next": "^15.0.0"}}, f)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write("---\nproyecto:\n  framework: hono\n---\n")
            config = load_project_config(tmpdir)
        self.assertEqual(config["proyecto"]["runtime"], "node")
        self.assertEqual(config["proyecto"]["framework"], "hono")

    def test_is_autopilot_configured_checks_all_phases(self):
        self.assertTrue(is_autopilot_configured(DEFAULT_CONFIG))
        config = load_config("/ruta/que/no/existe")
        config["autonomia"]["calidad"] = "interactivo"
        self.assertFalse(is_autopilot_configured(config))

    def test_is_autopilot_enabled_for_project_accepts_legacy_modo_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            state_path = os.path.join(claude_dir, "alfred-dev-state.json")
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump({"modo": "autopilot"}, f)
            self.assertTrue(is_autopilot_enabled_for_project(tmpdir))

    def test_get_active_optional_agents_returns_enabled_agents_in_catalog_order(self):
        config = load_config("/ruta/que/no/existe")
        config["agentes_opcionales"]["seo-specialist"] = True
        config["agentes_opcionales"]["copywriter"] = True
        self.assertEqual(
            get_active_optional_agents(config),
            ["seo-specialist", "copywriter"],
        )

    def test_build_equipo_sesion_from_config_returns_none_without_runtime_flags(self):
        config = load_config("/ruta/que/no/existe")
        self.assertIsNone(build_equipo_sesion_from_config(config))

    def test_build_equipo_sesion_from_config_preserves_catalog_and_memory(self):
        config = load_config("/ruta/que/no/existe")
        config["agentes_opcionales"]["github-manager"] = True
        config["memoria"]["enabled"] = True

        equipo = build_equipo_sesion_from_config(config)

        self.assertEqual(equipo["fuente"], "config_persistida")
        self.assertTrue(equipo["opcionales_activos"]["github-manager"])
        self.assertFalse(equipo["opcionales_activos"]["lucius"])
        self.assertTrue(equipo["infra"]["memoria"])

    def test_build_project_equipo_sesion_reads_local_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(
                    "---\n"
                    "agentes_opcionales:\n"
                    "  github-manager: true\n"
                    "memoria:\n"
                    "  enabled: true\n"
                    "---\n"
                )

            equipo = build_project_equipo_sesion(tmpdir)

        self.assertEqual(equipo["fuente"], "config_persistida")
        self.assertTrue(equipo["opcionales_activos"]["github-manager"])
        self.assertTrue(equipo["infra"]["memoria"])

    def test_render_config_markdown_serializes_canonical_frontmatter_and_notes(self):
        config = load_config("/ruta/que/no/existe")
        config["agentes_opcionales"]["github-manager"] = True
        config["personalidad"]["idioma"] = "es"
        content = render_config_markdown(config, notes="Preferir Netlify sobre Vercel.")

        self.assertTrue(content.startswith("---\nautonomia:\n"))
        self.assertIn("github-manager: true", content)
        self.assertIn("## Notas", content)
        self.assertIn("Preferir Netlify sobre Vercel.", content)
        self.assertNotIn("\nnotas:", content)

    def test_save_config_roundtrips_with_load_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            config = load_config("/ruta/que/no/existe")
            config["autonomia"]["calidad"] = "interactivo"
            config["agentes_opcionales"]["lucius"] = True
            config["memoria"]["enabled"] = True
            save_config(path, config, notes="Revisar copys antes de publicar.")

            reloaded = load_config(path)
        finally:
            os.unlink(path)

        self.assertEqual(reloaded["autonomia"]["calidad"], "interactivo")
        self.assertTrue(reloaded["agentes_opcionales"]["lucius"])
        self.assertTrue(reloaded["memoria"]["enabled"])
        self.assertIn("Revisar copys", reloaded["notas"])

    def test_save_project_config_writes_canonical_local_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config("/ruta/que/no/existe")
            config["agentes_opcionales"]["copywriter"] = True

            path = save_project_config(
                tmpdir,
                config,
                notes="Mantener el tono cercano.",
            )
            reloaded = load_config(path)

        self.assertTrue(path.endswith(os.path.join(".claude", "alfred-dev.local.md")))
        self.assertTrue(reloaded["agentes_opcionales"]["copywriter"])
        self.assertIn("tono cercano", reloaded["notas"])

    def test_ensure_bootstrap_local_config_creates_minimal_canonical_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        os.unlink(path)
        try:
            changed = ensure_bootstrap_local_config(path)
            reloaded = load_config(path)
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
        finally:
            os.unlink(path)

        self.assertTrue(changed)
        self.assertTrue(reloaded["memoria"]["enabled"])
        self.assertEqual(reloaded["autonomia"]["producto"], "autonomo")
        self.assertIn("Puedes personalizarlo con `/alfred-dev:config`.", content)

    def test_ensure_bootstrap_local_config_respects_explicit_memory_disable(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("---\nmemoria:\n  enabled: false\n---\n")
            path = f.name
        try:
            changed = ensure_bootstrap_local_config(path)
            reloaded = load_config(path)
        finally:
            os.unlink(path)

        self.assertTrue(changed)
        self.assertFalse(reloaded["memoria"]["enabled"])
        self.assertEqual(reloaded["autonomia"]["documentacion"], "autonomo")

    def test_ensure_bootstrap_local_config_wraps_body_only_content(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Notas\n\nmemoria:\n  enabled: true\n")
            path = f.name
        try:
            changed = ensure_bootstrap_local_config(path)
            reloaded = load_config(path)
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
        finally:
            os.unlink(path)

        self.assertTrue(changed)
        self.assertTrue(content.startswith("---\nautonomia:\n"))
        self.assertTrue(reloaded["memoria"]["enabled"])

    def test_build_config_section_summaries_describe_effective_state(self):
        config = load_config("/ruta/que/no/existe")
        config["autonomia"]["producto"] = "interactivo"
        config["autonomia"]["calidad"] = "semi-autonomo"
        config["agentes_opcionales"]["copywriter"] = True
        config["agentes_opcionales"]["librarian"] = True
        config["memoria"]["enabled"] = True

        summaries = build_config_section_summaries(config)

        self.assertEqual(
            [section["section"] for section in summaries],
            [
                "autonomia",
                "proyecto",
                "agentes_opcionales",
                "memoria",
                "compliance",
                "integraciones",
                "personalidad",
            ],
        )
        autonomy = next(section for section in summaries if section["section"] == "autonomia")
        agents = next(section for section in summaries if section["section"] == "agentes_opcionales")
        memory = next(section for section in summaries if section["section"] == "memoria")

        self.assertIn("interactivas", autonomy["summary"])
        self.assertIn("2 activos", agents["summary"])
        self.assertIn("Copywriter", agents["summary"])
        self.assertIn("Bajo demanda: Librarian", agents["summary"])
        self.assertIn("Activa con sync nativa", memory["summary"])

    def test_build_config_section_menu_uses_current_summaries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "name": "demo",
                        "dependencies": {"next": "^15.0.0", "@prisma/client": "^6.0.0"},
                        "devDependencies": {"vitest": "^3.0.0", "vite": "^6.0.0"},
                    },
                    f,
                )
            config = load_config("/ruta/que/no/existe")
            config["agentes_opcionales"]["github-manager"] = True
            menu = build_config_section_menu(config, project_dir=tmpdir)

        labels = [option["label"] for option in menu["options"]]
        project_option = next(
            option for option in menu["options"]
            if option["label"] == "Proyecto"
        )
        agents_option = next(
            option for option in menu["options"]
            if option["label"] == "Agentes opcionales"
        )

        self.assertEqual(menu["header"], "Config")
        self.assertEqual(menu["question"], "¿Qué sección quieres modificar ahora?")
        self.assertEqual(menu["questions"][0]["header"], "Config")
        self.assertEqual(menu["questions"][0]["question"], menu["question"])
        self.assertEqual(menu["questions"][0]["options"], menu["options"])
        self.assertEqual(menu["questions"][0]["multiSelect"], False)
        self.assertEqual(labels[0], "Salir sin cambios")
        self.assertIn("Autonomía por fase", labels)
        self.assertIn("Proyecto", labels)
        self.assertIn("Agentes opcionales", labels)
        self.assertIn("next", project_option["description"])
        self.assertIn("Detectado automáticamente.", project_option["description"])
        self.assertIn("GitHub Manager", agents_option["description"])

    def test_apply_config_section_update_normalizes_and_preserves_rest(self):
        config = load_config("/ruta/que/no/existe")
        config["memoria"]["enabled"] = True

        updated = apply_config_section_update(
            config,
            "autonomia",
            {
                "producto": "interactivo",
                "documentación": "semi-autónomo",
            },
        )

        self.assertEqual(updated["autonomia"]["producto"], "interactivo")
        self.assertEqual(updated["autonomia"]["documentacion"], "semi-autonomo")
        self.assertEqual(updated["autonomia"]["calidad"], "autonomo")
        self.assertTrue(updated["memoria"]["enabled"])

    def test_apply_config_section_update_keeps_optional_catalog_complete(self):
        config = load_config("/ruta/que/no/existe")

        updated = apply_config_section_update(
            config,
            "agentes_opcionales",
            {"lucius": True},
        )

        self.assertTrue(updated["agentes_opcionales"]["lucius"])
        self.assertFalse(updated["agentes_opcionales"]["github-manager"])
        self.assertEqual(
            set(updated["agentes_opcionales"].keys()),
            set(get_optional_agent_names()),
        )

    def test_all_config_sections_preview_and_persist_round_trip(self):
        updates = {
            "autonomia": {
                "producto": "interactivo",
                "calidad": "semi-autonomo",
            },
            "proyecto": {
                "runtime": "node",
                "lenguaje": "typescript",
                "framework": "next",
                "test_runner": "vitest",
                "bundler": "vite",
            },
            "agentes_opcionales": {
                "lucius": True,
                "github-manager": True,
            },
            "memoria": {
                "enabled": True,
                "sync_commits_limit": 3,
                "retention_days": 30,
            },
            "compliance": {
                "estilo": "strict",
                "lint": False,
                "format_on_save": False,
            },
            "integraciones": {
                "git": False,
                "ci": True,
                "deploy": True,
            },
            "personalidad": {
                "nivel_sarcasmo": 1,
                "verbosidad": "alta",
                "idioma": "es-ES",
                "celebrar_victorias": False,
            },
        }

        for section_name, patch in updates.items():
            with self.subTest(section=section_name):
                base_config = load_config("/ruta/que/no/existe")
                preview = build_config_section_change_preview(
                    base_config,
                    section_name,
                    patch,
                )

                self.assertTrue(preview["changed"], msg=preview)
                self.assertEqual(preview["section"], section_name)
                for key, value in patch.items():
                    self.assertEqual(preview["updated_config"][section_name][key], value)

                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".md",
                    delete=False,
                    encoding="utf-8",
                ) as f:
                    f.write(
                        "---\n"
                        "memoria:\n"
                        "  enabled: false\n"
                        "---\n\n"
                        "## Notas\n\n"
                        "Nota estable.\n"
                    )
                    path = f.name

                try:
                    persisted_preview = update_config_section(
                        path,
                        section_name,
                        patch,
                        include_defaults=False,
                    )
                    reloaded = load_config(path)
                finally:
                    os.unlink(path)

                self.assertEqual(persisted_preview["section"], section_name)
                for key, value in patch.items():
                    self.assertEqual(reloaded[section_name][key], value)
                self.assertIn("Nota estable", reloaded["notas"])

    def test_build_config_section_change_preview_reports_before_and_after(self):
        config = load_config("/ruta/que/no/existe")
        preview = build_config_section_change_preview(
            config,
            "memoria",
            {"enabled": True},
        )

        self.assertTrue(preview["changed"])
        self.assertEqual(preview["label"], "Memoria persistente")
        self.assertIn("Inactiva", preview["before"]["summary"])
        self.assertIn("Activa con sync nativa", preview["after"]["summary"])
        self.assertTrue(preview["updated_config"]["memoria"]["enabled"])

    def test_build_config_section_change_preview_detects_noop_updates(self):
        config = load_config("/ruta/que/no/existe")
        preview = build_config_section_change_preview(
            config,
            "integraciones",
            {"git": True},
        )

        self.assertFalse(preview["changed"])
        self.assertEqual(
            preview["before"]["details"],
            preview["after"]["details"],
        )

    def test_update_config_section_persists_one_section_and_keeps_notes(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(
                "---\n"
                "memoria:\n"
                "  enabled: false\n"
                "---\n\n"
                "## Notas\n\n"
                "Mantener tono cercano.\n"
            )
            path = f.name

        try:
            preview = update_config_section(
                path,
                "memoria",
                {"enabled": True},
                include_defaults=False,
            )
            reloaded = load_config(path)
        finally:
            os.unlink(path)

        self.assertTrue(preview["changed"])
        self.assertTrue(reloaded["memoria"]["enabled"])
        self.assertIn("Mantener tono cercano", reloaded["notas"])

    def test_update_project_config_section_writes_project_local_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write("---\nintegraciones:\n  ci: false\n---\n")

            preview = update_project_config_section(
                tmpdir,
                "integraciones",
                {"ci": True},
                include_defaults=False,
            )
            reloaded = load_project_config(tmpdir)

        self.assertTrue(preview["changed"])
        self.assertTrue(reloaded["integraciones"]["ci"])


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

    def test_prefers_frontend_framework_when_node_project_is_mixed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {
                "name": "test",
                "dependencies": {"react": "^18.0.0", "express": "^5.0.0"},
            }
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(pkg, f)
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["framework"], "react")

    def test_has_frontend_accepts_common_framework_aliases(self):
        self.assertTrue(has_frontend({"framework": "nextjs"}))
        self.assertTrue(has_frontend({"framework": "next.js"}))
        self.assertTrue(has_frontend({"framework": "reactjs"}))

    def test_python_detection_ignores_stub_packages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("django-stubs==5.0.0\npytest==8.0.0\n")
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["framework"], "desconocido")
        self.assertEqual(stack["orm"], "ninguno")
        self.assertEqual(stack["test_runner"], "pytest")

    def test_detects_jvm_maven_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "pom.xml"), "w", encoding="utf-8") as f:
                f.write(
                    "<project><dependencies>"
                    "<dependency><groupId>org.springframework.boot</groupId>"
                    "<artifactId>spring-boot-starter-web</artifactId></dependency>"
                    "<dependency><groupId>org.junit.jupiter</groupId>"
                    "<artifactId>junit-jupiter</artifactId></dependency>"
                    "</dependencies></project>"
                )
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["runtime"], "jvm")
        self.assertEqual(stack["lenguaje"], "java")
        self.assertEqual(stack["framework"], "spring-boot")
        self.assertEqual(stack["test_runner"], "junit")

    def test_detects_kotlin_gradle_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "build.gradle.kts"), "w", encoding="utf-8") as f:
                f.write(
                    "plugins { kotlin(\"jvm\") version \"2.0.0\" }\n"
                    "dependencies { implementation(\"io.quarkus:quarkus-rest\") }\n"
                )
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["runtime"], "jvm")
        self.assertEqual(stack["lenguaje"], "kotlin")
        self.assertEqual(stack["framework"], "quarkus")

    def test_detects_php_composer_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "composer.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "require": {
                            "laravel/framework": "^11.0",
                            "doctrine/orm": "^3.0",
                        },
                        "require-dev": {
                            "pestphp/pest": "^2.0",
                        },
                    },
                    f,
                )
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["runtime"], "php")
        self.assertEqual(stack["lenguaje"], "php")
        self.assertEqual(stack["framework"], "laravel")
        self.assertEqual(stack["orm"], "doctrine")
        self.assertEqual(stack["test_runner"], "pest")

    def test_detects_dotnet_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "App.csproj"), "w", encoding="utf-8") as f:
                f.write(
                    "<Project Sdk=\"Microsoft.NET.Sdk.Web\">"
                    "<ItemGroup>"
                    "<PackageReference Include=\"Microsoft.EntityFrameworkCore\" Version=\"8.0.0\" />"
                    "<PackageReference Include=\"xunit\" Version=\"2.8.0\" />"
                    "</ItemGroup>"
                    "</Project>"
                )
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["runtime"], "dotnet")
        self.assertEqual(stack["lenguaje"], "csharp")
        self.assertEqual(stack["framework"], "aspnet")
        self.assertEqual(stack["orm"], "entity-framework")
        self.assertEqual(stack["test_runner"], "xunit")

    def test_detects_swift_package_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Package.swift"), "w", encoding="utf-8") as f:
                f.write(
                    "let package = Package(\n"
                    "  dependencies: [.package(url: \"https://github.com/vapor/vapor\", from: \"4.0.0\")],\n"
                    "  targets: [.testTarget(name: \"AppTests\", dependencies: [\"App\"])]\n"
                    ")\n"
                )
            stack = detect_stack(tmpdir)
        self.assertEqual(stack["runtime"], "swift")
        self.assertEqual(stack["lenguaje"], "swift")
        self.assertEqual(stack["framework"], "vapor")
        self.assertEqual(stack["test_runner"], "swift-test")


class TestOptionalAgents(unittest.TestCase):
    """Tests para la configuración y descubrimiento de agentes opcionales."""

    def test_default_config_has_optional_agents(self):
        """La configuración por defecto incluye la sección de agentes opcionales."""
        self.assertIn("agentes_opcionales", DEFAULT_CONFIG)
        agents = DEFAULT_CONFIG["agentes_opcionales"]
        self.assertEqual(set(agents.keys()), set(get_optional_agent_names()))

    def test_all_optional_agents_disabled_by_default(self):
        """Todos los agentes opcionales están desactivados por defecto."""
        for name, active in DEFAULT_CONFIG["agentes_opcionales"].items():
            self.assertFalse(active, f"'{name}' debería estar desactivado por defecto")

    def test_optional_agent_catalog_keeps_group_distribution(self):
        grouped = get_optional_agents_by_group()
        self.assertEqual(grouped["technical"], [
            "data-engineer",
            "performance-engineer",
            "github-manager",
            "librarian",
        ])
        self.assertEqual(grouped["content"], [
            "ux-reviewer",
            "seo-specialist",
            "copywriter",
            "i18n-specialist",
        ])
        self.assertEqual(grouped["audit"], ["lucius"])

    def test_optional_agent_catalog_exposes_labels_and_specialties(self):
        self.assertEqual(get_optional_agent_display_label("github-manager"), "GitHub Manager")
        self.assertIn("Core Web Vitals", get_optional_agent_specialty("seo-specialist"))

    def test_build_group_menu_starts_with_explicit_exit_option(self):
        menu = build_optional_agent_group_menu("technical")
        self.assertEqual(menu["header"], "Tecnicos")
        self.assertEqual(
            menu["question"],
            "¿Qué agente técnico quieres activar ahora?",
        )
        self.assertEqual(menu["questions"][0]["header"], "Tecnicos")
        self.assertEqual(menu["questions"][0]["question"], menu["question"])
        self.assertEqual(menu["questions"][0]["options"], menu["options"])
        self.assertEqual(menu["questions"][0]["multiSelect"], False)
        self.assertEqual(menu["options"][0]["label"], "Seguir sin activar más")
        self.assertEqual(menu["options"][1]["label"], "Data Engineer")

    def test_build_group_menu_marks_recommended_and_active_options(self):
        menu = build_optional_agent_group_menu(
            "technical",
            suggested_reasons={
                "data-engineer": "El proyecto usa Prisma y la tarea implica migración de esquema",
            },
            active_names=["github-manager"],
        )
        labels = [option["label"] for option in menu["options"]]
        self.assertIn("Data Engineer (Recomendado)", labels)
        github_option = next(
            option for option in menu["options"]
            if option["label"] == "GitHub Manager"
        )
        self.assertIn("Activo actualmente.", github_option["description"])

    def test_build_group_menu_can_hide_already_selected_agents(self):
        menu = build_optional_agent_group_menu(
            "content",
            excluded_names=["ux-reviewer", "copywriter"],
            include_done_option=True,
        )
        labels = [option["label"] for option in menu["options"]]
        self.assertEqual(labels[:2], ["Seguir sin activar más", "Listo con este grupo"])
        self.assertNotIn("UX Reviewer", labels)
        self.assertNotIn("Copywriter", labels)
        self.assertIn("SEO Specialist", labels)

    def test_build_group_menus_returns_three_groups_in_canonical_order(self):
        menus = build_optional_agent_group_menus(
            suggested_reasons={"lucius": "La tarea pide una segunda opinión independiente"},
        )
        self.assertEqual(
            [menu["group"] for menu in menus],
            ["technical", "content", "audit"],
        )
        audit_labels = [option["label"] for option in menus[2]["options"]]
        self.assertIn("Lucius (Recomendado)", audit_labels)

    def test_group_menus_cover_each_selectable_agent_once(self):
        menus = build_optional_agent_group_menus(include_done_option=True)
        collected_labels = []

        for menu in menus:
            labels = [option["label"] for option in menu["options"]]
            self.assertEqual(labels[:2], ["Seguir sin activar más", "Listo con este grupo"])
            self.assertGreater(len(labels), 2)
            collected_labels.extend(labels[2:])

        expected_labels = [
            get_optional_agent_display_label(agent_name)
            for agent_name in get_optional_agent_names()
        ]
        self.assertEqual(collected_labels, expected_labels)
        self.assertEqual(len(collected_labels), len(set(collected_labels)))

    def test_every_selectable_agent_has_runtime_effect_or_is_explicitly_on_demand(self):
        integrations = get_optional_integrations()
        for agent_name in get_optional_agent_names():
            integration = integrations[agent_name]
            if agent_name == "librarian":
                self.assertEqual(integration["fases"], [])
                self.assertEqual(integration["posicion"], "none")
                continue

            self.assertTrue(
                integration["fases"],
                f"{agent_name} no debería ser seleccionable sin fases integradas",
            )
            self.assertIn(
                integration["posicion"],
                {"paralelo", "secuencial"},
                f"{agent_name} debe declarar un modo runtime claro",
            )

    def test_static_suggestions_exclude_lucius(self):
        self.assertNotIn("lucius", get_static_suggestible_agent_names())
        self.assertEqual(len(get_static_suggestible_agent_names()), 8)

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

    def test_i18n_signals_do_not_imply_copywriter_without_public_content(self):
        """i18n puro debe sugerir i18n-specialist, no copywriter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "i18n"))
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("i18n-specialist", agent_names)
        self.assertNotIn("copywriter", agent_names)
        self.assertNotIn("seo-specialist", agent_names)

    def test_frontend_without_public_html_does_not_imply_seo_or_copywriter(self):
        """Frontend privado no debe activar por sí solo copywriter ni SEO."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {
                "name": "dashboard",
                "dependencies": {"react": "^18.0.0"},
            }
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(pkg, f)
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("ux-reviewer", agent_names)
        self.assertNotIn("copywriter", agent_names)
        self.assertNotIn("seo-specialist", agent_names)

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

    def test_suggest_github_manager_with_github_remote(self):
        """Un proyecto con remote GitHub sugiere github-manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as f:
                f.write('[remote "origin"]\n\turl = git@github.com:user/repo.git\n')
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("github-manager", agent_names)

    def test_does_not_suggest_github_manager_for_non_github_remote(self):
        """No debe sugerirse github-manager en forjas no GitHub."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as f:
                f.write('[remote "origin"]\n\turl = git@gitlab.com:user/repo.git\n')
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertNotIn("github-manager", agent_names)

    def test_librarian_menu_option_is_explicitly_on_demand(self):
        option = build_optional_agent_menu_option("librarian")
        self.assertIn("Solo bajo demanda", option["description"])

    def test_suggests_ux_reviewer_for_mixed_react_and_express_project(self):
        """Si hay frontend y backend en el mismo package.json, debe aflorar la UI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {
                "name": "test",
                "dependencies": {"react": "^18.0.0", "express": "^5.0.0"},
            }
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(pkg, f)
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertIn("ux-reviewer", agent_names)

    def test_does_not_suggest_librarian_from_markdown_body_notes(self):
        """La sugerencia de librarian debe seguir el parser canónico."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            with open(
                os.path.join(claude_dir, "alfred-dev.local.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write("# Notas\n\nmemoria:\n  enabled: true\n")
            suggestions = suggest_optional_agents(tmpdir)
        agent_names = [s[0] for s in suggestions]
        self.assertNotIn("librarian", agent_names)


class TestConfigCli(unittest.TestCase):
    def test_summary_headless_renders_menu_and_bootstraps_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(os.path.dirname(__file__), "..", "core", "config_cli.py"),
                    tmpdir,
                    "--headless",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CONFIG_HEADLESS_MENU", result.stdout)
            self.assertIn("Autonomía", result.stdout)
            self.assertIn("Personalidad", result.stdout)
            self.assertTrue(
                os.path.isfile(os.path.join(tmpdir, ".claude", "alfred-dev.local.md"))
            )



if __name__ == "__main__":
    unittest.main()
