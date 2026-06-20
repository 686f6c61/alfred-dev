#!/usr/bin/env python3
"""Catalogo canonico de agentes opcionales del plugin Alfred Dev.

Centraliza el inventario de agentes opcionales para evitar que runtime,
composicion dinamica, sugerencias y documentacion operativa dupliquen listas
con riesgo de derivar entre si.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


OPTIONAL_AGENT_GROUP_ORDER: Tuple[str, ...] = (
    "technical",
    "content",
    "audit",
)

OPTIONAL_AGENT_GROUP_LABELS: Dict[str, str] = {
    "technical": "Tecnicos",
    "content": "Contenido y UX",
    "audit": "Auditoria",
}

OPTIONAL_AGENT_GROUP_QUESTIONS: Dict[str, str] = {
    "technical": "¿Qué agente técnico quieres activar ahora?",
    "content": "¿Qué agente de contenido o UX quieres activar ahora?",
    "audit": "¿Qué auditor externo quieres activar ahora?",
}

OPTIONAL_AGENT_MENU_EXIT = {
    "label": "Seguir sin activar más",
    "description": "Pasar al siguiente grupo",
}

OPTIONAL_AGENT_MENU_DONE = {
    "label": "Listo con este grupo",
    "description": "Mantener la selección actual y pasar al siguiente grupo",
}


OPTIONAL_AGENT_CATALOG: Dict[str, Dict[str, Any]] = {
    "data-engineer": {
        "group": "technical",
        "label": "Data Engineer",
        "specialty": "Modelado de datos, migraciones, queries y persistencia",
        "static_suggestion": True,
        "integration": {
            "fases": ["arquitectura", "desarrollo", "ejecucion_acotada", "diagnostico", "correccion"],
            "posicion": "paralelo",
        },
    },
    "performance-engineer": {
        "group": "technical",
        "label": "Performance Engineer",
        "specialty": "Profiling, latencia, bundles, memoria y cuellos de botella",
        "static_suggestion": True,
        "integration": {
            "fases": ["calidad", "validacion_rapida", "diagnostico", "validacion"],
            "posicion": "paralelo",
        },
    },
    "github-manager": {
        "group": "technical",
        "label": "GitHub Manager",
        "specialty": "PRs, releases, issues, labels y coordinación del repositorio",
        "static_suggestion": True,
        "integration": {
            "fases": ["entrega", "empaquetado", "despliegue"],
            "posicion": "secuencial",
        },
    },
    "librarian": {
        "group": "technical",
        "label": "Librarian",
        "specialty": "Memoria persistente, decisiones previas y cronología del proyecto",
        "static_suggestion": True,
        "runtime_mode": "on_demand",
        "integration": {
            "fases": [],
            "posicion": "none",
        },
    },
    "ux-reviewer": {
        "group": "content",
        "label": "UX Reviewer",
        "specialty": "Accesibilidad, usabilidad y flujos de interfaz",
        "static_suggestion": True,
        "integration": {
            "fases": ["calidad", "producto", "ejecucion_acotada", "validacion_rapida", "diagnostico", "validacion"],
            "posicion": "paralelo",
        },
    },
    "seo-specialist": {
        "group": "content",
        "label": "SEO Specialist",
        "specialty": "SEO técnico, datos estructurados y Core Web Vitals",
        "static_suggestion": True,
        "integration": {
            "fases": ["calidad", "validacion_rapida", "validacion"],
            "posicion": "paralelo",
        },
    },
    "copywriter": {
        "group": "content",
        "label": "Copywriter",
        "specialty": "Microcopy, CTAs, tono y textos visibles para usuario",
        "static_suggestion": True,
        "integration": {
            "fases": ["documentacion", "ejecucion_acotada", "correccion"],
            "posicion": "paralelo",
        },
    },
    "i18n-specialist": {
        "group": "content",
        "label": "i18n Specialist",
        "specialty": "Internacionalización, locales y cadenas hardcodeadas",
        "static_suggestion": True,
        "integration": {
            "fases": ["desarrollo", "calidad", "ejecucion_acotada", "validacion_rapida", "correccion", "validacion"],
            "posicion": "paralelo",
        },
    },
    "lucius": {
        "group": "audit",
        "label": "Lucius",
        "specialty": "Segunda opinión técnica externa y auditoría de cierre",
        "static_suggestion": False,
        "integration": {
            "fases": ["calidad", "validacion_rapida", "validacion", "auditoria_final", "auditoria_paralela"],
            "posicion": "secuencial",
        },
    },
}


def get_optional_agent_names() -> Tuple[str, ...]:
    """Devuelve los nombres de agentes opcionales en orden canonico."""
    return tuple(OPTIONAL_AGENT_CATALOG.keys())


def get_optional_agent_display_label(agent_name: str) -> str:
    """Devuelve el label visible canónico de un agente opcional."""
    metadata = OPTIONAL_AGENT_CATALOG.get(agent_name)
    if metadata is None:
        raise KeyError(f"Agente opcional desconocido: {agent_name}")
    return metadata["label"]


def get_optional_agent_specialty(agent_name: str) -> str:
    """Devuelve la descripción breve canónica del agente."""
    metadata = OPTIONAL_AGENT_CATALOG.get(agent_name)
    if metadata is None:
        raise KeyError(f"Agente opcional desconocido: {agent_name}")
    return metadata["specialty"]


def is_optional_agent_on_demand_only(agent_name: str) -> bool:
    """Indica si el agente no se integra automáticamente en fases."""
    metadata = OPTIONAL_AGENT_CATALOG.get(agent_name)
    if metadata is None:
        raise KeyError(f"Agente opcional desconocido: {agent_name}")
    return metadata.get("runtime_mode") == "on_demand"


def order_optional_agent_names(names: Iterable[str]) -> List[str]:
    """Ordena una colección de agentes siguiendo el catálogo canónico.

    Los nombres desconocidos se conservan al final, ordenados alfabéticamente,
    para no perder señal útil si entra algún valor legacy o externo.
    """
    seen = []
    for raw_name in names:
        agent_name = str(raw_name).strip()
        if agent_name and agent_name not in seen:
            seen.append(agent_name)

    ordered = [
        agent_name
        for agent_name in get_optional_agent_names()
        if agent_name in seen
    ]
    extras = sorted(
        agent_name
        for agent_name in seen
        if agent_name not in OPTIONAL_AGENT_CATALOG
    )
    return ordered + extras


def build_optional_agent_flags(default: bool = False) -> Dict[str, bool]:
    """Construye el bloque de flags bool para config/equipo_sesion."""
    return {
        agent_name: bool(default)
        for agent_name in get_optional_agent_names()
    }


def get_optional_agents_by_group() -> Dict[str, List[str]]:
    """Agrupa los agentes opcionales por grupo manteniendo el orden canonico."""
    grouped: Dict[str, List[str]] = {
        group_name: []
        for group_name in OPTIONAL_AGENT_GROUP_ORDER
    }
    for agent_name, metadata in OPTIONAL_AGENT_CATALOG.items():
        grouped[metadata["group"]].append(agent_name)
    return grouped


def build_optional_agent_menu_option(
    agent_name: str,
    *,
    suggested_reason: Optional[str] = None,
    active: bool = False,
) -> Dict[str, str]:
    """Construye una opción navegable canónica para AskUserQuestion.

    Args:
        agent_name: nombre canónico del agente.
        suggested_reason: razón contextual de recomendación. Si existe, el label
            se marca con ``(Recomendado)`` y la descripción usa esa razón.
        active: si ya está activo en la configuración actual.
    """
    label = get_optional_agent_display_label(agent_name)
    description = get_optional_agent_specialty(agent_name)

    if suggested_reason:
        label = f"{label} (Recomendado)"
        description = suggested_reason.strip()

    if is_optional_agent_on_demand_only(agent_name):
        description = (
            f"{description}. Solo bajo demanda: no entra automáticamente "
            "en ninguna fase."
        )

    if active:
        description = f"{description}. Activo actualmente."

    return {"label": label, "description": description}


def build_optional_agent_group_menu(
    group_name: str,
    *,
    suggested_reasons: Optional[Dict[str, str]] = None,
    active_names: Optional[Iterable[str]] = None,
    excluded_names: Optional[Iterable[str]] = None,
    include_done_option: bool = False,
) -> Dict[str, Any]:
    """Construye el menú navegable canónico de un grupo de opcionales.

    El menú siempre empieza con una salida explícita para que el usuario pueda
    avanzar sin quedar atrapado. Las opciones restantes aparecen en el orden
    canónico del catálogo y pueden excluir agentes ya elegidos en iteraciones
    previas del mismo grupo.
    """
    if group_name not in OPTIONAL_AGENT_GROUP_LABELS:
        raise KeyError(f"Grupo desconocido: {group_name}")

    suggested_reasons = suggested_reasons or {}
    active_set: Set[str] = set(active_names or ())
    excluded_set: Set[str] = set(excluded_names or ())

    options: List[Dict[str, str]] = [dict(OPTIONAL_AGENT_MENU_EXIT)]
    if include_done_option:
        options.append(dict(OPTIONAL_AGENT_MENU_DONE))

    for agent_name in get_optional_agents_by_group()[group_name]:
        if agent_name in excluded_set:
            continue
        options.append(
            build_optional_agent_menu_option(
                agent_name,
                suggested_reason=suggested_reasons.get(agent_name),
                active=agent_name in active_set,
            )
        )

    return {
        "group": group_name,
        "header": OPTIONAL_AGENT_GROUP_LABELS[group_name],
        "question": OPTIONAL_AGENT_GROUP_QUESTIONS[group_name],
        "options": options,
    }


def build_optional_agent_group_menus(
    *,
    suggested_reasons: Optional[Dict[str, str]] = None,
    active_names: Optional[Iterable[str]] = None,
    excluded_names_by_group: Optional[Dict[str, Iterable[str]]] = None,
    include_done_option: bool = False,
) -> List[Dict[str, Any]]:
    """Devuelve los tres menús navegables canónicos en el orden oficial."""
    menus: List[Dict[str, Any]] = []
    excluded_names_by_group = excluded_names_by_group or {}

    for group_name in OPTIONAL_AGENT_GROUP_ORDER:
        menus.append(
            build_optional_agent_group_menu(
                group_name,
                suggested_reasons=suggested_reasons,
                active_names=active_names,
                excluded_names=excluded_names_by_group.get(group_name),
                include_done_option=include_done_option,
            )
        )
    return menus


def get_static_suggestible_agent_names() -> Tuple[str, ...]:
    """Agentes sugeribles por I/O estatico del proyecto.

    Lucius queda fuera deliberadamente: se activa por contexto de tarea,
    no por heuristicas de stack.
    """
    return tuple(
        agent_name
        for agent_name, metadata in OPTIONAL_AGENT_CATALOG.items()
        if metadata.get("static_suggestion", False)
    )


def get_optional_integrations() -> Dict[str, Dict[str, Any]]:
    """Devuelve una copia ligera de las integraciones por fase."""
    return {
        agent_name: {
            "fases": list(metadata["integration"]["fases"]),
            "posicion": metadata["integration"]["posicion"],
        }
        for agent_name, metadata in OPTIONAL_AGENT_CATALOG.items()
    }
