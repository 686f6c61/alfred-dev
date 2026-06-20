#!/usr/bin/env python3
"""
Cargador de configuración del plugin Alfred Dev.

Este módulo se encarga de leer la configuración del usuario desde un fichero
.local.md con frontmatter YAML, detectar automáticamente el stack tecnológico
del proyecto y fusionar todo con unos valores por defecto sensatos.

El diseño busca funcionar sin dependencias externas: incluye un parser YAML
básico como fallback para entornos donde PyYAML no esté disponible.

Funciones públicas:
    - load_config(path): carga y fusiona configuración desde un fichero .local.md
    - load_project_config(project_dir): carga la config local y aplica detección de stack
    - detect_stack(project_dir): detecta runtime, lenguaje, framework y ORM
"""

import json
import os
import re
import copy
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.optional_agents import (
    build_optional_agent_flags,
    get_optional_agent_display_label,
    get_optional_integrations,
    get_static_suggestible_agent_names,
    order_optional_agent_names,
)

# Se intenta importar PyYAML; si no está disponible, se usa el parser básico
try:
    import yaml

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

try:
    from core.memory_config import DEFAULT_MEMORY_CONFIG
except Exception:
    DEFAULT_MEMORY_CONFIG = {
        "enabled": False,
        "sync_to_native": True,
        "sync_commits_limit": 10,
        "capture_decisions": True,
        "capture_commits": True,
        "retention_days": 365,
    }

_CANONICAL_AUTONOMY_DEFAULTS = {
    "producto": "autonomo",
    "arquitectura": "autonomo",
    "desarrollo": "autonomo",
    "calidad": "autonomo",
    "documentacion": "autonomo",
    "entrega": "autonomo",
}

_AUTONOMY_VALUE_ALIASES = {
    "interactivo": "interactivo",
    "autonomo": "autonomo",
    "semi_autonomo": "semi-autonomo",
}

_TOP_LEVEL_KEY_ALIASES = {
    "autonomia": "autonomia",
}

_LEGACY_AUTONOMY_KEY_ALIASES = {
    "docs": "documentacion",
    "documentacion": "documentacion",
    "documentación": "documentacion",
    "refactor": "desarrollo",
    "tests": "calidad",
    "devops": "entrega",
}

_SECURITY_PHASES = ("arquitectura", "calidad", "entrega")


# --- Configuración por defecto ---
# Estos valores representan el comportamiento base del plugin cuando el usuario
# no ha definido ninguna preferencia. Cada sección controla un aspecto distinto:
#
# - autonomía: cuánto puede decidir el plugin por su cuenta
# - proyecto: metadatos del proyecto (se rellenan con detect_stack)
# - compliance: reglas de cumplimiento y estilo
# - integraciones: servicios externos habilitados
# - personalidad: tono y nivel de sarcasmo del agente
# - notas: texto libre del usuario con preferencias adicionales

DEFAULT_CONFIG = {
    "autonomia": dict(_CANONICAL_AUTONOMY_DEFAULTS),
    "proyecto": {
        "runtime": "desconocido",
        "lenguaje": "desconocido",
        "framework": "desconocido",
        "orm": "ninguno",
        "test_runner": "desconocido",
        "bundler": "desconocido",
    },
    "compliance": {
        "estilo": "auto",
        "lint": True,
        "format_on_save": True,
    },
    "integraciones": {
        "git": True,
        "ci": False,
        "deploy": False,
    },
    "personalidad": {
        "nivel_sarcasmo": 3,
        "verbosidad": "normal",
        "idioma": "es",
        "celebrar_victorias": True,
        "insultar_malas_practicas": True,
    },
    # Agentes opcionales: predefinidos que el usuario activa según su proyecto.
    # Todos desactivados por defecto; se activan con /alfred config o por
    # descubrimiento contextual al iniciar el plugin en un proyecto nuevo.
    "agentes_opcionales": build_optional_agent_flags(),
    "memoria": dict(DEFAULT_MEMORY_CONFIG),
    "notas": "",
}

_CONFIG_FRONTMATTER_KEYS = tuple(
    key for key in DEFAULT_CONFIG.keys()
    if key != "notas"
)
_BOOTSTRAP_LOCAL_CONFIG_PATCH = {
    "autonomia": dict(_CANONICAL_AUTONOMY_DEFAULTS),
    "memoria": {
        "enabled": True,
        "sync_to_native": True,
        "sync_commits_limit": 10,
        "capture_decisions": True,
        "capture_commits": True,
        "retention_days": 365,
    },
}
_BOOTSTRAP_LOCAL_CONFIG_NOTE = (
    "Este fichero se genera automáticamente en la primera sesión.\n"
    "Puedes personalizarlo con `/alfred-dev:config`."
)
_CONFIG_SECTION_ORDER = (
    "autonomia",
    "proyecto",
    "agentes_opcionales",
    "memoria",
    "compliance",
    "integraciones",
    "personalidad",
)
_CONFIG_SECTION_LABELS = {
    "autonomia": "Autonomía por fase",
    "proyecto": "Proyecto",
    "agentes_opcionales": "Agentes opcionales",
    "memoria": "Memoria persistente",
    "compliance": "Compliance",
    "integraciones": "Integraciones",
    "personalidad": "Personalidad",
}
_CONFIG_SECTION_MENU_EXIT = {
    "label": "Salir sin cambios",
    "description": "Mantener la configuración actual por ahora",
}


def load_config(path):
    """
    Carga la configuración del plugin desde un fichero .local.md.

    El fichero utiliza frontmatter YAML (delimitado por ---) para los valores
    de configuración y el cuerpo Markdown para notas en texto libre. Si el
    fichero no existe o no se puede leer, se devuelven los valores por defecto.

    La fusión es recursiva: los valores del fichero sobreescriben solo las
    claves que definen, manteniendo el resto de los defaults intactos.

    Args:
        path: ruta absoluta o relativa al fichero de configuración.

    Returns:
        dict con la configuración fusionada. Siempre contiene todas las claves
        de DEFAULT_CONFIG aunque el fichero no defina ninguna.

    Ejemplo:
        >>> config = load_config("/proyecto/.dev-vago.local.md")
        >>> config["autonomia"]["producto"]
        'autonomo'
    """
    # Se parte siempre de una copia profunda de los defaults para no mutar
    # el diccionario global entre llamadas
    config = copy.deepcopy(DEFAULT_CONFIG)

    if not os.path.isfile(path):
        return config

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, IOError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo leer '{path}': {e}. "
            f"Se usarán los valores por defecto.",
            file=sys.stderr,
        )
        return config

    frontmatter, body = _parse_frontmatter(content)

    if frontmatter:
        parsed = _parse_yaml(frontmatter)
        if isinstance(parsed, dict):
            config = _deep_merge(config, _normalize_loaded_config(parsed))
        elif parsed is not None:
            print(
                f"[Alfred Dev] Aviso: el frontmatter de '{path}' no es un diccionario. "
                f"Se ignorará la configuración del fichero.",
                file=sys.stderr,
            )

    # Se extraen las notas del cuerpo Markdown.
    # Se busca cualquier sección cuyo título contenga "Notas" (h1-h6).
    # Todo el contenido desde esa cabecera hasta la siguiente cabecera
    # del mismo nivel o hasta el final del documento se considera notas.
    notas = _extract_notes(body)
    if notas:
        config["notas"] = notas

    return config


def load_project_config(project_dir: str) -> Dict[str, Any]:
    """Carga la configuración efectiva de un proyecto combinando config + stack.

    La detección automática rellena la sección ``proyecto`` cuando el usuario
    no la ha sobreescrito explícitamente en ``.claude/alfred-dev.local.md``.

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        Configuración fusionada y lista para consumo operativo.
    """
    config_path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")
    config = load_config(config_path)
    detected_stack = detect_stack(project_dir)

    effective_project = dict(detected_stack)
    configured_project = config.get("proyecto", {})
    defaults = DEFAULT_CONFIG["proyecto"]

    if isinstance(configured_project, dict):
        for key, value in configured_project.items():
            default_value = defaults.get(key)
            if key not in effective_project or value != default_value:
                effective_project[key] = value

    config["proyecto"] = effective_project
    return config


