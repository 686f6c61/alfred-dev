#!/usr/bin/env python3
"""Contratos de superficie publica para evitar desalineaciones de release.

Estos tests verifican que los numeros y claims principales del plugin
(agentes, comandos, skills, dominios, fases y requisitos de instalacion)
coincidan entre el estado real del repo y la documentacion/manifiestos
que se publican al usuario.
"""

from collections import Counter
import json
import os
import re
import unicodedata
import unittest


ROOT = os.path.join(os.path.dirname(__file__), "..")
SKILL_SUPPORTED_FIELDS = {
    "name",
    "description",
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "hooks",
    "paths",
    "shell",
}
SKILL_BOOLEAN_FIELDS = {"disable-model-invocation", "user-invocable"}
SKILL_BOOLEAN_VALUES = {"true", "false"}
SKILL_CONTEXT_VALUES = {"fork"}
SKILL_EFFORT_VALUES = {"low", "medium", "high", "xhigh", "max"}
SKILL_LISTING_TEXT_LIMIT = 1536
SKILL_SHELL_VALUES = {"bash", "powershell"}
COMMAND_SUPPORTED_FIELDS = {
    "allowed-tools",
    "argument-hint",
    "description",
    "disallowed-tools",
    "disable-model-invocation",
    "model",
}
AGENT_MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "inherit"}
AGENT_MODEL_ID_RE = re.compile(r"^claude-[a-z0-9]+(?:-[a-z0-9]+)*$")
ALFRED_AGENT_MODEL_POLICY = Counter({"inherit": 10})
AGENT_COLOR_VALUES = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
CLAUDE_TOOL_NAMES = {
    "Agent",
    "Artifact",
    "AskUserQuestion",
    "Bash",
    "CronCreate",
    "CronDelete",
    "CronList",
    "Edit",
    "EnterPlanMode",
    "EnterWorktree",
    "ExitPlanMode",
    "ExitWorktree",
    "Glob",
    "Grep",
    "ListMcpResourcesTool",
    "LSP",
    "Monitor",
    "NotebookEdit",
    "PowerShell",
    "PushNotification",
    "Read",
    "ReadMcpResourceTool",
    "RemoteTrigger",
    "SendMessage",
    "ShareOnboardingGuide",
    "WaitForMcpServers",
    "WebFetch",
    "WebSearch",
    "Workflow",
    "Write",
}
CLAUDE_PERMISSION_RULE_NAMES = CLAUDE_TOOL_NAMES | {"Skill"}
SUBAGENT_UNAVAILABLE_TOOLS = {
    "AskUserQuestion",
    "EnterPlanMode",
    "ExitPlanMode",
    "ScheduleWakeup",
    "WaitForMcpServers",
}


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


def _count_agent_files() -> int:
    count = 0
    for dirpath, _dirnames, filenames in os.walk(os.path.join(ROOT, "agents")):
        count += sum(1 for filename in filenames if filename.endswith(".md"))
    return count


def _iter_agent_files():
    agent_files = []
    for dirpath, _dirnames, filenames in os.walk(os.path.join(ROOT, "agents")):
        for filename in filenames:
            if filename.endswith(".md"):
                agent_files.append(os.path.join(dirpath, filename))
    return sorted(agent_files)


def _iter_manifest_skill_files():
    plugin = _read_json(".claude-plugin/plugin.json")
    skill_files = []
    declared = plugin.get("skills")
    roots = declared if declared else ["./skills/"]

    for relative_path in roots:
        absolute = os.path.join(ROOT, relative_path.lstrip("./"))
        if os.path.isdir(absolute):
            for dirpath, _dirnames, filenames in os.walk(absolute):
                if "SKILL.md" in filenames:
                    skill_files.append(os.path.join(dirpath, "SKILL.md"))
            continue

        if os.path.isfile(absolute) and os.path.basename(absolute) == "SKILL.md":
            skill_files.append(absolute)

    return sorted(skill_files)


