#!/usr/bin/env python3
"""Renderizado y escritura del artefacto docs/style-direction.md."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.selina_visual import read_latest_style_choice, resolve_state_dir


STYLE_DIRECTION_DOC_RELATIVE_PATH = os.path.join("docs", "style-direction.md")


def resolve_visual_session_dir(path: str) -> str:
    """Acepta session_dir o state_dir y devuelve el session_dir real."""
    state_dir = resolve_state_dir(path)
    return os.path.dirname(state_dir)


def discover_proposals_file(visual_path: str) -> Optional[str]:
    """Busca el sidecar JSON de propuestas en ubicaciones canónicas."""
    session_dir = resolve_visual_session_dir(visual_path)
    state_dir = resolve_state_dir(visual_path)
    candidates = [
        os.path.join(session_dir, "content", "style-options.json"),
        os.path.join(session_dir, "content", "proposals.json"),
        os.path.join(state_dir, "style-options.json"),
        os.path.join(state_dir, "proposals.json"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _coerce_string(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_coerce_string(item) for item in value if _coerce_string(item)]
    text = _coerce_string(value)
    return [text] if text else []


def _merge_unique_texts(*values: Any) -> List[str]:
    items: List[str] = []
    seen = set()
    for value in values:
        for item in _coerce_list(value):
            key = item.casefold()
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
    return items


def _normalize_palette(value: Any) -> List[Dict[str, str]]:
    if isinstance(value, dict):
        return [
            {"role": _coerce_string(role), "value": _coerce_string(color)}
            for role, color in value.items()
            if _coerce_string(role) and _coerce_string(color)
        ]
    if isinstance(value, list):
        items: List[Dict[str, str]] = []
        raw_colors: List[str] = []
        for entry in value:
            if isinstance(entry, dict):
                role = _coerce_string(entry.get("role") or entry.get("name"))
                color = _coerce_string(entry.get("value") or entry.get("color"))
                if role and color:
                    items.append({"role": role, "value": color})
                    continue
            color = _coerce_string(entry)
            if color:
                raw_colors.append(color)
        if items:
            return items
        if raw_colors:
            default_roles = [
                "surface",
                "surface_alt",
                "accent",
                "accent_alt",
                "ink",
                "muted",
            ]
            return [
                {
                    "role": default_roles[idx] if idx < len(default_roles) else f"color_{idx + 1}",
                    "value": color,
                }
                for idx, color in enumerate(raw_colors)
            ]
    return []


def _normalize_tokens(value: Any) -> List[Dict[str, str]]:
    if isinstance(value, dict):
        return [
            {"name": _coerce_string(name), "value": _coerce_string(token_value)}
            for name, token_value in value.items()
            if _coerce_string(name) and _coerce_string(token_value)
        ]
    if isinstance(value, list):
        items: List[Dict[str, str]] = []
        for entry in value:
            if isinstance(entry, dict):
                name = _coerce_string(entry.get("name"))
                token_value = _coerce_string(entry.get("value"))
                if name and token_value:
                    items.append({"name": name, "value": token_value})
        return items
    return []


def _normalize_typography(value: Any) -> Dict[str, str]:
    if isinstance(value, str):
        text = _coerce_string(value)
        if not text:
            return {}
        normalized: Dict[str, str] = {}
        families, separator, notes = text.partition("—")
        families = _coerce_string(families)
        notes = _coerce_string(notes if separator else "")
        parts = [part.strip() for part in families.split("/") if _coerce_string(part)]
        if parts:
            normalized["headings"] = parts[0]
        if len(parts) > 1:
            normalized["body"] = parts[1]
        if notes:
            normalized["notes"] = notes
        elif families:
            normalized["notes"] = families
        return normalized
    if not isinstance(value, dict):
        return {}
    normalized: Dict[str, str] = {}
    for key in (
        "pairing_id",
        "pairing_label",
        "headings",
        "body",
        "scale",
        "notes",
        "headings_url",
        "body_url",
        "css_url",
        "source",
        "custom_url",
    ):
        text = _coerce_string(value.get(key))
        if text:
            normalized[key] = text
    return normalized


def _normalize_reference_urls(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []

    items: List[Dict[str, str]] = []
    for entry in value:
        if isinstance(entry, dict):
            label = _coerce_string(entry.get("label") or entry.get("name") or entry.get("title"))
            url = _coerce_string(entry.get("url") or entry.get("href"))
            if label and url:
                items.append({"label": label, "url": url})
                continue

        if isinstance(entry, str):
            url = _coerce_string(entry)
            if url:
                items.append({"label": url, "url": url})
    return items


def _semantic_source_text(proposal: Dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            proposal.get("name", ""),
            proposal.get("concept", ""),
            proposal.get("tone", ""),
            proposal.get("rationale", ""),
            " ".join(proposal.get("context_signals", [])),
            " ".join(proposal.get("visual_principles", [])),
            proposal.get("layout_grammar", ""),
            proposal.get("surface_treatment", ""),
            proposal.get("shape_language", ""),
            proposal.get("motion_language", ""),
            " ".join(proposal.get("signature_elements", [])),
            " ".join(proposal.get("implementation_guardrails", [])),
            proposal.get("prompt_seed", ""),
            " ".join(item.get("role", "") for item in proposal.get("palette", [])),
        ]
        if part
    ).lower()


def _matches_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _infer_direction_flavor(proposal: Dict[str, Any]) -> str:
    text = _semantic_source_text(proposal)
    if _matches_any(
        text,
        ["grafana", "datadog", "monitorizacion", "monitorización", "dark", "oscuro", "tiempo real", "24/7"],
    ):
        return "technical"
    if _matches_any(
        text,
        ["editorial", "premium", "lujo", "magazine", "revista", "serif", "cálid", "calid"],
    ):
        return "editorial"
    if _matches_any(
        text,
        ["dashboard", "dato", "analítica", "analitica", "operativ", "enterprise", "métrica", "metrica"],
    ):
        return "operational"
    if _matches_any(
        text,
        ["minimal", "limpio", "clean", "airead", "sobrio", "negativo", "claridad", "linear", "notion", "attio", "saas moderno", "whitespace"],
    ):
        return "minimal"
    if _matches_any(
        text,
        ["vibrante", "expresiv", "energ", "bold", "experimental", "memorable", "impacto"],
    ):
        return "expressive"
    return "balanced"


def _human_join(items: List[str]) -> str:
    clean = [item for item in (_coerce_string(item) for item in items) if item]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} y {clean[1]}"
    return f"{', '.join(clean[:-1])} y {clean[-1]}"


def _lower_first(text: str) -> str:
    cleaned = _coerce_string(text)
    if not cleaned:
        return ""
    return cleaned[:1].lower() + cleaned[1:]


def _infer_tone(flavor: str) -> str:
    return {
        "editorial": "Cálido, curado y con sensación premium.",
        "technical": "Técnico, preciso y orientado a monitorización continua.",
        "operational": "Preciso, claro y orientado a decisión.",
        "minimal": "Sobrio, ligero y muy enfocado.",
        "expressive": "Vibrante, seguro y memorable.",
        "balanced": "Equilibrado, contemporáneo y fácil de leer.",
    }[flavor]


def _infer_concept(flavor: str) -> str:
    return {
        "editorial": "Lenguaje editorial con jerarquía clara, ritmo pausado y sensación cuidada.",
        "technical": "Interfaz técnica de contraste alto, señales semánticas claras y lectura inmediata del estado.",
        "operational": "Interfaz orientada a escaneo rápido, comparación y priorización de información.",
        "minimal": "Sistema limpio y enfocado, con mucho aire y una jerarquía simple.",
        "expressive": "Dirección con acento expresivo, contraste claro y personalidad reconocible.",
        "balanced": "Dirección equilibrada, con jerarquía clara y personalidad contenida.",
    }[flavor]


def _infer_spacing_density(flavor: str) -> str:
    return {
        "editorial": "Aireada, con bloques respirables y jerarquía pausada.",
        "technical": "Alta, con bloques compactos, lectura de estado y jerarquía de monitorización.",
        "operational": "Media-alta, pensada para escaneo rápido y densidad controlada.",
        "minimal": "Aireada, con mucho espacio negativo y pocos cambios de ritmo.",
        "expressive": "Media, con ritmo dinámico y contraste claro entre bloques.",
        "balanced": "Equilibrada, con margen suficiente y lectura cómoda.",
    }[flavor]


def _infer_sample_component(flavor: str) -> str:
    return {
        "editorial": "Hero editorial con titular protagonista, sumario breve y CTA sobrio.",
        "technical": "Panel técnico con estados, series temporales y alertas semánticas de alto contraste.",
        "operational": "Panel de resumen con métricas clave, estado visible y CTA contextual.",
        "minimal": "Hero de producto con beneficio principal, prueba social y CTA dominante.",
        "expressive": "Tarjeta o hero protagonista con visual dominante, titular corto y CTA muy claro.",
        "balanced": "Sección de resumen con titular fuerte, supporting copy y CTA principal.",
    }[flavor]


def _infer_context_signals(flavor: str) -> List[str]:
    return {
        "editorial": ["Necesidad de transmitir criterio, calma y sensación de cuidado."],
        "technical": ["Necesidad de monitorización continua, contraste alto y lectura rápida del estado."],
        "operational": ["Necesidad de lectura rápida, foco operativo y baja ambigüedad visual."],
        "minimal": ["Necesidad de claridad inmediata y reducción de ruido visual."],
        "expressive": ["Necesidad de identidad fuerte y recordación sin perder legibilidad."],
        "balanced": ["Necesidad de equilibrio entre personalidad visual y facilidad de uso."],
    }[flavor]


def _signals_to_rationale_prefix(signals: List[str]) -> str:
    cleaned = [_coerce_string(item).rstrip(".!?") for item in signals if _coerce_string(item)]
    if not cleaned:
        return ""

    lowered = [_lower_first(item) for item in cleaned]
    if all(item.startswith("necesidad de ") for item in lowered):
        needs = [item[len("necesidad de "):] for item in lowered]
        return f"Funciona bien cuando el producto necesita {_human_join(needs)}"

    return f"Funciona bien en contextos con {_lower_first(_human_join(cleaned))}"


def _infer_rationale(proposal: Dict[str, Any], flavor: str) -> str:
    signals = proposal.get("context_signals", [])
    if signals:
        concept_phrase = _lower_first(
            _coerce_string(proposal["concept"] or _infer_concept(flavor)).rstrip(".!?")
        )
        return (
            f"{_signals_to_rationale_prefix(signals[:2])} "
            f"porque refuerza {concept_phrase}."
        )

    return {
        "editorial": "Funciona bien cuando el producto necesita transmitir criterio, calma y sensación de cuidado.",
        "technical": "Funciona bien cuando el producto necesita monitorización continua, alto contraste y señales semánticas inequívocas.",
        "operational": "Funciona bien cuando el producto necesita confianza operativa, lectura rápida y foco en la tarea.",
        "minimal": "Funciona bien cuando el producto necesita claridad inmediata, foco y una primera impresión limpia.",
        "expressive": "Funciona bien cuando el producto necesita identidad visible y energía controlada sin perder legibilidad.",
        "balanced": "Funciona bien cuando el producto necesita personalidad contenida y una jerarquía fácil de entender.",
    }[flavor]


def _infer_not_this_direction(flavor: str) -> List[str]:
    return {
        "editorial": [
            "No es una UI de dashboard densa ni orientada a monitorización.",
            "No busca agresividad cromática ni sensación de producto técnico frío.",
        ],
        "technical": [
            "No es una propuesta lifestyle ni de marketing aspiracional.",
            "No prioriza calidez editorial ni respiración generosa sobre lectura de estado.",
        ],
        "operational": [
            "No es una propuesta lifestyle o de revista.",
            "No prioriza ornamento sobre legibilidad operativa.",
        ],
        "minimal": [
            "No es maximalista ni ornamental.",
            "No busca apariencia enterprise pesada ni recargada.",
        ],
        "expressive": [
            "No es minimalismo silencioso ni neutral.",
            "No busca una estética corporativa plana o sin tensión visual.",
        ],
        "balanced": [
            "No busca ruido visual ni decisiones ornamentales sin función.",
            "No pretende una estética extrema a costa de la claridad.",
        ],
    }[flavor]


def _enrich_proposal_semantics(proposal: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(proposal)
    flavor = _infer_direction_flavor(enriched)

    if not enriched.get("tone"):
        enriched["tone"] = _infer_tone(flavor)
    if not enriched.get("concept"):
        enriched["concept"] = _infer_concept(flavor)
    if not enriched.get("spacing_density"):
        enriched["spacing_density"] = _infer_spacing_density(flavor)
    if not enriched.get("sample_component"):
        enriched["sample_component"] = _infer_sample_component(flavor)
    if not enriched.get("context_signals"):
        enriched["context_signals"] = _infer_context_signals(flavor)
    if not enriched.get("rationale"):
        enriched["rationale"] = _infer_rationale(enriched, flavor)
    if not enriched.get("not_this_direction"):
        enriched["not_this_direction"] = _infer_not_this_direction(flavor)
    if not enriched.get("visual_principles"):
        enriched["visual_principles"] = [
            _infer_concept(flavor),
            _infer_spacing_density(flavor),
        ]
    if not enriched.get("layout_grammar"):
        enriched["layout_grammar"] = _infer_sample_component(flavor)
    if not enriched.get("surface_treatment"):
        enriched["surface_treatment"] = _infer_tone(flavor)
    if not enriched.get("shape_language"):
        enriched["shape_language"] = _infer_concept(flavor)
    if not enriched.get("motion_language"):
        enriched["motion_language"] = "Interacciones sobrias y coherentes con la jerarquia principal."
    if not enriched.get("signature_elements"):
        enriched["signature_elements"] = [enriched["sample_component"]]
    if not enriched.get("implementation_guardrails"):
        enriched["implementation_guardrails"] = list(enriched["not_this_direction"])
    if not enriched.get("prompt_seed"):
        enriched["prompt_seed"] = (
            f"Manten una direccion {flavor} coherente con el producto y evita mezclarla con sistemas visuales ajenos."
        )

    return enriched


def _normalize_single_proposal(choice: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
    name = _coerce_string(
        proposal.get("name")
        or proposal.get("label")
        or proposal.get("title")
        or choice
    )
    return _enrich_proposal_semantics({
        "choice": _coerce_string(choice),
        "name": name,
        "concept": _coerce_string(
            proposal.get("concept")
            or proposal.get("description")
            or proposal.get("summary")
            or proposal.get("pitch")
            or proposal.get("preview_copy")
        ),
        "style_family": _coerce_string(
            proposal.get("style_family")
            or proposal.get("style_trend")
            or proposal.get("trend_id")
            or proposal.get("style_id")
            or proposal.get("family")
        ),
        "style_family_label": _coerce_string(
            proposal.get("style_family_label")
            or proposal.get("trend_name")
            or proposal.get("style_name")
            or proposal.get("family_label")
        ),
        "palette_mode": _coerce_string(
            proposal.get("palette_mode")
            or proposal.get("color_mode")
            or proposal.get("palette_variant")
        ),
        "palette_mode_label": _coerce_string(
            proposal.get("palette_mode_label")
            or proposal.get("color_mode_label")
            or proposal.get("palette_variant_label")
        ),
        "variant_id": _coerce_string(
            proposal.get("variant_id")
            or proposal.get("variant")
        ),
        "variant_label": _coerce_string(
            proposal.get("variant_label")
            or proposal.get("variant_name")
        ),
        "preview_flavor": _coerce_string(proposal.get("preview_flavor")),
        "palette": _normalize_palette(proposal.get("palette")),
        "typography": _normalize_typography(proposal.get("typography")),
        "reference_urls": _normalize_reference_urls(
            proposal.get("reference_urls")
            or proposal.get("references")
            or proposal.get("example_urls")
            or proposal.get("inspiration_urls")
        ),
        "spacing_density": _coerce_string(
            proposal.get("spacing_density")
            or proposal.get("density")
            or proposal.get("spacing")
            or proposal.get("layout_density")
            or proposal.get("density_notes")
        ),
        "tone": _coerce_string(
            proposal.get("tone")
            or proposal.get("tone_visual")
            or proposal.get("tone_visual_general")
            or proposal.get("personality")
            or proposal.get("mood")
        ),
        "sample_component": _coerce_string(
            proposal.get("sample_component")
            or proposal.get("sample")
            or proposal.get("component")
            or proposal.get("component_example")
            or proposal.get("example_component")
            or proposal.get("hero_example")
        ),
        "visual_principles": _merge_unique_texts(
            proposal.get("visual_principles")
            or proposal.get("design_principles")
            or proposal.get("principles")
        ),
        "layout_grammar": _coerce_string(
            proposal.get("layout_grammar")
            or proposal.get("layout_principles")
            or proposal.get("composition_grammar")
        ),
        "surface_treatment": _coerce_string(
            proposal.get("surface_treatment")
            or proposal.get("surface_language")
            or proposal.get("materiality")
        ),
        "shape_language": _coerce_string(
            proposal.get("shape_language")
            or proposal.get("form_language")
            or proposal.get("shape_system")
        ),
        "motion_language": _coerce_string(
            proposal.get("motion_language")
            or proposal.get("motion_character")
            or proposal.get("interaction_motion")
        ),
        "signature_elements": _merge_unique_texts(
            proposal.get("signature_elements")
            or proposal.get("signature_motifs")
            or proposal.get("visual_motifs")
        ),
        "implementation_guardrails": _merge_unique_texts(
            proposal.get("implementation_guardrails")
            or proposal.get("guardrails")
            or proposal.get("execution_guardrails")
        ),
        "prompt_seed": _coerce_string(
            proposal.get("prompt_seed")
            or proposal.get("design_prompt")
            or proposal.get("prompt_injection")
        ),
        "rationale": _coerce_string(
            proposal.get("rationale")
            or proposal.get("why")
            or proposal.get("reason")
            or proposal.get("justification")
        ),
        "not_this_direction": _merge_unique_texts(
            proposal.get("not_this_direction")
            or proposal.get("anti_goals")
            or proposal.get("non_goals")
            or proposal.get("anti_patterns")
            or proposal.get("avoid")
        ),
        "tokens": _normalize_tokens(proposal.get("tokens")),
        "context_signals": _merge_unique_texts(
            proposal.get("context_signals"),
            proposal.get("signals"),
            proposal.get("audience"),
            proposal.get("product_signals"),
            proposal.get("constraints"),
            proposal.get("fit_for"),
        ),
    })


def load_style_proposals(proposals_file: str) -> Dict[str, Dict[str, Any]]:
    """Carga y normaliza el sidecar JSON de propuestas de Selina."""
    with open(proposals_file, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    if isinstance(raw, dict) and isinstance(raw.get("proposals"), list):
        source = raw.get("proposals")
    else:
        source = raw

    proposals: Dict[str, Dict[str, Any]] = {}
    if isinstance(source, list):
        for entry in source:
            if not isinstance(entry, dict):
                continue
            choice = _coerce_string(entry.get("choice"))
            if not choice:
                continue
            proposals[choice] = _normalize_single_proposal(choice, entry)
    elif isinstance(source, dict):
        for choice, entry in source.items():
            if not isinstance(entry, dict):
                continue
            normalized_choice = _coerce_string(entry.get("choice") or choice)
            if not normalized_choice:
                continue
            proposals[normalized_choice] = _normalize_single_proposal(normalized_choice, entry)

    return proposals


def build_style_direction_record(
    visual_path: str,
    *,
    proposals_file: Optional[str] = None,
    choice_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Combina la elección registrada y la propuesta seleccionada."""
    selected_choice = read_latest_style_choice(visual_path)
    if selected_choice is None and not choice_override:
        raise ValueError("No hay ninguna elección válida registrada todavía.")

    proposals_path = proposals_file or discover_proposals_file(visual_path)
    if not proposals_path:
        raise ValueError("No se ha encontrado ningún fichero de propuestas de Selina.")

    proposals = load_style_proposals(proposals_path)
    choice = _coerce_string(choice_override or (selected_choice or {}).get("choice"))
    if choice not in proposals:
        raise ValueError(f"La opción elegida '{choice}' no existe en el sidecar de propuestas.")

    proposal = proposals[choice]
    selected_label = _coerce_string((selected_choice or {}).get("label")) or proposal["name"]
    selected_at = _coerce_string((selected_choice or {}).get("timestamp"))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "choice": choice,
        "selected_label": selected_label,
        "selected_at": selected_at,
        "proposal": proposal,
        "proposals_file": proposals_path,
    }


