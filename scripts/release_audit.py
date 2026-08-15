#!/usr/bin/env python3
"""Verificador reproducible para la auditoria de release 0.7.0.

El modo por defecto ejecuta checks locales rapidos: versionado, manifiestos,
inventario del repositorio, documentacion de la auditoria y forma del MCP.
Los smokes que dependen de herramientas externas se activan con flags.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
import re
import selectors
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VERSION = "0.7.0"
OLD_VERSION = "0.5" + ".3"
INSTALLED_PLUGIN_DIR = Path.home() / ".claude" / "plugins" / "cache" / "alfred-dev" / "alfred-dev" / VERSION
GLOBAL_ALFRED_ALIAS_FILE = Path.home() / ".claude" / "skills" / "alfred" / "SKILL.md"
GLOBAL_ALFRED_COMMAND_FILE = Path.home() / ".claude" / "commands" / "alfred.md"
INSTALLED_CACHE_FRESHNESS_ROOTS = (
    ".claude-plugin",
    "agents",
    "commands",
    "core",
    "hooks",
    "mcp",
    "skills",
    "templates",
    ".mcp.json",
    "package.json",
    "README.md",
    "scripts",
)
PUBLISHABLE_SYMLINK_ROOTS = INSTALLED_CACHE_FRESHNESS_ROOTS

IGNORE_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "coverage-html",
    "site/dist",
    "site/node_modules",
}
IGNORED_TEXT_FILE_GLOBS = {
    "docs/external-live-smoke*.json",
    "docs/manual-smoke*.json",
    "docs/manual-smoke*.md",
}

MANUAL_ONLY_SKILLS = (
    "skills/style-direction/SKILL.md",
    "skills/incident-response/SKILL.md",
    "skills/sonarqube/SKILL.md",
    "skills/pr-workflow/SKILL.md",
)

TEMPLATE_PATHS = (
    "templates/adr.md",
    "templates/changelog-entry.md",
    "templates/prd.md",
    "templates/release-notes.md",
    "templates/sbom.md",
    "templates/test-plan.md",
    "templates/threat-model.md",
    "templates/compliance.md",
)

PLUGIN_COMPONENT_FIELDS_REQUIRING_EXPLICIT_AUDIT = {
    "agents": "Claude los descubre desde agents/",
    "hooks": "usar hooks/hooks.json y mantener el gate especifico de hooks",
    "mcpServers": "usar .mcp.json raiz y mantener el gate especifico de MCP",
    "lspServers": "anadir gate de LSP antes de publicarlo",
    "outputStyles": "anadir gate de output-styles antes de publicarlo",
    "channels": "anadir gate de channels/MCP antes de publicarlo",
    "dependencies": "anadir gate de dependencias de plugins antes de publicarlas",
}
PLUGIN_EXPERIMENTAL_FIELDS_REQUIRING_EXPLICIT_AUDIT = {
    "themes": "anadir gate de themes antes de publicarlo",
    "monitors": "anadir gate de monitors antes de publicarlo",
}
MARKETPLACE_ENTRY_FIELDS_REQUIRING_EXPLICIT_AUDIT = {
    "agents": "no suplementar agentes fuera de plugin.json",
    "commands": "no suplementar comandos fuera de plugin.json",
    "dependencies": "no introducir dependencias de marketplace sin gate",
    "hooks": "no suplementar hooks fuera de hooks/hooks.json",
    "lspServers": "no activar LSP desde marketplace sin gate",
    "mcpServers": "no suplementar MCP fuera de .mcp.json",
    "outputStyles": "no activar output-styles desde marketplace sin gate",
    "skills": "no suplementar skills fuera de plugin.json",
    "experimental": "no activar componentes experimentales desde marketplace sin gate",
    "defaultEnabled": "no cambiar enablement desde marketplace; plugin.json/documentacion deben ser la autoridad",
}

HOOK_EVENTS_WITHOUT_MATCHER = {
    "CwdChanged",
    "MessageDisplay",
    "PostToolBatch",
    "SessionEnd",
    "Stop",
    "TaskCompleted",
    "TaskCreated",
    "TeammateIdle",
    "UserPromptSubmit",
    "WorktreeCreate",
    "WorktreeRemove",
}
HOOK_EVENTS_WITH_IF_SUPPORT = {
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PermissionRequest",
    "PermissionDenied",
}
HOOK_SYNC_TIMEOUT_LIMIT = 10

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

AGENT_SUPPORTED_FIELDS = {
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

PLUGIN_IGNORED_AGENT_FIELDS = {"hooks", "mcpServers", "permissionMode"}

AGENT_MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "inherit"}
AGENT_MODEL_ID_RE = re.compile(r"^claude-[a-z0-9]+(?:-[a-z0-9]+)*$")
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
ALFRED_AGENT_MODEL_POLICY = Counter({"inherit": 10})


class AuditError(AssertionError):
    """Error de contrato de release."""


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def _has_site() -> bool:
    return (ROOT / "site" / "package.json").is_file()


def _fail(message: str) -> None:
    raise AuditError(message)


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iter_installed_cache_freshness_files() -> Iterable[str]:
    for root_name in INSTALLED_CACHE_FRESHNESS_ROOTS:
        root_path = ROOT / root_name
        if root_path.is_file():
            yield root_name
            continue
        if not root_path.is_dir():
            continue
        for path in sorted(root_path.rglob("*")):
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_file():
                yield _rel(path)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def _iter_text_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(ROOT)
        rel_name = str(rel_path)
        if any(rel_path.match(pattern) or rel_name == pattern for pattern in IGNORED_TEXT_FILE_GLOBS):
            continue
        rel_parts = path.relative_to(ROOT).parts
        rel_prefixes = {
            "/".join(rel_parts[:index])
            for index in range(1, len(rel_parts) + 1)
        }
        if rel_prefixes & IGNORE_DIRS:
            continue
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".db"}:
            continue
        yield path


def check_versions() -> list[str]:
    plugin = _json(".claude-plugin/plugin.json")
    package = _json("package.json")

    version_points = {
        ".claude-plugin/plugin.json": plugin.get("version"),
        "package.json": package.get("version"),
    }
    if _has_site():
        site_package = _json("site/package.json")
        site_lock = _json("site/package-lock.json")
        version_points.update({
            "site/package.json": site_package.get("version"),
            "site/package-lock.json": site_lock.get("version"),
            "site/package-lock root": site_lock["packages"][""].get("version"),
        })
    bad = {
        name: value
        for name, value in version_points.items()
        if value != VERSION
    }
    if bad:
        _fail(f"Versiones no alineadas a {VERSION}: {bad}")

    offenders: list[str] = []
    for path in _iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if OLD_VERSION in text or f"v{OLD_VERSION}" in text:
            offenders.append(_rel(path))
    if offenders:
        _fail(f"Quedan restos vivos de {OLD_VERSION}: {offenders}")

    return [f"versiones alineadas a {VERSION}", f"sin restos de {OLD_VERSION}"]


def _skill_files_from_manifest(plugin: dict) -> list[Path]:
    skill_files: list[Path] = []
    declared = plugin.get("skills") or ["./skills/"]
    for relative in declared:
        absolute = ROOT / relative.lstrip("./")
        if absolute.is_dir():
            skill_files.extend(sorted(absolute.rglob("SKILL.md")))
        elif absolute.name == "SKILL.md" and absolute.is_file():
            skill_files.append(absolute)
    return sorted(skill_files)


def _manifest_component_paths(plugin: dict, field: str) -> tuple[list[Path], list[str]]:
    values = plugin.get(field)
    if field == "skills" and values is None:
        return [ROOT / "skills"], []
    if not isinstance(values, list):
        return [], [f"plugin.json {field} debe ser una lista"]

    paths: list[Path] = []
    problems: list[str] = []
    seen: set[str] = set()
    root = ROOT.resolve()
    for index, raw_value in enumerate(values):
        label = f"plugin.json {field}[{index}]"
        if not isinstance(raw_value, str):
            problems.append(f"{label} debe ser string relativo: {raw_value!r}")
            continue
        if not raw_value.startswith("./"):
            problems.append(f"{label} debe empezar por ./ para resolverse desde el root del plugin: {raw_value!r}")
        if Path(raw_value).is_absolute():
            problems.append(f"{label} no puede ser absoluto: {raw_value!r}")
        if ".." in Path(raw_value).parts:
            problems.append(f"{label} no puede atravesar fuera del plugin con ..: {raw_value!r}")
        normalized = raw_value[2:] if raw_value.startswith("./") else raw_value
        if normalized in seen:
            problems.append(f"{label} duplica una ruta del manifest: {raw_value!r}")
        seen.add(normalized)
        target = (ROOT / normalized).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            problems.append(f"{label} resuelve fuera del root del plugin: {raw_value!r}")
        paths.append(ROOT / normalized)
    return paths, problems


def check_inventory() -> list[str]:
    plugin = _json(".claude-plugin/plugin.json")
    marketplace = _json(".claude-plugin/marketplace.json")
    marketplace_plugins = marketplace.get("plugins")
    marketplace_problems: list[str] = []
    if marketplace.get("name") != plugin.get("name"):
        marketplace_problems.append(
            f"marketplace.name debe coincidir con plugin.name: {marketplace.get('name')!r}"
        )
    if not isinstance(marketplace.get("owner"), dict) or not marketplace["owner"].get("name"):
        marketplace_problems.append("marketplace.owner.name es obligatorio")
    if not isinstance(marketplace_plugins, list) or len(marketplace_plugins) != 1:
        marketplace_problems.append("marketplace.plugins debe contener exactamente una entrada")
        marketplace_plugin = {}
    else:
        marketplace_plugin = marketplace_plugins[0]
        if not isinstance(marketplace_plugin, dict):
            marketplace_problems.append("marketplace.plugins[0] debe ser objeto")
            marketplace_plugin = {}
    if marketplace_plugin:
        if marketplace_plugin.get("name") != plugin.get("name"):
            marketplace_problems.append(
                "marketplace.plugins[0].name debe coincidir con plugin.name: "
                f"{marketplace_plugin.get('name')!r}"
            )
        if marketplace_plugin.get("strict") is False:
            marketplace_problems.append(
                "marketplace.plugins[0].strict=false haria que marketplace reemplace plugin.json"
            )
        marketplace_problems.extend(
            f"marketplace.plugins[0] no debe declarar {field}: {reason}"
            for field, reason in sorted(MARKETPLACE_ENTRY_FIELDS_REQUIRING_EXPLICIT_AUDIT.items())
            if field in marketplace_plugin
        )
    if marketplace_problems:
        _fail("Marketplace de Alfred Dev desalineado: " + "; ".join(marketplace_problems))

    plugin_component_problems = [
        f"plugin.json no debe declarar {field}: {reason}"
        for field, reason in sorted(PLUGIN_COMPONENT_FIELDS_REQUIRING_EXPLICIT_AUDIT.items())
        if field in plugin
    ]
    experimental = plugin.get("experimental")
    if experimental is not None and not isinstance(experimental, dict):
        plugin_component_problems.append("plugin.json experimental debe ser un objeto")
    elif isinstance(experimental, dict):
        plugin_component_problems.extend(
            f"plugin.json no debe declarar experimental.{field}: {reason}"
            for field, reason in sorted(
                PLUGIN_EXPERIMENTAL_FIELDS_REQUIRING_EXPLICIT_AUDIT.items()
            )
            if field in experimental
        )
    if plugin_component_problems:
        _fail("Componentes de plugin sin auditoria explicita: " + "; ".join(plugin_component_problems))

    command_paths, command_path_problems = _manifest_component_paths(plugin, "commands")
    _skill_manifest_paths, skill_path_problems = _manifest_component_paths(plugin, "skills")
    path_problems = command_path_problems + skill_path_problems
    if path_problems:
        _fail("Paths de componentes del manifest incompatibles: " + "; ".join(path_problems))

    missing_commands = [_rel(path) for path in command_paths if not path.exists()]
    if missing_commands:
        _fail(f"Comandos publicados inexistentes: {missing_commands}")
    public_command_paths = {path.resolve() for path in command_paths}
    extra_command_files = sorted(
        path for path in (ROOT / "commands").glob("*.md")
        if path.resolve() not in public_command_paths
    )
    if set(_rel(path) for path in extra_command_files) != {
        "commands/_composicion.md",
        "commands/_docs_vivas.md",
        "commands/next.md",
        "commands/search.md",
    }:
        _fail(
            "commands/ contiene ficheros no publicados inesperados: "
            f"{[_rel(path) for path in extra_command_files]}"
        )

    agent_files = sorted((ROOT / "agents").glob("*.md"))
    nested_agent_files = [
        path for path in (ROOT / "agents").rglob("*.md")
        if path.parent != ROOT / "agents"
    ]
    agent_frontmatter_problems: list[str] = []
    agent_models: Counter[str] = Counter()
    for path in agent_files:
        agent_text = _read(_rel(path))
        frontmatter_values = _frontmatter_top_level_values(agent_text)
        field_set = set(frontmatter_values)
        ignored = sorted(field_set & PLUGIN_IGNORED_AGENT_FIELDS)
        unknown = sorted(field_set - AGENT_SUPPORTED_FIELDS - PLUGIN_IGNORED_AGENT_FIELDS)
        if ignored:
            agent_frontmatter_problems.append(
                f"{_rel(path)} usa campos ignorados en agentes de plugin: {ignored}"
            )
        if unknown:
            agent_frontmatter_problems.append(
                f"{_rel(path)} usa campos no soportados en frontmatter: {unknown}"
            )
        for required in ("name", "description", "model"):
            if required not in field_set:
                agent_frontmatter_problems.append(f"{_rel(path)} no declara {required}")
        model = frontmatter_values.get("model")
        if model:
            agent_models[model] += 1
            if not _is_supported_agent_model(model):
                agent_frontmatter_problems.append(
                    f"{_rel(path)} usa modelo no soportado por Claude Code actual: {model!r}"
                )
        color = frontmatter_values.get("color")
        if color and color not in AGENT_COLOR_VALUES:
            agent_frontmatter_problems.append(
                f"{_rel(path)} usa color de subagente no soportado por Claude Code actual: {color!r}"
            )
        unavailable_tools = sorted(
            _frontmatter_tool_names(frontmatter_values.get("tools", ""))
            & SUBAGENT_UNAVAILABLE_TOOLS
        )
        unknown_tools = sorted(
            tool_name
            for tool_name in _frontmatter_tool_names(frontmatter_values.get("tools", ""))
            if not _is_known_agent_tool_name(tool_name)
        )
        if unknown_tools:
            agent_frontmatter_problems.append(
                f"{_rel(path)} lista herramientas desconocidas por Claude Code actual: {unknown_tools}"
            )
        if unavailable_tools:
            agent_frontmatter_problems.append(
                f"{_rel(path)} lista herramientas no disponibles en subagentes: {unavailable_tools}"
            )
        unavailable_mentions = sorted(
            tool for tool in SUBAGENT_UNAVAILABLE_TOOLS if tool in agent_text
        )
        if unavailable_mentions:
            agent_frontmatter_problems.append(
                f"{_rel(path)} instruye herramientas no disponibles en subagentes: {unavailable_mentions}"
            )
    if agent_models and agent_models != ALFRED_AGENT_MODEL_POLICY:
        agent_frontmatter_problems.append(
            "distribucion de modelos de agentes desalineada con la politica 0.7.0: "
            f"actual={dict(sorted(agent_models.items()))} "
            f"esperada={dict(sorted(ALFRED_AGENT_MODEL_POLICY.items()))}"
        )
    if agent_frontmatter_problems:
        _fail("Frontmatter de agentes incompatible: " + "; ".join(agent_frontmatter_problems))

    skill_files = _skill_files_from_manifest(plugin)
    skill_frontmatter_problems: list[str] = []
    skill_names: dict[str, list[str]] = {}
    for path in skill_files:
        skill_text = _read(_rel(path))
        frontmatter_values = _frontmatter_top_level_values(skill_text)
        field_set = set(frontmatter_values)
        unknown = sorted(field_set - SKILL_SUPPORTED_FIELDS)
        if unknown:
            skill_frontmatter_problems.append(
                f"{_rel(path)} usa campos no soportados en skill frontmatter: {unknown}"
            )
        for required in ("name", "description"):
            if required not in field_set:
                skill_frontmatter_problems.append(f"{_rel(path)} no declara {required}")
        listing_text_length = len(
            _frontmatter_field_text(skill_text, "description")
            + _frontmatter_field_text(skill_text, "when_to_use")
        )
        if listing_text_length > SKILL_LISTING_TEXT_LIMIT:
            skill_frontmatter_problems.append(
                f"{_rel(path)} excede el limite de listing de skills "
                f"{SKILL_LISTING_TEXT_LIMIT} chars: {listing_text_length}"
            )
        name = frontmatter_values.get("name")
        if name:
            skill_names.setdefault(name, []).append(_rel(path))
            if name != path.parent.name:
                skill_frontmatter_problems.append(
                    f"{_rel(path)} declara name={name!r} pero el directorio es {path.parent.name!r}"
                )
        for boolean_field in sorted(SKILL_BOOLEAN_FIELDS):
            value = frontmatter_values.get(boolean_field)
            if value and value.lower() not in SKILL_BOOLEAN_VALUES:
                skill_frontmatter_problems.append(
                    f"{_rel(path)} usa {boolean_field} no booleano: {value!r}"
                )
        model = frontmatter_values.get("model")
        if model and not _is_supported_agent_model(model):
            skill_frontmatter_problems.append(
                f"{_rel(path)} usa modelo de skill no soportado por Claude Code actual: {model!r}"
            )
        effort = frontmatter_values.get("effort")
        if effort and effort not in SKILL_EFFORT_VALUES:
            skill_frontmatter_problems.append(
                f"{_rel(path)} usa effort no soportado por Claude Code actual: {effort!r}"
            )
        context = frontmatter_values.get("context")
        if context and context not in SKILL_CONTEXT_VALUES:
            skill_frontmatter_problems.append(
                f"{_rel(path)} usa context no soportado por Claude Code actual: {context!r}"
            )
        if frontmatter_values.get("agent") and context != "fork":
            skill_frontmatter_problems.append(
                f"{_rel(path)} declara agent sin context: fork"
            )
        shell = frontmatter_values.get("shell")
        if shell and shell not in SKILL_SHELL_VALUES:
            skill_frontmatter_problems.append(
                f"{_rel(path)} usa shell no soportado por Claude Code actual: {shell!r}"
            )
        for tools_field in ("allowed-tools", "disallowed-tools"):
            unknown_tools = sorted(
                tool_name
                for tool_name in _frontmatter_tool_rule_names(
                    _frontmatter_field_rule_text(skill_text, tools_field)
                )
                if not _is_known_permission_rule_name(tool_name)
            )
            if unknown_tools:
                skill_frontmatter_problems.append(
                    f"{_rel(path)} {tools_field} declara herramientas desconocidas {unknown_tools}"
                )
    duplicated_skill_names = {
        name: paths for name, paths in sorted(skill_names.items()) if len(paths) > 1
    }
    if duplicated_skill_names:
        skill_frontmatter_problems.append(
            f"skills con name duplicado: {duplicated_skill_names}"
        )
    if skill_frontmatter_problems:
        _fail("Frontmatter de skills incompatible: " + "; ".join(skill_frontmatter_problems))

    domains = {
        path.relative_to(ROOT / "skills").parts[0]
        for path in skill_files
        if path.is_relative_to(ROOT / "skills")
    }
    if plugin.get("skills"):
        _fail(
            "plugin.json no debe listar skills: Claude las descubre en skills/*/SKILL.md"
        )
    if plugin.get("displayName") != "Alfred Dev":
        _fail("plugin.json debe declarar displayName humano 'Alfred Dev'")
    if marketplace_plugin.get("displayName") != plugin.get("displayName"):
        _fail("marketplace.json debe reutilizar el displayName humano del plugin")
    if "version" in marketplace_plugin:
        _fail(
            "marketplace.json no debe duplicar version cuando plugin.json ya "
            "declara version; Claude Code usa plugin.json como fuente canonica"
        )
    marketplace_source = marketplace_plugin.get("source")
    if isinstance(marketplace_source, str) and ".." in marketplace_source.split("/"):
        _fail("El source relativo del marketplace no debe escapar del root")
    if marketplace_source != "./":
        _fail(
            "El marketplace local debe apuntar al root del plugin para esta "
            f"auditoria: {marketplace_source!r}"
        )

    expected = {
        "commands": (len(plugin["commands"]), 18),
        "agents": (len(agent_files), 10),
        "nested_agents": (len(nested_agent_files), 0),
        "skills": (len(skill_files), 11),
        "skill_domains": (len(domains), 11),
    }
    bad = {
        key: {"actual": actual, "expected": wanted}
        for key, (actual, wanted) in expected.items()
        if actual != wanted
    }
    if bad:
        _fail(f"Inventario desalineado: {bad}")

    if not (ROOT / "commands" / "alfred.md").is_file():
        _fail("commands/alfred.md debe existir como comando publico")
    if "./commands/alfred.md" not in plugin.get("commands", []):
        _fail("plugin.json debe publicar ./commands/alfred.md")

    return [
        "18 comandos namespaced publicados",
        "commands/alfred.md publicado como entrada contextual",
        "commands/_composicion.md interno",
        "10 agentes en agents/ raiz",
        "frontmatter de agentes compatible con plugins",
        "herramientas de agentes validadas contra nombres oficiales de Claude Code",
        "herramientas no disponibles excluidas de subagentes",
        "modelos inherit en los 10 agentes",
        "11 skills planas",
        "frontmatter de skills compatible con Claude Code actual",
        "valores de frontmatter de skills validados contra Claude Code actual",
        "descripciones de skills dentro del limite de listing 1536",
        "displayName humano alineado entre manifest y marketplace",
        "version canonica solo en plugin.json; marketplace sin version duplicada",
        "marketplace no suplementa componentes ni enablement",
        "paths de comandos/skills acotados al root del plugin",
        "manifest sin componentes no auditados",
    ]


def _command_names_from_manifest(plugin: dict) -> list[str]:
    return [
        Path(relative_path).stem
        for relative_path in plugin["commands"]
    ]


def _public_route_names(plugin: dict | None = None) -> set[str]:
    plugin = plugin or _json(".claude-plugin/plugin.json")
    names = set(_command_names_from_manifest(plugin))
    return names


def _public_argument_commands(plugin: dict | None = None) -> set[str]:
    """Comandos cuya superficie publica acepta texto, flags u opciones libres."""
    plugin = plugin or _json(".claude-plugin/plugin.json")
    commands: set[str] = set()
    for relative_path in plugin["commands"]:
        text = _read(relative_path.lstrip("./"))
        frontmatter = _frontmatter_block(text)
        if "$ARGUMENTS" in text or re.search(r"(?m)^argument-hint:\s*.+$", frontmatter):
            commands.add(Path(relative_path).stem)
    if (ROOT / "skills" / "alfred" / "alfred" / "SKILL.md").exists():
        commands.add("alfred")
    return commands


def _validate_manual_option_contract_shape(manual_smoke, option_coverage: dict[str, list[str]]) -> None:
    """Evita falsos verdes por typos en los IDs de opciones manuales."""
    option_contracts = tuple(manual_smoke.OPTION_CONTRACTS)
    problems: list[str] = []

    duplicates = sorted({
        key for key in option_contracts
        if option_contracts.count(key) > 1
    })
    if duplicates:
        problems.append(f"OPTION_CONTRACTS duplicados: {duplicates}")

    malformed = sorted(
        key for key in option_contracts
        if key.count(":") != 1 or not key.split(":", 1)[0] or not key.split(":", 1)[1]
    )
    if malformed:
        problems.append(f"OPTION_CONTRACTS mal formados: {malformed}")

    public_commands = _public_route_names(_json(".claude-plugin/plugin.json"))
    aliases = getattr(manual_smoke, "_PUBLIC_COMMAND_ALIASES", {})
    unknown_prefixes = sorted({
        key.split(":", 1)[0]
        for key in option_contracts
        if key.count(":") == 1
        and key.split(":", 1)[0] not in public_commands
        and aliases.get(key.split(":", 1)[0]) not in public_commands
    })
    if unknown_prefixes:
        problems.append(f"OPTION_CONTRACTS con comandos no publicados: {unknown_prefixes}")

    from core import config_loader

    expected_config_options = {
        "config:exit-without-changes",
        *{
            f"config:{section.replace('_', '-')}"
            for section in config_loader._CONFIG_SECTION_ORDER
        },
    }
    actual_config_options = {
        key for key in option_contracts
        if key.startswith("config:")
    }
    missing_config_options = sorted(expected_config_options - actual_config_options)
    extra_config_options = sorted(actual_config_options - expected_config_options)
    if missing_config_options or extra_config_options:
        problems.append(
            "OPTION_CONTRACTS de /config desalineados: "
            f"missing={missing_config_options} extra={extra_config_options}"
        )

    expected_lucius_options = {
        "lucius:default-scope-all",
        "lucius:scope-all",
        "lucius:scope-security",
        "lucius:scope-tests",
        "lucius:scope-architecture",
        "lucius:scope-performance",
        "lucius:target-directory",
        "lucius:invalid-scope",
    }
    actual_lucius_options = {
        key for key in option_contracts
        if key.startswith("lucius:")
    }
    missing_lucius_options = sorted(expected_lucius_options - actual_lucius_options)
    extra_lucius_options = sorted(actual_lucius_options - expected_lucius_options)
    if missing_lucius_options or extra_lucius_options:
        problems.append(
            "OPTION_CONTRACTS de /lucius desalineados: "
            f"missing={missing_lucius_options} extra={extra_lucius_options}"
        )

    expected_human_menu_options = {
        "audit:sonarqube-docker-install-menu",
        "audit:sonarqube-docker-start-menu",
        "ship:deploy-confirmation-menu",
        "feature:user-gate-menu",
        "fix:user-gate-menu",
        "spike:conclusion-review-menu",
        "discuss:route-menu",
        "alfred:route-menu",
        "update:confirm-update-menu",
    }
    missing_human_menu_options = sorted(expected_human_menu_options - set(option_contracts))
    if missing_human_menu_options:
        problems.append(
            "OPTION_CONTRACTS sin menus humanos obligatorios: "
            f"{missing_human_menu_options}"
        )

    coverage_only = sorted(set(option_coverage) - set(option_contracts))
    if coverage_only:
        problems.append(f"option_coverage contiene claves fuera de OPTION_CONTRACTS: {coverage_only}")

    if problems:
        _fail("Contratos de opciones manuales invalidos: " + "; ".join(problems))


def _validate_manual_runtime_contract_shape(manual_smoke, runtime_coverage: dict[str, list[str]]) -> None:
    """Valida que los contratos runtime describan scopes reales de /update."""
    runtime_contracts = tuple(manual_smoke.RUNTIME_CONTRACTS)
    problems: list[str] = []

    duplicates = sorted({
        key for key in runtime_contracts
        if runtime_contracts.count(key) > 1
    })
    if duplicates:
        problems.append(f"RUNTIME_CONTRACTS duplicados: {duplicates}")

    malformed = sorted(
        key for key in runtime_contracts
        if key.count(":") != 1 or not key.split(":", 1)[0] or not key.split(":", 1)[1]
    )
    if malformed:
        problems.append(f"RUNTIME_CONTRACTS mal formados: {malformed}")

    public_commands = _public_route_names(_json(".claude-plugin/plugin.json"))
    unknown_prefixes = sorted({
        key.split(":", 1)[0]
        for key in runtime_contracts
        if key.count(":") == 1 and key.split(":", 1)[0] not in public_commands
    })
    if unknown_prefixes:
        problems.append(f"RUNTIME_CONTRACTS con comandos no publicados: {unknown_prefixes}")

    expected_update_contracts = {
        "update:scope-user-or-unknown",
        "update:scope-local-to-user",
        "update:scope-project-to-user",
        "update:scope-managed",
    }
    actual_update_contracts = {
        key for key in runtime_contracts
        if key.startswith("update:")
    }
    missing_update = sorted(expected_update_contracts - actual_update_contracts)
    extra_update = sorted(actual_update_contracts - expected_update_contracts)
    if missing_update or extra_update:
        problems.append(
            "RUNTIME_CONTRACTS de /update desalineados: "
            f"missing={missing_update} extra={extra_update}"
        )

    coverage_only = sorted(set(runtime_coverage) - set(runtime_contracts))
    if coverage_only:
        problems.append(f"runtime_coverage contiene claves fuera de RUNTIME_CONTRACTS: {coverage_only}")

    if problems:
        _fail("Contratos runtime manuales invalidos: " + "; ".join(problems))


def _validate_manual_case_contract_links(manual_smoke) -> None:
    """Asegura que cada contrato manual esté cubierto por un caso del comando correcto."""
    aliases = getattr(manual_smoke, "_PUBLIC_COMMAND_ALIASES", {})

    def _canon(name: str) -> str:
        return aliases.get(name, name)

    problems: list[str] = []
    for case in manual_smoke.CASES:
        case_commands = set(getattr(case, "commands", ()) or ())
        prompt = getattr(case, "prompt", "")
        prompt_commands = set(re.findall(r"/alfred-dev:([a-z0-9-]+)", prompt))
        if re.search(r"(?<!\S)/alfred(?:\s|$)", prompt):
            prompt_commands.add("alfred")
        mapped_case = {_canon(name) for name in case_commands}
        mapped_prompt = {_canon(name) for name in prompt_commands}
        if case_commands:
            missing_prompt_commands = sorted(mapped_case - mapped_prompt)
            extra_prompt_commands = sorted(mapped_prompt - mapped_case)
            if missing_prompt_commands:
                problems.append(
                    f"{case.case_id}: prompt no invoca {missing_prompt_commands}"
                )
            if extra_prompt_commands:
                problems.append(
                    f"{case.case_id}: prompt invoca comandos no declarados {extra_prompt_commands}"
                )
        elif prompt_commands:
            problems.append(
                f"{case.case_id}: prompt invoca comandos sin declarar {sorted(prompt_commands)}"
            )
        for key in getattr(case, "option_keys", ()) or ():
            command_name = key.split(":", 1)[0] if ":" in key else ""
            if _canon(command_name) not in mapped_case:
                problems.append(f"{case.case_id}: option {key} no corresponde a {sorted(case_commands)}")
        for key in getattr(case, "runtime_keys", ()) or ():
            command_name = key.split(":", 1)[0] if ":" in key else ""
            if _canon(command_name) not in mapped_case:
                problems.append(f"{case.case_id}: runtime {key} no corresponde a {sorted(case_commands)}")
    if problems:
        _fail("Contratos manuales enlazados al caso equivocado: " + "; ".join(problems))


def _slash_command_names(text: str) -> list[str]:
    return re.findall(r"`/alfred-dev:([a-z0-9-]+)`", text)


def _section_between(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def check_command_catalog() -> list[str]:
    plugin = _json(".claude-plugin/plugin.json")
    manifest_names = _command_names_from_manifest(plugin)
    manifest_set = set(manifest_names)
    architecture = _read("docs/architecture.md")
    alfred_text = _read("commands/alfred.md")

    unpublished = {"_composicion", "_docs_vivas", "next", "search"}
    disk_names = {
        path.stem
        for path in (ROOT / "commands").glob("*.md")
        if path.stem not in unpublished
    }

    problems: list[str] = []
    if manifest_set != disk_names:
        problems.append(
            "comandos publicados y commands/*.md no coinciden: "
            f"faltan={sorted(disk_names - manifest_set)} sobran={sorted(manifest_set - disk_names)}"
        )
    if "alfred" not in manifest_set:
        problems.append("falta el comando publico alfred")
    if "/alfred-dev:alfred" not in alfred_text and "/alfred" not in alfred_text:
        problems.append("commands/alfred.md debe describir la entrada contextual")
    if "18 comandos" not in architecture and "/alfred-dev:alfred" not in architecture:
        problems.append("docs/architecture.md debe mencionar 18 comandos o /alfred-dev:alfred")

    for relative_path, name in zip(plugin["commands"], manifest_names):
        text = _read(relative_path.lstrip("./"))
        if not text.startswith("---\n"):
            problems.append(f"{relative_path}: falta frontmatter")
            continue
        frontmatter = text.split("---", 2)[1]
        frontmatter_values = _frontmatter_top_level_values(text)
        unknown_fields = sorted(set(frontmatter_values) - COMMAND_SUPPORTED_FIELDS)
        if unknown_fields:
            problems.append(
                f"{relative_path}: campos de frontmatter no soportados {unknown_fields}"
            )
        if not re.search(r"(?m)^description:\s*['\"]?.+['\"]?\s*$", frontmatter):
            problems.append(f"{relative_path}: falta description en frontmatter")
        model = frontmatter_values.get("model")
        if model and not _is_supported_agent_model(model):
            problems.append(
                f"{relative_path}: usa modelo de comando no soportado por Claude Code actual: {model!r}"
            )
        for tools_field in ("allowed-tools", "disallowed-tools"):
            unknown_tools = sorted(
                tool_name
                for tool_name in _frontmatter_tool_rule_names(
                    _frontmatter_field_rule_text(text, tools_field)
                )
                if not _is_known_permission_rule_name(tool_name)
            )
            if unknown_tools:
                problems.append(
                    f"{relative_path}: {tools_field} declara herramientas desconocidas {unknown_tools}"
                )
        if f"/alfred-dev:{name}" not in text:
            problems.append(f"{relative_path}: no menciona su slash command")

    if problems:
        _fail("Catalogo de comandos desalineado: " + "; ".join(problems))

    return [
        "18 comandos namespaced alineados entre plugin.json y arquitectura",
        "commands/alfred.md publicado como entrada contextual",
        "frontmatter de comandos con description",
        "frontmatter de comandos compatible con Claude Code actual",
        "model de comandos validado contra Claude Code actual",
    ]


def _frontmatter_block(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else ""


def _frontmatter_top_level_fields(text: str) -> list[str]:
    fields: list[str] = []
    for line in _frontmatter_block(text).splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z_-]*)\s*:", line)
        if match:
            fields.append(match.group(1))
    return fields


def _frontmatter_top_level_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _frontmatter_block(text).splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z_-]*)\s*:\s*(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        values[key] = value.strip().strip('"').strip("'")
    return values


def _frontmatter_field_text(text: str, field: str) -> str:
    lines = _frontmatter_block(text).splitlines()
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

        collected: list[str] = []
        for following in lines[index + 1:]:
            if re.match(r"^[A-Za-z][A-Za-z_-]*\s*:", following):
                break
            if following.startswith((" ", "\t")):
                collected.append(following.strip())
        return "\n".join(collected)
    return ""


def _is_supported_agent_model(model: str) -> bool:
    return model in AGENT_MODEL_ALIASES or AGENT_MODEL_ID_RE.fullmatch(model) is not None


def _frontmatter_tool_names(tools: str) -> set[str]:
    names: set[str] = set()
    for item in tools.split(","):
        name = item.strip()
        if not name:
            continue
        names.add(re.split(r"[\s(]", name, maxsplit=1)[0])
    return names


def _frontmatter_tool_rule_names(rules: str) -> set[str]:
    return set(
        re.findall(r"(?:^|[\s,])([A-Za-z][A-Za-z0-9_]*)(?:\(|(?=$|[\s,]))", rules)
    )


def _frontmatter_field_rule_text(text: str, field: str) -> str:
    """Devuelve reglas inline o de lista YAML simple para allowed/disallowed tools."""
    lines = _frontmatter_block(text).splitlines()
    values: list[str] = []
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


def check_command_execution_contracts() -> list[str]:
    """Verifica que cada comando publicado conserve su estrategia operativa."""
    plugin = _json(".claude-plugin/plugin.json")
    commands = {
        Path(relative_path).stem: _read(relative_path.lstrip("./"))
        for relative_path in plugin["commands"]
    }
    composition = _read("commands/_composicion.md")
    problems: list[str] = []

    for name, text in commands.items():
        frontmatter = _frontmatter_block(text)
        has_arguments = "$ARGUMENTS" in text
        has_hint = re.search(r"(?m)^argument-hint:\s*.+$", frontmatter) is not None
        if has_arguments and not has_hint:
            problems.append(f"{name}: usa $ARGUMENTS pero no declara argument-hint")
        if has_hint and not has_arguments:
            problems.append(f"{name}: declara argument-hint pero no inserta $ARGUMENTS")
        if re.search(r"`/alfred:[^`]*`|^/alfred:", text, re.MULTILINE):
            problems.append(f"{name}: contiene slash command legacy /alfred:")
        if re.search(r"\bTask\b", text):
            problems.append(f"{name}: contiene nomenclatura obsoleta Task")
        if re.search(r"\*\*GATE \(libre\):\*\*.*\bSe aprueba siempre\b", text):
            problems.append(
                f"{name}: gate libre promete aprobacion incondicional sin evidencia"
            )

    helper_contracts = {
        "alfred": [
            'consume-prefetch "$PWD" --expected alfred',
            'alfred-continuity.py next "$PWD" --json',
            "No ofrezcas un menú por defecto",
        ],
        "discuss": [
            'consume-prefetch "$PWD" --expected discuss',
            'alfred-continuity.py discuss "$PWD" --raw "$ARGUMENTS"',
            "respuesta final",
            "commands/_docs_vivas.md",
        ],
        "map-codebase": [
            'consume-prefetch "$PWD" --expected map-codebase',
            'alfred-continuity.py map-codebase "$PWD" --raw "$ARGUMENTS"',
            "NO inventes stack, entrypoints o riesgos",
            "commands/_docs_vivas.md",
        ],
        "memory-ui": [
            'consume-prefetch "$PWD" --expected memory-ui',
            'alfred-continuity.py memory-ui "$PWD" --raw "$ARGUMENTS"',
            "--stop",
        ],
        "next": [
            'alfred-continuity.py next "$PWD" --json',
            "un único `AskUserQuestion` navegable",
        ],
        "pause": [
            'alfred-continuity.py pause "$PWD"',
            "Primero ejecuta el helper determinista",
            "No la reenvuelvas con un segundo resumen",
        ],
        "progress": [
            'alfred-continuity.py progress "$PWD"',
            "úsalo como respuesta final",
            "NO uses `AskUserQuestion`",
        ],
        "quick": [
            'alfred-continuity.py quick "$PWD" --raw "$ARGUMENTS"',
            "`Write` ni `Edit`",
            "## Cierre canónico del comando",
        ],
        "search": [
            'alfred-continuity.py search "$PWD" --raw "$ARGUMENTS"',
            "Si `$ARGUMENTS` está vacío, dilo claramente",
        ],
        "sync-github": [
            'alfred-continuity.py sync-github "$PWD" --raw "$ARGUMENTS"',
            "Mantén la verdad local",
        ],
        "uat": [
            'alfred-continuity.py verify "$PWD" --raw "$ARGUMENTS"',
            "NO marques una UAT como aprobada sin una indicación explícita",
            "NO añadas una segunda capa de resumen",
        ],
        "retomar": [
            'alfred-continuity.py resume "$PWD"',
            "Primero ejecuta el helper determinista",
        ],
    }
    commands_for_contracts = dict(commands)
    commands_for_contracts["alfred"] = _read("commands/alfred.md")
    commands_for_contracts["next"] = _read("commands/next.md")
    commands_for_contracts["search"] = _read("commands/search.md")
    for name, needles in helper_contracts.items():
        text = commands_for_contracts[name]
        for needle in needles:
            if needle not in text:
                problems.append(f"{name}: falta contrato helper {needle!r}")

    flow_contracts = {
        "feature": [
            "Flujo de hasta 7 fases",
            "## HARD-GATES",
            "Maximo 5 intentos",
            "## Cierre canónico del comando",
            "siguiente paso esperado",
            "commands/_docs_vivas.md",
            "check-project-docs",
        ],
        "fix": [
            "Flujo de 3 fases",
            "test que reproduce el bug",
            "Maximo 5 intentos",
            "## Cierre canónico del comando",
            "bug/causa raíz en curso",
            "commands/_docs_vivas.md",
        ],
        "quick": [
            "Flujo ligero de 2 fases",
            "Cuándo quick deja de ser quick",
            "## Cierre canónico del comando",
            "/alfred-dev:uat",
            "commands/_docs_vivas.md",
            "cierre",
        ],
        "spike": [
            "Flujo de 2 fases",
            "Los spikes NO generan código de producción",
            "## Cierre canónico del comando",
            "ADR",
            "no implementar todavía",
        ],
        "ship": [
            "Flujo de 4 fases",
            "Gate de despliegue SIEMPRE interactiva",
            "NUNCA auto-apruebes un despliegue",
            "## Cierre canónico del comando",
            "commands/_docs_vivas.md",
            "hygiene",
        ],
        "audit": [
            "Preflight de SonarQube",
            "Lanza 4 agentes EN PARALELO",
            "No toca código, solo genera informes",
            "## Cierre canónico del comando",
            "commands/_docs_vivas.md",
        ],
    }
    for name, needles in flow_contracts.items():
        text = commands[name]
        for needle in needles:
            if needle not in text:
                problems.append(f"{name}: falta contrato de flujo {needle!r}")

    composition_reader_contracts = ("feature", "fix", "quick", "spike", "ship", "audit")
    for name in composition_reader_contracts:
        text = commands[name]
        for needle in (
            "${CLAUDE_PLUGIN_ROOT}/commands/_composicion.md",
        ):
            if needle not in text:
                problems.append(f"{name}: carga _composicion sin contrato de plugin: {needle!r}")

    docs_reader_contracts = ("feature", "fix", "quick", "spike", "ship", "audit")
    for name in docs_reader_contracts:
        text = commands[name]
        if "${CLAUDE_PLUGIN_ROOT}/commands/_docs_vivas.md" not in text:
            problems.append(
                f"{name}: carga _docs_vivas sin contrato de plugin: "
                "'${CLAUDE_PLUGIN_ROOT}/commands/_docs_vivas.md'"
            )

    autopilot_texts = {
        "_composicion": composition,
        "feature": commands["feature"],
        "fix": commands["fix"],
        "ship": commands["ship"],
    }
    for name, text in autopilot_texts.items():
        if '"autopilot": true' not in text:
            problems.append(f"{name}: no reconoce el flag canonico de estado autopilot")
        if '"modo": "autopilot"' not in text:
            problems.append(f"{name}: no conserva el alias legacy de estado autopilot")

    interactive_contracts = {
        "ajustes": [
            "principal navegable",
            "core/config_cli.py",
            "CONFIG_HEADLESS_MENU",
            "no llames `AskUserQuestion`",
            "vuelve cancelada",
            "build_config_section_summaries()",
            "build_config_section_menu()",
            "build_config_section_change_preview()",
            "update_config_section()",
        ],
        "lucius": [
            "Argumentos del usuario: $ARGUMENTS",
            "codex login",
            "scope=all",
            "No implementes ningún ítem",
            "siguiente paso verificable",
        ],
        "update": [
            "semver real",
            "0.10.0",
            "un único `AskUserQuestion`",
            "ejecutar **`/reload-plugins`**",
            "`/reload-plugins --force`",
            "entonces debe reiniciar",
            "## Cierre canónico del comando",
        ],
    }
    for name, needles in interactive_contracts.items():
        text = commands[name]
        for needle in needles:
            if needle not in text:
                problems.append(f"{name}: falta contrato interactivo {needle!r}")

    if problems:
        _fail("Contratos de ejecución de comandos incompletos: " + "; ".join(problems))

    return [
        "18 comandos namespaced preservan argumentos, prefijo y nomenclatura actual",
        "18 wrappers helper-first cubiertos",
        "6 flujos principales con cierre canónico",
        "_composicion se carga desde la instalación del plugin",
        "config/lucius/update con contratos interactivos verificables",
        "gates libres sin aprobacion incondicional",
        "autopilot por config/estado sin flag publico fantasma",
    ]


def _registered_hook_script_count() -> int:
    hooks = _json("hooks/hooks.json").get("hooks", {})
    scripts: set[str] = set()
    for groups in hooks.values():
        for group in groups:
            for hook in group.get("hooks", []):
                args = hook.get("args", [])
                if not isinstance(args, list):
                    continue
                for arg in args:
                    if isinstance(arg, str) and arg.startswith("${CLAUDE_PLUGIN_ROOT}/hooks/"):
                        scripts.add(Path(arg).name)
    return len(scripts)


def check_public_claims() -> list[str]:
    """Mantiene los claims publicos alineados con inventario y docs actuales."""
    readme = _read("README.md")
    architecture = _read("docs/architecture.md")
    skills_doc = _read("docs/skills.md")
    help_command = _read("commands/alfred.md")
    alfred_agent = _read("agents/alfred.md")
    lucius_agent = _read("agents/lucius.md")
    agents_readme = _read("docs/agents/README.md")
    has_site = _has_site()
    personality = _read("docs/personality.md")
    changelog = _read("CHANGELOG.md")

    agent_count = len(list((ROOT / "agents").glob("*.md")))
    skill_count = len(list((ROOT / "skills").rglob("SKILL.md")))
    command_count = len(_json(".claude-plugin/plugin.json")["commands"])
    hook_script_count = _registered_hook_script_count()

    expected_counts = {
        "agents": (agent_count, 10),
        "skills": (skill_count, 11),
        "commands": (command_count, 18),
        "hooks": (hook_script_count, hook_script_count),
    }
    for label, (actual, expected) in expected_counts.items():
        if actual != expected:
            _fail(f"Inventario publico {label}={actual}, esperado {expected}")

    required = {
        "README.md": [
            "10 agentes",
            "11 skills",
            "quality gates",
            "https://code.claude.com/docs/en/overview",
            "Novedades en v0.7.0",
        ],
        "docs/skills.md": [
            "catalogo de 11 skills",
            "disable-model-invocation: true",
            "memory",
            "style-direction",
        ],
        "docs/architecture.md": [
            "18 comandos",
            "El manifiesto no declara la clave `agents`",
        ],
        "commands/alfred.md": [
            "Agent Teams",
            "/alfred-dev:feature",
        ],
        "agents/alfred.md": [
            "Alfred",
        ],
        "docs/agents/README.md": [
            "Claude Code los descubre directamente desde `agents/`",
            "el manifiesto `plugin.json` no declara una seccion `agents` manual",
            "quality gates verificables con evidencia",
            "El resultado no se promete determinista",
            "reduce variabilidad",
        ],
        "agents/lucius.md": [
            "No fuerces un modelo por tu cuenta",
            "Codex CLI (configuración local del usuario)",
            "codex exec",
            "--sandbox read-only",
            "--ephemeral",
            "--json",
            "--output-last-message",
            "codex_report",
            "codex_jsonl",
            "approval_policy",
            "status --porcelain=v1 -z",
        ],
        "CHANGELOG.md": [
            "displayName: \"Alfred Dev\"",
            "Alfred Dev (alfred-dev)",
            "namespace técnico",
            "42 opciones públicas",
            "4 contratos runtime de `/update`",
        ],
        "site/src/i18n/data.es.ts": [
            "displayName: \"Alfred Dev\"",
            "Alfred Dev (alfred-dev)",
            "namespace técnico",
            "Claude Code 2.1.183",
            "plugins, skills, hooks y MCP",
            "claude update",
        ],
        "site/src/i18n/data.en.ts": [
            "displayName: \"Alfred Dev\"",
            "Alfred Dev (alfred-dev)",
            "technical namespace",
            "Claude Code 2.1.183",
            "plugins, skills, hooks, and MCP",
            "claude update",
            "quality gates that require evidence before work can close",
        ],
    }
    sources = {
        "README.md": readme,
        "docs/skills.md": skills_doc,
        "docs/architecture.md": architecture,
        "commands/alfred.md": help_command,
        "agents/alfred.md": alfred_agent,
        "docs/agents/README.md": agents_readme,
        "agents/lucius.md": lucius_agent,
        "CHANGELOG.md": changelog,
    }
    if has_site:
        sources.update({
            "site/src/i18n/data.es.ts": _read("site/src/i18n/data.es.ts"),
            "site/src/i18n/data.en.ts": _read("site/src/i18n/data.en.ts"),
        })
    else:
        required = {
            path: needles
            for path, needles in required.items()
            if not path.startswith("site/")
        }
    missing: list[str] = []
    for path, needles in required.items():
        for needle in needles:
            if needle not in sources[path]:
                missing.append(f"{path}: {needle}")
    if missing:
        _fail(f"Claims publicos incompletos: {missing}")

    stale_exact = {
        "README.md": [
            "### Skills (60)",
            "### Hooks (12)",
            "### Core (6 modulos)",
            "### Core (6 módulos)",
            "GPT-5.4",
            "--autopilot",
            "keywords contextuales",
            "https://docs.anthropic.com/en/docs/claude-code",
            "quality gates infranqueables",
            "No hay excepciones, no hay modo de saltárselas",
        ],
        "docs/architecture.md": ["Agentes de nucleo** (9)", "se registran igualmente en `plugin.json`"],
        "docs/agents/README.md": [
            "tambien aparecen en `plugin.json`",
            "quality gates infranqueables",
            "El resultado es previsible y reproducible",
            "produce resultados consistentes porque no arrastra",
        ],
        "commands/alfred.md": ["GPT-5.4"],
        "agents/alfred.md": [
            "9 agentes de nucleo + 8 opcionales",
            "reglas infranqueables",
            "NUNCA se pueden saltar",
        ],
        "agents/lucius.md": ["GPT-5.4", "gpt-5.4"],
        "docs/personality.md": ["GPT-5.4"],
        "CHANGELOG.md": [
            "GPT-5.4",
            "gpt-5.4",
            "22 opciones/variantes",
            "`codex review`",
            "approval: never",
            "sin prompt de confirmación al usuario",
            "ejecuta el scanner end-to-end",
            "Quality gates infranqueables",
        ],
        "site/src/i18n/data.es.ts": [
            "6 módulos core",
            "GPT-5.4",
            "codex review",
            "approval: never",
            "--autopilot",
            "sin pedir confirmación al usuario",
            "Verificado end-to-end con Docker",
            "ejecuta el scanner end-to-end",
            "No hay requisito de versión mínima específica",
            "Cualquier versión de Claude Code",
            "Claude Code instalado.",
        ],
        "site/src/i18n/data.en.ts": [
            "6 core modules",
            "GPT-5.4",
            "modelo configurado por el usuario",
            "codex review",
            "approval: never",
            "--autopilot",
            "quality gates the workflow cannot skip",
            "without asking the user for confirmation",
            "Verified end-to-end with Docker",
            "runs the scanner end-to-end",
            "There is no specific minimum version requirement",
            "Any version of Claude Code",
            "Claude Code installed.",
        ],
        "site/src/components/BrutalistLandingPage.astro": [
            "GPT-5.4",
            "codex review",
            "Los quality gates son infranqueables",
        ],
        "hooks/session-start.sh": [
            "Las quality gates son infranqueables",
        ],
        "site/src/components/Footer.astro": ["https://docs.anthropic.com/en/docs/claude-code"],
        "docs/skills.md": [
            "garantizar que el resultado sea consistente, reproducible y de calidad profesional",
            "procedimiento verificable y reproducible",
            "garantizar que el software sea usable por todas las personas",
        ],
        "docs/flows.md": [
            "garantiza que cada linea de código tiene al menos un test",
            "garantiza que cada línea de código tiene al menos un test",
        ],
        "docs/agents/security-officer.md": [
            "garantizar que el software cumple con los estandares de seguridad",
        ],
        "agents/security-officer.md": [
            "garantiza que nada con vulnerabilidades conocidas llega a los usuarios",
            "bloqueantes absolutos. Sin excepciones",
            "seguridad infranqueable",
        ],
    }
    stale_sources = {
        "README.md": readme,
        "docs/skills.md": skills_doc,
        "docs/flows.md": _read("docs/flows.md"),
        "docs/agents/security-officer.md": _read("docs/agents/security-officer.md"),
        "agents/security-officer.md": _read("agents/security-officer.md"),
        "hooks/session-start.sh": _read("hooks/session-start.sh"),
        "docs/architecture.md": architecture,
        "commands/alfred.md": help_command,
        "agents/alfred.md": alfred_agent,
        "docs/agents/README.md": agents_readme,
        "agents/lucius.md": lucius_agent,
        "docs/personality.md": personality,
        "CHANGELOG.md": changelog,
    }
    if has_site:
        stale_sources.update({
            "site/src/i18n/data.es.ts": _read("site/src/i18n/data.es.ts"),
            "site/src/i18n/data.en.ts": _read("site/src/i18n/data.en.ts"),
            "site/src/components/BrutalistLandingPage.astro": _read("site/src/components/BrutalistLandingPage.astro"),
            "site/src/components/Footer.astro": _read("site/src/components/Footer.astro"),
        })
    else:
        stale_exact = {
            path: needles
            for path, needles in stale_exact.items()
            if not path.startswith("site/")
        }
    stale_hits: list[str] = []
    for path, needles in stale_exact.items():
        for needle in needles:
            if needle in stale_sources[path]:
                stale_hits.append(f"{path}: {needle}")
    if stale_hits:
        _fail(f"Claims obsoletos en superficie actual: {stale_hits}")

    manual_only_problems: list[str] = []
    for relative_path in MANUAL_ONLY_SKILLS:
        frontmatter = _frontmatter_block(_read(relative_path))
        if not re.search(r"(?m)^disable-model-invocation:\s*true\s*$", frontmatter):
            manual_only_problems.append(relative_path)
    if manual_only_problems:
        _fail(
            "Skills delicados sin activacion manual explicita: "
            f"{manual_only_problems}"
        )

    legacy_runtime: list[str] = []
    legacy_pattern = re.compile(r"/alfred\s+(feature|fix|ship|spike|audit|config)\b")
    for path in sorted((ROOT / "agents").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in legacy_pattern.finditer(text):
            legacy_runtime.append(f"{_rel(path)}:{match.group(0)}")
    if legacy_runtime:
        _fail(f"Prompts runtime con slash command legacy: {legacy_runtime}")

    surface_message = (
        "README, landing, arquitectura, help y agentes sin contadores antiguos"
        if has_site
        else "README, arquitectura, help y agentes sin contadores antiguos"
    )
    display_name_message = (
        "displayName humano reflejado en README, changelog y landing"
        if has_site
        else "displayName humano reflejado en README y changelog"
    )
    return [
        "inventario publico 10/11/18 verificado",
        surface_message,
        display_name_message,
        "skills delicados mantienen activacion manual explicita",
        "Lucius no fija modelo obsoleto de Codex CLI",
        "prompts runtime sin /alfred legacy",
    ]


def check_config_contracts() -> list[str]:
    """Verifica que /alfred-dev:ajustes exponga las opciones reales del runtime."""
    from core import config_loader
    from core import optional_agents

    def assert_ask_user_question_payload(label: str, payload: dict) -> None:
        questions = payload.get("questions")
        if not isinstance(questions, list) or len(questions) != 1:
            _fail(f"{label} no expone questions[0] para AskUserQuestion: {payload}")
        question = questions[0]
        if not isinstance(question, dict):
            _fail(f"{label}.questions[0] no es objeto: {question}")
        for field in ("question", "header", "options", "multiSelect"):
            if field not in question:
                _fail(f"{label}.questions[0] no declara {field}")
        if question["multiSelect"] is not False:
            _fail(f"{label}.questions[0].multiSelect debe ser false")
        if question["question"] != payload.get("question"):
            _fail(f"{label}.questions[0].question no coincide con legacy question")
        if question["header"] != payload.get("header"):
            _fail(f"{label}.questions[0].header no coincide con legacy header")
        if question["options"] != payload.get("options"):
            _fail(f"{label}.questions[0].options no coincide con legacy options")
        for index, option in enumerate(question["options"]):
            if not isinstance(option, dict):
                _fail(f"{label}.questions[0].options[{index}] no es objeto")
            if not str(option.get("label", "")).strip():
                _fail(f"{label}.questions[0].options[{index}] no declara label")
            if not str(option.get("description", "")).strip():
                _fail(f"{label}.questions[0].options[{index}] no declara description")

    def assert_prompt_examples_use_current_ask_user_question_schema(
        relative_path: str,
        text: str,
    ) -> None:
        for match in re.finditer(r"AskUserQuestion\(\{(?P<body>.*?)^\}\)", text, re.DOTALL | re.MULTILINE):
            body = match.group("body")
            missing = [
                needle
                for needle in ("questions: [", "multiSelect: false", "options: [")
                if needle not in body
            ]
            if missing:
                _fail(
                    "Ejemplo AskUserQuestion obsoleto en "
                    f"{relative_path}: faltan {missing}"
                )

    expected_sections = (
        "autonomia",
        "proyecto",
        "agentes_opcionales",
        "memoria",
        "compliance",
        "integraciones",
        "personalidad",
    )
    if tuple(config_loader._CONFIG_SECTION_ORDER) != expected_sections:
        _fail(
            "Orden de secciones config desalineado: "
            f"{config_loader._CONFIG_SECTION_ORDER}"
        )

    labels = config_loader._CONFIG_SECTION_LABELS
    if set(labels) != set(expected_sections):
        _fail(f"Labels config desalineados: {sorted(labels)}")

    summaries = config_loader.build_config_section_summaries(config_loader.DEFAULT_CONFIG)
    summary_sections = tuple(section["section"] for section in summaries)
    if summary_sections != expected_sections:
        _fail(f"Summaries config desalineados: {summary_sections}")

    menu = config_loader.build_config_section_menu(config_loader.DEFAULT_CONFIG)
    menu_labels = [option["label"] for option in menu["options"]]
    if menu_labels[0] != "Salir sin cambios":
        _fail(f"Menu config sin salida inicial: {menu_labels}")
    missing_labels = [
        labels[section]
        for section in expected_sections
        if labels[section] not in menu_labels
    ]
    if missing_labels:
        _fail(f"Menu config no expone secciones: {missing_labels}")
    assert_ask_user_question_payload("build_config_section_menu", menu)

    for group_name in optional_agents.OPTIONAL_AGENT_GROUP_ORDER:
        assert_ask_user_question_payload(
            f"build_optional_agent_group_menu[{group_name}]",
            optional_agents.build_optional_agent_group_menu(group_name),
        )

    preview = config_loader.build_config_section_change_preview(
        config_loader.DEFAULT_CONFIG,
        "memoria",
        {"enabled": True},
    )
    if not preview["changed"] or not preview["updated_config"]["memoria"]["enabled"]:
        _fail(f"Preview config no detecta cambio de memoria: {preview}")

    section_updates = {
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
    if tuple(section_updates) != expected_sections:
        _fail(f"Matriz config desalineada: {tuple(section_updates)}")

    stack_fixtures = {
        "node-typescript": {
            "files": {
                "package.json": json.dumps({"dependencies": {"next": "^15.0.0"}}),
                "tsconfig.json": "{}",
            },
            "expected": {"runtime": "node", "lenguaje": "typescript", "framework": "next"},
        },
        "python": {
            "files": {"requirements.txt": "fastapi==0.110.0\npytest==8.0.0\n"},
            "expected": {"runtime": "python", "lenguaje": "python", "framework": "fastapi"},
        },
        "rust": {
            "files": {"Cargo.toml": "[package]\nname = \"demo\"\n"},
            "expected": {"runtime": "rust", "lenguaje": "rust"},
        },
        "go": {
            "files": {"go.mod": "module example.com/demo\n"},
            "expected": {"runtime": "go", "lenguaje": "go"},
        },
        "ruby": {
            "files": {"Gemfile": "source 'https://rubygems.org'\n"},
            "expected": {"runtime": "ruby", "lenguaje": "ruby"},
        },
        "elixir": {
            "files": {"mix.exs": "defmodule Demo.MixProject do\nend\n"},
            "expected": {"runtime": "elixir", "lenguaje": "elixir"},
        },
        "java": {
            "files": {
                "pom.xml": (
                    "<project><dependencies>"
                    "<dependency><groupId>org.springframework.boot</groupId>"
                    "<artifactId>spring-boot-starter-web</artifactId></dependency>"
                    "</dependencies></project>"
                ),
            },
            "expected": {"runtime": "jvm", "lenguaje": "java", "framework": "spring-boot"},
        },
        "kotlin": {
            "files": {
                "build.gradle.kts": (
                    "plugins { kotlin(\"jvm\") version \"2.0.0\" }\n"
                    "dependencies { implementation(\"io.quarkus:quarkus-rest\") }\n"
                ),
            },
            "expected": {"runtime": "jvm", "lenguaje": "kotlin", "framework": "quarkus"},
        },
        "php": {
            "files": {
                "composer.json": json.dumps({"require": {"laravel/framework": "^11.0"}}),
            },
            "expected": {"runtime": "php", "lenguaje": "php", "framework": "laravel"},
        },
        "dotnet": {
            "files": {"App.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"></Project>'},
            "expected": {"runtime": "dotnet", "lenguaje": "csharp", "framework": "aspnet"},
        },
        "swift": {
            "files": {
                "Package.swift": (
                    "let package = Package("
                    "dependencies: [.package(url: \"https://github.com/vapor/vapor\", from: \"4.0.0\")])"
                ),
            },
            "expected": {"runtime": "swift", "lenguaje": "swift", "framework": "vapor"},
        },
    }
    with tempfile.TemporaryDirectory(prefix="alfred-stack-audit-") as tmp:
        tmp_path = Path(tmp)
        for fixture_name, fixture in stack_fixtures.items():
            project_path = tmp_path / fixture_name
            project_path.mkdir()
            for relative_path, content in fixture["files"].items():
                target = project_path / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            stack = config_loader.detect_stack(str(project_path))
            for key, expected_value in fixture["expected"].items():
                actual = stack.get(key)
                if actual != expected_value:
                    _fail(
                        "Deteccion de stack prometido desalineada: "
                        f"{fixture_name}.{key}={actual!r} != {expected_value!r}"
                    )

    with tempfile.TemporaryDirectory(prefix="alfred-config-audit-") as tmp:
        config_path = Path(tmp) / "alfred-dev.local.md"
        config_path.write_text(
            "---\n"
            "memoria:\n"
            "  enabled: false\n"
            "---\n\n"
            "## Notas\n\n"
            "Nota estable.\n",
            encoding="utf-8",
        )
        for section_name, values in section_updates.items():
            section_preview = config_loader.build_config_section_change_preview(
                config_loader.DEFAULT_CONFIG,
                section_name,
                values,
            )
            if not section_preview["changed"]:
                _fail(f"Preview config no detecta cambio en {section_name}: {section_preview}")
            for key, value in values.items():
                actual = section_preview["updated_config"][section_name].get(key)
                if actual != value:
                    _fail(
                        "Preview config no aplica valor "
                        f"{section_name}.{key}: {actual!r} != {value!r}"
                    )

            persisted_preview = config_loader.update_config_section(
                str(config_path),
                section_name,
                values,
                include_defaults=False,
            )
            if persisted_preview["section"] != section_name:
                _fail(
                    "Persistencia config devuelve seccion incorrecta: "
                    f"{persisted_preview}"
                )
            reloaded = config_loader.load_config(str(config_path))
            for key, value in values.items():
                actual = reloaded[section_name].get(key)
                if actual != value:
                    _fail(
                        "Persistencia config no conserva valor "
                        f"{section_name}.{key}: {actual!r} != {value!r}"
                    )
            if "Nota estable" not in reloaded.get("notas", ""):
                _fail(f"Persistencia config pierde notas tras {section_name}")

    command_norm = _normalize(_read("commands/ajustes.md"))
    docs_norm = _normalize(_read("docs/configuration.md"))
    architecture = _read("docs/architecture.md")
    assert_prompt_examples_use_current_ask_user_question_schema(
        "commands/ajustes.md",
        _read("commands/ajustes.md"),
    )
    assert_prompt_examples_use_current_ask_user_question_schema(
        "commands/_composicion.md",
        _read("commands/_composicion.md"),
    )
    required_human_labels = [
        "autonomia por fase",
        "proyecto",
        "agentes opcionales",
        "memoria persistente",
        "compliance",
        "integraciones",
        "personalidad",
    ]
    missing: list[str] = []
    for label in required_human_labels:
        if label not in command_norm:
            missing.append(f"commands/config.md: {label}")
        if label not in docs_norm:
            missing.append(f"docs/configuration.md: {label}")

    helper_names = [
        "build_config_section_summaries()",
        "build_config_section_menu()",
        "apply_config_section_update()",
        "build_config_section_change_preview()",
        "update_config_section()",
        "update_project_config_section()",
    ]
    for helper_name in helper_names:
        if helper_name not in _read("commands/ajustes.md"):
            missing.append(f"commands/config.md: {helper_name}")
        if helper_name not in _read("docs/configuration.md"):
            missing.append(f"docs/configuration.md: {helper_name}")
        if helper_name not in architecture:
            missing.append(f"docs/architecture.md: {helper_name}")

    for needle in ("questions[]", "multiselect: false"):
        if needle not in docs_norm:
            missing.append(f"docs/configuration.md: {needle}")

    if missing:
        _fail("Contratos config incompletos: " + "; ".join(missing))

    return [
        "7 secciones config alineadas con runtime",
        "deteccion automatica cubre stacks prometidos",
        "menu config principal expone salida y secciones canonicas",
        "preview config antes/despues operativo",
        "7 secciones config con round-trip preview/persistencia",
        "docs y comando config cubren helpers canonicos",
        "AskUserQuestion config/optional usa questions[] y multiSelect actuales",
    ]


def check_flow_gate_claims() -> list[str]:
    """Ejercita claims publicos de flujos, Selina, gates y autopilot."""
    from core.config_loader import has_frontend
    from core.orchestrator import (
        FLOWS,
        advance_phase,
        check_gate,
        create_session,
        is_autopilot_gate_passable,
    )

    problems: list[str] = []
    flows_doc = _read("docs/flows.md")
    configuration_doc = _read("docs/configuration.md")
    readme = _read("README.md")
    has_site = _has_site()

    free_gate_doc_requirements = {
        "docs/flows.md": (
            "evidencia directa del artefacto o checklist esperado",
            "no la convierte en una aprobacion incondicional",
            "Docs completas, gate libre con evidencia",
        ),
        "docs/configuration.md": (
            "Requiere resultado favorable y evidencia/checklist; no pide aprobacion humana.",
        ),
        "README.md": (
            "Todos los artefactos están documentados con checklist/evidencia revisable",
        ),
    }
    free_gate_sources = {
        "docs/flows.md": flows_doc,
        "docs/configuration.md": configuration_doc,
        "README.md": readme,
    }
    for path, needles in free_gate_doc_requirements.items():
        for needle in needles:
            if needle not in free_gate_sources[path]:
                problems.append(f"{path}: gate libre/documentacion sin contrato honesto {needle!r}")
    stale_free_gate_claims = {
        "docs/flows.md": (
            "Se supera siempre que el resultado sea favorable.",
            "Avance automático con gate libre",
        ),
        "docs/configuration.md": (
            "Se supera siempre que el resultado sea favorable.",
        ),
        "README.md": (
            "Todos los artefactos están documentados |",
        ),
    }
    for path, needles in stale_free_gate_claims.items():
        for needle in needles:
            if needle in free_gate_sources[path]:
                problems.append(f"{path}: claim de gate libre demasiado laxo {needle!r}")
    public_gate_sources = {
        "README.md": readme,
        "docs/README.md": _read("docs/README.md"),
        "docs/agents/README.md": _read("docs/agents/README.md"),
        "docs/hooks.md": _read("docs/hooks.md"),
        "docs/release.md": _read("docs/release.md"),
    }
    public_gate_requirements = {
        "README.md": (
            "quality gates verificables",
            "Autopilot solo resuelve gates de usuario configuradas",
            "no salta tests, seguridad, evidencia ni confirmación humana de despliegue",
        ),
        "docs/README.md": ("quality gates verificables con evidencia",),
        "docs/agents/README.md": ("quality gates verificables con evidencia",),
        "docs/hooks.md": ("quality gates verificables con evidencia",),
        "docs/release.md": ("quality gates son verificables por contrato local",),
    }
    if has_site:
        public_gate_sources["site/src/i18n/data.en.ts"] = _read("site/src/i18n/data.en.ts")
        public_gate_requirements["site/src/i18n/data.en.ts"] = (
            "quality gates that require evidence before work can close",
        )
    for path, needles in public_gate_requirements.items():
        for needle in needles:
            if needle not in public_gate_sources[path]:
                problems.append(f"{path}: claim de gates sin evidencia verificable {needle!r}")
    public_gate_stale = {
        "README.md": (
            "quality gates infranqueables",
            "No hay excepciones, no hay modo de saltárselas",
        ),
        "docs/README.md": ("quality gates infranqueables",),
        "docs/agents/README.md": ("quality gates infranqueables",),
        "docs/hooks.md": ("quality gates infranqueables",),
        "docs/release.md": ("quality gates son infranqueables",),
    }
    if has_site:
        public_gate_stale["site/src/i18n/data.en.ts"] = ("quality gates the workflow cannot skip",)
    for path, needles in public_gate_stale.items():
        for needle in needles:
            if needle in public_gate_sources[path]:
                problems.append(f"{path}: claim absoluto de gate sin matiz de evidencia {needle!r}")

    feature_phases = FLOWS["feature"]["fases"]
    if len(feature_phases) != 7:
        problems.append(f"feature debe tener 7 fases, tiene {len(feature_phases)}")
    estilo = feature_phases[1] if len(feature_phases) > 1 else {}
    expected_style_contract = {
        "nombre": "estilo_visual",
        "agentes": ["selina"],
        "gate_tipo": "usuario",
        "condicion": "tiene_frontend",
    }
    for key, expected in expected_style_contract.items():
        if estilo.get(key) != expected:
            problems.append(f"estilo_visual.{key}={estilo.get(key)!r} != {expected!r}")

    if not has_frontend({"framework": "next", "runtime": "node"}):
        problems.append("has_frontend no reconoce Next como frontend")
    if has_frontend({"framework": "fastapi", "runtime": "python"}):
        problems.append("has_frontend trata FastAPI como frontend")

    frontend_session = create_session(
        "feature",
        "Panel con UI",
        stack={"runtime": "node", "framework": "next"},
    )
    frontend_session = advance_phase(frontend_session, resultado="aprobado")
    if frontend_session["fase_actual"] != "estilo_visual":
        problems.append("feature con frontend no entra en estilo_visual tras producto")

    backend_session = create_session(
        "feature",
        "API sin UI",
        stack={"runtime": "python", "framework": "fastapi"},
    )
    backend_session = advance_phase(backend_session, resultado="aprobado")
    skipped_style = [
        phase
        for phase in backend_session.get("fases_completadas", [])
        if phase.get("nombre") == "estilo_visual"
    ]
    if backend_session["fase_actual"] != "arquitectura" or not skipped_style:
        problems.append("feature sin frontend no salta estilo_visual hacia arquitectura")
    elif skipped_style[0].get("resultado") != "saltada":
        problems.append(f"estilo_visual saltada registra resultado inesperado: {skipped_style[0]}")

    gate_session = create_session("feature", "Gates estrictas")
    gate_session = advance_phase(gate_session, resultado="aprobado")
    gate_session = advance_phase(gate_session, resultado="aprobado")
    gate_session = advance_phase(gate_session, resultado="aprobado")
    if check_gate(gate_session, resultado="aprobado", tests_ok=False)["passed"]:
        problems.append("gate automatica de desarrollo no bloquea tests rojos")
    gate_session = advance_phase(gate_session, resultado="aprobado", tests_ok=True)
    if check_gate(gate_session, resultado="aprobado", security_ok=False)["passed"]:
        problems.append("gate automatico+seguridad de calidad no bloquea seguridad KO")

    autopilot_session = create_session("feature", "Autopilot")
    autopilot_session["autopilot"] = True
    if not is_autopilot_gate_passable(autopilot_session)["passed"]:
        problems.append("autopilot no aprueba gate de usuario")
    autopilot_session = advance_phase(autopilot_session, resultado="aprobado")
    autopilot_session = advance_phase(autopilot_session, resultado="aprobado")
    autopilot_session = advance_phase(autopilot_session, resultado="aprobado")
    if is_autopilot_gate_passable(autopilot_session, tests_ok=False)["passed"]:
        problems.append("autopilot salta gate automatica con tests rojos")

    ship_session = create_session("ship", "Release autopilot")
    ship_session["autopilot"] = True
    ship_session = advance_phase(ship_session, resultado="aprobado", tests_ok=True, security_ok=True)
    ship_session = advance_phase(ship_session, resultado="aprobado")
    ship_session = advance_phase(ship_session, resultado="aprobado", tests_ok=True, security_ok=True)
    ship_gate = is_autopilot_gate_passable(ship_session, security_ok=True)
    if ship_session["fase_actual"] != "despliegue":
        problems.append(f"ship no llega a despliegue en la fase esperada: {ship_session['fase_actual']}")
    if ship_gate["passed"] or "confirmación explícita del usuario" not in ship_gate.get("reason", ""):
        problems.append("ship autopilot no conserva confirmacion humana de despliegue")

    if problems:
        _fail("Claims de flujos/gates desalineados: " + "; ".join(problems))

    return [
        "feature mantiene 7 fases con Selina condicional",
        "Selina se ejecuta solo con frontend y se salta con backend",
        "gates libres documentadas como evidencia sin aprobacion humana",
        "gates automaticas bloquean tests rojos y seguridad KO",
        "autopilot no salta gates automaticas ni despliegue humano",
    ]


def check_hook_contracts() -> list[str]:
    """Verifica que hooks.json siga el contrato moderno de Claude Code."""
    hooks_config = _json("hooks/hooks.json")
    hooks_by_event = hooks_config.get("hooks")
    if not isinstance(hooks_by_event, dict):
        _fail("hooks/hooks.json no declara hooks")

    expected_events = {
        "SessionStart",
        "SessionEnd",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
    }
    actual_events = set(hooks_by_event)
    if actual_events != expected_events:
        missing_events = sorted(expected_events - actual_events)
        extra_events = sorted(actual_events - expected_events)
        _fail(
            "Eventos de hooks desalineados: "
            f"actual={sorted(hooks_by_event)} missing={missing_events} extra={extra_events}"
        )

    visible_scripts = sorted(
        path.name
        for path in (ROOT / "hooks").iterdir()
        if path.is_file()
        and path.suffix in {".py", ".sh"}
        and path.name not in {"evidence_guard_lib.py", "secret-guard.sh"}
    )
    if len(visible_scripts) != 10:
        _fail(f"Hooks visibles inesperados: {visible_scripts}")

    registered: list[tuple[str, str, dict]] = []
    problems: list[str] = []
    for event, groups in hooks_by_event.items():
        if not isinstance(groups, list) or not groups:
            problems.append(f"{event}: debe contener grupos")
            continue
        for group in groups:
            if not isinstance(group, dict):
                problems.append(f"{event}: grupo no es objeto")
                continue
            if event in HOOK_EVENTS_WITHOUT_MATCHER and "matcher" in group:
                problems.append(
                    f"{event}: declara matcher que Claude Code ignora en este evento"
                )
            for hook in group.get("hooks", []):
                if not isinstance(hook, dict) or hook.get("type") != "command":
                    problems.append(f"{event}: hook no command")
                    continue
                if "if" in hook:
                    if event not in HOOK_EVENTS_WITH_IF_SUPPORT:
                        problems.append(
                            f"{event}: declara if que Claude Code no evalua en este evento"
                        )
                    elif not isinstance(hook["if"], str) or not hook["if"].strip():
                        problems.append(f"{event}: if debe ser string no vacio")
                command = hook.get("command")
                args = hook.get("args")
                if not isinstance(command, str) or not command:
                    problems.append(f"{event}: command invalido")
                    continue
                if "|| true" in command or "test -f" in command:
                    problems.append(f"{event}: command shell neutraliza errores: {command}")
                if "${CLAUDE_PLUGIN_ROOT}" in command:
                    problems.append(f"{event}: usa placeholder en command en vez de args: {command}")
                if not isinstance(args, list) or len(args) != 1 or not isinstance(args[0], str):
                    problems.append(f"{event}: hook sin args exec form para {command}")
                    continue
                script_arg = args[0]
                prefix = "${CLAUDE_PLUGIN_ROOT}/hooks/"
                if not script_arg.startswith(prefix):
                    problems.append(f"{event}: args no apunta a hooks/: {script_arg}")
                    continue
                script_name = script_arg.removeprefix(prefix)
                script_path = ROOT / "hooks" / script_name
                if not script_path.is_file():
                    problems.append(f"{event}: script no existe {script_name}")
                    continue
                if script_name.endswith(".py") and command != "python3":
                    problems.append(f"{script_name}: debe usar command python3")
                if script_name.endswith(".sh") and command != "bash":
                    problems.append(f"{script_name}: debe usar command bash")
                if "async" in hook and not isinstance(hook["async"], bool):
                    problems.append(f"{script_name}: async debe ser booleano")
                timeout = hook.get("timeout")
                if hook.get("async") is not True:
                    if type(timeout) is not int:
                        problems.append(f"{script_name}: hook sincronico sin timeout entero")
                    elif timeout > HOOK_SYNC_TIMEOUT_LIMIT:
                        problems.append(
                            f"{script_name}: hook sincronico supera timeout "
                            f"{HOOK_SYNC_TIMEOUT_LIMIT}s ({timeout}s)"
                        )
                registered.append((event, script_name, hook))

    registered_names = {script_name for _, script_name, _ in registered}
    missing = sorted(set(visible_scripts) - registered_names)
    extras = sorted(registered_names - set(visible_scripts))
    if missing:
        problems.append(f"scripts sin registrar: {missing}")
    if extras:
        problems.append(f"scripts registrados inesperados: {extras}")

    blocking = {
        "secret-guard.py",
        "dangerous-command-guard.py",
    }
    for script_name in blocking:
        matches = [
            (event, hook)
            for event, registered_script, hook in registered
            if registered_script == script_name
        ]
        if not matches:
            problems.append(f"{script_name}: no registrado")
            continue
        for event, hook in matches:
            if event != "PreToolUse":
                problems.append(f"{script_name}: debe registrarse en PreToolUse, no {event}")
            if hook.get("async"):
                problems.append(f"{script_name}: no puede ser async")
            if hook.get("timeout", 99) > 5:
                problems.append(f"{script_name}: timeout debe ser <= 5")

    for path in sorted((ROOT / "hooks").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

    for path in sorted((ROOT / "hooks").glob("*.sh")):
        result = subprocess.run(
            ["bash", "-n", str(path)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode != 0:
            problems.append(f"{_rel(path)}: bash -n fallo: {result.stdout}")

    wrapper_needles = (
        "EMBEDDED_PLUGIN_ROOT",
        "CLAUDE_PLUGIN_ROOT",
        "ALFRED_DEV_PLUGIN_ROOT",
        "def _cache_candidates():",
        "core/continuity.py",
    )
    for script_name in ("session-bootstrap.sh",):
        source = _read(f"hooks/{script_name}")
        for needle in wrapper_needles:
            if needle not in source:
                problems.append(f"{script_name}: wrapper no contiene {needle}")

    hooks_doc = _read("docs/hooks.md")
    if '"decisión": "block"' in hooks_doc:
        problems.append("docs/hooks.md usa clave obsoleta \"decisión\" en vez de decision")
    nested_hook_output = re.findall(
        r"hookSpecificOutput\.(?:"
        r"SessionStart|UserPromptSubmit|UserPromptExpansion|Stop|PreToolUse|PreCompact|PostToolUse|"
        r"PostToolUseFailure|PostToolBatch|PermissionRequest|Notification|"
        r"Setup|SubagentStart"
        r")\.[A-Za-z]",
        hooks_doc,
    )
    if nested_hook_output:
        problems.append(
            "docs/hooks.md usa hookSpecificOutput anidado por evento: "
            f"{sorted(set(nested_hook_output))}"
        )
    for needle in (
        '"decision": "block"',
        "hookSpecificOutput.hookEventName",
        "hookSpecificOutput.additionalContext",
        "systemMessage",
        "Claude Code ignora `matcher`",
        "El campo `if` solo se evalua en eventos de herramientas",
        "`manual\\|auto` omitido para cubrir ambos",
        "Claude Code ignora cualquier JSON cuando el proceso sale con `2`",
        "no mezcles JSON de control con `exit 2`",
    ):
        if needle not in hooks_doc:
            problems.append(f"docs/hooks.md no documenta contrato moderno de hooks: {needle}")
    if "Los hooks sincronos no deben superar los 10 segundos" not in hooks_doc:
        problems.append("docs/hooks.md no documenta limite de timeout sincronico")

    direct_checks = [
        (
            "secret-guard invalid json",
            ["bash", str(ROOT / "hooks" / "secret-guard.sh")],
            "not-json",
        ),
        (
            "dangerous-command invalid json",
            [sys.executable, str(ROOT / "hooks" / "dangerous-command-guard.py")],
            "not-json",
        ),
        (
            "dangerous-command rm root",
            [sys.executable, str(ROOT / "hooks" / "dangerous-command-guard.py")],
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": "rm -rf /"},
                }
            ),
        ),
    ]
    for name, command, stdin in direct_checks:
        result = subprocess.run(
            command,
            cwd=ROOT,
            input=stdin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
        if result.returncode != 2:
            problems.append(
                f"{name}: esperaba exit 2, obtuvo {result.returncode}; "
                f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
        if result.stdout:
            problems.append(
                f"{name}: un hook con exit 2 no debe emitir JSON/stdout "
                f"porque Claude Code lo ignora: {result.stdout!r}"
            )

    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        (project / ".claude").mkdir()
        (project / ".claude" / "alfred-prefetch.json").write_text(
            json.dumps(
                {
                    "source_command": "alfred",
                    "prefetched_command": "map-codebase",
                    "response_text": "prefetch listo",
                    "expires_at": "2999-01-01T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )
        pass

    if problems:
        _fail("Contratos de hooks incompletos: " + "; ".join(problems))

    return [
        "10 hooks visibles registrados",
        "scripts de hooks declarados existen y cubren los 9 visibles",
        "exec form sin shell wrappers ni rutas sin comillas",
        "hooks bloqueantes conservan exit 2",
        "hooks con exit 2 no emiten JSON ignorado por Claude Code",
        "eventos SessionStart, SessionEnd, UserPromptSubmit, PreToolUse y PostToolUse",
        "eventos sin matcher no declaran matcher ignorado",
        "hooks no usan if fuera de eventos de herramienta",
        "hooks sincronos declaran timeout entero <= 10 segundos",
        "sintaxis de hooks validada",
        "wrapper helper-first resiliente a cache de plugin rotada",
        "docs de hooks usan decision/hookSpecificOutput actuales",
    ]


def check_mcp_config() -> list[str]:
    mcp = _json(".mcp.json")
    server = mcp.get("mcpServers", {}).get("alfred-memory")
    if not isinstance(server, dict):
        _fail(".mcp.json no declara mcpServers.alfred-memory")
    if server.get("command") != "python3":
        _fail("alfred-memory debe arrancar con command python3 para que los instaladores puedan parchearlo")
    args = server.get("args")
    if not isinstance(args, list) or not args or "memory_server.py" not in str(args[0]):
        _fail("alfred-memory debe apuntar a mcp/memory_server.py")
    if "${CLAUDE_PLUGIN_ROOT}" not in str(args[0]):
        _fail("alfred-memory debe usar CLAUDE_PLUGIN_ROOT")

    return ["MCP raiz portable con memory_server.py"]


def _npm_pack_dry_run_package() -> dict:
    completed = subprocess.run(
        ["npm", "pack", "--dry-run", "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        _fail(f"npm pack --dry-run fallo: {completed.stderr.strip()}")

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        _fail(f"npm pack no devolvio JSON valido: {exc}: {completed.stdout[:500]}")
    if not isinstance(payload, list) or not payload:
        _fail(f"npm pack devolvio payload inesperado: {payload!r}")
    package = payload[0]
    if not isinstance(package, dict):
        _fail(f"npm pack devolvio paquete inesperado: {package!r}")
    return package


def _publishable_symlink_problems() -> list[str]:
    problems: list[str] = []
    root = ROOT.resolve()
    for root_name in PUBLISHABLE_SYMLINK_ROOTS:
        root_path = ROOT / root_name
        if not root_path.exists() and not root_path.is_symlink():
            continue
        candidates = [root_path]
        if root_path.is_dir() and not root_path.is_symlink():
            candidates.extend(root_path.rglob("*"))
        for path in candidates:
            if not path.is_symlink():
                continue
            try:
                target = path.resolve(strict=True)
            except FileNotFoundError:
                problems.append(f"{_rel(path)} es un symlink roto")
                continue
            try:
                target.relative_to(root)
            except ValueError:
                problems.append(
                    f"{_rel(path)} es un symlink fuera del plugin: {os.readlink(path)!r}"
                )
    return problems


def check_packaging_contracts() -> list[str]:
    """Verifica el paquete real que produciría npm antes de publicar."""
    package = _npm_pack_dry_run_package()
    if package.get("name") != "alfred-dev" or package.get("version") != VERSION:
        _fail(f"npm pack empaqueta identidad inesperada: {package}")

    packed_paths = {
        entry.get("path")
        for entry in package.get("files", [])
        if isinstance(entry, dict)
    }
    required_paths = {
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        ".mcp.json",
        "commands/_composicion.md",
        "commands/alfred.md",
        "agents/alfred.md",
        "hooks/hooks.json",
        "mcp/memory_server.py",
        "core/continuity.py",
        "scripts/release_audit.py",
        "visual/scripts/frame-template.html",
        "visual/scripts/helper.js",
        "visual/scripts/read-choice.py",
        "visual/scripts/server.cjs",
        "visual/scripts/start-server.sh",
        "visual/scripts/stop-server.sh",
        "visual/scripts/write-guided-style-options.py",
        "visual/scripts/write-style-demo-gallery.py",
        "visual/scripts/write-style-direction.py",
        "visual/scripts/write-style-options.py",
        "visual/scripts/write-style-selector.py",
    }
    required_paths.update(TEMPLATE_PATHS)
    missing_required = sorted(required_paths - packed_paths)
    if missing_required:
        _fail(f"npm pack no incluye artefactos criticos: {missing_required}")

    forbidden_prefixes = (
        ".alfred-dev/",
        ".claude/",
        ".crupier/",
        ".git/",
        ".pytest_cache/",
        "docs/manual-smoke",
        "node_modules/",
        "site/.astro/",
        "site/dist/",
        "site/node_modules/",
        "tests/",
    )
    forbidden_suffixes = (
        ".pyc",
        ".pyo",
    )
    leaked = sorted(
        path for path in packed_paths
        if path and (
            path.startswith(forbidden_prefixes)
            or any(part == "__pycache__" for part in path.split("/"))
            or path.endswith(forbidden_suffixes)
        )
    )
    if leaked:
        _fail(f"npm pack incluye artefactos locales o de test: {leaked[:20]}")
    symlink_problems = _publishable_symlink_problems()
    if symlink_problems:
        _fail("Symlinks publicables incompatibles con la cache de Claude: " + "; ".join(symlink_problems))

    manifest_command_paths = {
        path.lstrip("./")
        for path in _json(".claude-plugin/plugin.json")["commands"]
    }
    public_command_paths = [
        path for path in packed_paths
        if path in manifest_command_paths
    ]
    agent_paths = [
        path for path in packed_paths
        if path.startswith("agents/") and path.endswith(".md")
    ]
    skill_paths = [
        path for path in packed_paths
        if path.startswith("skills/") and path.endswith("/SKILL.md")
    ]
    template_paths = [
        path for path in packed_paths
        if path.startswith("templates/") and path.endswith(".md")
    ]
    if len(public_command_paths) != 18 or len(agent_paths) != 10 or len(skill_paths) != 11:
        _fail(
            "npm pack desalineado con inventario publico: "
            f"commands={len(public_command_paths)} agents={len(agent_paths)} skills={len(skill_paths)}"
        )
    if sorted(template_paths) != sorted(TEMPLATE_PATHS):
        _fail(
            "npm pack desalineado con templates de artefactos: "
            f"{sorted(template_paths)}"
        )

    return [
        f"npm pack dry-run {VERSION} valido",
        "paquete sin caches locales ni tests",
        "paquete sin .claude/.crupier ni evidencias manuales",
        "paquete sin symlinks publicables fuera del plugin",
        "paquete contiene 18 comandos namespaced, 10 agentes y 11 skills",
        "paquete contiene 8 templates de artefactos",
        "paquete contiene runtime visual de Selina",
    ]


def check_published_secret_scan() -> list[str]:
    """Escanea el artefacto publicable para detectar secretos reales."""
    from core.secrets import find_secret_label

    package = _npm_pack_dry_run_package()
    packed_paths = {
        entry.get("path")
        for entry in package.get("files", [])
        if isinstance(entry, dict)
    }
    findings: list[str] = []
    for relative in sorted(path for path in packed_paths if isinstance(path, str)):
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        label = find_secret_label(text)
        if label:
            findings.append(f"{relative}: {label}")

    if findings:
        _fail(
            "El paquete publicable contiene posibles secretos reales: "
            + "; ".join(findings[:20])
        )

    return ["paquete publicable sin patrones de secretos reales"]


def check_install_update_contracts() -> list[str]:
    """Verifica instalación, desinstalación y update con scopes explícitos."""
    install_sh = _read("install.sh")
    install_ps1 = _read("install.ps1")
    uninstall_sh = _read("uninstall.sh")
    uninstall_ps1 = _read("uninstall.ps1")
    update_command = _read("commands/update.md")
    installation_docs = _read("docs/installation.md")

    requirements = {
        "install.sh": [
            'claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope local',
            'claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope project',
            'claude plugin marketplace remove "${PLUGIN_NAME}" --scope local',
            'claude plugin marketplace remove "${PLUGIN_NAME}" --scope project',
            'claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope user',
            'claude plugin marketplace remove "${PLUGIN_NAME}" --scope user',
            'claude plugin marketplace add "${REPO}" --scope user',
            'claude plugin install "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope user',
            "claude plugin list --json",
            "Instalacion global de usuario confirmada (--scope user)",
            "No se pisa ~/.claude/skills",
            'HOOKS_JSON="${PLUGIN_ROOT}/hooks/hooks.json"',
            'MCP_JSON="${PLUGIN_ROOT}/.mcp.json"',
            "/reload-plugins",
            "MCP/coste de cache",
        ],
        "install.ps1": [
            "claude plugin uninstall $PluginKey --scope local",
            "claude plugin uninstall $PluginKey --scope project",
            "claude plugin marketplace remove $PluginName --scope local",
            "claude plugin marketplace remove $PluginName --scope project",
            "claude plugin uninstall $pluginKey --scope user",
            "claude plugin marketplace remove $PluginName --scope user",
            "claude plugin marketplace add $Repo --scope user",
            "claude plugin install $pluginKey --scope user",
            "claude plugin list --json",
            "Instalacion global de usuario confirmada (--scope user)",
            "No se pisa ~/.claude/skills",
            'Join-Path $PluginRoot "hooks/hooks.json"',
            'Join-Path $PluginRoot ".mcp.json"',
            "/reload-plugins",
            "MCP/coste de cache",
        ],
        "uninstall.sh": [
            'claude plugin uninstall "${PLUGIN_KEY}" --scope user',
            'claude plugin marketplace remove "${PLUGIN_NAME}" --scope user',
            'known_marketplaces.json',
            'installed_plugins.json',
            'enabledPlugins',
            "Alias global /alfred eliminado",
            "Shim de comando global /alfred eliminado",
        ],
        "uninstall.ps1": [
            "claude plugin uninstall $PluginKey --scope user",
            "claude plugin marketplace remove $PluginName --scope user",
            "known_marketplaces.json",
            "installed_plugins.json",
            "enabledPlugins",
            "Alias global /alfred eliminado",
            "Shim de comando global /alfred eliminado",
        ],
        "commands/update.md": [
            "claude plugin list --json",
            "semver real",
            "un único `AskUserQuestion`",
            "Actualizar ahora",
            "Ahora no",
            "normaliza a `--scope user`",
            "no pisa `~/.claude/skills`",
            "No uses `claude plugin update --scope local`",
            "`claude plugin update --scope project`",
            "curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash",
            "ejecutar **`/reload-plugins`**",
            "`/reload-plugins --force`",
            "entonces debe reiniciar",
        ],
        "docs/installation.md": [
            "--scope user",
            "instalación global de usuario",
            "No pisa",
            "~/.claude/commands/alfred.md",
            "claude plugin list --json",
            "No usa un marketplace oficial de Anthropic",
            "`/reload-plugins` aplica los cambios",
            "`/reload-plugins --force`",
        ],
    }
    sources = {
        "install.sh": install_sh,
        "install.ps1": install_ps1,
        "uninstall.sh": uninstall_sh,
        "uninstall.ps1": uninstall_ps1,
        "commands/update.md": update_command,
        "docs/installation.md": installation_docs,
    }
    missing = []
    for path, needles in requirements.items():
        for needle in needles:
            if needle not in sources[path]:
                missing.append(f"{path}: {needle}")
    if missing:
        _fail("Contratos install/update incompletos: " + "; ".join(missing))

    stateful_plugin_command = re.compile(
        r"\bclaude plugin "
        r"(?:(?:marketplace\s+(?:add|remove))|(?:install|uninstall|update))\b"
    )
    bad_scope = []
    for path in ("install.sh", "install.ps1", "uninstall.sh", "uninstall.ps1"):
        for line_number, line in enumerate(sources[path].splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not stateful_plugin_command.search(stripped):
                continue
            scope_match = re.search(r"--scope\s+([A-Za-z_$\{\}]+)", stripped)
            if not scope_match:
                bad_scope.append(f"{path}:{line_number}: {stripped}")
                continue
            scope = scope_match.group(1).strip("${}").lstrip("$")
            if scope == "user":
                continue
            is_cleanup = (
                path in {"install.sh", "install.ps1"}
                and scope in {"local", "project"}
                and (
                    "plugin uninstall" in stripped
                    or "plugin marketplace remove" in stripped
                )
            )
            if not is_cleanup:
                bad_scope.append(f"{path}:{line_number}: scope {scope} prohibido")
    if bad_scope:
        _fail(
            "CLI plugin sin scope explicito user o limpieza local/project permitida: "
            + "; ".join(bad_scope)
        )

    if "instalación local que limpiar" in uninstall_sh:
        _fail("uninstall.sh no debe describir Alfred Dev como instalacion local")

    return [
        "instaladores usan scope user explicito",
        "instaladores verifican scope user despues de instalar",
        "instaladores limpian scopes local/project heredados antes de instalar user",
        "instaladores no pisan ~/.claude/skills ni instalan alias global /alfred",
        "update conserva semver y menu humano, normaliza a scope user y documenta reload/reinicio",
    ]


def check_audit_docs() -> list[str]:
    package = _json("package.json")
    readme = _read("README.md")
    docs_readme = _read("docs/README.md")
    architecture = _read("docs/architecture.md")
    install = _read("docs/installation.md")
    release_doc = _read("docs/release.md")
    gitignore = _read(".gitignore")
    npmignore = _read(".npmignore")

    required = {
        "README.md": [
            "Novedades en v0.7.0",
            "docs/release.md",
            "MCP stdio moderno",
        ],
        "docs/README.md": [
            "release.md",
            "11 skills",
            "18 comandos",
        ],
        "docs/installation.md": [
            "plugin:alfred-dev:alfred-memory",
            "Pending approval",
            "No hay que aprobar esa entrada de proyecto",
            'claude plugin marketplace add "$PWD" --scope user',
            "Claude Code actual sí ofrece diagnósticos útiles",
            "claude plugin details alfred-dev@alfred-dev",
            "claude plugin validate . --strict",
            "claude --debug",
            "/plugin validate",
        ],
        "docs/architecture.md": [
            "`matcher` es opcional",
            "solo se declara en eventos donde Claude Code lo soporta",
            "Claude Code lo ignora",
            "PreCompact",
            "manuales como automáticas",
        ],
        "docs/release.md": [
            "18 comandos",
            "10 agentes",
            "11 skills",
            "10 hooks",
            "displayName: \"Alfred Dev\"",
            "namespace técnico es `alfred-dev`",
            "no pisa `~/.claude/skills`",
            "`_composicion.md`",
            "`_docs_vivas.md`",
            "commands/ como skills planas soportadas",
            "UX pública",
            "`/alfred-dev:*`",
            "argument-hint",
            "$ARGUMENTS",
            "1.536 caracteres",
            "disable-model-invocation: true",
            "npm run release:audit",
            "npm run release:audit:manual",
            "npm run release:audit:manual:evidence",
            "npm run release:audit:prepublish",
            "18 rutas publicas",
            "40 opciones publicas",
            "4 contratos runtime",
            "--auth-preflight",
            "core/secrets.py",
            "permisos `0600`",
            "evidence_file",
            "evidence_sha256",
            "plugin_surface.sha256",
            "notes_low_quality",
            "notes_repeated",
            "--require-current-auth-preflight",
            "auth_preflight.status=ok",
            "scripts/manual_smoke.py",
            "scripts/external_live_smoke.py",
            "no crea issues, no arranca contenedores",
            "quality gates son verificables por contrato local",
            "questions[]",
            "multiSelect",
            "hookSpecificOutput.additionalContext",
            "No aprueba la release por sí mismo",
            "Pendientes que no cubre el contrato local",
            "claude auth login",
            "scripts/claude_auth_recovery.py",
        ],
    }
    sources = {
        "README.md": readme,
        "docs/README.md": docs_readme,
        "docs/architecture.md": architecture,
        "docs/installation.md": install,
        "docs/release.md": release_doc,
    }
    missing = []
    for path, needles in required.items():
        for needle in needles:
            if needle not in sources[path]:
                missing.append(f"{path}: {needle}")
    if re.search(r"PreCompact[^.\n]*(?:ignora|ignorado)", architecture):
        _fail("docs/architecture.md afirma incorrectamente que PreCompact ignora matcher")
    if 'displayName: "Alfred Dev"' not in release_doc:
        _fail("docs/release.md debe documentar displayName humano")
    if re.search(r"plugin_surface\.sha256=[0-9a-f]{64}", release_doc):
        _fail("docs/release.md no debe congelar plugin_surface.sha256")
    if "docs/manual-smoke*.json" not in gitignore:
        _fail(".gitignore debe excluir evidencias/reviews manuales docs/manual-smoke*.json")
    if "docs/manual-smoke*.json" not in npmignore:
        _fail(".npmignore debe excluir evidencias/reviews manuales docs/manual-smoke*.json")
    if "docs/manual-smoke*.md" not in gitignore:
        _fail(".gitignore debe excluir reportes manuales docs/manual-smoke*.md")
    if "docs/manual-smoke*.md" not in npmignore:
        _fail(".npmignore debe excluir reportes manuales docs/manual-smoke*.md")
    if "docs/project/" not in gitignore:
        _fail(".gitignore debe excluir estado operativo local docs/project/")
    if "docs/project/" not in npmignore:
        _fail(".npmignore debe excluir estado operativo local docs/project/")
    if "docs/external-live-smoke*.json" not in gitignore:
        _fail(".gitignore debe excluir evidencias externas docs/external-live-smoke*.json")
    if "docs/external-live-smoke*.json" not in npmignore:
        _fail(".npmignore debe excluir evidencias externas docs/external-live-smoke*.json")
    if "docs/claude-auth-recovery*.json" not in gitignore:
        _fail(".gitignore debe excluir diagnosticos de auth docs/claude-auth-recovery*.json")
    if "docs/claude-auth-recovery*.json" not in npmignore:
        _fail(".npmignore debe excluir diagnosticos de auth docs/claude-auth-recovery*.json")
    if missing:
        _fail(f"Documentacion de auditoria incompleta: {missing}")
    scripts = package.get("scripts", {})
    expected_scripts = {
        "release:audit:external:preflight": (
            "python3 scripts/external_live_smoke.py --output docs/external-live-smoke-0.7.0.json"
        ),
        "release:audit:claude:commands": "python3 scripts/claude_command_discovery.py",
        "release:audit:manual": "python3 scripts/manual_smoke.py",
        "release:audit:manual:evidence": (
            "python3 scripts/manual_smoke.py --auth-preflight --output docs/manual-smoke-0.7.0.json"
        ),
        "release:audit:manual:evidence:installed": (
            "python3 scripts/manual_smoke.py --installed --auth-preflight --output docs/manual-smoke-installed-0.7.0.json"
        ),
        "release:audit:manual:preflight": "python3 scripts/manual_smoke.py --auth-preflight --preflight-only",
        "release:audit:manual:preflight:diagnose": (
            "python3 scripts/manual_smoke.py --auth-preflight --preflight-only --allow-auth-failure"
        ),
        "release:audit:manual:auth:diagnose": "python3 scripts/claude_auth_recovery.py",
        "release:audit:manual:auth:strict": "python3 scripts/claude_auth_recovery.py --strict",
        "release:audit:manual:review:init": (
            "python3 scripts/manual_review_gate.py --init-template docs/manual-smoke-0.7.0.json docs/manual-smoke-review-0.7.0.json"
        ),
        "release:audit:manual:review": (
            "python3 scripts/manual_review_gate.py --require-current-auth-preflight --expect-plugin-source worktree docs/manual-smoke-0.7.0.json docs/manual-smoke-review-0.7.0.json"
        ),
        "release:audit:manual:report": (
            "python3 scripts/manual_review_report.py docs/manual-smoke-0.7.0.json docs/manual-smoke-review-0.7.0.json --output docs/manual-smoke-report-0.7.0.md"
        ),
        "release:audit:manual:review:installed:init": (
            "python3 scripts/manual_review_gate.py --init-template docs/manual-smoke-installed-0.7.0.json docs/manual-smoke-installed-review-0.7.0.json"
        ),
        "release:audit:manual:review:installed": (
            "python3 scripts/manual_review_gate.py --require-current-auth-preflight --expect-plugin-source installed-cache docs/manual-smoke-installed-0.7.0.json docs/manual-smoke-installed-review-0.7.0.json"
        ),
        "release:audit:manual:report:installed": (
            "python3 scripts/manual_review_report.py docs/manual-smoke-installed-0.7.0.json docs/manual-smoke-installed-review-0.7.0.json --output docs/manual-smoke-installed-report-0.7.0.md"
        ),
        "release:audit:prepublish:prepare": (
            "npm run release:audit:full && "
            "npm run release:audit:manual:evidence && "
            "npm run release:audit:manual:evidence:installed"
        ),
        "release:audit:prepublish": (
            "npm run release:audit:full && "
            "npm run release:audit:manual:preflight && "
            "npm run release:audit:manual:review && "
            "npm run release:audit:manual:review:installed"
        ),
    }
    bad_scripts = {
        name: {"actual": scripts.get(name), "expected": expected}
        for name, expected in expected_scripts.items()
        if scripts.get(name) != expected
    }
    if bad_scripts:
        _fail(f"Scripts npm de smoke manual desalineados: {bad_scripts}")
    if not (ROOT / "scripts" / "manual_smoke.py").is_file():
        _fail("Falta scripts/manual_smoke.py para reproducir la matriz manual")
    if not (ROOT / "scripts" / "manual_review_gate.py").is_file():
        _fail("Falta scripts/manual_review_gate.py para validar la revision humana")
    if not (ROOT / "scripts" / "external_live_smoke.py").is_file():
        _fail("Falta scripts/external_live_smoke.py para capturar preflight externo")
    if not (ROOT / "scripts" / "claude_command_discovery.py").is_file():
        _fail("Falta scripts/claude_command_discovery.py para probar /alfred-dev:alfred interactivo")
    if not (ROOT / "docs" / "release.md").is_file():
        _fail("Falta docs/release.md para auditar claims y readiness de salida")
    prepare = scripts.get("release:audit:prepublish:prepare", "")
    required_prepare_parts = (
        "npm run release:audit:full",
        "npm run release:audit:manual:evidence",
        "npm run release:audit:manual:evidence:installed",
    )
    missing_prepare = [
        part for part in required_prepare_parts if part not in prepare
    ]
    if missing_prepare:
        _fail(f"release:audit:prepublish:prepare incompleto: {missing_prepare}")

    prepublish = scripts.get("release:audit:prepublish", "")
    required_prepublish_parts = (
        "npm run release:audit:full",
        "npm run release:audit:manual:preflight",
        "npm run release:audit:manual:review",
        "npm run release:audit:manual:review:installed",
    )
    missing_prepublish = [
        part for part in required_prepublish_parts if part not in prepublish
    ]
    if missing_prepublish:
        _fail(f"release:audit:prepublish incompleto: {missing_prepublish}")
    prepublish_parts = {part.strip() for part in prepublish.split("&&")}
    forbidden_prepublish_parts = {
        "npm run release:audit:manual:evidence",
        "npm run release:audit:manual:evidence:installed",
    }
    forbidden_present = sorted(prepublish_parts & forbidden_prepublish_parts)
    if forbidden_present:
        _fail(
            "release:audit:prepublish no debe regenerar evidencias ya revisadas: "
            f"{forbidden_present}"
        )

    spec = importlib.util.spec_from_file_location(
        "manual_smoke_release_audit",
        ROOT / "scripts" / "manual_smoke.py",
    )
    if spec is None or spec.loader is None:
        _fail("No se pudo cargar scripts/manual_smoke.py para auditar cobertura")
    manual_smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manual_smoke)
    if "plugin_surface.sha256" not in release_doc:
        _fail("docs/release.md debe exigir plugin_surface.sha256 de la run, no un hash congelado")
    manual_smoke_text = _read("scripts/manual_smoke.py")
    manual_review_gate_text = _read("scripts/manual_review_gate.py")
    manual_review_report_text = _read("scripts/manual_review_report.py")
    manual_smoke_runtime_needles = (
        '"--permission-mode",',
        '"bypassPermissions",',
        'parser.add_argument("--budget", default="1.50"',
        'parser.add_argument(\n        "--preflight-only"',
        'if args.preflight_only:',
        'error_max_budget_usd',
    )
    missing_manual_smoke_runtime = [
        needle for needle in manual_smoke_runtime_needles if needle not in manual_smoke_text
    ]
    if missing_manual_smoke_runtime:
        _fail(
            "El smoke manual debe reproducir claude -p real sin permisos interactivos ni presupuesto bajo: "
            f"{missing_manual_smoke_runtime}"
        )
    preview_sanitizer_needles = (
        "from core.secrets import sanitize_text",
        "def _safe_preview(",
        "path.chmod(0o600)",
        "previews[relative] = _safe_preview(",
        '"response_preview": _safe_preview(response_text, 2000)',
        '"stderr_preview": _safe_preview(result.stderr, 2000)',
        '"response_preview": _safe_preview(response_text, 500)',
        '"stderr_preview": _safe_preview(result.stderr, 500)',
    )
    missing_preview_sanitizer = [
        needle for needle in preview_sanitizer_needles if needle not in manual_smoke_text
    ]
    if missing_preview_sanitizer:
        _fail(
            "La evidencia manual debe sanear previews con core/secrets.py: "
            f"{missing_preview_sanitizer}"
        )
    review_secret_gate_needles = (
        "from core.secrets import find_secret_label",
        "def _iter_secret_findings(",
        "evidence_secret_findings = _iter_secret_findings(evidence, \"evidence\")",
        "review_secret_findings = _iter_secret_findings(review, \"review\")",
        "evidence contiene posibles secretos reales",
        "review contiene posibles secretos reales",
        "No se crea plantilla de revisión con evidencia que contiene",
        "review_path.chmod(0o600)",
        "GENERIC_REVIEW_NOTES",
        "MIN_REVIEW_NOTE_CHARS",
        "MIN_REVIEW_NOTE_WORDS",
        "def _is_low_quality_review_note(",
        "review.cases con notes humanas demasiado genericas o cortas",
        "review.cases contiene notes humanas repetidas",
        "--require-current-auth-preflight",
        "preflight actual de Claude CLI no esta ok",
    )
    missing_review_secret_gate = [
        needle for needle in review_secret_gate_needles if needle not in manual_review_gate_text
    ]
    if missing_review_secret_gate:
        _fail(
            "El gate de revision manual debe rechazar secretos con core/secrets.py: "
            f"{missing_review_secret_gate}"
        )
    review_report_note_needles = (
        "def _plugin_surface_flags(",
        "## Superficie Del Plugin",
        "evidence.plugin_surface.roots no coincide con el plugin actual",
        "evidence.plugin_surface.file_count no coincide con el plugin actual",
        "evidence.plugin_surface.sha256 no coincide con el plugin actual",
        "def _review_quality_flags(",
        "_manual_review_gate_module()",
        "## Calidad De Review Humana",
        "notes_missing",
        "notes_low_quality",
        "notes_repeated",
        "review_secret_findings",
        "Sin flags automaticos de notas humanas",
    )
    missing_review_report_notes = [
        needle
        for needle in review_report_note_needles
        if needle not in manual_review_report_text
    ]
    if missing_review_report_notes:
        _fail(
            "El reporte de revision manual debe mostrar notas humanas debiles o repetidas: "
            f"{missing_review_report_notes}"
        )
    review_traceability_needles = (
        "review.evidence_file es obligatorio",
        "review.evidence_file no coincide con el evidence pasado al gate",
        "review.evidence_file coincide",
        "review.cases desalineados con matriz actual",
        "review.cases coincide con la matriz manual actual",
    )
    missing_review_traceability = [
        needle
        for needle in review_traceability_needles
        if needle not in manual_review_gate_text
    ]
    if missing_review_traceability:
        _fail(
            "El gate de revision manual debe atar evidence_file a la evidencia validada: "
            f"{missing_review_traceability}"
        )
    _validate_manual_case_contract_links(manual_smoke)
    coverage = manual_smoke._case_command_coverage()
    missing = [name for name, case_ids in coverage.items() if not case_ids]
    if len(coverage) != 18 or missing:
        _fail(f"La matriz manual no cubre las 18 rutas publicas: missing={missing}")
    option_coverage = manual_smoke._case_option_coverage()
    missing_options = [
        name for name, case_ids in option_coverage.items()
        if not case_ids
    ]
    expected_option_contracts = len(manual_smoke.OPTION_CONTRACTS)
    if len(option_coverage) != expected_option_contracts or missing_options:
        _fail(
            "La matriz manual no cubre las opciones publicas: "
            f"total={len(option_coverage)} missing={missing_options}"
        )
    _validate_manual_option_contract_shape(manual_smoke, option_coverage)
    aliases = getattr(manual_smoke, "_PUBLIC_COMMAND_ALIASES", {})
    covered_option_commands = set()
    for name, case_ids in option_coverage.items():
        if not case_ids:
            continue
        prefix = name.split(":", 1)[0]
        covered_option_commands.add(prefix)
        mapped = aliases.get(prefix)
        if mapped:
            covered_option_commands.add(mapped)
    argument_commands = _public_argument_commands()
    missing_argument_commands = sorted(argument_commands - covered_option_commands)
    if missing_argument_commands:
        _fail(
            "Comandos con argument-hint/$ARGUMENTS sin contrato de opcion manual: "
            f"{missing_argument_commands}"
        )
    runtime_coverage = manual_smoke._case_runtime_coverage()
    missing_runtime = [
        name for name, case_ids in runtime_coverage.items()
        if not case_ids
    ]
    _validate_manual_runtime_contract_shape(manual_smoke, runtime_coverage)
    if len(runtime_coverage) != 4 or missing_runtime:
        _fail(
            "La matriz manual no cubre los contratos runtime: "
            f"total={len(runtime_coverage)} missing={missing_runtime}"
        )

    return [
        "docs/release.md es la pagina viva de auditoria",
        "nota project-scope MCP documentada",
        "commands/ documentado como skills planas soportadas",
        "matriz manual cubre 18 rutas publicas",
        f"matriz manual cubre {expected_option_contracts} opciones publicas",
        "matriz manual valida IDs de opcion contra comandos publicos",
        "matriz manual enlaza contratos al comando correcto",
        "matriz manual valida prompts contra comandos declarados",
        "matriz manual ata cada argument-hint a una opcion cubierta",
        "matriz manual valida contratos runtime de update",
        "matriz manual cubre 4 contratos runtime",
        "manual smoke usa worktree por defecto y --installed explicito",
        "manual smoke tiene preflight de autenticacion real y evidencia fail-fast",
        "evidencia manual y plantillas se escriben con permisos 0600",
        "evidencias manuales ignoradas por git y npm",
        "estado operativo docs/project ignorado por git y npm",
        "evidencia manual sanea previews con core/secrets.py",
        "manual review gate exige aprobacion humana explicita",
        "manual review gate rechaza evidencia/review con secretos",
        "manual review gate no crea plantillas desde evidencia con secretos",
        "manual review gate exige preflight actual antes de aprobar",
        "manual review report muestra notas humanas debiles o repetidas",
        "manual review gate exige origen worktree/installed correcto",
        "manual review gate ata evidence_file al JSON validado",
        "plugin_surface.sha256 se exige en revision humana, no se congela en docs",
        "manual review gate valida metadatos de casos contra matriz actual",
        "manual review gate valida metadatos de review contra matriz actual",
        "manual review gate valida mapas de cobertura contra matriz actual",
        "scripts npm manual/preflight alineados",
        "prepublish:prepare genera evidencias manuales antes de la revision humana",
        "prepublish valida evidencias manuales ya revisadas sin regenerarlas",
        "matriz documenta empaquetado seco",
        "plugin details documenta displayName humano",
        "docs oficiales revalidadas 2026-08-15",
        "readiness de salida mantiene pendientes humanos y externos",
        "runbook de revision humana documenta criterios y bloqueos",
    ]


def check_human_contracts() -> list[str]:
    """Verifica contratos prompt-level de trato humano y honestidad operativa."""
    command_names = [
        "_composicion",
        "alfred",
        "ajustes",
        "discuss",
        "feature",
        "fix",
        "map-codebase",
        "memory-ui",
        "next",
        "pause",
        "progress",
        "quick",
        "retomar",
        "search",
        "ship",
        "sync-github",
        "uat",
        "update",
    ]
    commands = {name: _read(f"commands/{name}.md") for name in command_names}
    commands_norm = {name: _normalize(text) for name, text in commands.items()}
    alfred_agent = _read("agents/alfred.md")
    alfred_agent_norm = _normalize(alfred_agent)

    requirements = {
        "clarifying questions": [
            ("Solo usa `AskUserQuestion` si de verdad hay dos caminos plausibles", commands["alfred"]),
            ("una sola pregunta corta", commands["alfred"]),
            ("único `AskUserQuestion` con menú seleccionable real", commands["alfred"]),
            ("Si necesitas preguntar por ambigüedad real", commands["next"]),
            ("un único `AskUserQuestion` navegable", commands["next"]),
            ("NO uses `AskUserQuestion` por defecto", commands["discuss"]),
            ("no hace falta el menú", commands["discuss"]),
            ("DISCUSS_ROUTE_MENU_HEADLESS", commands["discuss"]),
            ("vuelve cancelada", commands["discuss"]),
            ("principal navegable", commands_norm["ajustes"]),
            ("config_headless_menu", commands_norm["ajustes"]),
            ("un único `AskUserQuestion`", commands["update"]),
        ],
        "human gates": [
            ("Si una gate de usuario queda pendiente, usa un único `AskUserQuestion`", commands["feature"]),
            ("Si una gate de usuario queda pendiente, usa un único `AskUserQuestion`", commands["fix"]),
            ("gate de despliegue siempre interactiva", commands_norm["ship"]),
            ("nunca auto-apruebes un despliegue", commands_norm["ship"]),
            ("NO marques una UAT como aprobada sin una indicación explícita del usuario", commands["uat"]),
            ("`/alfred-dev:verify aprobado`", commands["uat"]),
        ],
        "operational honesty": [
            ("Honestidad operativa y antifingimiento", commands["_composicion"]),
            ("No digas \"he ejecutado\", \"ha pasado\" o \"está validado\" si solo lo has inferido", commands["_composicion"]),
            ("Distingue siempre entre \"recomiendo ejecutar X\" y \"he ejecutado X", commands["_composicion"]),
            ("No finjas evidencia", commands["alfred"]),
            ("salida de herramienta", commands["alfred"]),
            ("siguiente paso verificable", commands["alfred"]),
            ("No finjas evidencia", alfred_agent),
            ("confirmación explícita del usuario", alfred_agent),
        ],
        "grounded fallbacks": [
            ("NO inventes stack, entrypoints o riesgos", commands["map-codebase"]),
            ("NO inventes un handoff", commands["pause"]),
            ("aceptacion manual prematura", commands_norm["uat"]),
            ("Si `$ARGUMENTS` está vacío, dilo claramente y no inventes una búsqueda", commands["search"]),
        ],
    }
    missing: list[str] = []
    for group, checks in requirements.items():
        for needle, haystack in checks:
            if needle not in haystack:
                missing.append(f"{group}: {needle}")

    helper_wrappers = [
        "alfred",
        "discuss",
        "map-codebase",
        "memory-ui",
        "pause",
        "progress",
        "retomar",
        "search",
        "sync-github",
        "uat",
    ]
    final_markers = (
        "respuesta final",
        "tal cual",
        "usala y termina",
        "usalo como respuesta final",
        "no sigas explorando",
        "segunda capa",
        "no la reenvuelvas",
    )
    for name in helper_wrappers:
        text_norm = commands_norm[name]
        if "helper" not in text_norm and "alfred-continuity.py" not in commands[name]:
            missing.append(f"helper-first {name}: falta helper")
        if not any(marker in text_norm for marker in final_markers):
            missing.append(f"helper-first {name}: falta regla de salida final sin reenvolver")

    if "No digas" not in commands["_composicion"] or "siguiente paso verificable" not in commands["alfred"]:
        missing.append("humanidad: falta contrato antifingimiento central")
    if "No finjas evidencia" not in alfred_agent:
        missing.append("humanidad: falta contrato antifingimiento en agente Alfred")

    if missing:
        _fail("Contratos de humanidad incompletos: " + "; ".join(missing))

    return [
        "AskUserQuestion limitado a ambigüedad real y gates humanas",
        "helpers operativos no duplican ni reenvuelven salida",
        "UAT exige indicación humana explícita",
        "antifingimiento centralizado en comandos y agente Alfred",
    ]


def check_external_contracts() -> list[str]:
    audit = _read("commands/audit.md")
    audit_norm = _normalize(audit)
    sonarqube = _read("skills/sonarqube/SKILL.md")
    sonarqube_norm = _normalize(sonarqube)
    sync = _read("commands/sync-github.md")
    sync_norm = _normalize(sync)
    lucius_command = _read("commands/lucius.md")
    lucius_agent = _read("agents/lucius.md")
    lucius_all = lucius_command + "\n" + lucius_agent
    lucius_norm = _normalize(lucius_all)
    ship = _read("commands/ship.md")
    ship_norm = _normalize(ship)

    requirements = {
        "audit SonarQube preflight": [
            ("docker --version", audit),
            ("docker info", audit),
            ("AskUserQuestion", audit),
            ("NO intentes instalarlo por tu cuenta", audit),
            ("NO intentes arrancarlo por tu cuenta", audit),
            ("incluso si el proyecto esta en modo autopilot", audit_norm),
            ("sonarqube se omitio por decision explicita del usuario", audit_norm),
        ],
        "sonarqube skill permission": [
            ("no instales docker, no abras docker desktop y no arranques el daemon sin aprobacion explicita del usuario.", sonarqube_norm),
            ("si no existe una autorizacion previa, pidela ahora y espera respuesta.", sonarqube_norm),
            ("puerto `9000` ya esta en uso", sonarqube_norm),
            ("docker rm -f sonarqube-alfred", sonarqube),
            ("intenta igualmente la limpieza final del contenedor temporal", sonarqube_norm),
        ],
        "sync-github safe mirror": [
            ('python3 .claude/alfred-continuity.py sync-github "$PWD" --raw "$ARGUMENTS"', sync),
            ("gh --version", sync),
            ("gh auth status", sync),
            ("NO uses `AskUserQuestion` por defecto", sync),
            ("No borres issues ajenos a Alfred", sync),
            ("Mantén la verdad local", sync),
        ],
        "lucius external audit": [
            ("codex --version", lucius_all),
            ("codex login", lucius_all),
            ("confirmación explícita", lucius_all),
            ("codex exec", lucius_all),
            ("--sandbox read-only", lucius_all),
            ("--ephemeral", lucius_all),
            ("--json", lucius_all),
            ("--output-last-message", lucius_all),
            ("codex_report", lucius_all),
            ("codex_jsonl", lucius_all),
            ("approval_policy", lucius_all),
            ("status --porcelain=v1 -z", lucius_all),
            ("no modifiques ningun fichero", lucius_norm),
            ("nunca ejecutas codigo del proyecto", lucius_norm),
            ("no sustituyes a `qa-engineer`, `security-officer` ni `architect`", lucius_norm),
            ("no reemplaza el sign-off canonico", lucius_norm),
        ],
        "ship deploy gate": [
            ("gate de despliegue", ship_norm),
            ("siempre interactiva", ship_norm),
            ("un único `AskUserQuestion`", ship),
            ("nunca auto-apruebes un despliegue", ship_norm),
            ("usuario+seguridad", ship),
        ],
    }
    missing: list[str] = []
    for group, checks in requirements.items():
        for needle, haystack in checks:
            if needle not in haystack:
                missing.append(f"{group}: {needle}")
    if missing:
        _fail("Contratos externos incompletos: " + "; ".join(missing))

    return [
        "Docker/SonarQube pide permiso y documenta omisiones",
        "sync-github mantiene GitHub como espejo seguro",
        "Lucius confirma coste y no modifica ficheros",
        "ship mantiene deploy con gate humana",
    ]


def run_command(name: str, command: list[str], timeout: int = 120) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise AuditError(
            f"{name} fallo con codigo {result.returncode}\n{result.stdout}"
        )
    return result.stdout


def _materialized_alfred_alias_bytes(*, invocable: bool = True) -> bytes:
    alias_source = ROOT / "skills" / "alfred" / "alfred" / "SKILL.md"
    text = alias_source.read_text(encoding="utf-8")
    value = "true" if invocable else "false"
    if re.search(r"(?m)^user-invocable:\s*(true|false)\s*$", text):
        text = re.sub(
            r"(?m)^user-invocable:\s*(true|false)\s*$",
            f"user-invocable: {value}",
            text,
            count=1,
        )
    elif text.startswith("---\n"):
        text = text.replace("---\n", f"---\nuser-invocable: {value}\n", 1)
    return text.encode("utf-8")


def check_installed_cache_freshness() -> list[str]:
    if not INSTALLED_PLUGIN_DIR.is_dir():
        _fail(
            "No existe la cache instalada 0.7.0 de Claude. Refrescala con:\n"
            "claude plugin marketplace remove alfred-dev --scope user\n"
            "claude plugin marketplace add \"$PWD\" --scope user\n"
            "claude plugin uninstall alfred-dev@alfred-dev --scope user\n"
            "claude plugin install alfred-dev@alfred-dev --scope user"
        )

    missing: list[str] = []
    drifted: list[str] = []
    for relative in _iter_installed_cache_freshness_files():
        worktree_path = ROOT / relative
        installed_path = INSTALLED_PLUGIN_DIR / relative
        if not installed_path.is_file():
            missing.append(relative)
            continue
        if _sha256(worktree_path) != _sha256(installed_path):
            drifted.append(relative)

    if missing or drifted:
        details = []
        if missing:
            details.append("missing=" + ", ".join(missing[:12]))
        if drifted:
            details.append("drifted=" + ", ".join(drifted[:12]))
        _fail(
            "La cache instalada de Claude no coincide con el worktree auditado "
            f"({'; '.join(details)}). Refrescala con:\n"
            "claude plugin marketplace remove alfred-dev --scope user\n"
            "claude plugin marketplace add \"$PWD\" --scope user\n"
            "claude plugin uninstall alfred-dev@alfred-dev --scope user\n"
            "claude plugin install alfred-dev@alfred-dev --scope user"
        )

    return [
        "cache instalada 0.7.0 completa y coincide con el worktree"
    ]


def _run_continuity(project_dir: Path, *args: str, timeout: int = 60) -> str:
    return run_command(
        f"continuity {' '.join(args)}",
        [sys.executable, str(ROOT / "core" / "continuity.py"), *args],
        timeout=timeout,
    )


def _run_continuity_raw(project_dir: Path, *args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "core" / "continuity.py"), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def _complete_quick_session(project_dir: Path) -> None:
    from core.orchestrator import advance_phase, create_session, save_state

    session = create_session("quick", "Ajustar copy login")
    while session["fase_actual"] != "completado":
        session = advance_phase(session, resultado="aprobado", artefactos=[])
    save_state(session, str(project_dir / ".claude" / "alfred-dev-state.json"))


def check_continuity_smoke() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="alfred-release-audit-") as tmp:
        project = Path(tmp)
        (project / "src").mkdir()
        (project / "package.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
        (project / "src" / "app.js").write_text(
            "export function label() { return 'Login'; }\n",
            encoding="utf-8",
        )

        sync_empty = project / "sync-empty"
        sync_empty.mkdir()
        sync_fail = _run_continuity_raw(sync_empty, "sync-github", str(sync_empty), "--raw", "owner/repo")
        if sync_fail.returncode == 0:
            _fail("sync-github deberia fallar sin tareas sincronizables preparadas para GitHub")
        sync_error = sync_fail.stderr + sync_fail.stdout
        if (
            "No hay tareas con identificador [T-XXX]" not in sync_error
            and "No hay tareas en docs/project/kanban/" not in sync_error
        ):
            _fail(f"sync-github no fallo de forma explicita sin tareas: {sync_error}")

        next_initial = json.loads(_run_continuity(project, "next", str(project), "--json"))
        if next_initial.get("command") != "map-codebase":
            _fail(f"next inicial esperaba map-codebase, obtuvo {next_initial}")

        mapped = json.loads(
            _run_continuity(project, "map-codebase", str(project), "--raw", "login", "--json")
        )
        if mapped.get("recommended_command") != "discuss":
            _fail(f"map-codebase esperaba recommend discuss, obtuvo {mapped}")
        if not (project / "docs" / "project" / "codebase-map.md").exists():
            _fail("map-codebase no creo docs/project/codebase-map.md")

        from core.continuity import save_prefetch_result

        save_prefetch_result(
            str(project),
            {
                "source_command": "map-codebase",
                "prefetched_command": "map-codebase",
                "project_name": "fixture",
                "stack": {"runtime": "node", "framework": "desconocido"},
                "recommended_command": "discuss",
            },
        )
        consumed = _run_continuity(
            project,
            "consume-prefetch",
            str(project),
            "--expected",
            "map-codebase",
        )
        if "## Mapeo brownfield completado" not in consumed:
            _fail("consume-prefetch no devolvio la respuesta helper-first esperada")
        if (project / ".claude" / "alfred-prefetch.json").exists():
            _fail("consume-prefetch no limpio el prefetch transitorio")

        discussed = json.loads(
            _run_continuity(project, "discuss", str(project), "--raw", "ajustar login", "--json")
        )
        if discussed.get("recommended_command") not in {"feature", "quick", "fix", "spike"}:
            _fail(f"discuss devolvio recomendacion inesperada: {discussed}")

        quick = _run_continuity(project, "quick", str(project), "--raw", "cambiar CTA")
        if "## Quick preparado" not in quick or "/alfred-dev:verify" not in quick:
            _fail("quick no devolvio resumen humano con siguiente verify")

        handoff = json.loads(_run_continuity(project, "write-handoff", str(project)))
        handoff_path = project / ".claude" / "alfred-handoff.json"
        handoff_payload = json.loads(handoff_path.read_text(encoding="utf-8")) if handoff_path.exists() else {}
        if handoff_payload.get("command") != "quick" or not Path(handoff.get("json_path", "")).exists():
            _fail(f"write-handoff no persistio handoff de quick: {handoff}")

        bypass = json.loads(
            _run_continuity(
                project,
                "allow-stop-once",
                str(project),
                "--command",
                "/alfred-dev:status",
            )
        )
        if bypass.get("command") != "/alfred-dev:status" or not Path(bypass.get("bypass_path", "")).exists():
            _fail(f"allow-stop-once no armo bypass valido: {bypass}")

        status = _run_continuity(project, "status", str(project))
        if "## Estado operativo de Alfred Dev" not in status:
            _fail("status no devolvio resumen operativo")

        pause = _run_continuity(project, "pause", str(project))
        if "## Sesión pausada" not in pause:
            _fail("pause no dejo salida humana de pausa")

        resume = _run_continuity(project, "resume", str(project))
        if "## Sesión reanudada" not in resume:
            _fail("resume no dejo salida humana de reanudacion")

        for command, expected in [
            ("progress", "## Resumen operativo del proyecto"),
            ("standup", "## Standup diario"),
            ("blocked", "## Tareas en blocked"),
            ("in-progress", "## Tareas en in progress"),
            ("validate", "## Validación operativa"),
        ]:
            output = _run_continuity(project, command, str(project))
            if expected not in output:
                _fail(f"{command} no contiene {expected!r}")

        search = _run_continuity(project, "search", str(project), "--raw", "login")
        if "## Resultados para `login`" not in search:
            _fail("search no devolvio resultados humanos")

        kanban = project / "docs" / "project" / "kanban"
        kanban.mkdir(parents=True, exist_ok=True)
        (kanban / "backlog.md").write_text(
            "# Backlog\n\n"
            "### [T-010] Validar login con /alfred-dev:verify\n\n"
            "- **Agente:** alfred:verify\n",
            encoding="utf-8",
        )
        for lane in ("in-progress", "done", "blocked"):
            (kanban / f"{lane}.md").write_text(f"# {lane.title()}\n", encoding="utf-8")
        normalize = _run_continuity(project, "normalize-kanban", str(project))
        if "## Normalización de kanban" not in normalize or "Tareas ajustadas" not in normalize:
            _fail("normalize-kanban no devolvio resumen de normalizacion")

        memory_started = False
        try:
            memory_ui = json.loads(
                _run_continuity(
                    project,
                    "memory-ui",
                    str(project),
                    "--json",
                    "--no-open",
                    timeout=90,
                )
            )
            memory_started = True
            if not str(memory_ui.get("url", "")).startswith("http://127.0.0.1:"):
                _fail(f"memory-ui no devolvio URL local valida: {memory_ui}")
            if not (project / ".claude" / "alfred-memory-ui.json").exists():
                _fail("memory-ui no persistio .claude/alfred-memory-ui.json")
        finally:
            if memory_started:
                _run_continuity(project, "memory-ui", str(project), "--stop", "--json", timeout=90)

        _complete_quick_session(project)
        verify = _run_continuity(project, "verify", str(project), "--raw", "aprobado")
        uat_path = project / ".claude" / "alfred-uat.json"
        uat = json.loads(uat_path.read_text(encoding="utf-8")) if uat_path.exists() else {}
        if (
            "Verificación manual / UAT" not in verify
            or "aprobada" not in verify.lower()
            or uat.get("status") != "approved"
        ):
            _fail("verify aprobado no registro UAT humana")

    return [
        "next/map-codebase/discuss/quick",
        "status/pause/resume/progress/standup",
        "blocked/in-progress/validate/search/verify",
        "write-handoff/allow-stop-once/consume-prefetch/normalize-kanban/memory-ui/sync-github-fail-closed",
    ]


class _MCPJsonlClient:
    def __init__(self, project_dir: Path) -> None:
        self._next_id = 1
        self._proc = subprocess.Popen(
            [sys.executable, str(ROOT / "mcp" / "memory_server.py")],
            cwd=project_dir,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._selector = selectors.DefaultSelector()
        assert self._proc.stdout is not None
        self._selector.register(self._proc.stdout, selectors.EVENT_READ)

    def close(self) -> None:
        if self._proc.stdin is not None:
            try:
                self._proc.stdin.close()
            except OSError:
                pass
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.terminate()
            self._proc.wait(timeout=5)
        if self._proc.returncode not in {0, None}:
            stderr = self._proc.stderr.read() if self._proc.stderr else ""
            _fail(f"Servidor MCP termino con codigo {self._proc.returncode}: {stderr}")

    def notify(self, method: str, params: dict | None = None) -> None:
        assert self._proc.stdin is not None
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()

    def request(self, method: str, params: dict | None = None) -> dict:
        assert self._proc.stdin is not None
        request_id = self._next_id
        self._next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()

        events = self._selector.select(timeout=10)
        if not events:
            stderr = self._proc.stderr.read() if self._proc.stderr else ""
            _fail(f"Timeout esperando respuesta MCP para {method}: {stderr}")
        line = self._proc.stdout.readline()  # type: ignore[union-attr]
        if not line:
            stderr = self._proc.stderr.read() if self._proc.stderr else ""
            _fail(f"Servidor MCP cerro stdout durante {method}: {stderr}")
        response = json.loads(line)
        if response.get("id") != request_id:
            _fail(f"Respuesta MCP con id inesperado: {response}")
        if "error" in response:
            _fail(f"Error MCP en {method}: {response['error']}")
        return response["result"]

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        result = self.request(
            "tools/call",
            {"name": name, "arguments": arguments or {}},
        )
        if result.get("isError"):
            _fail(f"{name} devolvio isError: {result}")
        content = result.get("content") or []
        if not content or content[0].get("type") != "text":
            _fail(f"{name} no devolvio contenido text: {result}")
        return json.loads(content[0]["text"])


def check_mcp_tools_smoke() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="alfred-mcp-audit-") as tmp:
        project = Path(tmp)
        (project / ".claude").mkdir()
        adr_dir = project / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "0001-cache.md").write_text(
            "# Usar Redis\n\n"
            "## Contexto\n\nNecesitamos cachear lecturas frecuentes.\n\n"
            "## Decisión\n\nUsar Redis para cache compartida.\n",
            encoding="utf-8",
        )

        client = _MCPJsonlClient(project)
        try:
            init = client.request(
                "initialize",
                {
                    "protocolVersion": "2025-11-25",
                    "clientInfo": {"name": "alfred-release-audit", "version": VERSION},
                    "capabilities": {},
                },
            )
            if init.get("serverInfo", {}).get("name") != "alfred-memory":
                _fail(f"initialize inesperado: {init}")
            client.notify("notifications/initialized")

            tools = client.request("tools/list")["tools"]
            tool_names = [tool["name"] for tool in tools]
            if len(tool_names) != 15:
                _fail(f"tools/list esperaba 15 herramientas, obtuvo {tool_names}")
            tool_by_name = {tool["name"]: tool for tool in tools}
            expected_limits = {
                "memory_search": 100,
                "memory_get_decisions": 200,
                "memory_import": 1000,
            }
            for tool_name, maximum in expected_limits.items():
                schema = tool_by_name[tool_name]["inputSchema"]["properties"]["limit"]
                if schema.get("minimum") != 1 or schema.get("maximum") != maximum:
                    _fail(
                        f"{tool_name} no declara limites MCP defensivos: {schema}"
                    )
            event_schema = tool_by_name["memory_log_event"]["inputSchema"]["properties"]
            expected_event_bounds = {
                "event_type": 80,
                "phase": 80,
                "summary": 500,
                "content": 8000,
            }
            for field, maximum in expected_event_bounds.items():
                if event_schema[field].get("maxLength") != maximum:
                    _fail(f"memory_log_event no declara maxLength para {field}: {event_schema[field]}")
            if "preview" not in event_schema["payload"].get("description", ""):
                _fail("memory_log_event no documenta preview para payload enorme")

            started = client.call_tool(
                "memory_manage_iteration",
                {"action": "start", "command": "feature", "description": "Login release audit"},
            )
            iteration_id = started.get("iteration_id")
            if not iteration_id:
                _fail(f"memory_manage_iteration no devolvio iteration_id: {started}")

            dec1 = client.call_tool(
                "memory_log_decision",
                {
                    "title": "Cache de login",
                    "chosen": "Redis",
                    "context": "Login con lecturas frecuentes",
                    "tags": ["release-audit"],
                },
            )["decision_id"]
            dec2 = client.call_tool(
                "memory_log_decision",
                {
                    "title": "Sesion de usuario",
                    "chosen": "Cookie segura",
                    "tags": ["release-audit"],
                },
            )["decision_id"]
            client.call_tool(
                "memory_update_decision",
                {"id": dec1, "status": "superseded", "tags": ["mcp-smoke"]},
            )
            client.call_tool(
                "memory_link_decisions",
                {"source_id": dec1, "target_id": dec2, "link_type": "relates"},
            )
            client.call_tool(
                "memory_log_commit",
                {
                    "sha": "abc123releaseaudit",
                    "message": "feat: login cache",
                    "author": "Alfred Audit",
                    "decision_ids": [dec1],
                    "files": ["src/login.py"],
                },
            )
            client.call_tool(
                "memory_log_event",
                {
                    "event_type": "gate_passed",
                    "phase": "calidad",
                    "summary": "Redis cache validada",
                    "payload": {"note": "redis cache validada"},
                },
            )
            large_event = client.call_tool(
                "memory_log_event",
                {
                    "event_type": "custom",
                    "phase": "calidad",
                    "summary": "evento MCP grande",
                    "content": "x" * 9000,
                    "payload": {"blob": "y" * 9000},
                },
            )
            if not large_event.get("content_truncated") or not large_event.get("payload_truncated"):
                _fail(f"memory_log_event no recorto content/payload enormes: {large_event}")

            search = client.call_tool("memory_search", {"query": "Redis", "limit": 10})
            if search.get("total", 0) < 1:
                _fail(f"memory_search no encontro datos sembrados: {search}")
            capped_search = client.call_tool(
                "memory_search",
                {"query": "Redis", "limit": 999999},
            )
            if capped_search.get("applied_limit") != 100:
                _fail(f"memory_search no recorto limit abusivo: {capped_search}")
            if client.call_tool("memory_get_iteration", {"id": iteration_id}).get("iteration") is None:
                _fail("memory_get_iteration no devolvio la iteracion creada")
            if client.call_tool("memory_get_timeline", {"iteration_id": iteration_id}).get("total", 0) < 1:
                _fail("memory_get_timeline no devolvio eventos")
            if client.call_tool("memory_get_decisions", {"tags": ["release-audit"]}).get("total", 0) < 2:
                _fail("memory_get_decisions no devolvio decisiones sembradas")
            if client.call_tool("memory_stats").get("total_decisions", 0) < 2:
                _fail("memory_stats no conto decisiones")
            if client.call_tool("memory_health").get("status") != "healthy":
                _fail("memory_health no devolvio healthy")
            export_path = str(project / "DECISIONS.md")
            if client.call_tool("memory_export", {"format": "markdown", "path": export_path}).get("exported", 0) < 2:
                _fail("memory_export no exporto decisiones")
            if not Path(export_path).exists():
                _fail("memory_export no creo DECISIONS.md")
            blocked_export = client.request(
                "tools/call",
                {
                    "name": "memory_export",
                    "arguments": {
                        "format": "markdown",
                        "path": str(project.parent / "OUTSIDE.md"),
                    },
                },
            )
            if not blocked_export.get("isError"):
                _fail(f"memory_export permitio escribir fuera del proyecto: {blocked_export}")
            if client.call_tool("memory_import", {"source": "adr", "path": str(adr_dir)}).get("imported") != 1:
                _fail("memory_import adr no importo el ADR fixture")
            purge = client.call_tool("memory_purge", {"retention_days": 1})
            if "purged_events" not in purge:
                _fail("memory_purge no devolvio purged_events")
            client.call_tool("memory_manage_iteration", {"action": "complete", "iteration_id": iteration_id})
        finally:
            client.close()

    return [
        "15 tools listadas",
        "15 tools invocadas con datos reales",
        "limites MCP defensivos en schemas y handlers",
        "memory_log_event recorta payload/content MCP enormes",
        "rutas MCP acotadas al proyecto",
        "SQLite temporal saludable",
    ]


def check_external(args: argparse.Namespace) -> list[str]:
    ok: list[str] = []
    if args.with_external_contracts:
        for line in check_external_contracts():
            ok.append(f"external {line}")
    if args.with_human_contracts:
        for line in check_human_contracts():
            ok.append(f"human {line}")
    if args.with_continuity:
        for line in check_continuity_smoke():
            ok.append(f"continuity {line}")
    if args.with_mcp_tools:
        for line in check_mcp_tools_smoke():
            ok.append(f"mcp-tools {line}")

    if args.with_claude:
        for line in check_installed_cache_freshness():
            ok.append(f"claude {line}")
        details = run_command(
            "claude plugin validate/details",
            [
                "sh",
                "-c",
                "claude plugin validate . --strict && "
                "claude plugin details alfred-dev@alfred-dev | sed -n '1,18p' && "
                "claude mcp get plugin:alfred-dev:alfred-memory",
            ],
            timeout=90,
        )
        for needle in ("Alfred Dev (alfred-dev) 0.7.0", "Skills (11)", "Agents (10)", "MCP servers (1)", "Status: ✔ Connected"):
            if needle not in details:
                _fail(f"Smoke Claude no contiene {needle!r}")
        ok.append("Claude CLI valida inventario y MCP")
        discovery = run_command(
            "claude interactive /alfred discovery",
            [sys.executable, str(ROOT / "scripts" / "claude_command_discovery.py")],
            timeout=35,
        )
        if "ok claude interactive command discovery" not in discovery:
            _fail("Smoke Claude no confirmo descubrimiento interactivo de /alfred")
        if "FAIL claude-command-discovery" in discovery:
            _fail("Smoke Claude sigue mostrando fallo de descubrimiento interactivo de /alfred")
        ok.append("Claude CLI descubre /alfred en selector interactivo")

    if args.with_site:
        run_command("npm site check/build", ["sh", "-c", "npm --prefix site run check && npm --prefix site run build"], timeout=180)
        ok.append("site check/build")

    if args.with_tests:
        run_command("pytest completo", ["python3", "-m", "pytest", "tests/", "-q"], timeout=300)
        ok.append("pytest completo")

    if args.with_syntax:
        run_command(
            "syntax/json/diff",
            [
                "sh",
                "-c",
                "bash -n install.sh && "
                "python3 -m json.tool .mcp.json >/dev/null && "
                "python3 -m json.tool .claude-plugin/plugin.json >/dev/null && "
                "python3 -m json.tool .claude-plugin/marketplace.json >/dev/null && "
                "git diff --check",
            ],
            timeout=60,
        )
        ok.append("syntax/json/diff-check")

    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-claude", action="store_true", help="Ejecuta smokes con claude plugin/mcp.")
    parser.add_argument("--with-site", action="store_true", help="Ejecuta npm --prefix site run check/build.")
    parser.add_argument("--with-tests", action="store_true", help="Ejecuta python3 -m pytest tests/ -q.")
    parser.add_argument("--with-syntax", action="store_true", help="Ejecuta bash -n, json.tool y git diff --check.")
    parser.add_argument("--with-continuity", action="store_true", help="Ejecuta smoke operativo de helpers en fixture temporal.")
    parser.add_argument("--with-mcp-tools", action="store_true", help="Invoca las 15 herramientas MCP en una SQLite temporal.")
    parser.add_argument("--with-external-contracts", action="store_true", help="Verifica prompts seguros para Docker, GitHub, Lucius y deploy.")
    parser.add_argument("--with-human-contracts", action="store_true", help="Verifica trato humano, AskUserQuestion, UAT y antifingimiento.")
    parser.add_argument("--full", action="store_true", help="Activa todos los smokes externos.")
    args = parser.parse_args(argv)

    if args.full:
        args.with_claude = args.with_site = args.with_tests = True
        args.with_syntax = args.with_continuity = True
        args.with_mcp_tools = args.with_external_contracts = True
        args.with_human_contracts = True

    checks = [
        ("versionado", check_versions),
        ("inventario", check_inventory),
        ("catalogo", check_command_catalog),
        ("comandos", check_command_execution_contracts),
        ("claims", check_public_claims),
        ("config", check_config_contracts),
        ("flows", check_flow_gate_claims),
        ("hooks", check_hook_contracts),
        ("mcp", check_mcp_config),
        ("packaging", check_packaging_contracts),
        ("secrets", check_published_secret_scan),
        ("install", check_install_update_contracts),
        ("docs", check_audit_docs),
    ]

    try:
        for name, check in checks:
            for line in check():
                print(f"ok {name}: {line}")
        for line in check_external(args):
            print(f"ok smoke: {line}")
    except (AuditError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL release-audit: {exc}", file=sys.stderr)
        return 1

    print(f"release-audit {VERSION} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