def _iter_manifest_command_files():
    plugin = _read_json(".claude-plugin/plugin.json")
    return [
        os.path.join(ROOT, relative_path.lstrip("./"))
        for relative_path in plugin["commands"]
    ]


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
        match = re.match(r"^([A-Za-z][A-Za-z_-]*)\s*:\s*(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def _frontmatter_field_text(path: str, field: str) -> str:
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.join(ROOT, path))

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    if not text.startswith("---\n"):
        return ""

    lines = text.split("---", 2)[1].splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^([A-Za-z][A-Za-z_-]*)\s*:\s*(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        if key != field:
            continue
        stripped_value = value.strip()
        if stripped_value not in {"|", ">"}:
            return stripped_value.strip('"').strip("'")

        collected = []
        for following in lines[index + 1:]:
            if re.match(r"^[A-Za-z][A-Za-z_-]*\s*:", following):
                break
            if following.startswith((" ", "\t")):
                collected.append(following.strip())
        return "\n".join(collected)
    return ""


def _extract_site_skill_names(relative_path: str):
    text = _read(relative_path)
    start = text.index("skills: {")
    end = text.index("\n\n  // ----------------------------------------------------------------\n  // Infra", start)
    section = text[start:end]
    return set(re.findall(r"\{ name: '([^']+)'", section))


def _is_supported_agent_model(model: str) -> bool:
    return model in AGENT_MODEL_ALIASES or AGENT_MODEL_ID_RE.fullmatch(model) is not None


def _frontmatter_tool_names(tools: str):
    names = set()
    for item in tools.split(","):
        name = item.strip()
        if not name:
            continue
        names.add(re.split(r"[\s(]", name, maxsplit=1)[0])
    return names


def _frontmatter_tool_rule_names(rules: str):
    return set(
        re.findall(r"(?:^|[\s,])([A-Za-z][A-Za-z0-9_]*)(?:\(|(?=$|[\s,]))", rules)
    )


def _frontmatter_field_rule_text(path: str, field: str):
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.join(ROOT, path))

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    if not text.startswith("---\n"):
        return ""

    lines = text.split("---", 2)[1].splitlines()
    values = []
    collecting = False
    for line in lines:
        top_level = re.match(r"^([A-Za-z][A-Za-z_-]*)\s*:\s*(.*)$", line)
        if top_level:
            key, value = top_level.groups()
            collecting = key == field
            if collecting and value.strip():
                values.append(value.strip().strip("[]").strip('"').strip("'"))
            continue
        if collecting:
            list_item = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if list_item:
                values.append(list_item.group(1))
    return " ".join(values)


def _is_known_agent_tool_name(tool_name: str) -> bool:
    return tool_name in CLAUDE_TOOL_NAMES or tool_name.startswith("mcp__")


def _is_known_permission_rule_name(tool_name: str) -> bool:
    return tool_name in CLAUDE_PERMISSION_RULE_NAMES or tool_name.startswith("mcp__")


def _has_site() -> bool:
    return os.path.exists(os.path.join(ROOT, "site", "package.json"))