def _render_table(headers: List[str], rows: List[List[str]]) -> List[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _fallback_text(value: str, fallback: str = "Sin documentar todavía.") -> str:
    return value or fallback


def _ensure_sentence(text: str) -> str:
    cleaned = _coerce_string(text)
    if not cleaned:
        return ""
    if cleaned[-1] in ".!?":
        return cleaned
    return f"{cleaned}."


def _proposal_source_label(record: Dict[str, Any]) -> str:
    proposals_file = _coerce_string(record.get("proposals_file"))
    if not proposals_file:
        return ""

    visual_session_dir = _coerce_string(record.get("visual_session_dir"))
    if visual_session_dir:
        try:
            session_root = os.path.abspath(visual_session_dir)
            proposals_path = os.path.abspath(proposals_file)
            if os.path.commonpath([session_root, proposals_path]) == session_root:
                return os.path.relpath(proposals_path, session_root)
        except ValueError:
            pass

    project_dir = _coerce_string(record.get("project_dir"))
    if project_dir:
        try:
            project_root = os.path.abspath(project_dir)
            proposals_path = os.path.abspath(proposals_file)
            if os.path.commonpath([project_root, proposals_path]) == project_root:
                return os.path.relpath(proposals_path, project_root)
        except ValueError:
            pass

    return os.path.basename(proposals_file)


def render_style_direction_markdown(record: Dict[str, Any]) -> str:
    """Genera el Markdown final de docs/style-direction.md."""
    proposal = _normalize_single_proposal(
        _coerce_string(record.get("choice") or (record.get("proposal") or {}).get("choice") or "A"),
        dict(record["proposal"]),
    )
    decision_summary = _ensure_sentence(
        proposal["concept"] or proposal["tone"] or proposal["rationale"]
    ) or "Selina deja la dirección elegida registrada, pero todavía falta enriquecer la intención visual."
    rationale = _fallback_text(
        proposal["rationale"],
        "Falta aterrizar por qué esta propuesta gana frente a las demás.",
    )
    proposals_source = _proposal_source_label(record)
    lines: List[str] = [
        "# Sistema de diseño base",
        "",
        "## Resumen",
        "",
        f"Selina recomienda `{record['choice']}` — {record['selected_label']} como sistema de diseño base para esta fase.",
        "",
        f"Esta opción prioriza {decision_summary[0].lower() + decision_summary[1:] if len(decision_summary) > 1 else decision_summary.lower()}",
        "",
        f"- Nombre operativo: **{proposal['name']}**",
    ]
    if record.get("selected_at"):
        lines.append(f"- Elección registrada en: {record['selected_at']}")
    lines.extend(
        [
            f"- Artefacto generado: `{STYLE_DIRECTION_DOC_RELATIVE_PATH}`",
            "",
            "## Sistema de diseño elegido",
            "",
            f"**Nombre:** {proposal['name']}",
            "",
            f"**Concepto:** {_fallback_text(proposal['concept'])}",
            "",
        ]
    )

    if proposal.get("style_family_label") or proposal.get("style_family"):
        family_label = proposal.get("style_family_label") or proposal.get("style_family")
        lines.extend(
            [
                "### Base del sistema",
                "",
                f"- Familia: {family_label}",
            ]
        )
        if proposal.get("style_family"):
            lines.append(f"- Id canónico: `{proposal['style_family']}`")
        if proposal.get("palette_mode"):
            palette_mode_label = proposal.get("palette_mode_label") or proposal["palette_mode"]
            lines.append(f"- Modo de paleta: **{palette_mode_label}**")
            if palette_mode_label != proposal["palette_mode"]:
                lines.append(f"- Id de paleta: `{proposal['palette_mode']}`")
        if proposal.get("variant_label"):
            lines.append(f"- Variante final: **{proposal['variant_label']}**")
        lines.append("")

    lines.extend(["### Paleta", ""])
    if proposal["palette"]:
        lines.extend(
            _render_table(
                ["Rol", "Valor"],
                [[item["role"], item["value"]] for item in proposal["palette"]],
            )
        )
    else:
        lines.append("Pendiente de documentar.")

    lines.extend(["", "### Tipografía", ""])
    typography = proposal["typography"]
    if typography:
        if typography.get("pairing_label"):
            lines.append(f"- Pairing: {typography['pairing_label']}")
        if typography.get("pairing_id"):
            lines.append(f"- Id pairing: `{typography['pairing_id']}`")
        if typography.get("headings"):
            lines.append(f"- Encabezados: {typography['headings']}")
        if typography.get("body"):
            lines.append(f"- Cuerpo: {typography['body']}")
        if typography.get("scale"):
            lines.append(f"- Escala: {typography['scale']}")
        if typography.get("notes"):
            lines.append(f"- Notas: {typography['notes']}")
        if typography.get("headings_url"):
            lines.append(f"- URL headings: {typography['headings_url']}")
        if typography.get("body_url"):
            lines.append(f"- URL body: {typography['body_url']}")
        if typography.get("css_url"):
            lines.append(f"- CSS URL: {typography['css_url']}")
        if typography.get("source"):
            lines.append(f"- Fuente tipográfica: {typography['source']}")
    else:
        lines.append("- Pendiente de documentar.")

    lines.extend(
        [
            "",
            "### Espaciado y densidad",
            "",
            _fallback_text(proposal["spacing_density"]),
            "",
            "### Tono visual general",
            "",
            _fallback_text(proposal["tone"]),
            "",
            "### Componente de muestra",
            "",
            _fallback_text(proposal["sample_component"]),
        ]
    )
    lines.extend(["", "## Principios ejecutables del sistema", ""])
    if proposal["visual_principles"]:
        lines.extend(f"- {item}" for item in proposal["visual_principles"])
    else:
        lines.append("- Sin documentar todavía.")

    lines.extend(
        [
            "",
            "### Gramática de composición",
            "",
            _fallback_text(proposal["layout_grammar"]),
            "",
            "### Tratamiento de superficies",
            "",
            _fallback_text(proposal["surface_treatment"]),
            "",
            "### Lenguaje de forma",
            "",
            _fallback_text(proposal["shape_language"]),
            "",
            "### Lenguaje de movimiento",
            "",
            _fallback_text(proposal["motion_language"]),
            "",
            "### Elementos firma",
            "",
        ]
    )
    if proposal["signature_elements"]:
        lines.extend(f"- {item}" for item in proposal["signature_elements"])
    else:
        lines.append("- Sin documentar todavía.")

    lines.extend(["", "### Guardrails de implementación", ""])
    if proposal["implementation_guardrails"]:
        lines.extend(f"- {item}" for item in proposal["implementation_guardrails"])
    else:
        lines.append("- Sin documentar todavía.")

    lines.extend(
        [
            "",
            "## Semilla de dirección",
            "",
            _fallback_text(proposal["prompt_seed"]),
            "",
            "## Por qué gana esta opción",
            "",
            rationale,
            "",
            "## Qué NO es este sistema",
            "",
        ]
    )
    if proposal["not_this_direction"]:
        lines.extend(f"- {item}" for item in proposal["not_this_direction"])
    else:
        lines.append("- Sin delimitar todavía.")

    lines.extend(["", "## Tokens iniciales sugeridos", ""])
    if proposal["tokens"]:
        lines.extend(
            _render_table(
                ["Token", "Valor inicial"],
                [[item["name"], item["value"]] for item in proposal["tokens"]],
            )
        )
    else:
        lines.append("Sin documentar todavía.")

    if proposal["context_signals"]:
        lines.extend(["", "## Señales del contexto", ""])
        lines.extend(f"- {item}" for item in proposal["context_signals"])

    if proposal.get("reference_urls"):
        lines.extend(["", "## Referencias visuales", ""])
        lines.extend(
            f"- [{item['label']}]({item['url']})"
            for item in proposal["reference_urls"]
        )

    lines.extend(
        [
            "",
            "## Metadatos",
            "",
            f"- Generado automáticamente el {record['generated_at']}",
        ]
    )
    if proposals_source:
        lines.append(f"- Propuestas fuente: `{proposals_source}`")
    return "\n".join(lines).rstrip() + "\n"


def write_style_direction_artifact(
    project_dir: str,
    visual_path: str,
    *,
    proposals_file: Optional[str] = None,
    choice_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Escribe docs/style-direction.md a partir de la opción elegida."""
    record = build_style_direction_record(
        visual_path,
        proposals_file=proposals_file,
        choice_override=choice_override,
    )
    record["project_dir"] = project_dir
    record["visual_session_dir"] = resolve_visual_session_dir(visual_path)
    output_path = os.path.join(project_dir, STYLE_DIRECTION_DOC_RELATIVE_PATH)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(render_style_direction_markdown(record))
    return {
        "status": "ok",
        "artifact_path": output_path,
        "choice": record["choice"],
        "selected_label": record["selected_label"],
        "selected_at": record.get("selected_at", ""),
        "proposals_file": record.get("proposals_file", ""),
    }