def get_active_optional_agents(config: Dict[str, Any]) -> List[str]:
    """Devuelve los agentes opcionales activos en orden canónico."""
    opcionales = config.get("agentes_opcionales", {})
    if not isinstance(opcionales, dict):
        return []

    return order_optional_agent_names(
        name
        for name, enabled in opcionales.items()
        if enabled
    )


def build_equipo_sesion_from_config(
    config: Dict[str, Any],
    *,
    source: str = "config_persistida",
) -> Optional[Dict[str, Any]]:
    """Construye el ``equipo_sesion`` runtime a partir de la config efectiva.

    Esta función traduce la configuración persistida del proyecto al mismo
    contrato estructural que usa la composición dinámica. Así evitamos que
    runtime, hooks y documentación operativa mantengan dos fuentes de verdad
    distintas sobre qué opcionales están activos.

    Args:
        config: configuración efectiva ya fusionada.
        source: valor de ``fuente`` a registrar en la sesión.

    Returns:
        Un diccionario ``equipo_sesion`` listo para runtime, o ``None`` si no
        hay nada operativo que inyectar (sin opcionales activos y memoria
        desactivada).
    """
    flags = build_optional_agent_flags()
    raw_optionals = config.get("agentes_opcionales", {})
    if isinstance(raw_optionals, dict):
        for agent_name in flags:
            if agent_name in raw_optionals:
                flags[agent_name] = bool(raw_optionals.get(agent_name, False))

    memory = config.get("memoria", {})
    memory_enabled = False
    if isinstance(memory, dict):
        memory_enabled = bool(memory.get("enabled", False))

    if not any(flags.values()) and not memory_enabled:
        return None

    return {
        "opcionales_activos": flags,
        "infra": {
            "memoria": memory_enabled,
        },
        "fuente": source,
    }


def build_project_equipo_sesion(
    project_dir: str,
    *,
    source: str = "config_persistida",
) -> Optional[Dict[str, Any]]:
    """Carga la config del proyecto y deriva su ``equipo_sesion`` runtime."""
    config = load_project_config(project_dir)
    return build_equipo_sesion_from_config(config, source=source)