class TestRuntimeSurfaceCounts(unittest.TestCase):
    def test_manifest_and_filesystem_reflect_current_counts(self):
        plugin = _read_json(".claude-plugin/plugin.json")
        published_skill_files = _iter_manifest_skill_files()

        self.assertEqual(len(plugin["commands"]), 18)
        self.assertNotIn("agents", plugin)
        self.assertEqual(_count_agent_files(), 10)
        self.assertNotIn("mcpServers", plugin)
        self.assertEqual(_count_skill_files(), 11)
        self.assertEqual(len(published_skill_files), 11)
        self.assertEqual(len(set(published_skill_files)), 11)

        for relative_path in plugin["commands"]:
            absolute = os.path.join(ROOT, relative_path.lstrip("./"))
            self.assertTrue(
                os.path.exists(absolute),
                f"No existe el recurso declarado en plugin.json: {relative_path}",
            )
        self.assertTrue(os.path.exists(os.path.join(ROOT, ".mcp.json")))
        mcp = _read_json(".mcp.json")
        alfred_memory = mcp["mcpServers"]["alfred-memory"]
        self.assertEqual(alfred_memory["command"], "python3")
        self.assertIn("memory_server.py", alfred_memory["args"][0])
        self.assertIn("CLAUDE_PLUGIN_ROOT", alfred_memory["args"][0])

    def test_published_skills_have_canonical_frontmatter(self):
        skill_names = {}
        for skill_path in _iter_manifest_skill_files():
            frontmatter = _parse_frontmatter_fields(skill_path)
            unknown = set(frontmatter) - SKILL_SUPPORTED_FIELDS
            self.assertFalse(
                unknown,
                f"Campos de frontmatter de skill no soportados en {skill_path}: {unknown}",
            )
            self.assertTrue(
                frontmatter.get("name"),
                f"Falta `name` en el frontmatter de {skill_path}",
            )
            self.assertTrue(
                frontmatter.get("description"),
                f"Falta `description` en el frontmatter de {skill_path}",
            )
            listing_text_length = len(
                _frontmatter_field_text(skill_path, "description")
                + _frontmatter_field_text(skill_path, "when_to_use")
            )
            self.assertLessEqual(
                listing_text_length,
                SKILL_LISTING_TEXT_LIMIT,
                f"description + when_to_use excede el limite de listing de Claude Code en {skill_path}: {listing_text_length}",
            )
            expected_name = os.path.basename(os.path.dirname(skill_path))
            self.assertEqual(
                frontmatter.get("name"),
                expected_name,
                f"El name del skill debe coincidir con su directorio en {skill_path}",
            )
            for boolean_field in SKILL_BOOLEAN_FIELDS:
                value = frontmatter.get(boolean_field)
                if value:
                    self.assertIn(
                        value.lower(),
                        SKILL_BOOLEAN_VALUES,
                        f"{boolean_field} debe ser booleano en {skill_path}: {value}",
                    )
            model = frontmatter.get("model")
            if model:
                self.assertTrue(
                    _is_supported_agent_model(model),
                    f"Modelo de skill no soportado por Claude Code actual en {skill_path}: {model}",
                )
            effort = frontmatter.get("effort")
            if effort:
                self.assertIn(
                    effort,
                    SKILL_EFFORT_VALUES,
                    f"Effort de skill no soportado por Claude Code actual en {skill_path}: {effort}",
                )
            context = frontmatter.get("context")
            if context:
                self.assertIn(
                    context,
                    SKILL_CONTEXT_VALUES,
                    f"Context de skill no soportado por Claude Code actual en {skill_path}: {context}",
                )
            if frontmatter.get("agent"):
                self.assertEqual(
                    context,
                    "fork",
                    f"El campo agent solo debe usarse con context: fork en {skill_path}",
                )
            shell = frontmatter.get("shell")
            if shell:
                self.assertIn(
                    shell,
                    SKILL_SHELL_VALUES,
                    f"Shell de skill no soportado por Claude Code actual en {skill_path}: {shell}",
                )
            for tools_field in ("allowed-tools", "disallowed-tools"):
                unknown_tools = [
                    tool_name
                    for tool_name in _frontmatter_tool_rule_names(
                        _frontmatter_field_rule_text(skill_path, tools_field)
                    )
                    if not _is_known_permission_rule_name(tool_name)
                ]
                self.assertFalse(
                    unknown_tools,
                    f"{tools_field} de skill declara herramientas desconocidas en {skill_path}: {unknown_tools}",
                )
            skill_names.setdefault(frontmatter["name"], []).append(skill_path)
        duplicated = {
            name: paths for name, paths in skill_names.items() if len(paths) > 1
        }
        self.assertFalse(duplicated, f"Skills con name duplicado: {duplicated}")

    def test_published_commands_have_current_frontmatter_fields(self):
        for command_path in _iter_manifest_command_files():
            frontmatter = _parse_frontmatter_fields(command_path)
            unknown = set(frontmatter) - COMMAND_SUPPORTED_FIELDS
            self.assertFalse(
                unknown,
                f"Campos de frontmatter de comando no soportados en {command_path}: {unknown}",
            )
            self.assertTrue(
                frontmatter.get("description"),
                f"Falta `description` en el frontmatter de {command_path}",
            )
            model = frontmatter.get("model")
            if model:
                self.assertTrue(
                    _is_supported_agent_model(model),
                    f"Modelo de comando no soportado por Claude Code actual en {command_path}: {model}",
                )
            for tools_field in ("allowed-tools", "disallowed-tools"):
                unknown_tools = [
                    tool_name
                    for tool_name in _frontmatter_tool_rule_names(
                        _frontmatter_field_rule_text(command_path, tools_field)
                    )
                    if not _is_known_permission_rule_name(tool_name)
                ]
                self.assertFalse(
                    unknown_tools,
                    f"{tools_field} de comando declara herramientas desconocidas en {command_path}: {unknown_tools}",
                )

    def test_plugin_agent_frontmatter_avoids_fields_ignored_by_claude_plugins(self):
        supported = {
            "name",
            "description",
            "prompt",
            "tools",
            "disallowedTools",
            "model",
            "maxTurns",
            "skills",
            "initialPrompt",
            "memory",
            "effort",
            "background",
            "isolation",
            "color",
        }
        ignored_by_plugin_agents = {"hooks", "mcpServers", "permissionMode"}
        model_counts = Counter()

        for agent_path in _iter_agent_files():
            frontmatter = _parse_frontmatter_fields(agent_path)
            field_names = set(frontmatter)
            self.assertTrue(
                {"name", "description", "model"}.issubset(field_names),
                f"El agente {agent_path} debe declarar name, description y model",
            )
            self.assertFalse(
                field_names & ignored_by_plugin_agents,
                f"Claude ignora estos campos en agentes de plugin: {agent_path}",
            )
            self.assertFalse(
                field_names - supported - ignored_by_plugin_agents,
                f"Campos de frontmatter no soportados en {agent_path}",
            )
            model = frontmatter["model"]
            model_counts[model] += 1
            self.assertTrue(
                _is_supported_agent_model(model),
                f"Modelo no soportado por Claude Code actual en {agent_path}: {model}",
            )
            color = frontmatter.get("color")
            self.assertTrue(color, f"El agente {agent_path} debe declarar color")
            self.assertIn(
                color,
                AGENT_COLOR_VALUES,
                f"Color no soportado por Claude Code actual en {agent_path}: {color}",
            )
            self.assertFalse(
                _frontmatter_tool_names(frontmatter.get("tools", ""))
                & SUBAGENT_UNAVAILABLE_TOOLS,
                f"El agente {agent_path} lista herramientas no disponibles en subagentes",
            )
            unknown_tools = [
                tool_name
                for tool_name in _frontmatter_tool_names(frontmatter.get("tools", ""))
                if not _is_known_agent_tool_name(tool_name)
            ]
            self.assertFalse(
                unknown_tools,
                f"El agente {agent_path} lista herramientas desconocidas: {unknown_tools}",
            )
            agent_text = _read(os.path.relpath(agent_path, ROOT))
            self.assertFalse(
                [tool for tool in SUBAGENT_UNAVAILABLE_TOOLS if tool in agent_text],
                f"El agente {agent_path} instruye herramientas no disponibles en subagentes",
            )

        self.assertEqual(model_counts, ALFRED_AGENT_MODEL_POLICY)

    def test_manual_only_skills_keep_explicit_disable_model_invocation(self):
        manual_only = [
            "skills/style-direction/SKILL.md",
            "skills/incident-response/SKILL.md",
            "skills/sonarqube/SKILL.md",
            "skills/pr-workflow/SKILL.md",
        ]

        for relative_path in manual_only:
            frontmatter = _parse_frontmatter_fields(relative_path)
            self.assertEqual(
                frontmatter.get("disable-model-invocation"),
                "true",
                f"El skill manual {relative_path} debe mantener disable-model-invocation: true",
            )

    def test_alfred_is_a_published_plugin_command(self):
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
        self.assertEqual(collisions, [])
        self.assertIn("alfred", command_names)
        self.assertIn("./commands/alfred.md", plugin["commands"])


