#!/usr/bin/env python3
"""Contratos de superficie publica para evitar desalineaciones de release.

Estos tests verifican que los numeros y claims principales del plugin
(agentes, comandos, skills, dominios, fases y requisitos de instalacion)
coincidan entre el estado real del repo y la documentacion/manifiestos
que se publican al usuario.
"""

import json
import os
import re
import unicodedata
import unittest


ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relative_path: str) -> str:
    path = os.path.normpath(os.path.join(ROOT, relative_path))
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _read_json(relative_path: str):
    return json.loads(_read(relative_path))


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def _slice_between(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def _count_skill_files() -> int:
    count = 0
    for dirpath, _dirnames, filenames in os.walk(os.path.join(ROOT, "skills")):
        count += filenames.count("SKILL.md")
    return count


def _count_skill_domains() -> int:
    domains = set()
    skills_root = os.path.join(ROOT, "skills")
    for dirpath, _dirnames, filenames in os.walk(skills_root):
        if "SKILL.md" not in filenames:
            continue
        rel = os.path.relpath(dirpath, skills_root)
        domain = rel.split(os.sep, 1)[0]
        domains.add(domain)
    return len(domains)


def _iter_manifest_skill_files():
    plugin = _read_json(".claude-plugin/plugin.json")
    skill_files = []

    for relative_path in plugin["skills"]:
        absolute = os.path.join(ROOT, relative_path.lstrip("./"))
        if os.path.isdir(absolute):
            for dirpath, _dirnames, filenames in os.walk(absolute):
                if "SKILL.md" in filenames:
                    skill_files.append(os.path.join(dirpath, "SKILL.md"))
            continue

        if os.path.isfile(absolute) and os.path.basename(absolute) == "SKILL.md":
            skill_files.append(absolute)

    return sorted(skill_files)


def _parse_frontmatter_fields(path: str):
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.join(ROOT, path))

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    if not text.startswith("---\n"):
        return {}

    fields = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


class TestRuntimeSurfaceCounts(unittest.TestCase):
    def test_manifest_and_filesystem_reflect_current_counts(self):
        plugin = _read_json(".claude-plugin/plugin.json")
        published_skill_files = _iter_manifest_skill_files()

        self.assertEqual(len(plugin["commands"]), 26)
        self.assertEqual(len(plugin["agents"]), 19)
        self.assertEqual(_count_skill_files(), 61)
        self.assertEqual(_count_skill_domains(), 14)
        self.assertEqual(len(published_skill_files), 61)
        self.assertEqual(len(set(published_skill_files)), 61)

        for relative_path in plugin["commands"] + plugin["agents"] + plugin["skills"]:
            absolute = os.path.join(ROOT, relative_path.lstrip("./"))
            self.assertTrue(
                os.path.exists(absolute),
                f"No existe el recurso declarado en plugin.json: {relative_path}",
            )

    def test_published_skills_have_canonical_frontmatter(self):
        for skill_path in _iter_manifest_skill_files():
            frontmatter = _parse_frontmatter_fields(skill_path)
            self.assertTrue(
                frontmatter.get("name"),
                f"Falta `name` en el frontmatter de {skill_path}",
            )
            self.assertTrue(
                frontmatter.get("description"),
                f"Falta `description` en el frontmatter de {skill_path}",
            )

    def test_manual_only_skills_keep_explicit_disable_model_invocation(self):
        manual_only = [
            "skills/estilo/style-direction/SKILL.md",
            "skills/calidad/incident-response/SKILL.md",
            "skills/calidad/sonarqube/SKILL.md",
            "skills/devops/release-planning/SKILL.md",
            "skills/github/pr-workflow/SKILL.md",
            "skills/github/release/SKILL.md",
            "skills/github/repo-setup/SKILL.md",
        ]

        for relative_path in manual_only:
            frontmatter = _parse_frontmatter_fields(relative_path)
            self.assertEqual(
                frontmatter.get("disable-model-invocation"),
                "true",
                f"El skill manual {relative_path} debe mantener disable-model-invocation: true",
            )

    def test_published_skill_names_do_not_shadow_commands(self):
        plugin = _read_json(".claude-plugin/plugin.json")
        command_names = {
            os.path.splitext(os.path.basename(relative_path))[0]
            for relative_path in plugin["commands"]
        }
        skill_names = {
            _parse_frontmatter_fields(skill_path).get("name")
            for skill_path in _iter_manifest_skill_files()
        }
        collisions = sorted(name for name in (skill_names & command_names) if name)
        self.assertFalse(
            collisions,
            f"Las skills publicadas no deben sombrear comandos existentes: {collisions}",
        )


