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
        config["agentes_opcionales"]["lucius"] = True
        self.assertEqual(
            get_active_optional_agents(config),
            ["lucius"],
        )

    def test_build_equipo_sesion_from_config_returns_none_without_runtime_flags(self):
        config = load_config("/ruta/que/no/existe")
        self.assertIsNone(build_equipo_sesion_from_config(config))

    def test_build_equipo_sesion_from_config_preserves_catalog_and_memory(self):
        config = load_config("/ruta/que/no/existe")
        config["agentes_opcionales"]["lucius"] = True
        config["memoria"]["enabled"] = True

        equipo = build_equipo_sesion_from_config(config)

        self.assertEqual(equipo["fuente"], "config_persistida")
        self.assertTrue(equipo["opcionales_activos"]["lucius"])
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
                    "  lucius: true\n"
                    "memoria:\n"
                    "  enabled: true\n"
                    "---\n"
                )

            equipo = build_project_equipo_sesion(tmpdir)

        self.assertEqual(equipo["fuente"], "config_persistida")
        self.assertTrue(equipo["opcionales_activos"]["lucius"])
        self.assertTrue(equipo["infra"]["memoria"])

    def test_render_config_markdown_serializes_canonical_frontmatter_and_notes(self):
        config = load_config("/ruta/que/no/existe")
        config["agentes_opcionales"]["lucius"] = True
        config["personalidad"]["idioma"] = "es"
        content = render_config_markdown(config, notes="Preferir Netlify sobre Vercel.")

        self.assertTrue(content.startswith("---\nautonomia:\n"))
        self.assertIn("lucius: true", content)
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
            config["agentes_opcionales"]["lucius"] = True

            path = save_project_config(
                tmpdir,
                config,
                notes="Mantener el tono cercano.",
            )
            reloaded = load_config(path)

        self.assertTrue(path.endswith(os.path.join(".claude", "alfred-dev.local.md")))
        self.assertTrue(reloaded["agentes_opcionales"]["lucius"])
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
        self.assertIn("Puedes personalizarlo con `/alfred-dev:ajustes`.", content)

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
        config["agentes_opcionales"]["lucius"] = True
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
        self.assertIn("1 activo", agents["summary"])
        self.assertIn("Lucius", agents["summary"])
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
            config["agentes_opcionales"]["lucius"] = True
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
        self.assertIn("Lucius", agents_option["description"])

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
    """Tests para el catalogo reducido de opcionales (solo Lucius)."""

    def test_default_config_has_optional_agents(self):
        self.assertIn("agentes_opcionales", DEFAULT_CONFIG)
        agents = DEFAULT_CONFIG["agentes_opcionales"]
        self.assertEqual(set(agents.keys()), {"lucius"})
        self.assertFalse(agents["lucius"])

    def test_optional_agent_catalog_keeps_group_distribution(self):
        grouped = get_optional_agents_by_group()
        self.assertEqual(list(grouped), ["audit"])
        self.assertEqual(grouped["audit"], ["lucius"])

    def test_build_group_menus_returns_audit_only(self):
        menus = build_optional_agent_group_menus()
        self.assertEqual([menu["group"] for menu in menus], ["audit"])
        labels = [option["label"] for option in menus[0]["options"]]
        self.assertEqual(labels[0], "Seguir sin activar más")
        self.assertIn("Lucius", labels)

    def test_static_suggestions_exclude_lucius(self):
        self.assertEqual(get_static_suggestible_agent_names(), ())

    def test_suggest_empty_for_any_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            suggestions = suggest_optional_agents(tmpdir)
        self.assertEqual(suggestions, [])

    def test_legacy_optional_flags_are_ignored(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nagentes_opcionales:\n  data-engineer: true\n  lucius: true\n---\n")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertTrue(config["agentes_opcionales"]["lucius"])
        self.assertNotIn("data-engineer", config["agentes_opcionales"])


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