class TestReadmeAndDocsSurface(unittest.TestCase):
    def test_readme_matches_current_public_claims(self):
        readme = _read("README.md")
        self.assertIn("11 skills", _normalize(readme))
        self.assertIn("Python 3.10+", readme)
        self.assertIn("Novedades en v0.7.0", readme)

    def test_docs_readme_and_architecture_match_current_surface(self):
        docs_readme = _read("docs/README.md")
        architecture = _read("docs/architecture.md")
        agents_readme = _read("docs/agents/README.md")

        self.assertIn("10 agentes", _normalize(docs_readme))
        self.assertIn("11 skills", _normalize(docs_readme))
        self.assertIn("18 comandos", _normalize(architecture))
        self.assertIn("El manifiesto no declara la clave `agents`", architecture)
        self.assertIn("optional_agents.py", architecture)
        self.assertIn("build_optional_agent_group_menus()", architecture)
        self.assertNotIn("TASK_KEYWORDS", architecture)
        self.assertIn("estilo visual", agents_readme)
        self.assertIn("style-direction", _read("docs/skills.md"))

    def test_skills_docs_cover_manual_and_special_domains_in_catalog(self):
        skills_doc = _read("docs/skills.md")
        self.assertIn("incident-response", skills_doc)
        self.assertIn("style-direction", skills_doc)
        self.assertIn("sonarqube", skills_doc)
        self.assertIn("memory", skills_doc)

    def test_every_manifest_agent_has_public_docs_page(self):
        docs_readme = _read("docs/README.md")
        agents_index = _read("docs/agents/README.md")

        for absolute_agent in _iter_agent_files():
            relative_path = os.path.relpath(absolute_agent, ROOT)
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
        feature_command = _read("commands/feature.md")
        lucius = _read("docs/agents/lucius.md")

        self.assertIn("estilo", _normalize(flows))
        self.assertIn("selina", _normalize(feature_command))
        self.assertIn("lucius", _normalize(lucius))

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
        self.assertIn("/alfred-dev:uat", quick_command)

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

    def test_docs_navigation_keeps_public_plugin_docs_only(self):
        docs_readme = _read("docs/README.md")
        self.assertNotIn("[audit.md](audit.md)", docs_readme)
        self.assertNotIn("internal/docs-audit.md", docs_readme)
        self.assertNotIn("internal/", docs_readme)
        self.assertIn("release.md", docs_readme)
        self.assertNotIn("release-audit-0.6.0.md", docs_readme)
        self.assertNotIn("promise-evidence-0.6.0.md", docs_readme)

    def test_configuration_surface_uses_canonical_phase_schema(self):
        readme = _read("README.md")
        config_command_norm = _normalize(_read("commands/ajustes.md"))
        configuration_doc_norm = _normalize(_read("docs/configuration.md"))

        readme_config = _slice_between(
            readme,
            "## Configuracion",
            "## Descargo de responsabilidad",
        )
        self.assertIn("entrega: autonomo", readme_config)
        self.assertIn("lucius: false", readme_config)
        self.assertNotIn("seguridad: autonomo", readme_config)
        self.assertNotIn("devops: semi-autonomo", readme_config)

        self.assertIn(
            "producto, arquitectura, desarrollo, calidad, documentacion, entrega",
            config_command_norm,
        )
        self.assertIn("principal navegable", config_command_norm)
        self.assertIn("modo no interactivo", config_command_norm)
        self.assertIn("config_headless_menu", config_command_norm)
        self.assertIn("vuelve cancelada", config_command_norm)
        self.assertIn("core/config_cli.py", config_command_norm)
        self.assertIn("menu", config_command_norm)
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
        self.assertIn("auditoria", configuration_doc_norm)
        self.assertIn("segunda opinion externa", configuration_doc_norm)
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
        sync_github_command = _read("commands/sync-github.md")
        pause_command = _read("commands/pause.md")
        resume_command = _read("commands/retomar.md")
        verify_command = _read("commands/uat.md")
        update_command = _read("commands/update.md")

        self.assertIn('python3 .claude/alfred-continuity.py next "$PWD" --json', next_command)
        self.assertIn("source_label", next_command)
        self.assertIn("directive", next_command)
        self.assertIn('python3 .claude/alfred-continuity.py progress "$PWD"', progress_command)
        self.assertIn("focus", progress_command)
        self.assertIn("directive", progress_command)
        self.assertIn("úsalo como respuesta final", progress_command)
        self.assertIn('python3 .claude/alfred-continuity.py resume "$PWD"', resume_command)
        self.assertIn("focus", sync_github_command)
        self.assertIn("directive", sync_github_command)
        self.assertIn("úsala como respuesta final y termina", sync_github_command)
        self.assertIn("menos de 12 líneas", sync_github_command)
        self.assertIn("no añadas bloques `Insight`", sync_github_command)
        self.assertIn("no sigas explorando", sync_github_command)
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

    def test_long_flows_are_helper_first_for_headless_runs(self):
        activity_capture = _read("hooks/activity-capture.py")
        session_start = _read("hooks/session-start.sh")

        self.assertIn("start_flow_session", activity_capture)
        self.assertIn('"audit"', activity_capture)
        self.assertIn('"feature"', activity_capture)
        self.assertIn('"fix"', activity_capture)
        self.assertIn('"spike"', activity_capture)
        self.assertIn('"ship"', activity_capture)
        self.assertIn("/alfred-dev:feature", session_start)

        markers = {
            "audit": "AUDIT_HEADLESS_START",
            "feature": "FEATURE_HEADLESS_START",
            "fix": "FIX_HEADLESS_START",
            "spike": "SPIKE_HEADLESS_START",
            "ship": "SHIP_HEADLESS_START",
        }
        for command, marker in markers.items():
            command_doc = _read(f"commands/{command}.md")
            self.assertIn("consume-prefetch", command_doc)
            self.assertIn("start-flow", command_doc)
            self.assertIn("--command " + command, command_doc)
            self.assertIn("modo headless", _normalize(command_doc))
            self.assertIn(marker, command_doc)
            self.assertIn("NO", command_doc)
            self.assertIn("llames agentes", command_doc)

        audit_command = _read("commands/audit.md")
        self.assertIn("AUDIT_DOCKER_INSTALL_MENU_HEADLESS", audit_command)
        self.assertIn("AUDIT_DOCKER_START_MENU_HEADLESS", audit_command)
        self.assertIn("no autoelijas", audit_command)

    def test_lucius_is_helper_first_for_headless_runs(self):
        activity_capture = _read("hooks/activity-capture.py")
        session_start = _read("hooks/session-start.sh")
        lucius_command = _read("commands/lucius.md")

        self.assertIn('"lucius"', activity_capture)
        self.assertIn("prepare_lucius_review", activity_capture)
        self.assertIn("Lucius", session_start)
        self.assertIn("consume-prefetch", lucius_command)
        self.assertIn('python3 .claude/alfred-continuity.py lucius "$PWD" --raw "$ARGUMENTS"', lucius_command)
        self.assertIn("modo headless", _normalize(lucius_command))
        self.assertIn("LUCIUS_HEADLESS_START", lucius_command)
        self.assertIn("LUCIUS_INVALID_SCOPE", lucius_command)
        self.assertIn("NO lances Agent", lucius_command)
        self.assertIn("ejecutes `codex exec`", lucius_command)
        self.assertIn("NO presentes una revisión como hecha", lucius_command)