class TestReadmeAndDocsSurface(unittest.TestCase):
    def test_readme_matches_current_public_claims(self):
        readme = _read("README.md")
        self.assertIn("catalogo publicado de 61 skills en 14 dominios", _normalize(readme))
        self.assertIn("Ciclo completo de hasta 7 fases", readme)
        self.assertIn("Python 3.10+ (para hooks, core y MCP en macOS, Linux y Windows).", readme)
        self.assertIn("historico por version", _normalize(readme))

    def test_docs_readme_and_architecture_match_current_surface(self):
        docs_readme = _read("docs/README.md")
        architecture = _read("docs/architecture.md")
        agents_readme = _read("docs/agents/README.md")

        self.assertIn("feature -- hasta 7 fases", docs_readme)
        self.assertIn("Catalogo publicado de 61 skills en 14 dominios", docs_readme)
        self.assertIn("26 comandos registrados en `plugin.json`", architecture)
        self.assertIn("Por que los agentes de nucleo tambien aparecen en `plugin.json`", architecture)
        self.assertIn("Agentes opcionales** (9)", architecture)
        self.assertIn("optional_agents.py", architecture)
        self.assertIn("build_optional_agent_group_menus()", architecture)
        self.assertNotIn("TASK_KEYWORDS", architecture)
        self.assertIn("hasta siete fases", agents_readme)
        self.assertIn("estilo visual", agents_readme)
        self.assertIn("publica el catalogo completo por dominios", _normalize(_read("docs/skills.md")))

    def test_skills_docs_cover_manual_and_special_domains_in_catalog(self):
        skills_doc = _read("docs/skills.md")
        self.assertIn("e2e-testing", skills_doc)
        self.assertIn("incident-response", skills_doc)
        self.assertIn("release-planning", skills_doc)
        self.assertIn("style-direction", skills_doc)
        self.assertIn("dependency-strategy", skills_doc)
        self.assertIn("## Estilo", skills_doc)

    def test_every_manifest_agent_has_public_docs_page(self):
        plugin = _read_json(".claude-plugin/plugin.json")
        docs_readme = _read("docs/README.md")
        agents_index = _read("docs/agents/README.md")

        for relative_path in plugin["agents"]:
            agent_name = os.path.splitext(os.path.basename(relative_path))[0]
            public_doc = f"docs/agents/{agent_name}.md"
            absolute_doc = os.path.join(ROOT, public_doc)
            self.assertTrue(
                os.path.exists(absolute_doc),
                f"Falta la ficha pública del agente {agent_name}: {public_doc}",
            )
            self.assertIn(
                f"agents/{agent_name}.md",
                docs_readme,
                f"docs/README.md no enlaza la ficha pública de {agent_name}",
            )
            self.assertIn(
                f"[{agent_name}.md]({agent_name}.md)",
                agents_index,
                f"docs/agents/README.md no enlaza la ficha pública de {agent_name}",
            )

    def test_feature_docs_protect_selina_phase(self):
        flows = _read("docs/flows.md")
        alfred_agent = _read("docs/agents/alfred.md")
        feature_command = _read("commands/feature.md")
        fix_command = _read("commands/fix.md")
        quick_command = _read("commands/quick.md")
        spike_command = _read("commands/spike.md")
        audit_command = _read("commands/audit.md")
        seo_specialist = _read("docs/agents/seo-specialist.md")
        lucius = _read("docs/agents/lucius.md")
        copywriter = _read("docs/agents/copywriter.md")
        ship_command = _read("commands/ship.md")
        github_manager = _read("docs/agents/github-manager.md")
        librarian = _read("docs/agents/librarian.md")
        devops = _read("docs/agents/devops-engineer.md")
        tech_writer = _read("docs/agents/tech-writer.md")

        self.assertIn("Fase 1b: estilo visual", flows)
        self.assertIn("gate_estilo", flows)
        self.assertIn("| `feature` | Nueva funcionalidad, desde la idea hasta la entrega | 7", flows)
        self.assertIn("gate_arquitectura [usuario+seguridad]", flows)
        self.assertIn("gate_empaquetado [automático+seguridad]", flows)
        self.assertIn("## Flujo quick", flows)
        self.assertIn("gate_validacion_rapida", flows)
        self.assertIn("fuente runtime", flows)
        self.assertIn("## Flujo spike", flows)
        self.assertIn("bajo demanda", flows)
        self.assertIn("hasta 7 fases", alfred_agent)
        self.assertIn("Flujo de hasta 7 fases", feature_command)
        self.assertIn("**librarian** | Consulta histórica bajo demanda", feature_command)
        self.assertIn("**lucius** | Calidad", feature_command)
        self.assertIn("composición dinámica efímera o por fallback a `.claude/alfred-dev.local.md`", feature_command)
        self.assertIn("consulta `equipo_sesion` como fuente runtime canónica", feature_command)
        self.assertIn("Si `lucius` está activo en `equipo_sesion`", flows)
        self.assertIn("Si `copywriter` está activo", flows)
        self.assertIn("usuario+seguridad", ship_command)
        self.assertIn("**GATE (automático+seguridad):** Pipeline verde y firma válida.", ship_command)
        self.assertIn("confirmación siempre interactiva", ship_command)
        self.assertIn("Si hay opcionales activos en `equipo_sesion`", fix_command)
        self.assertIn("fallback a `.claude/alfred-dev.local.md`", fix_command)
        self.assertIn("Consulta `equipo_sesion` como fuente runtime canónica", fix_command)
        self.assertIn("Si `github-manager` está activo en `equipo_sesion`", ship_command)
        self.assertIn("Si `equipo_sesion` trae opcionales activos", ship_command)
        self.assertIn("consúltalo siempre", ship_command)
        self.assertIn("fuente runtime canónica", ship_command)
        self.assertIn("ship:empaquetado", github_manager)
        self.assertIn("`validacion`: `performance-engineer`, `ux-reviewer`, `seo-specialist`, `i18n-specialist`", fix_command)
        self.assertIn("fix:validacion", seo_specialist)
        self.assertIn("Si `lucius` está activo", quick_command)
        self.assertIn("fallback a `.claude/alfred-dev.local.md`", quick_command)
        self.assertIn("fuente runtime canónica", quick_command)
        self.assertIn("fallback a `.claude/alfred-dev.local.md`", spike_command)
        self.assertIn("bajo demanda", spike_command)
        self.assertIn("Si `lucius` está activo en `equipo_sesion`", ship_command)
        self.assertIn("Si `copywriter` está activo", ship_command)
        self.assertIn("Si `lucius` está activo en `equipo_sesion`", audit_command)
        self.assertIn("fallback a `.claude/alfred-dev.local.md`", audit_command)
        self.assertIn("fuente runtime canónica", audit_command)
        self.assertIn("ship:documentacion", copywriter)
        self.assertIn("remote GitHub", github_manager)
        self.assertIn("No redactar desde cero changelog", github_manager)
        self.assertIn("No construir binarios ni ejecutar despliegues", github_manager)
        self.assertIn("No redacta changelog ni release notes", devops)
        self.assertIn("No gestiona PRs, issues ni la publicación de la release en GitHub", devops)
        self.assertIn("Si `github-manager` está activo", devops)
        self.assertIn("No publica tags, releases ni artefactos en GitHub", tech_writer)
        self.assertIn("bajo demanda", librarian)
        self.assertIn("No entra automáticamente en ninguna fase", librarian)
        self.assertIn("ship:auditoria_final", lucius)
        self.assertIn("quick:validacion_rapida", lucius)
        self.assertIn("No mueve gates ni reabre una fase por sí solo", lucius)
        self.assertIn("No sustituye la aprobación de QA, seguridad o arquitectura", lucius)
        self.assertIn("Tampoco sustituye el sign-off de QA, seguridad o arquitectura", _read("commands/lucius.md"))
        self.assertIn("Incluso en modo autopilot, esta confirmación humana se mantiene", flows)

    def test_large_commands_define_canonical_closeout_contracts(self):
        feature_command = _read("commands/feature.md")
        quick_command = _read("commands/quick.md")
        fix_command = _read("commands/fix.md")
        ship_command = _read("commands/ship.md")
        audit_command = _read("commands/audit.md")

        self.assertIn("## Cierre canónico del comando", feature_command)
        self.assertIn(".claude/alfred-dev-state.json", feature_command)
        self.assertIn("docs/project/current.md", feature_command)
        self.assertIn("AskUserQuestion", feature_command)
        self.assertIn("siguiente paso esperado", feature_command)

        self.assertIn("## Cierre canónico del comando", quick_command)
        self.assertIn("segunda planificación libre", quick_command)
        self.assertIn("docs/project/traceability.md", quick_command)
        self.assertIn("/alfred-dev:verify", quick_command)

        self.assertIn("## Cierre canónico del comando", fix_command)
        self.assertIn("bug/causa raíz en curso", fix_command)
        self.assertIn("docs/project/progress.md", fix_command)

        self.assertIn("## Cierre canónico del comando", ship_command)
        self.assertIn("La gate de despliegue debe resolverse con un único `AskUserQuestion`", ship_command)
        self.assertIn("fase de release actual", ship_command)
        self.assertIn("todavía no desplegar", ship_command)

        self.assertIn("## Cierre canónico del comando", audit_command)
        self.assertIn("preflight de SonarQube requiere decisión humana", audit_command)
        self.assertIn("resumen ejecutivo accionable", audit_command)
        self.assertIn("no sustituye los hallazgos", audit_command)

    def test_hooks_docs_keep_dangerous_command_guard_fail_closed(self):
        hooks_doc_norm = _normalize(_read("docs/hooks.md"))
        self.assertIn("la politica de este hook es **fail-closed**", hooks_doc_norm)
        self.assertIn("dangerous-command-guard.py", hooks_doc_norm)

    def test_internal_audit_does_not_leak_into_public_docs_navigation(self):
        docs_readme = _read("docs/README.md")
        self.assertNotIn("[audit.md](audit.md)", docs_readme)
        self.assertIn("internal/", docs_readme)
        self.assertTrue(
            os.path.exists(os.path.join(ROOT, "internal", "docs-audit.md")),
            "La auditoría interna de documentación debe vivir fuera de docs/.",
        )

    def test_configuration_surface_uses_canonical_phase_schema(self):
        readme = _read("README.md")
        config_command_norm = _normalize(_read("commands/config.md"))
        configuration_doc_norm = _normalize(_read("docs/configuration.md"))

        readme_config = _slice_between(
            readme,
            "## Configuracion",
            "## Descargo de responsabilidad",
        )
        self.assertIn("entrega: semi-autonomo", readme_config)
        self.assertIn("lucius: false", readme_config)
        self.assertNotIn("seguridad: autonomo", readme_config)
        self.assertNotIn("devops: semi-autonomo", readme_config)

        self.assertIn(
            "producto, arquitectura, desarrollo, calidad, documentacion, entrega",
            config_command_norm,
        )
        self.assertIn("principal navegable", config_command_norm)
        self.assertIn("3 menus navegables", config_command_norm)
        self.assertIn("uno por interaccion", config_command_norm)
        self.assertIn("build_config_section_summaries()", config_command_norm)
        self.assertIn("build_config_section_menu()", config_command_norm)
        self.assertIn("apply_config_section_update()", config_command_norm)
        self.assertIn("build_config_section_change_preview()", config_command_norm)
        self.assertIn("update_config_section()", config_command_norm)
        self.assertIn("update_project_config_section()", config_command_norm)
        self.assertIn("lucius: false", configuration_doc_norm)
        self.assertIn("build_config_section_summaries()", configuration_doc_norm)
        self.assertIn("build_config_section_menu()", configuration_doc_norm)
        self.assertIn("build_config_section_change_preview()", configuration_doc_norm)
        self.assertIn("update_config_section()", configuration_doc_norm)
        self.assertIn("update_project_config_section()", configuration_doc_norm)
        self.assertIn("3 menus navegables", configuration_doc_norm)
        self.assertIn("auditoria externa", configuration_doc_norm)
        self.assertIn("memoria.enabled: true", configuration_doc_norm)
        self.assertIn("ship:despliegue", configuration_doc_norm)
        self.assertIn("confirmacion humana obligatoria", configuration_doc_norm)
        architecture = _normalize(_read("docs/architecture.md"))
        self.assertIn("build_config_section_summaries()", architecture)
        self.assertIn("build_config_section_menu()", architecture)
        self.assertIn("build_config_section_change_preview()", architecture)
        self.assertIn("update_config_section()", architecture)
        self.assertIn("update_project_config_section()", architecture)

    def test_operational_commands_use_canonical_continuity_helpers(self):
        next_command = _read("commands/next.md")
        progress_command = _read("commands/progress.md")
        status_command = _read("commands/status.md")
        help_command = _read("commands/help.md")
        sync_github_command = _read("commands/sync-github.md")
        pause_command = _read("commands/pause.md")
        resume_command = _read("commands/resume.md")
        verify_command = _read("commands/verify.md")
        update_command = _read("commands/update.md")

        self.assertIn('python3 .claude/alfred-continuity.py next "$PWD" --json', next_command)
        self.assertIn("source_label", next_command)
        self.assertIn("directive", next_command)
        self.assertIn('python3 .claude/alfred-continuity.py progress "$PWD"', progress_command)
        self.assertIn("focus", progress_command)
        self.assertIn("directive", progress_command)
        self.assertIn("úsalo como respuesta final", progress_command)
        self.assertIn('python3 .claude/alfred-continuity.py status "$PWD"', status_command)
        self.assertIn("wrapper del helper determinista", status_command)
        self.assertIn("úsalo como respuesta final", status_command)
        self.assertIn("/alfred-dev:next", help_command)
        self.assertIn("/alfred-dev:progress", help_command)
        self.assertIn("/alfred-dev:status", help_command)
        self.assertIn('python3 .claude/alfred-continuity.py next "$PWD" --json', help_command)
        self.assertIn("foco operativo actual", help_command)
        self.assertIn("| `/alfred-dev:alfred` | [petición opcional] |", help_command)
        self.assertIn("composición dinámica", help_command)
        self.assertIn("remote GitHub", help_command)
        self.assertIn("solo bajo demanda", help_command)
        self.assertIn("no conviertas `/alfred-dev:help` en un segundo `/next`", help_command)
        self.assertIn("focus", sync_github_command)
        self.assertIn("directive", sync_github_command)
        self.assertIn("úsala como respuesta final y termina", sync_github_command)
        self.assertIn('python3 .claude/alfred-continuity.py pause "$PWD"', pause_command)
        self.assertIn("Primero ejecuta el helper determinista", pause_command)
        self.assertIn("Solo si el helper falla, cae al modo manual", pause_command)
        self.assertIn("No la reenvuelvas con un segundo resumen", pause_command)
        self.assertIn('python3 .claude/alfred-continuity.py resume "$PWD"', resume_command)
        self.assertIn("Primero ejecuta el helper determinista", resume_command)
        self.assertIn("Solo si el helper falla, cae al modo manual", resume_command)
        self.assertIn("No la reenvuelvas con un segundo resumen", resume_command)
        self.assertIn('python3 .claude/alfred-continuity.py verify "$PWD" --raw "$ARGUMENTS"', verify_command)
        self.assertIn("Si el helper devuelve una respuesta válida, úsala como respuesta final", verify_command)
        self.assertIn("NO añadas una segunda capa de resumen", verify_command)
        self.assertIn("## Cierre canónico del comando", update_command)
        self.assertIn("un único menú seleccionable real", update_command)


