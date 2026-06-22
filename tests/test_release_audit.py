#!/usr/bin/env python3
"""Tests del verificador de auditoria de release."""

import importlib.util
import os
from pathlib import Path
import re
import tempfile
import unittest


ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(ROOT, "scripts", "release_audit.py")
MANUAL_SMOKE_PATH = os.path.join(ROOT, "scripts", "manual_smoke.py")


def _load_release_audit_module():
    spec = importlib.util.spec_from_file_location("release_audit", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_manual_smoke_module():
    spec = importlib.util.spec_from_file_location("manual_smoke", MANUAL_SMOKE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestReleaseAuditScript(unittest.TestCase):
    def _skip_without_site(self):
        if not (Path(ROOT) / "site" / "package.json").is_file():
            self.skipTest("La landing vive en la rama Alfred-Astro")

    def test_default_release_audit_passes_local_contracts(self):
        """El modo por defecto no depende de red ni de la CLI de Claude."""
        release_audit = _load_release_audit_module()

        self.assertEqual(release_audit.main([]), 0)

    def test_version_scan_ignores_generated_manual_evidence(self):
        """Las evidencias manuales ignoradas no son superficie viva de release."""
        release_audit = _load_release_audit_module()
        json_artifact = Path(release_audit.ROOT) / "docs" / "manual-smoke-ignore-test.json"
        md_artifact = Path(release_audit.ROOT) / "docs" / "manual-smoke-ignore-test.md"
        json_artifact.write_text(
            f'{{"response_preview": "Claude menciono v{release_audit.OLD_VERSION}"}}\n',
            encoding="utf-8",
        )
        md_artifact.write_text(
            f"# Reporte\n\nClaude menciono v{release_audit.OLD_VERSION}\n",
            encoding="utf-8",
        )
        try:
            result = release_audit.check_versions()
        finally:
            json_artifact.unlink(missing_ok=True)
            md_artifact.unlink(missing_ok=True)

        self.assertIn(f"sin restos de {release_audit.OLD_VERSION}", result)

    def test_inventory_keeps_composition_helper_internal(self):
        """_composicion se empaqueta como recurso, no como comando publico."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_inventory()

        self.assertIn("25 comandos namespaced publicados", result)
        self.assertIn("ruta global /alfred instalada como skill personal global sin shim de comando duplicado", result)
        self.assertIn(
            "commands/_composicion.md y commands/alfred.md empaquetados solo como recursos internos",
            result,
        )
        self.assertIn("displayName humano alineado entre manifest y marketplace", result)
        self.assertIn("skill fuente /alfred oculto en plugin para evitar duplicado de selector", result)
        self.assertTrue(
            any("version canonica solo en plugin.json" in line for line in result),
            result,
        )
        self.assertIn("marketplace no suplementa componentes ni enablement", result)
        self.assertIn("marketplace root con skills por dominio explicito", result)
        self.assertIn("paths de comandos/skills acotados al root del plugin", result)
        self.assertIn("manifest sin componentes no auditados", result)

    def test_inventory_rejects_manifest_components_without_release_gate(self):
        """Los componentes estructurales deben tener gate antes de declararse."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/plugin.json":
                data = dict(data)
                data["agents"] = ["./agents/alfred.md"]
                data["mcpServers"] = {"alfred-memory": {"command": "python3"}}
                data["lspServers"] = {
                    "python": {
                        "command": "pyright-langserver",
                        "extensionToLanguage": {".py": "python"},
                    }
                }
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        message = str(context.exception)
        self.assertIn("Componentes de plugin sin auditoria explicita", message)
        self.assertIn("agents", message)
        self.assertIn("mcpServers", message)
        self.assertIn("lspServers", message)
        self.assertIn("gate de LSP", message)

    def test_inventory_rejects_experimental_components_without_release_gate(self):
        """Themes/monitors experimentales no deben colarse sin pruebas dedicadas."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/plugin.json":
                data = dict(data)
                data["experimental"] = {
                    "monitors": "./monitors/monitors.json",
                    "themes": "./themes/",
                }
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        message = str(context.exception)
        self.assertIn("experimental.monitors", message)
        self.assertIn("experimental.themes", message)

    def test_inventory_rejects_marketplace_component_supplements(self):
        """El marketplace de Alfred no debe alterar el inventario probado en plugin.json."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/marketplace.json":
                data = dict(data)
                plugin_entry = dict(data["plugins"][0])
                plugin_entry["skills"] = ["./skills/"]
                plugin_entry["mcpServers"] = "./mcp-extra.json"
                data["plugins"] = [plugin_entry]
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        message = str(context.exception)
        self.assertIn("Marketplace de Alfred Dev desalineado", message)
        self.assertIn("skills", message)
        self.assertIn("mcpServers", message)

    def test_inventory_rejects_marketplace_strict_false_or_enablement_override(self):
        """strict=false/defaultEnabled cambiarian la autoridad del plugin auditado."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/marketplace.json":
                data = dict(data)
                plugin_entry = dict(data["plugins"][0])
                plugin_entry["strict"] = False
                plugin_entry["defaultEnabled"] = False
                data["plugins"] = [plugin_entry]
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        message = str(context.exception)
        self.assertIn("strict=false", message)
        self.assertIn("defaultEnabled", message)

    def test_inventory_rejects_marketplace_duplicate_plugin_entries(self):
        """La auditoria 0.6.0 asume una sola entrada alfred-dev en marketplace local."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/marketplace.json":
                data = dict(data)
                data["plugins"] = [dict(data["plugins"][0]), dict(data["plugins"][0])]
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("exactamente una entrada", str(context.exception))

    def test_inventory_rejects_generic_skills_manifest_for_root_marketplace(self):
        """El marketplace root debe publicar los dominios de skills explícitos."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/plugin.json":
                data = dict(data)
                data["skills"] = ["./skills/"]
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("dominios skills/ publicados", str(context.exception))

    def test_inventory_rejects_manifest_component_path_without_dot_slash(self):
        """Claude resuelve paths de componentes relativos al root; usamos ./ explícito."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/plugin.json":
                data = dict(data)
                data["commands"] = list(data["commands"])
                data["commands"][0] = "commands/alfred.md"
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("Paths de componentes del manifest incompatibles", str(context.exception))
        self.assertIn("debe empezar por ./", str(context.exception))

    def test_inventory_rejects_manifest_component_absolute_path(self):
        """El paquete instalado no puede depender de rutas absolutas del dev host."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/plugin.json":
                data = dict(data)
                data["commands"] = list(data["commands"])
                data["commands"][0] = "/tmp/alfred.md"
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("no puede ser absoluto", str(context.exception))

    def test_inventory_rejects_manifest_component_traversal(self):
        """Los componentes declarados no deben apuntar fuera del plugin con ..."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/plugin.json":
                data = dict(data)
                data["skills"] = list(data["skills"])
                data["skills"][0] = "./../shared-skills/"
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        message = str(context.exception)
        self.assertIn("no puede atravesar fuera del plugin", message)
        self.assertIn("resuelve fuera del root", message)

    def test_inventory_rejects_duplicate_manifest_component_paths(self):
        """Las rutas duplicadas inflan el inventario y hacen ambigua la auditoria."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/plugin.json":
                data = dict(data)
                data["skills"] = list(data["skills"])
                data["skills"].append(data["skills"][0])
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("duplica una ruta del manifest", str(context.exception))

    def test_inventory_rejects_marketplace_display_name_drift(self):
        """La UI humana debe mantener el mismo displayName en manifest y marketplace."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/marketplace.json":
                data = dict(data)
                data["plugins"] = [dict(data["plugins"][0], displayName="Alfred")]
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("displayName humano", str(context.exception))

    def test_inventory_rejects_marketplace_version_duplication(self):
        """La version canonica vive en plugin.json, no duplicada en marketplace."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/marketplace.json":
                data = dict(data)
                data["plugins"] = [dict(data["plugins"][0], version="0.6.0")]
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("no debe duplicar version", str(context.exception))

    def test_inventory_rejects_marketplace_source_escaping_root(self):
        """El source relativo del marketplace no debe apuntar fuera del root."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == ".claude-plugin/marketplace.json":
                data = dict(data)
                data["plugins"] = [dict(data["plugins"][0], source="./../alfred-dev")]
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._json = original_json

        self.assertIn("no debe escapar del root", str(context.exception))

    def test_inventory_rejects_unsupported_skill_frontmatter_field(self):
        """Los SKILL.md no deben usar campos de frontmatter que Claude Code no documenta."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "skills/desarrollo/refactor/SKILL.md":
                return text.replace(
                    "description:",
                    "unsupported-field: true\ndescription:",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("Frontmatter de skills incompatible", str(context.exception))
        self.assertIn("unsupported-field", str(context.exception))

    def test_inventory_rejects_skill_name_different_from_directory(self):
        """El name del skill debe quedar estable y coincidir con la ruta invocable."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "skills/desarrollo/refactor/SKILL.md":
                return text.replace("name: refactor", "name: refactor-code", 1)
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("Frontmatter de skills incompatible", str(context.exception))
        self.assertIn("directorio", str(context.exception))
        self.assertIn("refactor-code", str(context.exception))

    def test_inventory_rejects_invalid_skill_boolean_value(self):
        """Los booleanos de SKILL.md deben usar valores que Claude entienda."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "skills/desarrollo/refactor/SKILL.md":
                return text.replace(
                    "description:",
                    "disable-model-invocation: maybe\ndescription:",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("Frontmatter de skills incompatible", str(context.exception))
        self.assertIn("disable-model-invocation", str(context.exception))
        self.assertIn("maybe", str(context.exception))

    def test_inventory_rejects_skill_listing_text_over_claude_limit(self):
        """Claude trunca description + when_to_use por encima de 1536 chars."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read
        long_description = "a" * (release_audit.SKILL_LISTING_TEXT_LIMIT + 1)

        def fake_read(path):
            text = original_read(path)
            if path == "skills/desarrollo/refactor/SKILL.md":
                return re.sub(
                    r"(?m)^description: .+$",
                    f"description: {long_description}",
                    text,
                    count=1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("Frontmatter de skills incompatible", str(context.exception))
        self.assertIn("limite de listing", str(context.exception))
        self.assertIn(str(release_audit.SKILL_LISTING_TEXT_LIMIT + 1), str(context.exception))

    def test_inventory_rejects_invalid_skill_effort_value(self):
        """Los effort de skills deben seguir el set documentado por Claude Code."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "skills/desarrollo/refactor/SKILL.md":
                return text.replace("description:", "effort: enormous\ndescription:", 1)
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("Frontmatter de skills incompatible", str(context.exception))
        self.assertIn("effort no soportado", str(context.exception))
        self.assertIn("enormous", str(context.exception))

    def test_inventory_rejects_unknown_skill_allowed_tool_name(self):
        """Los permisos de SKILL.md deben nombrar herramientas reales."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "skills/desarrollo/refactor/SKILL.md":
                return text.replace(
                    "description:",
                    "allowed-tools: Browser\ndescription:",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("Frontmatter de skills incompatible", str(context.exception))
        self.assertIn("allowed-tools", str(context.exception))
        self.assertIn("Browser", str(context.exception))

    def test_inventory_rejects_unsupported_agent_model(self):
        """Los agentes no deben usar valores de model fuera del contrato actual."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "agents/alfred.md":
                return text.replace("model: opus", "model: llama", 1)
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("modelo no soportado", str(context.exception))
        self.assertIn("llama", str(context.exception))

    def test_inventory_rejects_supported_agent_model_when_release_policy_drifts(self):
        """Un alias válido de Claude también debe actualizar la política/documentación."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "agents/qa-engineer.md":
                return text.replace("model: sonnet", "model: haiku", 1)
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("distribucion de modelos", str(context.exception))
        self.assertIn("haiku", str(context.exception))

    def test_inventory_rejects_unsupported_agent_color(self):
        """Los colores de subagentes deben seguir el set documentado por Claude Code."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "agents/project-manager.md":
                return text.replace("color: cyan", "color: magenta", 1)
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("color de subagente no soportado", str(context.exception))
        self.assertIn("magenta", str(context.exception))

    def test_inventory_rejects_unavailable_subagent_tool(self):
        """Los agentes de plugin no deben listar herramientas que Claude no da a subagentes."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "agents/alfred.md":
                return text.replace(
                    "tools: Glob,Grep,Read,Write,Edit,Bash,Agent,WebSearch",
                    "tools: Glob,Grep,Read,Write,Edit,Bash,Agent,WebSearch,AskUserQuestion",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("herramientas no disponibles en subagentes", str(context.exception))
        self.assertIn("AskUserQuestion", str(context.exception))

    def test_inventory_rejects_unknown_agent_tool_name(self):
        """Los tools de agentes deben usar nombres reales de Claude Code o patrones MCP."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "agents/alfred.md":
                return text.replace(
                    "tools: Glob,Grep,Read,Write,Edit,Bash,Agent,WebSearch",
                    "tools: Glob,Grep,Read,Write,Edit,Bash,Agent,WebSearch,Browser",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_inventory()
        finally:
            release_audit._read = original_read

        self.assertIn("herramientas desconocidas", str(context.exception))
        self.assertIn("Browser", str(context.exception))

    def test_continuity_smoke_covers_human_operational_helpers(self):
        """El smoke operativo recorre helpers reales en un fixture temporal."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_continuity_smoke()

        self.assertIn("next/map-codebase/discuss/quick", result)
        self.assertIn("blocked/in-progress/validate/search/verify", result)
        self.assertIn(
            "write-handoff/allow-stop-once/consume-prefetch/normalize-kanban/memory-ui/sync-github-fail-closed",
            result,
        )

    def test_mcp_tools_smoke_invokes_all_memory_tools(self):
        """El smoke MCP no se limita a tools/list: invoca las 15 tools."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_mcp_tools_smoke()

        self.assertIn("15 tools listadas", result)
        self.assertIn("15 tools invocadas con datos reales", result)
        self.assertIn("limites MCP defensivos en schemas y handlers", result)
        self.assertIn("memory_log_event recorta payload/content MCP enormes", result)
        self.assertIn("rutas MCP acotadas al proyecto", result)

    def test_external_contracts_cover_human_permission_boundaries(self):
        """Docker, GitHub, Lucius y deploy deben tener límites humanos claros."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_external_contracts()

        self.assertIn("Docker/SonarQube pide permiso y documenta omisiones", result)
        self.assertIn("Lucius confirma coste y no modifica ficheros", result)
        self.assertIn("ship mantiene deploy con gate humana", result)

    def test_command_catalog_is_exhaustive_and_deduplicated(self):
        """La ayuda y arquitectura deben reflejar todos los comandos publicados."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_command_catalog()

        self.assertIn("25 comandos namespaced alineados entre plugin.json, help y arquitectura", result)
        self.assertIn("ruta global /alfred documentada como skill personal global invocable sin shim de comando duplicado", result)
        self.assertIn("frontmatter de comandos compatible con Claude Code actual", result)
        self.assertIn("model de comandos validado contra Claude Code actual", result)
        self.assertIn("help sin bloques duplicados", result)

    def test_command_catalog_rejects_unsupported_frontmatter_field(self):
        """Los slash commands no deben usar campos de frontmatter que Claude ignore."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "commands/quick.md":
                return text.replace("description:", "unknown-field: true\ndescription:", 1)
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_command_catalog()
        finally:
            release_audit._read = original_read

        self.assertIn("campos de frontmatter no soportados", str(context.exception))
        self.assertIn("unknown-field", str(context.exception))

    def test_command_catalog_rejects_skill_only_frontmatter_field(self):
        """Los comandos no deben aceptar campos que solo pertenecen a SKILL.md."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "commands/quick.md":
                return text.replace(
                    "description:",
                    "disable-model-invocation: true\ndescription:",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_command_catalog()
        finally:
            release_audit._read = original_read

        self.assertIn("campos de frontmatter no soportados", str(context.exception))
        self.assertIn("disable-model-invocation", str(context.exception))

    def test_command_catalog_rejects_unknown_allowed_tool(self):
        """Los permisos de slash commands deben nombrar herramientas reales."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "commands/quick.md":
                return text.replace(
                    "argument-hint:",
                    "allowed-tools: Browser\nargument-hint:",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_command_catalog()
        finally:
            release_audit._read = original_read

        self.assertIn("allowed-tools", str(context.exception))
        self.assertIn("Browser", str(context.exception))

    def test_command_catalog_rejects_unknown_allowed_tool_in_yaml_list(self):
        """Las listas YAML de tools en commands se validan igual que los valores inline."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "commands/quick.md":
                return text.replace(
                    "argument-hint:",
                    "allowed-tools:\n  - Browser\nargument-hint:",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_command_catalog()
        finally:
            release_audit._read = original_read

        self.assertIn("allowed-tools", str(context.exception))
        self.assertIn("Browser", str(context.exception))

    def test_command_catalog_rejects_unsupported_command_model(self):
        """El model opcional de commands debe usar alias/ID aceptado por Claude Code."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "commands/quick.md":
                return text.replace(
                    "description:",
                    "model: llama\ndescription:",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_command_catalog()
        finally:
            release_audit._read = original_read

        self.assertIn("modelo de comando no soportado", str(context.exception))
        self.assertIn("llama", str(context.exception))

    def test_command_execution_contracts_cover_all_public_commands(self):
        """Los comandos publicados deben conservar argumentos, helpers y cierres."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_command_execution_contracts()

        self.assertIn("25 comandos namespaced y /alfred preservan argumentos, prefijo y nomenclatura actual", result)
        self.assertIn("18 wrappers helper-first cubiertos", result)
        self.assertIn("6 flujos principales con cierre canónico", result)
        self.assertIn("_composicion se carga desde la instalación del plugin", result)
        self.assertIn("gates libres sin aprobacion incondicional", result)
        self.assertIn("autopilot por config/estado sin flag publico fantasma", result)

    def test_command_execution_contracts_reject_unconditional_free_gates(self):
        """Las gates libres no deben declarar aprobacion sin evidencia."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "commands/ship.md":
                return original_read(path).replace(
                    "Puede cerrarse sin aprobación humana, pero no declares la fase superada si faltan artefactos.",
                    "Se aprueba siempre.",
                    1,
                )
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_command_execution_contracts()
        finally:
            release_audit._read = original_read

        self.assertIn("ship", str(context.exception))
        self.assertIn("aprobacion incondicional", str(context.exception))

    def test_public_claims_do_not_drift_from_current_inventory(self):
        """README, web, arquitectura y agentes no deben prometer contadores viejos."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_public_claims()

        self.assertIn("inventario publico 19/62/26/13 verificado", result)
        self.assertIn("README, arquitectura, help y agentes sin contadores antiguos", result)
        self.assertIn("displayName humano reflejado en README y changelog", result)
        self.assertIn("skills delicados mantienen activacion manual explicita", result)
        self.assertIn("prompts runtime sin /alfred legacy", result)
        self.assertIn("Lucius no fija modelo obsoleto de Codex CLI", result)

    def test_public_claims_reject_absolute_gate_language(self):
        """La superficie publica no debe prometer gates absolutas sin matiz."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "README.md":
                return original_read(path) + "\nNo hay excepciones, no hay modo de saltárselas\n"
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("README.md", str(context.exception))
        self.assertIn("No hay excepciones", str(context.exception))

    def test_public_claims_reject_llm_determinism_overclaim(self):
        """La docs de agentes no debe prometer determinismo de modelo."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "docs/agents/README.md":
                return (
                    original_read(path)
                    + "\nEl resultado es previsible y reproducible: produce resultados consistentes porque no arrastra contexto.\n"
                )
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/agents/README.md", str(context.exception))
        self.assertIn("previsible y reproducible", str(context.exception))

    def test_public_claims_reject_absolute_quality_overclaims(self):
        """TDD, seguridad, UX e i18n deben prometer evidencia, no garantias totales."""
        cases = [
            (
                "docs/flows.md",
                "garantiza que cada linea de código tiene al menos un test",
                "cada linea",
            ),
            (
                "docs/skills.md",
                "garantizar que el software sea usable por todas las personas",
                "usable por todas",
            ),
            (
                "docs/agents/security-officer.md",
                "garantizar que el software cumple con los estandares de seguridad",
                "estandares de seguridad",
            ),
            (
                "agents/security-officer.md",
                "garantiza que nada con vulnerabilidades conocidas llega a los usuarios",
                "vulnerabilidades conocidas",
            ),
            (
                "agents/i18n-specialist.md",
                "garantizar que el software habla todos los idiomas que dice hablar",
                "todos los idiomas",
            ),
            (
                "agents/alfred.md",
                "Las HARD-GATES son condiciones que NUNCA se pueden saltar",
                "NUNCA se pueden saltar",
            ),
            (
                "agents/security-officer.md",
                "bloqueantes absolutos. Sin excepciones",
                "Sin excepciones",
            ),
            (
                "hooks/session-start.sh",
                "Las quality gates son infranqueables",
                "infranqueables",
            ),
        ]

        for path, stale_claim, expected_fragment in cases:
            with self.subTest(path=path):
                release_audit = _load_release_audit_module()
                original_read = release_audit._read

                def fake_read(read_path):
                    if read_path == path:
                        return original_read(read_path) + f"\n{stale_claim}\n"
                    return original_read(read_path)

                release_audit._read = fake_read
                try:
                    with self.assertRaises(release_audit.AuditError) as context:
                        release_audit.check_public_claims()
                finally:
                    release_audit._read = original_read

                self.assertIn(path, str(context.exception))
                self.assertIn(expected_fragment, str(context.exception))

    def test_public_claims_reject_agent_manifest_drift(self):
        """Los docs no pueden volver a decir que plugin.json declara agents."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "docs/agents/README.md":
                return (
                    "Los agentes tambien aparecen en `plugin.json` para que "
                    "la superficie publicada sea completa."
                )
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/agents/README.md", str(context.exception))
        self.assertIn("plugin.json", str(context.exception))

    def test_public_claims_reject_stale_core_counter_on_landing(self):
        """La landing no debe volver al contador congelado de seis modulos core."""
        self._skip_without_site()
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "site/src/i18n/data.en.ts":
                return original_read(path) + "\nconst stale = '6 core modules';\n"
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("site/src/i18n/data.en.ts", str(context.exception))
        self.assertIn("6 core modules", str(context.exception))

    def test_public_claims_reject_sonarqube_without_confirmation_claim(self):
        """SonarQube/Docker no debe prometer ejecucion sin confirmacion humana."""
        self._skip_without_site()
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "site/src/i18n/data.en.ts":
                return (
                    original_read(path)
                    + "\nconst stale = 'start SonarQube without asking the user for confirmation';\n"
                )
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("site/src/i18n/data.en.ts", str(context.exception))
        self.assertIn("without asking the user for confirmation", str(context.exception))

    def test_public_claims_reject_sonarqube_end_to_end_docker_claim(self):
        """La landing no debe afirmar SonarQube Docker real sin evidencia externa."""
        self._skip_without_site()
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "site/src/i18n/data.en.ts":
                return original_read(path) + "\nconst stale = 'Verified end-to-end with Docker';\n"
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("site/src/i18n/data.en.ts", str(context.exception))
        self.assertIn("Verified end-to-end with Docker", str(context.exception))

    def test_public_claims_reject_changelog_docker_without_prompt_claim(self):
        """El changelog publico no debe reintroducir Docker sin confirmacion."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "CHANGELOG.md":
                return original_read(path) + "\nSonarQube sin prompt de confirmación al usuario\n"
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("CHANGELOG.md", str(context.exception))
        self.assertIn("sin prompt de confirmación al usuario", str(context.exception))

    def test_public_claims_reject_stale_manual_matrix_option_count(self):
        """El changelog no debe quedarse con el conteo antiguo de opciones manuales."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "CHANGELOG.md":
                return original_read(path).replace(
                    "40 opciones públicas y 4 contratos runtime de `/update`",
                    "22 opciones/variantes documentadas",
                    1,
                )
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("CHANGELOG.md", str(context.exception))
        self.assertIn("40 opciones públicas", str(context.exception))
        self.assertIn("4 contratos runtime", str(context.exception))

    def test_public_claims_reject_keyword_based_dynamic_composition(self):
        """La composición dinámica publica no debe prometer matching por keywords."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "README.md":
                return original_read(path) + "\nmatching con keywords contextuales\n"
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("README.md", str(context.exception))
        self.assertIn("keywords contextuales", str(context.exception))

    def test_public_claims_reject_manual_only_skill_drift(self):
        """Los skills delicados no deben volver a activacion automatica."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "skills/calidad/sonarqube/SKILL.md":
                return text.replace("disable-model-invocation: true\n", "")
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_public_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("skills/calidad/sonarqube/SKILL.md", str(context.exception))
        self.assertIn("activacion manual explicita", str(context.exception))

    def test_config_contracts_cover_all_public_sections(self):
        """El comando config debe exponer las 7 secciones reales del runtime."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_config_contracts()

        self.assertIn("7 secciones config alineadas con runtime", result)
        self.assertIn("deteccion automatica cubre stacks prometidos", result)
        self.assertIn("menu config principal expone salida y secciones canonicas", result)
        self.assertIn("docs y comando config cubren helpers canonicos", result)
        self.assertIn("AskUserQuestion config/optional usa questions[] y multiSelect actuales", result)

    def test_config_contracts_reject_obsolete_ask_user_question_examples(self):
        """Los ejemplos de AskUserQuestion deben usar el schema actual."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "commands/config.md":
                return original_read(path).replace(
                    "AskUserQuestion({\n"
                    "  questions: [\n"
                    "    {\n"
                    "      question: \"¿Qué agente técnico quieres activar ahora?\",\n"
                    "      header: \"Técnicos\",\n"
                    "      multiSelect: false,\n"
                    "      options: [\n"
                    "        { label: \"Seguir sin activar más\", description: \"Pasar al siguiente grupo\" },\n"
                    "        { label: \"Data Engineer\", description: \"<razón contextual>\" },\n"
                    "        { label: \"Performance Engineer\", description: \"<razón contextual>\" },\n"
                    "        { label: \"GitHub Manager\", description: \"<razón contextual>\" }\n"
                    "      ]\n"
                    "    }\n"
                    "  ]\n"
                    "})",
                    "AskUserQuestion({\n"
                    "  question: \"¿Qué agente técnico quieres activar ahora?\",\n"
                    "  header: \"Técnicos\",\n"
                    "  options: [\n"
                    "    { label: \"Seguir sin activar más\", description: \"Pasar al siguiente grupo\" }\n"
                    "  ]\n"
                    "})",
                )
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_config_contracts()
        finally:
            release_audit._read = original_read

        self.assertIn("AskUserQuestion obsoleto", str(context.exception))
        self.assertIn("questions: [", str(context.exception))
        self.assertIn("multiSelect: false", str(context.exception))

    def test_flow_gate_claims_cover_selina_and_autopilot_boundaries(self):
        """Los claims de Selina, gates y autopilot deben ejercitar orquestador real."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_flow_gate_claims()

        self.assertIn("feature mantiene 7 fases con Selina condicional", result)
        self.assertIn("gates libres documentadas como evidencia sin aprobacion humana", result)
        self.assertIn("gates automaticas bloquean tests rojos y seguridad KO", result)
        self.assertIn("autopilot no salta gates automaticas ni despliegue humano", result)

    def test_flow_gate_claims_reject_lax_free_gate_docs(self):
        """Las docs no deben volver a convertir gate libre en aprobacion ceremonial."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "docs/flows.md":
                return text.replace(
                    "Se supera cuando el resultado del agente responsable es favorable y hay evidencia directa del artefacto o checklist esperado.",
                    "Se supera siempre que el resultado sea favorable.",
                    1,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_flow_gate_claims()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/flows.md", str(context.exception))
        self.assertIn("gate libre", str(context.exception))

    def test_hook_contracts_keep_exec_form_and_fail_closed_guards(self):
        """Los hooks deben usar exec form y conservar bloqueos exit 2."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_hook_contracts()

        self.assertIn("13 hooks visibles registrados", result)
        self.assertIn("scripts de hooks declarados existen y cubren los 13 visibles", result)
        self.assertIn("exec form sin shell wrappers ni rutas sin comillas", result)
        self.assertIn("hooks bloqueantes conservan exit 2", result)
        self.assertIn("hooks con exit 2 no emiten JSON ignorado por Claude Code", result)
        self.assertIn("eventos sin matcher no declaran matcher ignorado", result)
        self.assertIn("hooks no usan if fuera de eventos de herramienta", result)
        self.assertIn("hooks sincronos declaran timeout entero <= 10 segundos", result)
        self.assertIn("docs de hooks usan decision/hookSpecificOutput actuales", result)

    def test_hook_contracts_reject_if_on_non_tool_event(self):
        """Claude solo evalúa if en eventos de herramienta."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == "hooks/hooks.json":
                data = dict(data)
                hooks = {
                    event: [
                        {
                            **group,
                            "hooks": [dict(hook) for hook in group.get("hooks", [])],
                        }
                        for group in groups
                    ]
                    for event, groups in data["hooks"].items()
                }
                hooks["Stop"][0]["hooks"][0]["if"] = "Bash(*)"
                data["hooks"] = hooks
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._json = original_json

        self.assertIn("declara if que Claude Code no evalua", str(context.exception))
        self.assertIn("Stop", str(context.exception))

    def test_hook_contracts_reject_matcher_on_event_that_ignores_it(self):
        """Claude ignora matcher en algunos eventos; no debemos dar falsa precision."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == "hooks/hooks.json":
                data = dict(data)
                hooks = {
                    event: [dict(group) for group in groups]
                    for event, groups in data["hooks"].items()
                }
                hooks["Stop"][0]["matcher"] = "Bash"
                data["hooks"] = hooks
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._json = original_json

        self.assertIn("matcher que Claude Code ignora", str(context.exception))
        self.assertIn("Stop", str(context.exception))

    def test_hook_contracts_require_user_prompt_expansion(self):
        """Los slash commands directos deben quedar cubiertos por UserPromptExpansion."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == "hooks/hooks.json":
                data = dict(data)
                hooks = dict(data["hooks"])
                hooks.pop("UserPromptExpansion", None)
                data["hooks"] = hooks
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._json = original_json

        self.assertIn("Eventos de hooks desalineados", str(context.exception))
        self.assertIn("UserPromptExpansion", str(context.exception))

    def test_hook_contracts_reject_slow_sync_hooks(self):
        """Los hooks síncronos deben tener timeout explicito y conservador."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == "hooks/hooks.json":
                data = dict(data)
                hooks = {
                    event: [
                        {
                            **group,
                            "hooks": [dict(hook) for hook in group.get("hooks", [])],
                        }
                        for group in groups
                    ]
                    for event, groups in data["hooks"].items()
                }
                hooks["Stop"][0]["hooks"][1]["timeout"] = 15
                data["hooks"] = hooks
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._json = original_json

        self.assertIn("hook sincronico supera timeout 10s", str(context.exception))
        self.assertIn("stop-hook.py", str(context.exception))

    def test_hook_contracts_reject_sync_hooks_without_timeout(self):
        """Un hook síncrono sin timeout puede dejar la sesión bloqueada."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == "hooks/hooks.json":
                data = dict(data)
                hooks = {
                    event: [
                        {
                            **group,
                            "hooks": [dict(hook) for hook in group.get("hooks", [])],
                        }
                        for group in groups
                    ]
                    for event, groups in data["hooks"].items()
                }
                hooks["UserPromptSubmit"][0]["hooks"][0].pop("timeout", None)
                data["hooks"] = hooks
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._json = original_json

        self.assertIn("hook sincronico sin timeout entero", str(context.exception))
        self.assertIn("activity-capture.py", str(context.exception))

    def test_hook_contracts_reject_boolean_sync_timeout(self):
        """Un timeout booleano no es un entero valido para hooks."""
        release_audit = _load_release_audit_module()
        original_json = release_audit._json

        def fake_json(path):
            data = original_json(path)
            if path == "hooks/hooks.json":
                data = dict(data)
                hooks = {
                    event: [
                        {
                            **group,
                            "hooks": [dict(hook) for hook in group.get("hooks", [])],
                        }
                        for group in groups
                    ]
                    for event, groups in data["hooks"].items()
                }
                hooks["UserPromptSubmit"][0]["hooks"][0]["timeout"] = True
                data["hooks"] = hooks
            return data

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._json = original_json

        self.assertIn("hook sincronico sin timeout entero", str(context.exception))
        self.assertIn("activity-capture.py", str(context.exception))

    def test_hook_contracts_reject_spanish_decision_key_in_docs(self):
        """La doc de hooks no debe enseñar claves JSON que Claude Code no entiende."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "docs/hooks.md":
                return text + '\nEjemplo obsoleto: {"decisión": "block"}\n'
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._read = original_read

        self.assertIn("decisión", str(context.exception))

    def test_hook_contracts_reject_nested_event_specific_hook_output_docs(self):
        """La doc no debe enseñar hookSpecificOutput.<Evento>.additionalContext."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "docs/hooks.md":
                return text + "\nEjemplo viejo: hookSpecificOutput.PreCompact.additionalContext\n"
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_hook_contracts()
        finally:
            release_audit._read = original_read

        message = str(context.exception)
        self.assertIn("hookSpecificOutput anidado", message)
        self.assertIn("PreCompact", message)

    def test_packaging_contracts_exclude_local_artifacts(self):
        """El paquete seco no debe incluir caches, sesiones locales ni tests."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_packaging_contracts()

        self.assertIn(f"npm pack dry-run {release_audit.VERSION} valido", result)
        self.assertIn("paquete sin caches locales ni tests", result)
        self.assertIn("paquete sin .claude/.crupier ni evidencias manuales", result)
        self.assertIn("paquete sin symlinks publicables fuera del plugin", result)
        self.assertIn("paquete contiene 25 comandos namespaced, /alfred como skill personal global fuente sin shim de comando duplicado, 19 agentes y 62 skills", result)
        self.assertIn("paquete contiene 7 templates de artefactos", result)
        self.assertIn("paquete contiene runtime visual de Selina", result)

    def test_packaging_contracts_reject_publishable_symlink_problem(self):
        """El gate de empaquetado debe fallar si el escaneo de symlinks detecta problemas."""
        release_audit = _load_release_audit_module()
        original_symlink_scan = release_audit._publishable_symlink_problems

        release_audit._publishable_symlink_problems = lambda: [
            "templates/external.md es un symlink fuera del plugin: '../external.md'"
        ]
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_packaging_contracts()
        finally:
            release_audit._publishable_symlink_problems = original_symlink_scan

        self.assertIn("Symlinks publicables incompatibles", str(context.exception))
        self.assertIn("templates/external.md", str(context.exception))

    def test_publishable_symlink_scan_rejects_external_target(self):
        """Claude salta symlinks fuera del plugin al copiar a cache; no pueden ser superficie."""
        release_audit = _load_release_audit_module()
        original_root = release_audit.ROOT
        original_roots = release_audit.PUBLISHABLE_SYMLINK_ROOTS

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "plugin"
            external = Path(tmpdir) / "external.md"
            (workspace / "templates").mkdir(parents=True)
            external.write_text("outside\n", encoding="utf-8")
            os.symlink(external, workspace / "templates" / "external.md")
            release_audit.ROOT = workspace
            release_audit.PUBLISHABLE_SYMLINK_ROOTS = ("templates",)
            try:
                problems = release_audit._publishable_symlink_problems()
            finally:
                release_audit.ROOT = original_root
                release_audit.PUBLISHABLE_SYMLINK_ROOTS = original_roots

        self.assertTrue(any("symlink fuera del plugin" in problem for problem in problems), problems)

    def test_publishable_symlink_scan_rejects_broken_link(self):
        """Un symlink roto puede pasar desapercibido hasta instalación; se bloquea antes."""
        release_audit = _load_release_audit_module()
        original_root = release_audit.ROOT
        original_roots = release_audit.PUBLISHABLE_SYMLINK_ROOTS

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "plugin"
            (workspace / "templates").mkdir(parents=True)
            os.symlink(workspace / "templates" / "missing.md", workspace / "templates" / "broken.md")
            release_audit.ROOT = workspace
            release_audit.PUBLISHABLE_SYMLINK_ROOTS = ("templates",)
            try:
                problems = release_audit._publishable_symlink_problems()
            finally:
                release_audit.ROOT = original_root
                release_audit.PUBLISHABLE_SYMLINK_ROOTS = original_roots

        self.assertTrue(any("symlink roto" in problem for problem in problems), problems)

    def test_packaging_contracts_reject_crupier_artifacts(self):
        """El paquete seco no debe arrastrar auditorias locales de .crupier."""
        release_audit = _load_release_audit_module()
        original_pack = release_audit._npm_pack_dry_run_package
        base_package = original_pack()
        leaked = dict(base_package)
        leaked["files"] = list(base_package["files"]) + [
            {"path": ".crupier/audits/project_doctor.json", "size": 2}
        ]

        release_audit._npm_pack_dry_run_package = lambda: leaked
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_packaging_contracts()
        finally:
            release_audit._npm_pack_dry_run_package = original_pack

        self.assertIn(".crupier/audits/project_doctor.json", str(context.exception))

    def test_packaging_contracts_reject_missing_template(self):
        """Las plantillas citadas por agentes y skills son superficie publicable."""
        release_audit = _load_release_audit_module()
        original_pack = release_audit._npm_pack_dry_run_package
        base_package = original_pack()
        missing_template = dict(base_package)
        missing_template["files"] = [
            entry
            for entry in base_package["files"]
            if entry.get("path") != "templates/prd.md"
        ]

        release_audit._npm_pack_dry_run_package = lambda: missing_template
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_packaging_contracts()
        finally:
            release_audit._npm_pack_dry_run_package = original_pack

        self.assertIn("templates/prd.md", str(context.exception))

    def test_packaging_contracts_reject_missing_selina_visual_runtime(self):
        """El companion visual de Selina debe viajar en el paquete instalable."""
        release_audit = _load_release_audit_module()
        original_pack = release_audit._npm_pack_dry_run_package
        base_package = original_pack()
        missing_visual = dict(base_package)
        missing_visual["files"] = [
            entry
            for entry in base_package["files"]
            if entry.get("path") != "visual/scripts/start-server.sh"
        ]

        release_audit._npm_pack_dry_run_package = lambda: missing_visual
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_packaging_contracts()
        finally:
            release_audit._npm_pack_dry_run_package = original_pack

        self.assertIn("visual/scripts/start-server.sh", str(context.exception))

    def test_published_package_secret_scan_uses_canonical_patterns(self):
        """El artefacto publicable no debe contener patrones reales de secretos."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_published_secret_scan()

        self.assertIn("paquete publicable sin patrones de secretos reales", result)

    def test_install_update_contracts_use_explicit_safe_scopes(self):
        """Install/update deben usar scopes explícitos y mantener gate humana."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_install_update_contracts()

        self.assertIn("instaladores usan scope user explicito", result)
        self.assertIn("instaladores verifican scope user despues de instalar", result)
        self.assertIn("instaladores limpian scopes local/project heredados antes de instalar user", result)
        self.assertIn("instaladores materializan /alfred como skill personal global y eliminan shim de comando obsoleto", result)
        self.assertNotIn("instalación local que limpiar", release_audit._read("uninstall.sh"))
        self.assertIn("update conserva semver y menu humano, normaliza a scope user y documenta reload/reinicio", result)

    def test_install_update_contracts_reject_new_stateful_cli_without_user_scope(self):
        """El gate debe detectar rutas nuevas aunque los comandos canonicos existan."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "install.sh":
                return text + '\nclaude plugin marketplace add "${REPO}"\n'
            return text

        try:
            release_audit._read = fake_read
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_install_update_contracts()
        finally:
            release_audit._read = original_read

        self.assertIn("CLI plugin sin scope explicito user", str(context.exception))
        self.assertIn("install.sh", str(context.exception))

    def test_human_contracts_cover_questions_uat_and_honesty(self):
        """El release no puede perder menus humanos ni antifingimiento."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_human_contracts()

        self.assertIn("AskUserQuestion limitado a ambigüedad real y gates humanas", result)
        self.assertIn("UAT exige indicación humana explícita", result)
        self.assertIn("antifingimiento centralizado en comandos y agente Alfred", result)

    def test_audit_docs_require_manual_matrix_for_all_public_commands(self):
        """La matriz manual debe cubrir comandos y opciones publicas."""
        release_audit = _load_release_audit_module()

        result = release_audit.check_audit_docs()

        self.assertIn("matriz manual cubre 26 rutas publicas", result)
        self.assertIn("commands/ documentado como skills planas soportadas", result)
        self.assertIn("matriz manual cubre 40 opciones publicas", result)
        self.assertIn("matriz manual valida IDs de opcion contra comandos publicos", result)
        self.assertIn("manual review report muestra notas humanas debiles o repetidas", result)
        self.assertIn("manual review gate exige preflight actual antes de aprobar", result)
        self.assertIn("matriz manual enlaza contratos al comando correcto", result)
        self.assertIn("matriz manual valida prompts contra comandos declarados", result)
        self.assertIn("matriz manual ata cada argument-hint a una opcion cubierta", result)
        self.assertIn("matriz manual valida contratos runtime de update", result)
        self.assertIn("matriz manual cubre 4 contratos runtime", result)
        self.assertIn("manual smoke tiene preflight de autenticacion real y evidencia fail-fast", result)
        self.assertIn("evidencia manual y plantillas se escriben con permisos 0600", result)
        self.assertIn("evidencias manuales ignoradas por git y npm", result)
        self.assertIn("estado operativo docs/project ignorado por git y npm", result)
        self.assertIn("evidencia manual sanea previews con core/secrets.py", result)
        self.assertIn("manual review gate exige aprobacion humana explicita", result)
        self.assertIn("manual review gate rechaza evidencia/review con secretos", result)
        self.assertIn("manual review gate no crea plantillas desde evidencia con secretos", result)
        self.assertIn("manual review gate ata evidence_file al JSON validado", result)
        self.assertIn("plugin_surface.sha256 documentado coincide con superficie real del plugin", result)
        self.assertIn("manual review gate valida metadatos de review contra matriz actual", result)
        self.assertIn("manual review gate valida mapas de cobertura contra matriz actual", result)
        self.assertIn("scripts npm manual/preflight alineados", result)
        self.assertIn("prepublish:prepare genera evidencias manuales antes de la revision humana", result)
        self.assertIn("prepublish valida evidencias manuales ya revisadas sin regenerarlas", result)
        self.assertIn("plugin details documenta displayName humano", result)
        self.assertIn("docs oficiales revalidadas 2026-06-20", result)
        self.assertIn("readiness de salida mantiene pendientes humanos y externos", result)
        self.assertIn("runbook de revision humana documenta criterios y bloqueos", result)

    def test_audit_docs_require_safe_external_preflight_runner(self):
        """Los pendientes externos deben tener evidencia sin efectos por defecto."""
        release_audit = _load_release_audit_module()
        package = release_audit._json("package.json")

        result = release_audit.check_audit_docs()

        self.assertIn("readiness de salida mantiene pendientes humanos y externos", result)
        self.assertEqual(
            package["scripts"]["release:audit:external:preflight"],
            "python3 scripts/external_live_smoke.py --output docs/external-live-smoke-0.6.0.json",
        )
        self.assertIn("docs/external-live-smoke*.json", release_audit._read(".gitignore"))
        self.assertIn("docs/external-live-smoke*.json", release_audit._read(".npmignore"))

    def test_audit_docs_reject_prepare_without_evidence_generation(self):
        """La preparación debe escribir evidencia antes de que exista revisión humana."""
        release_audit = _load_release_audit_module()
        package = release_audit._json("package.json")
        original_json = release_audit._json

        def fake_json(path):
            if path == "package.json":
                mutated = dict(package)
                scripts = dict(mutated["scripts"])
                scripts["release:audit:prepublish:prepare"] = (
                    "npm run release:audit:full && "
                    "npm run release:audit:manual:preflight"
                )
                mutated["scripts"] = scripts
                return mutated
            return original_json(path)

        release_audit._json = fake_json
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._json = original_json

        self.assertIn("release:audit:prepublish:prepare", str(context.exception))
        self.assertIn("release:audit:manual:evidence", str(context.exception))

    def test_audit_docs_reject_manual_evidence_missing_from_gitignore_or_npmignore(self):
        """Los JSON de evidencia manual no deben aparecer en git ni en npm pack."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read_without_gitignore(path):
            text = original_read(path)
            if path == ".gitignore":
                return text.replace("docs/manual-smoke*.json\n", "")
            return text

        release_audit._read = fake_read_without_gitignore
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/manual-smoke*.json", str(context.exception))

        def fake_read_without_npmignore(path):
            text = original_read(path)
            if path == ".npmignore":
                return text.replace("docs/manual-smoke*.json\n", "")
            return text

        release_audit._read = fake_read_without_npmignore
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/manual-smoke*.json", str(context.exception))

    def test_audit_docs_reject_manual_reports_missing_from_gitignore_or_npmignore(self):
        """Los reportes Markdown de evidencia manual tampoco deben empaquetarse."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read_without_gitignore(path):
            text = original_read(path)
            if path == ".gitignore":
                return text.replace("docs/manual-smoke*.md\n", "")
            return text

        release_audit._read = fake_read_without_gitignore
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/manual-smoke*.md", str(context.exception))

    def test_audit_docs_reject_project_state_missing_from_gitignore_or_npmignore(self):
        """Los artefactos operativos docs/project/ no forman parte del release."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read_without_gitignore(path):
            text = original_read(path)
            if path == ".gitignore":
                return text.replace("docs/project/\n", "")
            return text

        release_audit._read = fake_read_without_gitignore
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/project/", str(context.exception))

        def fake_read_without_npmignore(path):
            text = original_read(path)
            if path == ".npmignore":
                return text.replace("docs/project/\n", "")
            return text

        release_audit._read = fake_read_without_npmignore
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/project/", str(context.exception))

        def fake_read_without_npmignore(path):
            text = original_read(path)
            if path == ".npmignore":
                return text.replace("docs/manual-smoke*.md\n", "")
            return text

        release_audit._read = fake_read_without_npmignore
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/manual-smoke*.md", str(context.exception))

    def test_audit_docs_reject_stale_plugin_details_display_name(self):
        """La evidencia local debe reflejar el displayName visible en Claude Code."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "docs/release-audit-0.6.0.md":
                return text.replace(
                    "Resultado: Alfred Dev (alfred-dev) 0.6.0",
                    "Resultado: alfred-dev 0.6.0",
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("displayName humano", str(context.exception))

    def test_audit_docs_reject_stale_plugin_surface_hash(self):
        """La revisión humana debe quedar atada a la superficie real del plugin."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "docs/release-audit-0.6.0.md":
                return re.sub(
                    r"plugin_surface\.sha256=[0-9a-f]{64}",
                    "plugin_surface.sha256=" + ("0" * 64),
                    text,
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("plugin_surface.sha256 obsoleto", str(context.exception))

    def test_audit_docs_reject_architecture_claiming_all_hooks_have_matcher(self):
        """La arquitectura no debe prometer matcher universal en hooks."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "docs/architecture.md":
                return text.replace(
                    "`matcher` es opcional",
                    "cada hook tiene un matcher",
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("docs/architecture.md", str(context.exception))
        self.assertIn("`matcher` es opcional", str(context.exception))

    def test_audit_docs_reject_precompact_ignored_matcher_claim(self):
        """PreCompact soporta matcher; Alfred lo omite para cubrir manual y auto."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            text = original_read(path)
            if path == "docs/architecture.md":
                return text.replace(
                    "En `PreCompact`, Alfred omite `matcher` para cubrir tanto compactaciones manuales como automáticas.",
                    "En `PreCompact`, Alfred evita declarar `matcher` porque Claude Code lo ignora.",
                )
            return text

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("PreCompact ignora matcher", str(context.exception))

    def test_argument_hint_commands_are_covered_by_manual_options(self):
        """Todo comando con argument-hint/$ARGUMENTS debe tener opcion manual."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        argument_commands = release_audit._public_argument_commands()
        option_commands = {
            key.split(":", 1)[0]
            for key in manual_smoke.OPTION_CONTRACTS
        }

        self.assertEqual(
            argument_commands,
            {
                "alfred",
                "discuss",
                "feature",
                "fix",
                "lucius",
                "map-codebase",
                "quick",
                "search",
                "spike",
                "sync-github",
                "verify",
            },
        )
        self.assertEqual(sorted(argument_commands - option_commands), [])

    def test_new_argument_hint_without_manual_option_is_rejected(self):
        """Si un comando nuevo acepta argumentos, la matriz manual debe crecer."""
        release_audit = _load_release_audit_module()
        original_read = release_audit._read

        def fake_read(path):
            if path == "commands/status.md":
                return (
                    "---\n"
                    "description: \"Estado\"\n"
                    "argument-hint: \"[filtro opcional]\"\n"
                    "---\n"
                    "# /alfred-dev:status\n\n"
                    "Filtro: $ARGUMENTS\n"
                )
            return original_read(path)

        release_audit._read = fake_read
        try:
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_audit_docs()
        finally:
            release_audit._read = original_read

        self.assertIn("status", str(context.exception))

    def test_option_contract_shape_rejects_typos(self):
        """Los IDs de opciones deben apuntar a comandos reales y config exacta."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        bad_contracts = tuple(manual_smoke.OPTION_CONTRACTS) + (
            "statuz:filter",
            "config:fantasma",
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"OPTION_CONTRACTS": bad_contracts})
        option_coverage = {key: ["case"] for key in bad_contracts}

        with self.assertRaises(release_audit.AuditError) as context:
            release_audit._validate_manual_option_contract_shape(
                fake_manual_smoke,
                option_coverage,
            )

        message = str(context.exception)
        self.assertIn("statuz", message)
        self.assertIn("config:fantasma", message)

    def test_option_contract_shape_requires_explicit_lucius_all_scope(self):
        """Lucius debe probar --scope all explicito, no solo el default all."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        bad_contracts = tuple(
            key for key in manual_smoke.OPTION_CONTRACTS
            if key != "lucius:scope-all"
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"OPTION_CONTRACTS": bad_contracts})
        option_coverage = {key: ["case"] for key in bad_contracts}

        with self.assertRaises(release_audit.AuditError) as context:
            release_audit._validate_manual_option_contract_shape(
                fake_manual_smoke,
                option_coverage,
            )

        self.assertIn("lucius:scope-all", str(context.exception))

    def test_option_contract_shape_requires_human_permission_menus(self):
        """Los menus AskUserQuestion de permisos/gates son opciones publicas."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        bad_contracts = tuple(
            key for key in manual_smoke.OPTION_CONTRACTS
            if key != "audit:sonarqube-docker-install-menu"
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"OPTION_CONTRACTS": bad_contracts})
        option_coverage = {key: ["case"] for key in bad_contracts}

        with self.assertRaises(release_audit.AuditError) as context:
            release_audit._validate_manual_option_contract_shape(
                fake_manual_smoke,
                option_coverage,
            )

        self.assertIn("audit:sonarqube-docker-install-menu", str(context.exception))

    def test_runtime_contract_shape_rejects_typos(self):
        """Los contratos runtime deben apuntar a /update y scopes conocidos."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        bad_contracts = tuple(manual_smoke.RUNTIME_CONTRACTS) + (
            "updat:scope-local-to-user",
            "update:scope-worktree",
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"RUNTIME_CONTRACTS": bad_contracts})
        runtime_coverage = {key: ["case"] for key in bad_contracts}

        with self.assertRaises(release_audit.AuditError) as context:
            release_audit._validate_manual_runtime_contract_shape(
                fake_manual_smoke,
                runtime_coverage,
            )

        message = str(context.exception)
        self.assertIn("updat", message)
        self.assertIn("scope-worktree", message)

    def test_case_contract_links_reject_wrong_command_case(self):
        """Una opcion cubierta por un caso de otro comando no debe pasar."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        bad_option_case = manual_smoke.ManualCase(
            "wrong-option",
            "/alfred-dev:help",
            "No debe cubrir Lucius.",
            commands=("help",),
            option_keys=("lucius:scope-tests",),
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"CASES": (bad_option_case,)})

        with self.assertRaises(release_audit.AuditError) as option_context:
            release_audit._validate_manual_case_contract_links(fake_manual_smoke)

        bad_runtime_case = manual_smoke.ManualCase(
            "wrong-runtime",
            "/alfred-dev:status",
            "No debe cubrir update.",
            commands=("status",),
            runtime_keys=("update:scope-local-to-user",),
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"CASES": (bad_runtime_case,)})

        with self.assertRaises(release_audit.AuditError) as runtime_context:
            release_audit._validate_manual_case_contract_links(fake_manual_smoke)

        self.assertIn("wrong-option", str(option_context.exception))
        self.assertIn("lucius:scope-tests", str(option_context.exception))
        self.assertIn("wrong-runtime", str(runtime_context.exception))
        self.assertIn("update:scope-local-to-user", str(runtime_context.exception))

    def test_case_prompt_must_invoke_declared_command(self):
        """El prompt real del caso debe usar el slash command declarado."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        wrong_prompt_case = manual_smoke.ManualCase(
            "wrong-prompt",
            "/alfred-dev:help",
            "No debe declarar Lucius si el prompt ejecuta help.",
            commands=("lucius",),
            option_keys=("lucius:scope-tests",),
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"CASES": (wrong_prompt_case,)})

        with self.assertRaises(release_audit.AuditError) as context:
            release_audit._validate_manual_case_contract_links(fake_manual_smoke)

        message = str(context.exception)
        self.assertIn("wrong-prompt", message)
        self.assertIn("prompt no invoca", message)
        self.assertIn("help", message)

    def test_case_prompt_accepts_global_alfred_alias_for_alfred_command(self):
        """El alias /alfred cubre el contrato manual del comando contextual."""
        release_audit = _load_release_audit_module()
        manual_smoke = _load_manual_smoke_module()

        alias_case = manual_smoke.ManualCase(
            "alfred-alias",
            "/alfred que toca hacer ahora?",
            "Debe aceptar el alias corto como invocacion de Alfred.",
            commands=("alfred",),
            option_keys=("alfred:optional-prompt",),
        )
        fake_manual_smoke = type("FakeManualSmoke", (), {"CASES": (alias_case,)})

        release_audit._validate_manual_case_contract_links(fake_manual_smoke)

    def test_installed_cache_freshness_detects_worktree_drift(self):
        """El smoke Claude no debe aceptar una cache instalada stale."""
        release_audit = _load_release_audit_module()
        freshness_files = set(release_audit._iter_installed_cache_freshness_files())
        self.assertIn(".mcp.json", freshness_files)
        self.assertIn("package.json", freshness_files)
        self.assertIn("core/continuity.py", freshness_files)
        self.assertIn("templates/prd.md", freshness_files)
        self.assertIn("skills/alfred/alfred/SKILL.md", freshness_files)
        self.assertIn("scripts/claude_auth_recovery.py", freshness_files)

        def seed_cache_and_alias(tmpdir: str) -> Path:
            cache = Path(tmpdir) / "cache"
            release_audit.INSTALLED_PLUGIN_DIR = cache
            for relative in freshness_files:
                source = release_audit.ROOT / relative
                target = cache / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            alias_file = Path(tmpdir) / "home" / ".claude" / "skills" / "alfred" / "SKILL.md"
            alias_file.parent.mkdir(parents=True, exist_ok=True)
            alias_file.write_bytes(release_audit._materialized_alfred_alias_bytes())
            release_audit.GLOBAL_ALFRED_ALIAS_FILE = alias_file
            command_alias_file = Path(tmpdir) / "home" / ".claude" / "commands" / "alfred.md"
            command_alias_file.parent.mkdir(parents=True, exist_ok=True)
            command_alias_file.unlink(missing_ok=True)
            release_audit.GLOBAL_ALFRED_COMMAND_FILE = command_alias_file
            return cache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = seed_cache_and_alias(tmpdir)
            transient_pyc = release_audit.ROOT / "hooks" / "__pycache__" / "transient.cpython-314.pyc"
            try:
                transient_pyc.parent.mkdir(exist_ok=True)
                transient_pyc.write_bytes(b"transient")

                result = release_audit.check_installed_cache_freshness()
                self.assertIn("alias global /alfred", result[0])
                self.assertIn("sin shim de comando", result[0])
            finally:
                transient_pyc.unlink(missing_ok=True)

            release_audit.GLOBAL_ALFRED_ALIAS_FILE.unlink()
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_installed_cache_freshness()
            self.assertIn("No existe el alias personal global /alfred", str(context.exception))

            release_audit.GLOBAL_ALFRED_ALIAS_FILE.parent.mkdir(parents=True, exist_ok=True)
            release_audit.GLOBAL_ALFRED_ALIAS_FILE.write_text("stale alias\n", encoding="utf-8")
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_installed_cache_freshness()
            self.assertIn("alias personal global /alfred no coincide", str(context.exception))

            release_audit.GLOBAL_ALFRED_ALIAS_FILE.write_bytes(
                release_audit._materialized_alfred_alias_bytes()
            )
            release_audit.GLOBAL_ALFRED_COMMAND_FILE.parent.mkdir(parents=True, exist_ok=True)
            release_audit.GLOBAL_ALFRED_COMMAND_FILE.write_text("stale command alias\n", encoding="utf-8")
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_installed_cache_freshness()
            self.assertIn("duplica el selector", str(context.exception))

            release_audit.GLOBAL_ALFRED_COMMAND_FILE.unlink()
            (cache / "agents" / "lucius.md").write_text("stale lucius\n", encoding="utf-8")
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_installed_cache_freshness()

        self.assertIn("no coincide", str(context.exception))
        self.assertIn("agents/lucius.md", str(context.exception))

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = seed_cache_and_alias(tmpdir)
            (cache / "core" / "continuity.py").write_text("stale core\n", encoding="utf-8")
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_installed_cache_freshness()

        self.assertIn("core/continuity.py", str(context.exception))

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = seed_cache_and_alias(tmpdir)
            (cache / "templates" / "prd.md").write_text("stale template\n", encoding="utf-8")
            with self.assertRaises(release_audit.AuditError) as context:
                release_audit.check_installed_cache_freshness()

        self.assertIn("templates/prd.md", str(context.exception))


if __name__ == "__main__":
    unittest.main()