class TestInstallSurfaceContracts(unittest.TestCase):
    def test_windows_installation_requires_and_patches_python(self):
        install_ps1 = _read("install.ps1")
        install_doc = _read("docs/installation.md")

        self.assertIn("Get-CompatiblePython", install_ps1)
        self.assertIn("Get-InstalledPluginRoot", install_ps1)
        self.assertIn("Get-CompatiblePython", install_ps1)
        self.assertIn('Write-Ok "hooks.json parcheado', install_ps1)
        self.assertIn('Write-Ok ".mcp.json parcheado', install_ps1)
        self.assertIn("Python 3.10+", install_doc)
        self.assertIn("hooks, core y MCP", install_doc)
        self.assertIn("actualiza `hooks.json` y `.mcp.json`", install_doc)

    def test_linux_installation_patches_hooks_and_mcp(self):
        install_sh = _read("install.sh")
        self.assertIn("Parchear hooks y MCP", install_sh)
        self.assertIn("MCP_JSON", install_sh)
        self.assertIn("mcpServers", install_sh)
        self.assertIn('ok ".mcp.json parcheado', install_sh)
        self.assertIn("resolve_installed_plugin_root", install_sh)
        self.assertIn("resolve_installed_plugin_root", install_sh)

    def test_quick_headless_closes_compactly_after_helper_first(self):
        quick = _read("commands/quick.md")

        self.assertIn("cierra con ese resumen y termina", quick)
        self.assertIn("menos de 20 líneas", quick)
        self.assertIn("sin bloques `Insight`", quick)

    def test_installation_docs_describe_claude_cli_based_flow(self):
        install_doc = _read("docs/installation.md")
        readme = _read("README.md")
        update_command = _read("commands/update.md")
        docs_readme = _read("docs/README.md")

        self.assertIn("claude plugin marketplace add 686f6c61/alfred-dev --scope user", install_doc)
        self.assertIn("claude plugin install alfred-dev@alfred-dev --scope user", install_doc)
        self.assertIn("claude plugin uninstall alfred-dev@alfred-dev --scope local", install_doc)
        self.assertIn("claude plugin uninstall alfred-dev@alfred-dev --scope project", install_doc)
        self.assertIn('claude plugin marketplace add "$PWD" --scope user', install_doc)
        self.assertIn("~/.claude/skills/alfred/SKILL.md", install_doc)
        self.assertIn("~/.claude/commands/alfred.md", install_doc)
        self.assertIn("bash ./install.sh", install_doc)
        self.assertIn("bash ./install.sh", readme)
        self.assertIn("bash ./uninstall.sh", install_doc)
        self.assertIn("bash ./uninstall.sh", readme)
        self.assertIn("https://code.claude.com/docs/en/overview", readme)
        self.assertNotIn("https://docs.anthropic.com/en/docs/claude-code", readme)
        self.assertIn("/reload-plugins", readme)
        self.assertIn("/reload-plugins", install_doc)
        self.assertIn("/reload-plugins --force", install_doc)
        self.assertIn("/reload-plugins", update_command)
        self.assertIn("claude plugin details alfred-dev@alfred-dev", install_doc)
        self.assertIn("claude plugin validate . --strict", install_doc)
        self.assertIn("claude --debug", install_doc)
        self.assertIn("/plugin validate", install_doc)
        self.assertNotIn("Claude Code no ofrece diagnosticos", install_doc)
        self.assertNotIn("completamente silencioso", install_doc)
        self.assertIn("hooks.json", install_doc)
        self.assertIn(".mcp.json", install_doc)
        self.assertIn("fuente github propia", _normalize(install_doc))
        self.assertIn("no oficial", _normalize(install_doc))
        self.assertIn("fuente github global", _normalize(readme))
        self.assertIn("unico menu seleccionable", _normalize(install_doc))
        self.assertIn("un unico `askuserquestion`", _normalize(update_command))
        self.assertIn("claude plugin list --json", update_command)
        self.assertIn("normaliza a `--scope user`", update_command)
        self.assertIn("no pisa `~/.claude/skills`", update_command)
        self.assertNotIn("alias personal global `/alfred`", update_command)
        self.assertIn("~/.claude/skills/alfred/SKILL.md", install_doc)
        self.assertIn("~/.claude/commands/alfred.md", update_command)
        self.assertIn("no se usa `--scope local` como ruta soportada", install_doc)
        self.assertIn("limpia primero cualquier rastro `local` o `project`", install_doc)
        self.assertIn("No uses `claude plugin update --scope local`", update_command)
        self.assertIn("plugin:alfred-dev:alfred-memory", install_doc)
        self.assertIn("Pending approval", install_doc)
        self.assertIn("docs/release.md", readme)
        self.assertIn("release.md", docs_readme)
        self.assertNotIn("release-audit-0.6.0.md", readme)
        self.assertNotIn("release-audit-0.6.0.md", docs_readme)
        self.assertIn("Nunca", update_command)
        self.assertIn("0.10.0", update_command)
        self.assertIn('echo \'{"version":2,"plugins":{}}\'', install_doc)
        self.assertNotIn("git clone --depth 1", install_doc)
        self.assertNotIn("git (para la descarga del plugin)", _normalize(install_doc))
        self.assertNotIn("git (para la descarga del plugin)", _normalize(readme))
        self.assertNotIn("0.4.7", install_doc)
        self.assertNotIn("os.replace", install_doc)
        self.assertNotIn("actualizan `installed_plugins.json` con el nuevo sha y version", _normalize(install_doc))

    def test_site_install_and_metadata_match_current_release_contract(self):
        if not _has_site():
            self.skipTest("La landing vive en la rama Alfred-Astro")

        plugin = _read_json(".claude-plugin/plugin.json")
        es_site = _read("site/src/i18n/data.es.ts")
        en_site = _read("site/src/i18n/data.en.ts")
        changelog = _read("CHANGELOG.md")
        landing_component = _read("site/src/components/BrutalistLandingPage.astro")
        site_ui = _read("site/src/i18n/ui.ts")
        changelog_modal = _read("site/src/components/ChangelogModal.astro")

        expected_version = plugin["version"]
        expected_display_name = plugin["displayName"]
        self.assertIn("softwareVersion: data.footer.version.replace(/^v/i, '')", landing_component)
        self.assertIn(f"version: 'v{expected_version}'", es_site)
        self.assertIn(f"version: 'v{expected_version}'", en_site)
        self.assertIn(f'displayName: "{expected_display_name}"', es_site)
        self.assertIn(f'displayName: "{expected_display_name}"', en_site)
        self.assertIn(f'displayName: "{expected_display_name}"', changelog)
        self.assertIn(f"{expected_display_name} (alfred-dev)", es_site)
        self.assertIn(f"{expected_display_name} (alfred-dev)", en_site)
        self.assertIn(f"{expected_display_name} (alfred-dev)", changelog)

        self.assertIn("Python 3.10+", es_site)
        self.assertIn("Python 3.10+", en_site)
        self.assertIn("/reload-plugins", es_site)
        self.assertIn("/reload-plugins", en_site)
        self.assertIn("Claude Code 2.1.183", es_site)
        self.assertIn("Claude Code 2.1.183", en_site)
        self.assertIn("plugins/skills/hooks/MCP", es_site)
        self.assertIn("plugins/skills/hooks/MCP", en_site)
        self.assertIn("plugins, skills, hooks y MCP", es_site)
        self.assertIn("plugins, skills, hooks, and MCP", en_site)
        self.assertIn("claude update", es_site)
        self.assertIn("claude update", en_site)
        self.assertNotIn("git, Python 3.10+", es_site)
        self.assertNotIn("git, Python 3.10+", en_site)
        self.assertNotIn("No necesita Python", es_site)
        self.assertNotIn("Python not required", en_site)
        self.assertNotIn("No hay requisito de versión mínima específica", es_site)
        self.assertNotIn("There is no specific minimum version requirement", en_site)
        self.assertNotIn("Cualquier versión de Claude Code", es_site)
        self.assertNotIn("Any version of Claude Code", en_site)
        self.assertIn("catalogo publicado de 62 skills", _normalize(es_site))
        self.assertIn("published catalog of 62 skills", en_site)
        self.assertIn("publica el catalogo completo", _normalize(es_site))
        self.assertIn("publishes the full catalog", en_site)
        self.assertIn("changelogHistoryNote", site_ui)
        self.assertIn("historyNote", changelog_modal)

    def test_site_skill_names_match_repository_catalog(self):
        if not _has_site():
            self.skipTest("La landing vive en la rama Alfred-Astro")

        repository_skill_names = {
            _parse_frontmatter_fields(skill_path)["name"]
            for skill_path in _iter_manifest_skill_files()
        }
        self.assertEqual(
            _extract_site_skill_names("site/src/i18n/data.es.ts"),
            repository_skill_names,
        )
        self.assertEqual(
            _extract_site_skill_names("site/src/i18n/data.en.ts"),
            repository_skill_names,
        )

    def test_uninstall_surface_is_also_cli_first(self):
        uninstall_sh = _read("uninstall.sh")
        uninstall_ps1 = _read("uninstall.ps1")
        install_doc = _read("docs/installation.md")
        readme = _read("README.md")

        self.assertIn('claude plugin uninstall "${PLUGIN_KEY}" --scope user', uninstall_sh)
        self.assertIn('claude plugin marketplace remove "${PLUGIN_NAME}" --scope user', uninstall_sh)
        self.assertIn("find_compatible_python", uninstall_sh)
        self.assertIn("remove_global_alfred_alias", uninstall_sh)
        self.assertIn("Alias global /alfred eliminado", uninstall_sh)
        self.assertIn("& claude plugin uninstall $PluginKey --scope user", uninstall_ps1)
        self.assertIn("& claude plugin marketplace remove $PluginName --scope user", uninstall_ps1)
        self.assertIn("Remove-GlobalAlfredAlias", uninstall_ps1)
        self.assertIn("Alias global /alfred eliminado", uninstall_ps1)
        self.assertIn("cli nativa de claude code", _normalize(install_doc))
        self.assertIn("claude plugin uninstall alfred-dev@alfred-dev --scope user", _normalize(install_doc))
        self.assertIn("claude plugin marketplace remove alfred-dev --scope user", _normalize(install_doc))
        self.assertIn("cli nativa de claude code", _normalize(readme))
        if _has_site():
            site = _read("site/src/components/BrutalistLandingPage.astro")
            self.assertIn("claude plugin uninstall alfred-dev@alfred-dev --scope user", site)
            self.assertIn("claude plugin marketplace remove alfred-dev --scope user", site)