class TestInstallSurfaceContracts(unittest.TestCase):
    def test_windows_installation_requires_and_patches_python(self):
        install_ps1 = _read("install.ps1")
        install_doc = _read("docs/installation.md")

        self.assertIn("Get-CompatiblePython", install_ps1)
        self.assertIn("Get-InstalledPluginRoot", install_ps1)
        self.assertIn('Write-Ok "hooks.json parcheado', install_ps1)
        self.assertIn('Join-Path $PluginRoot "hooks/hooks.json"', install_ps1)
        self.assertIn('Write-Ok "mcp.json parcheado', install_ps1)
        self.assertIn("Python 3.10+", install_doc)
        self.assertIn("hooks, core y MCP", install_doc)
        self.assertIn("`hooks/hooks.json` y `mcp.json`", install_doc)

    def test_linux_installation_patches_hooks_and_mcp(self):
        install_sh = _read("install.sh")
        self.assertIn("Parchear hooks y MCP", install_sh)
        self.assertIn("MCP_JSON", install_sh)
        self.assertIn('ok "mcp.json parcheado', install_sh)
        self.assertIn("resolve_installed_plugin_root", install_sh)

    def test_installation_docs_describe_claude_cli_based_flow(self):
        install_doc = _read("docs/installation.md")
        readme = _read("README.md")
        update_command = _read("commands/update.md")

        self.assertIn("claude plugin marketplace add 686f6c61/alfred-dev", install_doc)
        self.assertIn("claude plugin install alfred-dev@alfred-dev", install_doc)
        self.assertIn("bash ./install.sh", install_doc)
        self.assertIn("bash ./install.sh", readme)
        self.assertIn("bash ./uninstall.sh", install_doc)
        self.assertIn("bash ./uninstall.sh", readme)
        self.assertIn("hooks.json", install_doc)
        self.assertIn("mcp.json", install_doc)
        self.assertIn("fuente github propia", _normalize(install_doc))
        self.assertIn("no oficial", _normalize(install_doc))
        self.assertIn("fuente github global", _normalize(readme))
        self.assertIn("unico menu seleccionable", _normalize(install_doc))
        self.assertIn("un unico `askuserquestion`", _normalize(update_command))
        self.assertIn("Nunca", update_command)
        self.assertIn("0.10.0", update_command)
        self.assertIn('echo \'{"version":2,"plugins":{}}\'', install_doc)
        self.assertNotIn("git clone --depth 1", install_doc)
        self.assertNotIn("git (para la descarga del plugin)", _normalize(install_doc))
        self.assertNotIn("git (para la descarga del plugin)", _normalize(readme))
        self.assertNotIn("0.4.7", install_doc)
        self.assertNotIn("os.replace", install_doc)
        self.assertNotIn("actualizan `installed_plugins.json` con el nuevo sha y version", _normalize(install_doc))

    def test_uninstall_surface_is_also_cli_first(self):
        uninstall_sh = _read("uninstall.sh")
        uninstall_ps1 = _read("uninstall.ps1")
        install_doc = _read("docs/installation.md")
        readme = _read("README.md")

        self.assertIn('claude plugin uninstall "${PLUGIN_KEY}"', uninstall_sh)
        self.assertIn('claude plugin marketplace remove "${PLUGIN_NAME}"', uninstall_sh)
        self.assertIn("find_compatible_python", uninstall_sh)
        self.assertIn("& claude plugin uninstall $PluginKey", uninstall_ps1)
        self.assertIn("& claude plugin marketplace remove $PluginName", uninstall_ps1)
        self.assertIn("cli nativa de claude code", _normalize(install_doc))
        self.assertIn("claude plugin uninstall alfred-dev@alfred-dev", _normalize(install_doc))
        self.assertIn("claude plugin marketplace remove alfred-dev", _normalize(install_doc))
        self.assertIn("cli nativa de claude code", _normalize(readme))