def build_config_section_summaries(
    config: Dict[str, Any],
    *,
    project_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Describe la configuración actual por secciones con resúmenes canónicos.

    Esta estructura está pensada para que `/alfred-dev:config` pueda mostrar el
    estado actual en un menú navegable sin volver a reconstruir frases a mano.
    """
    effective_config = _deep_merge(
        DEFAULT_CONFIG,
        _normalize_loaded_config(config if isinstance(config, dict) else {}),
    )
    project_stack = detect_stack(project_dir) if project_dir else None

    return [
        _describe_config_section(
            section_name,
            effective_config,
            project_stack=project_stack,
        )
        for section_name in _CONFIG_SECTION_ORDER
    ]


def build_config_section_menu(
    config: Dict[str, Any],
    *,
    project_dir: Optional[str] = None,
    include_exit_option: bool = True,
) -> Dict[str, Any]:
    """Construye el menú principal navegable de `/alfred-dev:config`."""
    options: List[Dict[str, str]] = []
    if include_exit_option:
        options.append(dict(_CONFIG_SECTION_MENU_EXIT))

    for section in build_config_section_summaries(config, project_dir=project_dir):
        options.append(
            {
                "label": section["label"],
                "description": section["summary"],
            }
        )

    question = "¿Qué sección quieres modificar ahora?"
    header = "Config"

    return {
        "questions": [
            {
                "question": question,
                "header": header,
                "options": options,
                "multiSelect": False,
            }
        ],
        "header": "Config",
        "question": question,
        "options": options,
    }


def apply_config_section_update(
    config: Dict[str, Any],
    section_name: str,
    values: Any,
) -> Dict[str, Any]:
    """Aplica un cambio sobre una sección canónica y devuelve la config final.

    Usa la misma normalización que `load_config()` para que `/alfred-dev:config`
    pueda actualizar solo una sección sin perder orden, defaults ni aliases.
    """
    if section_name not in _CONFIG_SECTION_ORDER:
        raise KeyError(f"Sección de configuración desconocida: {section_name}")

    effective_config = _deep_merge(
        DEFAULT_CONFIG,
        _normalize_loaded_config(config if isinstance(config, dict) else {}),
    )
    patch = _normalize_loaded_config({section_name: values})
    return _deep_merge(effective_config, patch)


def build_config_section_change_preview(
    config: Dict[str, Any],
    section_name: str,
    values: Any,
    *,
    project_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Resume el cambio efectivo de una sección antes de persistirlo.

    Devuelve el resumen canónico antes/después y la configuración actualizada
    para que `/alfred-dev:config` pueda confirmar el cambio sin reconstruirlo
    a mano ni reimplementar la normalización.
    """
    effective_config = _deep_merge(
        DEFAULT_CONFIG,
        _normalize_loaded_config(config if isinstance(config, dict) else {}),
    )
    updated_config = apply_config_section_update(
        effective_config,
        section_name,
        values,
    )
    project_stack = detect_stack(project_dir) if project_dir else None
    before = _describe_config_section(
        section_name,
        effective_config,
        project_stack=project_stack,
    )
    after = _describe_config_section(
        section_name,
        updated_config,
        project_stack=project_stack,
    )

    return {
        "section": section_name,
        "label": before["label"],
        "changed": before["details"] != after["details"] or before["summary"] != after["summary"],
        "before": before,
        "after": after,
        "updated_config": updated_config,
    }


def update_config_section(
    path: str,
    section_name: str,
    values: Any,
    *,
    notes: Optional[str] = None,
    include_defaults: bool = True,
) -> Dict[str, Any]:
    """Actualiza una sección concreta de un `.local.md` de forma canónica.

    El flujo es siempre el mismo: cargar, normalizar, aplicar el patch por
    sección, persistir y devolver un preview estructurado del cambio.
    """
    current_config = load_config(path)
    preview = build_config_section_change_preview(
        current_config,
        section_name,
        values,
    )
    save_config(
        path,
        preview["updated_config"],
        notes=current_config.get("notas", "") if notes is None else notes,
        include_defaults=include_defaults,
    )
    return preview


def update_project_config_section(
    project_dir: str,
    section_name: str,
    values: Any,
    *,
    notes: Optional[str] = None,
    include_defaults: bool = True,
) -> Dict[str, Any]:
    """Actualiza una sección de la config persistida del proyecto."""
    path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")
    return update_config_section(
        path,
        section_name,
        values,
        notes=notes,
        include_defaults=include_defaults,
    )


def render_config_markdown(
    config: Dict[str, Any],
    *,
    notes: Optional[str] = None,
    include_defaults: bool = True,
) -> str:
    """Serializa una configuración al formato canónico ``.local.md``.

    El frontmatter se escribe con claves canónicas y orden estable para que
    el runtime, los hooks y `/alfred-dev:config` compartan exactamente el
    mismo formato base.
    """
    normalized_input = _normalize_loaded_config(config)
    if include_defaults:
        normalized = _deep_merge(DEFAULT_CONFIG, normalized_input)
    else:
        normalized = copy.deepcopy(normalized_input)
    notes_body = (
        notes
        if notes is not None
        else normalized.get("notas", "")
    )
    frontmatter_payload = {
        key: copy.deepcopy(normalized[key])
        for key in _CONFIG_FRONTMATTER_KEYS
        if key in normalized
    }
    frontmatter = _render_yaml_mapping(frontmatter_payload, DEFAULT_CONFIG)

    parts = ["---", frontmatter.rstrip(), "---"]
    trimmed_notes = str(notes_body or "").strip()
    if trimmed_notes:
        parts.extend(["", "## Notas", "", trimmed_notes])
    return "\n".join(parts) + "\n"


def save_config(
    path: str,
    config: Dict[str, Any],
    *,
    notes: Optional[str] = None,
    include_defaults: bool = True,
) -> None:
    """Escribe una configuración canónica en disco."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = render_config_markdown(
        config,
        notes=notes,
        include_defaults=include_defaults,
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def save_project_config(
    project_dir: str,
    config: Dict[str, Any],
    *,
    notes: Optional[str] = None,
    include_defaults: bool = True,
) -> str:
    """Guarda la configuración del proyecto en ``.claude/alfred-dev.local.md``."""
    path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")
    save_config(path, config, notes=notes, include_defaults=include_defaults)
    return path


def ensure_bootstrap_local_config(
    path: str,
    *,
    default_note: str = _BOOTSTRAP_LOCAL_CONFIG_NOTE,
) -> bool:
    """Garantiza una config local mínima canónica para el primer arranque.

    Reglas:
    - Si el fichero no existe, lo crea con autonomía por fases y memoria activa.
    - Si existe pero no tiene frontmatter, envuelve el contenido existente en una
      config canónica mínima y conserva el texto como notas.
    - Si existe con frontmatter, solo añade las secciones top-level ausentes
      (`autonomia` y `memoria`) sin pisar preferencias explícitas.

    Returns:
        ``True`` si ha escrito cambios; ``False`` si el fichero ya estaba listo.
    """
    if not os.path.exists(path):
        save_config(
            path,
            _BOOTSTRAP_LOCAL_CONFIG_PATCH,
            notes=default_note,
            include_defaults=False,
        )
        return True

    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    frontmatter, body = _parse_frontmatter(content)
    body_text = body.strip()

    if not frontmatter:
        save_config(
            path,
            _BOOTSTRAP_LOCAL_CONFIG_PATCH,
            notes=body_text or default_note,
            include_defaults=False,
        )
        return True

    parsed = _parse_yaml(frontmatter)
    normalized = _normalize_loaded_config(parsed if isinstance(parsed, dict) else {})
    changed = False

    if not _has_top_level_frontmatter_section(frontmatter, "autonomia"):
        normalized["autonomia"] = copy.deepcopy(_BOOTSTRAP_LOCAL_CONFIG_PATCH["autonomia"])
        changed = True

    if not _has_top_level_frontmatter_section(frontmatter, "memoria"):
        normalized["memoria"] = copy.deepcopy(_BOOTSTRAP_LOCAL_CONFIG_PATCH["memoria"])
        changed = True

    if not changed:
        return False

    save_config(
        path,
        normalized,
        notes=body_text or None,
        include_defaults=False,
    )
    return True


def ensure_bootstrap_project_config(
    project_dir: str,
    *,
    default_note: str = _BOOTSTRAP_LOCAL_CONFIG_NOTE,
) -> str:
    """Aplica el bootstrap canónico sobre `.claude/alfred-dev.local.md`."""
    path = os.path.join(project_dir, ".claude", "alfred-dev.local.md")
    ensure_bootstrap_local_config(path, default_note=default_note)
    return path


def _describe_config_section(
    section_name: str,
    config: Dict[str, Any],
    *,
    project_stack: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construye una descripción humana y estable de una sección."""
    if section_name == "autonomia":
        autonomy = config.get("autonomia", {})
        autonomy_counts = {"interactivo": 0, "semi-autonomo": 0, "autonomo": 0}
        for phase_name in _CANONICAL_AUTONOMY_DEFAULTS:
            level = autonomy.get(phase_name, _CANONICAL_AUTONOMY_DEFAULTS[phase_name])
            if level in autonomy_counts:
                autonomy_counts[level] += 1

        if autonomy_counts["autonomo"] == len(_CANONICAL_AUTONOMY_DEFAULTS):
            summary = "Autopilot completo en las 6 fases."
        else:
            parts = []
            if autonomy_counts["interactivo"]:
                parts.append(f"{autonomy_counts['interactivo']} interactivas")
            if autonomy_counts["semi-autonomo"]:
                parts.append(f"{autonomy_counts['semi-autonomo']} semi-autónomas")
            if autonomy_counts["autonomo"]:
                parts.append(f"{autonomy_counts['autonomo']} autónomas")
            summary = "Autonomía por fase: " + ", ".join(parts) + "."

        details = [
            {
                "name": phase_name,
                "value": autonomy.get(phase_name, _CANONICAL_AUTONOMY_DEFAULTS[phase_name]),
            }
            for phase_name in _CANONICAL_AUTONOMY_DEFAULTS
        ]
    elif section_name == "proyecto":
        configured_project = config.get("proyecto", {})
        project = dict(project_stack or DEFAULT_CONFIG["proyecto"])
        if isinstance(configured_project, dict):
            for key, value in configured_project.items():
                default_value = DEFAULT_CONFIG["proyecto"].get(key)
                if key not in project or value != default_value:
                    project[key] = value
        fields = [
            project.get("runtime", "desconocido"),
            project.get("lenguaje", "desconocido"),
            project.get("framework", "desconocido"),
            project.get("orm", "ninguno"),
            project.get("test_runner", "desconocido"),
            project.get("bundler", "desconocido"),
        ]
        summary = " / ".join(str(value) for value in fields) + "."
        details = [
            {"name": key, "value": project.get(key, DEFAULT_CONFIG["proyecto"][key])}
            for key in DEFAULT_CONFIG["proyecto"]
        ]
        if project_stack:
            overrides = [
                key
                for key in DEFAULT_CONFIG["proyecto"]
                if project.get(key, DEFAULT_CONFIG["proyecto"][key]) != project_stack.get(key)
                and project.get(key, DEFAULT_CONFIG["proyecto"][key]) != DEFAULT_CONFIG["proyecto"][key]
            ]
            summary += " Detectado automáticamente." if not overrides else (
                " Override manual en " + ", ".join(overrides) + "."
            )
    elif section_name == "agentes_opcionales":
        active_names = get_active_optional_agents(config)
        if active_names:
            active_labels = ", ".join(
                get_optional_agent_display_label(agent_name)
                for agent_name in active_names
            )
            on_demand_names = [
                agent_name
                for agent_name in active_names
                if not get_optional_integrations()[agent_name]["fases"]
            ]
            summary = f"{len(active_names)} activos: {active_labels}."
            if on_demand_names:
                on_demand_labels = ", ".join(
                    get_optional_agent_display_label(agent_name)
                    for agent_name in on_demand_names
                )
                summary += f" Bajo demanda: {on_demand_labels}."
        else:
            summary = "Ningún opcional activo."
        details = [
            {"name": agent_name, "value": bool(config["agentes_opcionales"].get(agent_name, False))}
            for agent_name in build_optional_agent_flags()
        ]
    elif section_name == "memoria":
        memory = config.get("memoria", {})
        if memory.get("enabled"):
            summary = (
                "Activa con sync nativa "
                f"({memory.get('sync_commits_limit', DEFAULT_MEMORY_CONFIG['sync_commits_limit'])} commits), "
                f"decisiones={'sí' if memory.get('capture_decisions', True) else 'no'} "
                f"y commits={'sí' if memory.get('capture_commits', True) else 'no'}."
            )
        else:
            summary = "Inactiva; no registrará nuevas decisiones ni commits."
        details = [
            {"name": key, "value": memory.get(key, DEFAULT_MEMORY_CONFIG.get(key))}
            for key in DEFAULT_MEMORY_CONFIG
        ]
    elif section_name == "compliance":
        compliance = config.get("compliance", {})
        summary = (
            f"estilo={compliance.get('estilo', 'auto')}, "
            f"lint={'activo' if compliance.get('lint', True) else 'desactivado'}, "
            f"format_on_save={'activo' if compliance.get('format_on_save', True) else 'desactivado'}."
        )
        details = [
            {"name": key, "value": compliance.get(key, DEFAULT_CONFIG["compliance"][key])}
            for key in DEFAULT_CONFIG["compliance"]
        ]
    elif section_name == "integraciones":
        integrations = config.get("integraciones", {})
        summary = ", ".join(
            f"{key}={'activo' if integrations.get(key, DEFAULT_CONFIG['integraciones'][key]) else 'desactivado'}"
            for key in DEFAULT_CONFIG["integraciones"]
        ) + "."
        details = [
            {"name": key, "value": integrations.get(key, DEFAULT_CONFIG["integraciones"][key])}
            for key in DEFAULT_CONFIG["integraciones"]
        ]
    elif section_name == "personalidad":
        personality = config.get("personalidad", {})
        summary = (
            f"idioma={personality.get('idioma', 'es')}, "
            f"sarcasmo={personality.get('nivel_sarcasmo', 3)}/5, "
            f"verbosidad={personality.get('verbosidad', 'normal')}."
        )
        details = [
            {"name": key, "value": personality.get(key, DEFAULT_CONFIG["personalidad"][key])}
            for key in DEFAULT_CONFIG["personalidad"]
        ]
    else:
        raise KeyError(f"Sección de configuración desconocida: {section_name}")

    return {
        "section": section_name,
        "label": _CONFIG_SECTION_LABELS[section_name],
        "summary": summary,
        "details": details,
    }


def is_autopilot_configured(config: Dict[str, Any]) -> bool:
    """Indica si la autonomía por fases activa autopilot por configuración."""
    autonomia = config.get("autonomia", {})
    if not isinstance(autonomia, dict):
        return False

    return all(
        autonomia.get(phase_name) == "autonomo"
        for phase_name in _CANONICAL_AUTONOMY_DEFAULTS
    )


def is_autopilot_enabled_for_project(
    project_dir: str,
    state_path: Optional[str] = None,
) -> bool:
    """Resuelve si el proyecto debe operar en autopilot por config o estado.

    Args:
        project_dir: ruta al directorio raíz del proyecto.
        state_path: ruta opcional al fichero de estado. Si no se pasa, usa
            ``.claude/alfred-dev-state.json``.

    Returns:
        True si la config habilita autopilot o si el estado persistido lo marca.
    """
    config = load_project_config(project_dir)
    if is_autopilot_configured(config):
        return True

    resolved_state_path = state_path or os.path.join(
        project_dir,
        ".claude",
        "alfred-dev-state.json",
    )
    try:
        with open(resolved_state_path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, IOError, json.JSONDecodeError):
        return False

    if not isinstance(state, dict):
        return False

    if state.get("autopilot") is True:
        return True

    return state.get("modo") == "autopilot"


def detect_stack(project_dir):
    """
    Detecta el stack tecnológico de un proyecto analizando ficheros clave.

    Examina la presencia de ficheros como package.json, tsconfig.json,
    pyproject.toml, Cargo.toml, go.mod, pom.xml, composer.json,
    ficheros .csproj o Package.swift para inferir el runtime, lenguaje,
    framework y ORM del proyecto.

    La detección de frameworks y ORMs se hace leyendo las dependencias
    declaradas en los manifiestos del proyecto (package.json para Node,
    pyproject.toml para Python, etc.).

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        dict con las claves: runtime, lenguaje, framework, orm, test_runner,
        bundler. Los valores no detectados se devuelven como 'desconocido'
        o 'ninguno' según corresponda.

    Ejemplo:
        >>> stack = detect_stack("/mi-proyecto-next")
        >>> stack["framework"]
        'next'
    """
    stack = {
        "runtime": "desconocido",
        "lenguaje": "desconocido",
        "framework": "desconocido",
        "orm": "ninguno",
        "test_runner": "desconocido",
        "bundler": "desconocido",
    }

    # --- Detección de runtime y lenguaje ---
    # El orden importa: se comprueba primero lo más específico.
    # Si hay package.json es un proyecto Node; la presencia de tsconfig.json
    # lo eleva a TypeScript.

    has_package_json = os.path.isfile(os.path.join(project_dir, "package.json"))
    has_tsconfig = os.path.isfile(os.path.join(project_dir, "tsconfig.json"))
    has_pyproject = os.path.isfile(os.path.join(project_dir, "pyproject.toml"))
    has_setup_py = os.path.isfile(os.path.join(project_dir, "setup.py"))
    has_requirements = os.path.isfile(os.path.join(project_dir, "requirements.txt"))
    has_cargo = os.path.isfile(os.path.join(project_dir, "Cargo.toml"))
    has_go_mod = os.path.isfile(os.path.join(project_dir, "go.mod"))
    has_gemfile = os.path.isfile(os.path.join(project_dir, "Gemfile"))
    has_mix = os.path.isfile(os.path.join(project_dir, "mix.exs"))
    has_pom = os.path.isfile(os.path.join(project_dir, "pom.xml"))
    has_gradle = any(
        os.path.isfile(os.path.join(project_dir, name))
        for name in ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")
    )
    has_composer = os.path.isfile(os.path.join(project_dir, "composer.json"))
    has_dotnet = _has_root_file_with_suffix(project_dir, (".csproj", ".sln"))
    has_package_swift = os.path.isfile(os.path.join(project_dir, "Package.swift"))

    if has_package_json:
        stack["runtime"] = "node"
        stack["lenguaje"] = "typescript" if has_tsconfig else "javascript"
        _detect_node_details(project_dir, stack)
    elif has_pyproject or has_setup_py or has_requirements:
        stack["runtime"] = "python"
        stack["lenguaje"] = "python"
        _detect_python_details(project_dir, stack)
    elif has_cargo:
        stack["runtime"] = "rust"
        stack["lenguaje"] = "rust"
    elif has_go_mod:
        stack["runtime"] = "go"
        stack["lenguaje"] = "go"
    elif has_gemfile:
        stack["runtime"] = "ruby"
        stack["lenguaje"] = "ruby"
    elif has_mix:
        stack["runtime"] = "elixir"
        stack["lenguaje"] = "elixir"
    elif has_pom or has_gradle:
        stack["runtime"] = "jvm"
        stack["lenguaje"] = "kotlin" if _looks_like_kotlin_project(project_dir) else "java"
        _detect_jvm_details(project_dir, stack)
    elif has_composer:
        stack["runtime"] = "php"
        stack["lenguaje"] = "php"
        _detect_php_details(project_dir, stack)
    elif has_dotnet:
        stack["runtime"] = "dotnet"
        stack["lenguaje"] = "csharp"
        _detect_dotnet_details(project_dir, stack)
    elif has_package_swift:
        stack["runtime"] = "swift"
        stack["lenguaje"] = "swift"
        _detect_swift_details(project_dir, stack)

    return stack


# --- Frameworks con interfaz de usuario ---

_FRONTEND_FRAMEWORKS = frozenset({
    "next", "nuxt", "astro", "remix", "gatsby",
    "svelte", "solid-js", "qwik",
    "react", "vue", "angular",
})

_FRONTEND_FRAMEWORK_ALIASES = {
    "nextjs": "next",
    "next.js": "next",
    "reactjs": "react",
    "vuejs": "vue",
    "solid": "solid-js",
}


def has_frontend(stack: dict) -> bool:
    """
    Determina si el stack del proyecto incluye un framework con interfaz de usuario.

    Se usa como condicion de activacion para el agente Selina (la estilista),
    que solo interviene en proyectos que tienen una capa visual.

    Args:
        stack: Diccionario de stack devuelto por ``detect_stack``.
               Se espera que contenga la clave ``"framework"``.

    Returns:
        ``True`` si el framework pertenece al conjunto de frameworks frontend
        conocidos; ``False`` en caso contrario o si la clave no existe.

    Example:
        >>> stack = detect_stack("/ruta/al/proyecto")
        >>> if has_frontend(stack):
        ...     # Activar fase de estilo visual
        ...     pass
    """
    raw_framework = str(stack.get("framework", "desconocido") or "desconocido").strip().lower()
    normalized_framework = _FRONTEND_FRAMEWORK_ALIASES.get(raw_framework, raw_framework)
    return normalized_framework in _FRONTEND_FRAMEWORKS


# --- Funciones internas ---


def _find_first_match(candidates, deps):
    """
    Busca la primera coincidencia entre una lista de candidatos y un conjunto de dependencias.

    Recorre los candidatos en orden y devuelve el primero que aparezca como
    clave en el diccionario/conjunto de dependencias. Se usa para detectar
    frameworks, ORMs, test runners y bundlers por prioridad.

    Args:
        candidates: lista de nombres de paquetes a buscar, en orden de prioridad.
        deps: diccionario o conjunto de dependencias donde buscar.

    Returns:
        str con el nombre del paquete encontrado, o None si no hay coincidencia.
    """
    for candidate in candidates:
        if candidate in deps:
            return candidate
    return None


def _has_root_file_with_suffix(project_dir, suffixes):
    try:
        return any(
            name.endswith(suffixes)
            for name in os.listdir(project_dir)
            if os.path.isfile(os.path.join(project_dir, name))
        )
    except OSError:
        return False


def _read_text_if_exists(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, IOError, UnicodeDecodeError):
        return ""


def _root_file_text(project_dir, names):
    parts = []
    for name in names:
        text = _read_text_if_exists(os.path.join(project_dir, name))
        if text:
            parts.append(text)
    return "\n".join(parts).lower()


def _project_has_source_suffix(project_dir, suffixes, max_depth=3):
    root_depth = len(os.path.abspath(project_dir).split(os.sep))
    ignored = {".git", "node_modules", "vendor", "target", "build", ".build", "bin", "obj"}
    for current, dirs, files in os.walk(project_dir):
        dirs[:] = [name for name in dirs if name not in ignored]
        depth = len(os.path.abspath(current).split(os.sep)) - root_depth
        if depth > max_depth:
            dirs[:] = []
            continue
        if any(name.endswith(suffixes) for name in files):
            return True
    return False


def _looks_like_kotlin_project(project_dir):
    return (
        os.path.isfile(os.path.join(project_dir, "build.gradle.kts"))
        or os.path.isfile(os.path.join(project_dir, "settings.gradle.kts"))
        or _project_has_source_suffix(project_dir, (".kt", ".kts"))
    )


def _extract_python_dependency_names(text):
    """Extrae nombres normalizados de dependencias Python desde texto libre."""
    names = set()
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("["):
            continue

        if line.startswith(('"', "'")):
            match = re.match(r"""^["']([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?""", line)
        else:
            match = re.match(r"""^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?""", line)

        if not match:
            continue

        name = match.group(1).lower().replace("_", "-")
        names.add(name)

    return names


def _normalize_scoped_package(name):
    """
    Normaliza un nombre de paquete con scope (@org/paquete) a su forma base.

    Elimina el prefijo '@' y se queda con la parte del scope (sin el nombre
    del sub-paquete). Por ejemplo: '@nestjs/core' -> 'nestjs', '@prisma/client' -> 'prisma'.
    Los paquetes sin scope se devuelven tal cual.

    Args:
        name: nombre del paquete npm.

    Returns:
        str con el nombre normalizado.
    """
    if name.startswith("@"):
        return name.replace("@", "").split("/")[0]
    return name


def _parse_frontmatter(content):
    """
    Extrae el frontmatter YAML y el cuerpo Markdown de un texto.

    El frontmatter debe estar delimitado por líneas que contengan
    exactamente '---'. El primer delimitador debe ser la primera línea
    no vacía del documento.

    Args:
        content: texto completo del fichero.

    Returns:
        tupla (frontmatter_str, body_str). Si no hay frontmatter,
        frontmatter_str será una cadena vacía.
    """
    # Se busca el patrón ---\n...\n--- al principio del contenido.
    # El grupo central usa .*? (lazy) para detenerse en el primer cierre ---.
    match = re.match(
        r"\A(?:\ufeff)?(?:[ \t]*\n)*---[ \t]*\n(.*?)\n---[ \t]*\n?(.*)",
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1), match.group(2)
    return "", content


def _has_top_level_frontmatter_section(frontmatter: str, section: str) -> bool:
    """Indica si un frontmatter crudo contiene una sección top-level."""
    target = f"{section}:"
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if not stripped or line.startswith((" ", "\t")):
            continue
        if stripped == target:
            return True
    return False


def _strip_accents(value: str) -> str:
    """Normaliza una cadena Unicode retirando acentos para comparaciones."""
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def _normalize_identifier(value: Any) -> Any:
    """Convierte claves humanas a un identificador estable para alias internos."""
    if not isinstance(value, str):
        return value

    normalized = _strip_accents(value).strip().lower()
    normalized = normalized.replace("-", "_").replace(" ", "_")
    return normalized


def _normalize_autonomy_value(value: Any) -> Any:
    """Canaliza variantes como 'autónomo' o 'semi autónomo' al formato ASCII."""
    if not isinstance(value, str):
        return value

    normalized = _normalize_identifier(value)
    return _AUTONOMY_VALUE_ALIASES.get(normalized, value)


def _normalize_autonomy_section(section: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibiliza esquemas antiguos de autonomía con el esquema por fases."""
    primary: Dict[str, Any] = {}
    legacy: Dict[str, Any] = {}
    security_value: Optional[Any] = None

    for raw_key, raw_value in section.items():
        normalized_key = _normalize_identifier(raw_key)
        normalized_value = _normalize_autonomy_value(raw_value)

        if normalized_key == "seguridad":
            security_value = normalized_value
            continue

        if normalized_key in _CANONICAL_AUTONOMY_DEFAULTS:
            primary[normalized_key] = normalized_value
            continue

        alias_target = _LEGACY_AUTONOMY_KEY_ALIASES.get(normalized_key)
        if alias_target is not None:
            legacy[alias_target] = normalized_value
            continue

        primary[raw_key] = normalized_value

    normalized_section = dict(primary)
    for canonical_key, legacy_value in legacy.items():
        normalized_section.setdefault(canonical_key, legacy_value)

    if security_value is not None:
        for phase_name in _SECURITY_PHASES:
            normalized_section.setdefault(phase_name, security_value)

    return normalized_section


def _normalize_loaded_config(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza alias históricos y secciones documentadas a la forma canónica."""
    normalized: Dict[str, Any] = {}

    for raw_key, raw_value in parsed.items():
        canonical_key = _TOP_LEVEL_KEY_ALIASES.get(
            _normalize_identifier(raw_key),
            raw_key,
        )
        normalized_key = _normalize_identifier(canonical_key)

        if normalized_key == "autonomia" and isinstance(raw_value, dict):
            normalized["autonomia"] = _normalize_autonomy_section(raw_value)
            continue

        normalized[canonical_key] = raw_value

    return normalized


def _deep_merge(base, override):
    """
    Fusiona dos diccionarios de forma recursiva.

    Los valores del diccionario 'override' sobreescriben los de 'base'.
    Cuando ambos valores son diccionarios, se fusionan recursivamente
    en lugar de reemplazar el diccionario completo. Esto permite que el
    usuario defina solo las claves que quiere cambiar sin perder los
    valores por defecto del resto.

    Args:
        base: diccionario base (se copia, no se muta).
        override: diccionario con los valores que sobreescriben.

    Returns:
        dict nuevo con la fusión de ambos.

    Ejemplo:
        >>> _deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"x": 99}})
        {'a': {'x': 99, 'y': 2}}
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _parse_yaml(text):
    """
    Parsea un texto YAML y devuelve un diccionario.

    Intenta usar PyYAML si está disponible. En caso contrario, recurre
    a un parser básico que soporta el subconjunto de YAML necesario
    para la configuración del plugin: diccionarios anidados con valores
    escalares (strings, números, booleanos).

    El parser básico no soporta listas, anclas, aliases ni otros
    constructos avanzados de YAML. Para configuraciones complejas
    se recomienda instalar PyYAML.

    Args:
        text: cadena con contenido YAML.

    Returns:
        dict con los valores parseados, o dict vacío si el parseo falla.
    """
    if _HAS_YAML:
        try:
            result = yaml.safe_load(text)
            if not isinstance(result, dict):
                print(
                    "[Alfred Dev] Aviso: el frontmatter YAML no es un diccionario. "
                    "Se ignorará la configuración del fichero.",
                    file=sys.stderr,
                )
                return {}
            return result
        except yaml.YAMLError as e:
            print(
                f"[Alfred Dev] Error de sintaxis en el frontmatter YAML: {e}. "
                f"Se ignorará la configuración del fichero.",
                file=sys.stderr,
            )
            return {}

    return _basic_yaml_parse(text)


def _basic_yaml_parse(text):
    """
    Parser YAML minimalista sin dependencias externas.

    Soporta el subconjunto necesario para la configuración del plugin:
    - Pares clave: valor
    - Anidamiento por indentación (espacios)
    - Valores escalares: strings, enteros, floats, booleanos, null

    No soporta listas, strings multilínea, anclas ni aliases. Esto es
    un fallback para entornos sin PyYAML; en producción se recomienda
    tener PyYAML instalado.

    Args:
        text: cadena con contenido YAML básico.

    Returns:
        dict con los valores parseados.
    """
    result = {}
    # Pila para rastrear el nivel de anidamiento actual.
    # Cada elemento es (indent_level, dict_referencia)
    stack = [(0, result)]

    for line in text.split("\n"):
        # Se ignoran líneas vacías y comentarios
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Se calcula la indentación para determinar el nivel
        indent = len(line) - len(line.lstrip())

        # Se busca el patrón clave: valor
        match = re.match(r"^(\w[\w\-]*):\s*(.*)", stripped)
        if not match:
            continue

        key = match.group(1)
        raw_value = match.group(2).strip()

        # Se retrocede en la pila hasta encontrar el padre correcto
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        parent = stack[-1][1]

        if raw_value:
            # Es un par clave: valor escalar
            parent[key] = _coerce_yaml_value(raw_value)
        else:
            # Es una clave que abre un diccionario anidado
            new_dict = {}
            parent[key] = new_dict
            stack.append((indent, new_dict))

    return result


def _coerce_yaml_value(value):
    """
    Convierte un valor YAML en cadena al tipo Python correspondiente.

    Reglas de conversión:
    - 'true'/'false' (case insensitive) -> bool
    - 'null'/'~' -> None
    - Números enteros -> int
    - Números decimales -> float
    - Strings entre comillas -> string sin comillas
    - Todo lo demás -> string tal cual

    Args:
        value: cadena con el valor YAML crudo.

    Returns:
        valor Python convertido al tipo apropiado.
    """
    # Booleanos
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Null
    if value.lower() in ("null", "~"):
        return None

    # Strings entrecomillados: se eliminan las comillas externas
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    # Enteros
    try:
        return int(value)
    except ValueError:
        pass

    # Floats
    try:
        return float(value)
    except ValueError:
        pass

    return value


def _extract_notes(body):
    """
    Extrae el contenido de la sección de notas del cuerpo Markdown.

    Busca una cabecera (h1-h6) cuyo texto contenga 'Notas' y extrae
    todo el contenido hasta la siguiente cabecera del mismo nivel o
    hasta el final del documento.

    Args:
        body: texto Markdown (sin frontmatter).

    Returns:
        str con el contenido de la sección de notas, o cadena vacía
        si no se encuentra ninguna sección con ese título.
    """
    # Se busca una línea que empiece con # y contenga "Notas".
    # Se usa [^\n]*? (lazy) para evitar backtracking excesivo en líneas largas.
    pattern = re.compile(r"^(#{1,6})\s+[^\n]*?[Nn]otas[^\n]*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""

    header_level = len(match.group(1))
    start = match.end()

    # Se busca la siguiente cabecera del mismo nivel o superior
    next_header = re.compile(
        r"^#{1," + str(header_level) + r"}\s+", re.MULTILINE
    )
    next_match = next_header.search(body, start)

    if next_match:
        notes_text = body[start : next_match.start()]
    else:
        notes_text = body[start:]

    return notes_text.strip()


def _ordered_dict_items(
    data: Dict[str, Any],
    template: Optional[Dict[str, Any]] = None,
) -> List[Tuple[str, Any]]:
    """Devuelve items en orden estable siguiendo un template si existe."""
    seen = set()
    items: List[Tuple[str, Any]] = []

    if isinstance(template, dict):
        for key in template.keys():
            if key in data:
                items.append((key, data[key]))
                seen.add(key)

    for key in data.keys():
        if key not in seen:
            items.append((key, data[key]))
            seen.add(key)

    return items


def _render_yaml_scalar(value: Any) -> str:
    """Renderiza un escalar Python a una forma YAML simple y estable."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)

    text = str(value)
    if not text:
        return '""'

    if re.fullmatch(r"[A-Za-z0-9_./:-]+", text):
        return text

    return json.dumps(text, ensure_ascii=False)


def _render_yaml_mapping(
    data: Dict[str, Any],
    template: Optional[Dict[str, Any]] = None,
    *,
    indent: int = 0,
) -> str:
    """Renderiza un diccionario simple como YAML estable."""
    lines: List[str] = []
    prefix = " " * indent

    for key, value in _ordered_dict_items(data, template):
        if isinstance(value, dict):
            child_template = template.get(key) if isinstance(template, dict) else None
            rendered_child = _render_yaml_mapping(
                value,
                child_template if isinstance(child_template, dict) else None,
                indent=indent + 2,
            )
            lines.append(f"{prefix}{key}:")
            if rendered_child:
                lines.append(rendered_child)
        else:
            lines.append(f"{prefix}{key}: {_render_yaml_scalar(value)}")

    return "\n".join(lines)


def _detect_node_details(project_dir, stack):
    """
    Detecta framework, ORM, test runner y bundler en un proyecto Node.

    Lee el package.json y analiza tanto 'dependencies' como
    'devDependencies' para identificar las herramientas del proyecto.

    Args:
        project_dir: ruta al directorio del proyecto.
        stack: diccionario de stack que se modifica in-place.
    """
    pkg_path = os.path.join(project_dir, "package.json")
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    except (OSError, IOError, json.JSONDecodeError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo leer '{pkg_path}': {e}. "
            f"La detección de framework será incompleta.",
            file=sys.stderr,
        )
        return

    # Se unifican todas las dependencias para buscar en un solo paso
    all_deps = {
        **pkg.get("dependencies", {}),
        **pkg.get("devDependencies", {}),
    }

    # Frameworks: si conviven frontend y backend, priorizamos la UI para que
    # las fases condicionales y sugerencias reflejen la presencia real de interfaz.
    frontend_frameworks = [
        "next", "nuxt", "astro", "remix", "gatsby", "svelte",
        "solid-js", "qwik", "vue", "react", "angular", "@angular/core",
    ]
    backend_frameworks = [
        "hono", "express", "fastify", "koa", "nest", "@nestjs/core",
    ]

    found = _find_first_match(frontend_frameworks, all_deps)
    if not found:
        found = _find_first_match(backend_frameworks, all_deps)
    if found:
        stack["framework"] = _normalize_scoped_package(found)

    # ORMs y query builders
    orms = [
        "drizzle-orm", "prisma", "@prisma/client", "typeorm",
        "sequelize", "knex", "mongoose", "mikro-orm", "@mikro-orm/core",
    ]

    found = _find_first_match(orms, all_deps)
    if found:
        # Se simplifica: @prisma/client -> prisma, drizzle-orm -> drizzle
        name = _normalize_scoped_package(found)
        stack["orm"] = name.replace("-orm", "").replace("-client", "")

    # Test runners
    test_runners = [
        "vitest", "jest", "mocha", "ava", "tap", "playwright", "cypress",
    ]

    found = _find_first_match(test_runners, all_deps)
    if found:
        stack["test_runner"] = found

    # Bundlers
    bundlers = [
        "vite", "webpack", "esbuild", "rollup",
        "parcel", "turbopack", "tsup", "unbuild",
    ]

    found = _find_first_match(bundlers, all_deps)
    if found:
        stack["bundler"] = found


def _detect_python_details(project_dir, stack):
    """
    Detecta framework, ORM y test runner en un proyecto Python.

    Lee pyproject.toml (de forma básica, sin parser TOML completo)
    y requirements.txt para identificar las dependencias.

    Args:
        project_dir: ruta al directorio del proyecto.
        stack: diccionario de stack que se modifica in-place.
    """
    deps_text = ""

    # Se intenta leer pyproject.toml para extraer dependencias
    pyproject_path = os.path.join(project_dir, "pyproject.toml")
    if os.path.isfile(pyproject_path):
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                deps_text += f.read()
        except (OSError, IOError) as e:
            print(
                f"[Alfred Dev] Aviso: no se pudo leer '{pyproject_path}': {e}. "
                f"La detección de framework será incompleta.",
                file=sys.stderr,
            )

    # Se complementa con requirements.txt si existe
    reqs_path = os.path.join(project_dir, "requirements.txt")
    if os.path.isfile(reqs_path):
        try:
            with open(reqs_path, "r", encoding="utf-8") as f:
                deps_text += "\n" + f.read()
        except (OSError, IOError) as e:
            print(
                f"[Alfred Dev] Aviso: no se pudo leer '{reqs_path}': {e}. "
                f"La detección de framework será incompleta.",
                file=sys.stderr,
            )

    dependency_names = _extract_python_dependency_names(deps_text)

    # Frameworks Python (orden = prioridad)
    py_frameworks = [
        "fastapi", "django", "flask", "starlette",
        "litestar", "sanic", "tornado", "aiohttp",
    ]

    found = _find_first_match(py_frameworks, dependency_names)
    if found:
        stack["framework"] = found

    # ORMs Python: se usan tuplas solo cuando la clave de busqueda
    # difiere del nombre que se asigna (django -> django-orm)
    py_orms = [
        ("sqlalchemy", "sqlalchemy"),
        ("sqlmodel", "sqlmodel"),
        ("django", "django-orm"),
        ("tortoise-orm", "tortoise"),
        ("peewee", "peewee"),
        ("pony", "pony"),
    ]

    for dep_name, orm_name in py_orms:
        if dep_name in dependency_names:
            stack["orm"] = orm_name
            break

    # Test runners Python
    py_test_runners = ["pytest", "unittest", "nose"]

    found = _find_first_match(py_test_runners, dependency_names)
    if found:
        stack["test_runner"] = found


def _detect_jvm_details(project_dir, stack):
    """Detecta framework y runner en proyectos Java/Kotlin."""
    text = _root_file_text(
        project_dir,
        (
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
        ),
    )
    if not text:
        return

    framework_markers = (
        ("spring-boot", ("spring-boot", "org.springframework.boot")),
        ("quarkus", ("quarkus", "io.quarkus")),
        ("micronaut", ("micronaut", "io.micronaut")),
    )
    for framework, markers in framework_markers:
        if any(marker in text for marker in markers):
            stack["framework"] = framework
            break

    if "junit" in text:
        stack["test_runner"] = "junit"
    elif "kotest" in text:
        stack["test_runner"] = "kotest"


def _detect_php_details(project_dir, stack):
    """Detecta framework, ORM y runner en proyectos PHP con Composer."""
    composer_path = os.path.join(project_dir, "composer.json")
    try:
        with open(composer_path, "r", encoding="utf-8") as f:
            composer = json.load(f)
    except (OSError, IOError, json.JSONDecodeError):
        return

    deps = {
        **composer.get("require", {}),
        **composer.get("require-dev", {}),
    }

    frameworks = (
        ("laravel", "laravel/framework"),
        ("symfony", "symfony/framework-bundle"),
        ("slim", "slim/slim"),
    )
    for framework, package in frameworks:
        if package in deps:
            stack["framework"] = framework
            break

    if "doctrine/orm" in deps:
        stack["orm"] = "doctrine"
    if "phpunit/phpunit" in deps:
        stack["test_runner"] = "phpunit"
    elif "pestphp/pest" in deps:
        stack["test_runner"] = "pest"


def _detect_dotnet_details(project_dir, stack):
    """Detecta framework, ORM y runner en proyectos C#/.NET."""
    parts = []
    try:
        root_names = os.listdir(project_dir)
    except OSError:
        root_names = []
    for name in root_names:
        if name.endswith((".csproj", ".sln")):
            parts.append(_read_text_if_exists(os.path.join(project_dir, name)))
    text = "\n".join(parts).lower()

    if "microsoft.net.sdk.web" in text:
        stack["framework"] = "aspnet"
    if "microsoft.aspnetcore.components.webassembly" in text or "blazor" in text:
        stack["framework"] = "blazor"
    if "microsoft.entityframeworkcore" in text:
        stack["orm"] = "entity-framework"

    if "xunit" in text:
        stack["test_runner"] = "xunit"
    elif "nunit" in text:
        stack["test_runner"] = "nunit"
    elif "mstest" in text:
        stack["test_runner"] = "mstest"


def _detect_swift_details(project_dir, stack):
    """Detecta framework y runner en proyectos Swift Package Manager."""
    text = _read_text_if_exists(os.path.join(project_dir, "Package.swift")).lower()
    if "vapor" in text:
        stack["framework"] = "vapor"
    if ".testtarget" in text or "swift-testing" in text:
        stack["test_runner"] = "swift-test"


# --- Descubrimiento contextual de agentes opcionales ----------------------


def _has_github_remote(project_dir):
    """Comprueba si el proyecto tiene un remote de GitHub configurado.

    Lee directamente el fichero .git/config para evitar dependencias de
    subprocesos. Solo considera válido un remote cuya URL apunte a GitHub,
    para no sugerir ``github-manager`` en repositorios de GitLab, Bitbucket
    u otras forjas.

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        True si hay al menos un remote de GitHub, False en caso contrario.
    """
    git_config = os.path.join(project_dir, ".git", "config")
    if not os.path.isfile(git_config):
        return False
    try:
        with open(git_config, "r", encoding="utf-8") as f:
            content = f.read().lower()
            return "github.com:" in content or "github.com/" in content
    except (OSError, IOError) as e:
        print(
            f"[Alfred Dev] Aviso: no se pudo leer .git/config: {e}",
            file=sys.stderr,
        )
        return False


def _has_public_html(project_dir):
    """Detecta si el proyecto tiene contenido web público.

    Busca indicadores comunes de sitios web estáticos o landing pages:
    ficheros HTML en la raíz o en directorios típicos (public/, site/, dist/).

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        True si se detectan ficheros HTML públicos, False en caso contrario.
    """
    # Ficheros HTML directos en la raíz
    for name in ("index.html", "index.htm"):
        if os.path.isfile(os.path.join(project_dir, name)):
            return True

    # Directorios típicos de contenido público
    for dirname in ("public", "site", "dist", "docs"):
        dirpath = os.path.join(project_dir, dirname)
        if os.path.isdir(dirpath):
            for entry in os.listdir(dirpath):
                if entry.endswith((".html", ".htm")):
                    return True

    return False


def _scan_dir_for_sources(dirpath, source_extensions, skip_dirs, errors, max_depth, depth=0):
    """Cuenta ficheros de código fuente en un directorio de forma recursiva.

    Recursion controlada por profundidad para evitar latencia excesiva en
    proyectos con node_modules u otros directorios de dependencias grandes.

    Args:
        dirpath: directorio a escanear.
        source_extensions: conjunto de extensiones de código fuente.
        skip_dirs: conjunto de nombres de directorio a ignorar.
        errors: lista mutable donde se acumulan errores de acceso.
        max_depth: profundidad máxima de recursión desde el directorio raíz.
        depth: profundidad actual (0 = directorio raíz).

    Returns:
        int con el número de ficheros de código fuente encontrados.
    """
    count = 0
    try:
        for entry in os.scandir(dirpath):
            if entry.is_file() and os.path.splitext(entry.name)[1] in source_extensions:
                count += 1
            elif entry.is_dir() and entry.name not in skip_dirs and depth < max_depth:
                count += _scan_dir_for_sources(
                    entry.path, source_extensions, skip_dirs, errors, max_depth, depth + 1
                )
    except (OSError, PermissionError) as e:
        errors.append(str(e))
    return count


def _count_source_files(project_dir):
    """Cuenta ficheros de código fuente en el proyecto (hasta 2 niveles de profundidad).

    Recorre hasta 2 niveles de profundidad para evitar latencia excesiva
    en proyectos con node_modules o directorios de dependencias grandes.
    Ignora directorios de dependencias y artefactos conocidos.

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        int con el número de ficheros de código fuente encontrados.
    """
    source_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go",
        ".rb", ".ex", ".exs", ".java", ".kt", ".swift", ".cs",
        ".vue", ".svelte", ".astro", ".php", ".c", ".cpp", ".h",
    }
    skip_dirs = {
        "node_modules", ".git", "dist", "build", ".next", "__pycache__",
        ".venv", "venv", "vendor", "target", ".cargo",
    }
    scan_errors = []
    count = _scan_dir_for_sources(project_dir, source_extensions, skip_dirs, scan_errors, max_depth=2)
    if scan_errors:
        print(
            f"[Alfred Dev] Aviso: no se pudieron escanear {len(scan_errors)} "
            f"directorios. El conteo de ficheros puede ser parcial.",
            file=sys.stderr,
        )
    return count


def _is_memory_enabled(project_dir):
    """Comprueba si la memoria persistente está habilitada en la configuración local.

    Delegamos en el parser canónico de ``core.memory_config`` para evitar
    discrepancias entre la detección de sugerencias y el runtime real.

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        True si la memoria está habilitada, False en caso contrario.
    """
    try:
        from core.memory_config import is_memory_enabled
    except Exception:
        return False

    return is_memory_enabled(project_dir)


def _has_i18n_signals(project_dir):
    """Detecta señales de internacionalización en el proyecto.

    Busca directorios o ficheros típicos de i18n: carpetas ``i18n``,
    ``locales``, ``translations``, ficheros ``*.po``, ``*.xliff`` o
    ficheros de configuración de i18n como ``next-i18next.config.*``,
    ``vue-i18n``, etc.

    Args:
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        True si se detectan señales de internacionalización.
    """
    # Directorios típicos de i18n
    i18n_dirs = ("i18n", "locales", "translations", "lang", "langs")
    for d in i18n_dirs:
        if os.path.isdir(os.path.join(project_dir, d)):
            return True
        if os.path.isdir(os.path.join(project_dir, "src", d)):
            return True

    # Ficheros de configuración de i18n
    i18n_files = (
        "next-i18next.config.js",
        "next-i18next.config.mjs",
        "i18n.config.ts",
        "i18n.config.js",
        ".i18nrc",
        ".i18nrc.json",
    )
    for f in i18n_files:
        if os.path.isfile(os.path.join(project_dir, f)):
            return True

    return False


def _build_suggestion_checks(stack, project_dir):
    """Evalúa las señales del proyecto y devuelve los checks de sugerencia.

    Cada elemento describe un agente opcional candidato con su condición
    de activación y la razón legible para el usuario. El orden determina
    la prioridad de presentación en la UI de configuración.

    Args:
        stack: diccionario de stack detectado por ``detect_stack``.
        project_dir: ruta al directorio raíz del proyecto.

    Returns:
        Lista de tuplas ``(nombre_agente, condicion_bool, razon)``
        listas para filtrar contra la configuración activa.
    """
    framework = stack.get("framework", "desconocido")
    has_public = _has_public_html(project_dir)
    checks = {
        "data-engineer": (
            stack.get("orm", "ninguno") != "ninguno",
            f"Usas {stack.get('orm')} como ORM: te ayuda con esquemas, migraciones y queries",
        ),
        "performance-engineer": (
            _count_source_files(project_dir) > 50,
            "Proyecto con más de 50 ficheros fuente: ayuda con profiling, benchmarks y optimización",
        ),
        "github-manager": (
            _has_github_remote(project_dir),
            "Repositorio con remote GitHub: gestiona PRs, releases, issues y configuración de repo",
        ),
        "librarian": (
            _is_memory_enabled(project_dir),
            "Memoria persistente activa: consulta decisiones, historial y cronología del proyecto bajo demanda",
        ),
        "ux-reviewer": (
            framework in _FRONTEND_FRAMEWORKS,
            f"Proyecto con {framework}: revisa accesibilidad, usabilidad y flujos de usuario",
        ),
        "seo-specialist": (
            has_public,
            "Contenido web público detectado: optimiza SEO, meta tags y datos estructurados",
        ),
        "copywriter": (
            has_public,
            "Textos públicos detectados: mejora copys, CTAs y tono de comunicación",
        ),
        "i18n-specialist": (
            _has_i18n_signals(project_dir),
            "Ficheros de internacionalización detectados: revisa claves, formatos y cadenas hardcodeadas",
        ),
    }
    return [
        (agent_name, *checks[agent_name])
        for agent_name in get_static_suggestible_agent_names()
    ]


def suggest_optional_agents(project_dir, current_config=None):
    """Analiza el proyecto y sugiere agentes opcionales relevantes.

    Examina el stack tecnológico, la presencia de base de datos, frontend,
    contenido web público, remote GitHub y tamaño del proyecto para recomendar
    qué agentes opcionales podrían ser útiles.

    Solo sugiere agentes que no estén ya activados en la configuración actual.

    Args:
        project_dir: ruta al directorio raíz del proyecto.
        current_config: diccionario de configuración actual (opcional).
            Si se proporciona, se filtran los agentes ya activos.

    Returns:
        Lista de tuplas (nombre_agente, razon) con las sugerencias.
        Cada tupla contiene el identificador del agente y una cadena
        explicando por qué se sugiere.

    Ejemplo:
        >>> suggestions = suggest_optional_agents("/mi-proyecto-next")
        >>> suggestions
        [('ux-reviewer', 'Proyecto con frontend Next.js'),
         ('github-manager', 'Repositorio con remote en GitHub')]
    """
    if current_config is None:
        current_config = copy.deepcopy(DEFAULT_CONFIG)

    active = current_config.get("agentes_opcionales", {})
    stack = detect_stack(project_dir)
    checks = _build_suggestion_checks(stack, project_dir)

    return [
        (agent, reason)
        for agent, condition, reason in checks
        if condition and not active.get(agent)
    ]