class TestOptionalAgentsContracts(unittest.TestCase):
    def test_config_and_composition_include_nine_optional_agents(self):
        config = _read("commands/ajustes.md")
        composition = _read("commands/_composicion.md")
        configuration = _read("docs/configuration.md")

        self.assertIn("lucius", _normalize(config))
        self.assertIn("build_optional_agent_group_menu", config)
        self.assertIn("Selina", composition)
        self.assertIn("build_optional_agent_group_menus()", configuration)

    def test_copywriter_doc_does_not_overpromise_automatic_quality_integration(self):
        self.skipTest("copywriter ya no es agente del plugin")
        copywriter = _read("docs/agents/copywriter.md")
        self.assertIn(
            "Durante `feature:documentacion`, `ship:documentacion` o una ejecución acotada con copy visible",
            copywriter,
        )
        self.assertIn("no se considera una etapa automática universal del flujo", copywriter)
        self.assertNotIn("Ficheros de internacionalizacion o localizacion", copywriter)

    def test_content_optional_docs_keep_runtime_boundaries_clear(self):
        self.skipTest("agentes de contenido eliminados")
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
        self.skipTest("opcionales tecnicos eliminados; solo queda lucius")
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
        self.skipTest("project-manager ya no es agente; SonIA queda como artefactos")
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