class TestOptionalAgentsContracts(unittest.TestCase):
    def test_config_and_composition_include_nine_optional_agents(self):
        config = _read("commands/config.md")
        composition = _read("commands/_composicion.md")
        configuration = _read("docs/configuration.md")

        self.assertIn("10 agentes de núcleo", config)
        self.assertIn("9 agentes opcionales", config)
        self.assertIn("3 menús navegables", config)
        self.assertIn("un agente por interacción", config)
        self.assertIn("Seguir sin activar más", config)
        self.assertIn("build_optional_agent_group_menu", config)
        self.assertIn("lucius: false", config)

        self.assertIn("Selina", composition)
        self.assertIn("9 agentes opcionales", composition)
        self.assertIn("build_optional_agent_group_menus", composition)
        self.assertIn('label: "Lucius"', composition)
        self.assertIn('"lucius": True/False', composition)
        self.assertIn("build_optional_agent_group_menus()", configuration)

    def test_copywriter_doc_does_not_overpromise_automatic_quality_integration(self):
        copywriter = _read("docs/agents/copywriter.md")
        self.assertIn(
            "Durante `feature:documentacion`, `ship:documentacion` o una ejecución acotada con copy visible",
            copywriter,
        )
        self.assertIn("no se considera una etapa automática universal del flujo", copywriter)
        self.assertNotIn("Ficheros de internacionalizacion o localizacion", copywriter)

    def test_content_optional_docs_keep_runtime_boundaries_clear(self):
        composition = _read("commands/_composicion.md")
        seo = _read("docs/agents/seo-specialist.md")
        ux = _read("docs/agents/ux-reviewer.md")
        i18n = _read("docs/agents/i18n-specialist.md")

        self.assertIn("Reglas anti-solape para contenido y UX", composition)
        self.assertIn("No es el dueño del tono", composition)
        self.assertIn("No es el dueño del SEO técnico", composition)
        self.assertIn("No es el dueño de la usabilidad del flujo", composition)
        self.assertIn("quick:validacion_rapida", seo)
        self.assertIn("No decidir el tono del texto", seo)
        self.assertIn("No se encarga del SEO técnico", ux)
        self.assertIn("No decide indexación", i18n)

    def test_technical_optional_docs_keep_runtime_boundaries_clear(self):
        composition = _read("commands/_composicion.md")
        data = _read("docs/agents/data-engineer.md")
        performance = _read("docs/agents/performance-engineer.md")
        config = _read("commands/config.md")
        help_command = _read("commands/help.md")
        readme = _read("README.md")
        configuration = _read("docs/configuration.md")

        self.assertIn("Reglas anti-solape para datos y rendimiento", composition)
        self.assertIn("Si el síntoma es \"va lento\" pero aún no sabemos por qué, empieza por `performance-engineer`", composition)
        self.assertIn("No actua como profiler general del sistema", data)
        self.assertIn("Sugerencia estática (`suggest_optional_agents`)", data)
        self.assertIn("stack detectado tenga un ORM distinto de `ninguno`", data)
        self.assertIn("No reescribe esquemas, migraciones ni índices por defecto", performance)
        self.assertIn("más de 50 ficheros fuente", performance)
        self.assertIn("Esquema, migraciones, queries, índices o persistencia", config)
        self.assertIn("Latencia, bundles, memoria o cuellos de botella medibles", config)
        self.assertIn("Esquema, migraciones, queries, índices o persistencia", help_command)
        self.assertIn("Latencia, bundles, memoria o cuellos de botella medibles", help_command)
        self.assertIn("Esquema, migraciones, queries, índices o persistencia", readme)
        self.assertIn("Latencia, bundles, memoria o cuellos de botella medibles", readme)
        self.assertIn("Estas sugerencias estáticas son deliberadamente conservadoras", configuration)
        self.assertIn("performance-engineer, quizá data-engineer", configuration)

    def test_project_manager_doc_keeps_operational_boundary_clear(self):
        sonia = _read("docs/agents/project-manager.md")
        agents_readme = _read("docs/agents/README.md")
        architecture = _read("docs/architecture.md")

        self.assertIn("convierte PRDs ya aprobados", sonia)
        self.assertIn("Materializa en el kanban el trabajo ya definido", sonia)
        self.assertIn("de forma objetiva desde el estado", sonia)
        self.assertIn("No reprioriza el roadmap", sonia)
        self.assertIn("Materializa kanban, trazabilidad y siguiente paso operativo", agents_readme)
        self.assertIn("PM operativo y trazabilidad", architecture)

    def test_core_agent_docs_keep_product_architecture_orchestration_boundary_clear(self):
        po = _read("docs/agents/product-owner.md")
        architect = _read("docs/agents/architect.md")
        alfred = _read("docs/agents/alfred.md")
        agents_readme = _read("docs/agents/README.md")

        self.assertIn("No redefine arquitectura, componentes ni elecciones de stack", po)
        self.assertIn("decide **qué** problema merece resolverse y **por qué**", po)
        self.assertIn("No redefine alcance, historias ni criterios de aceptación ya aprobados en el PRD", architect)
        self.assertIn("decide **cómo** se estructura la solución técnica", architect)
        self.assertIn("No redefine alcance funcional ni sustituye un PRD aprobado por criterio propio", alfred)
        self.assertIn("`product-owner` decide **qué** se quiere construir y **por qué**", alfred)
        self.assertIn("`architect` decide **cómo** se resuelve técnicamente", alfred)
        self.assertIn("`alfred`** decide **cuándo** interviene cada uno", agents_readme)

if __name__ == "__main__":
    unittest.main()