class TestLandingSurfaceContracts(unittest.TestCase):
    def test_spanish_landing_uses_current_counts(self):
        if not _has_site():
            self.skipTest("La landing vive en la rama Alfred-Astro")

        es = _read("site/src/i18n/data.es.ts")
        self.assertIn("catalogo publicado de 62 skills", _normalize(es))
        self.assertIn("62 skills en 15 dominios", es)
        self.assertIn("{ number: 62, label: 'Skills' }", es)
        self.assertIn("Son 9 agentes especializados", es)
        self.assertIn("19 agentes. catalogo publicado de 62 skills. 13 hooks. 25 comandos namespaced + /alfred.", _normalize(es))
        self.assertIn("Lucius", es)

    def test_english_landing_uses_current_counts(self):
        if not _has_site():
            self.skipTest("La landing vive en la rama Alfred-Astro")

        en = _read("site/src/i18n/data.en.ts")
        self.assertIn("published catalog of 62 skills", en)
        self.assertIn("62 skills across 15 domains", en)
        self.assertIn("{ number: 62, label: 'Skills' }", en)
        self.assertIn("They are 9 specialised agents", en)
        self.assertIn("19 agents. Published catalog of 62 skills. 13 hooks. 25 namespaced commands + /alfred.", en)
        self.assertIn("Lucius", en)


if __name__ == "__main__":
    unittest.main()
