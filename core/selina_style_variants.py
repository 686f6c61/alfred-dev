#!/usr/bin/env python3
"""Generación guiada de tres variantes finales para Selina."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from core.selina_style_catalog import (
    build_style_catalog_proposal,
    get_style_trend,
    resolve_font_pairing,
    resolve_palette_mode_meta,
)
from core.selina_style_direction import resolve_visual_session_dir
from core.selina_style_options import write_style_options_html
from core.selina_style_selector import parse_guided_choice
from core.selina_visual import read_latest_style_choice


STYLE_VARIANTS_JSON_FILENAME = "style-options.json"


STYLE_VARIANT_FLAVORS: Dict[str, Tuple[str, str, str]] = {
    "free-default": ("balanced", "minimal", "editorial"),
    "maximalism-neo-retro": ("expressive", "editorial", "balanced"),
    "kinetic-typography": ("editorial", "expressive", "minimal"),
    "interactive-3d-webgl": ("expressive", "technical", "balanced"),
    "glassmorphism-2": ("balanced", "minimal", "technical"),
    "dopamine-colors": ("expressive", "balanced", "minimal"),
    "nature-distilled": ("editorial", "balanced", "minimal"),
    "neo-brutalism": ("expressive", "operational", "minimal"),
    "ai-hyperminimalism": ("minimal", "balanced", "editorial"),
    "narrative-scroll-gamification": ("editorial", "expressive", "balanced"),
}


VARIANT_PROFILES: Dict[str, Dict[str, str]] = {
    "expressive": {
        "label": "Firma expresiva",
        "concept_suffix": "como firma visible, con más tensión y presencia inmediata",
        "preview_copy": "La versión más de marca, más frontal y con mayor gesto visual.",
        "preview_note": "Firma expresiva",
        "density": "Media, con bloques protagonistas, contraste marcado y ritmo algo más teatral.",
        "tone_suffix": "Se siente más frontal, memorables los acentos y menos neutral la composición.",
        "component": "Hero protagonista con gesto fuerte, acentos de marca y CTA muy visible.",
        "rationale_suffix": "Es la que mejor defiende identidad y recuerdo sin abandonar el sistema elegido.",
        "not_this": "No intenta suavizar la personalidad ni parecer una interfaz corporativa plana.",
    },
    "editorial": {
        "label": "Narrativa editorial",
        "concept_suffix": "con más jerarquía narrativa, lectura guiada y sensación curada",
        "preview_copy": "La versión que explica mejor y da más sensación de criterio visual.",
        "preview_note": "Narrativa editorial",
        "density": "Aireada, con secuencia clara, titulares más protagonistas y respiración deliberada.",
        "tone_suffix": "Se percibe más curada, pausada y orientada a explicar antes que a empujar.",
        "component": "Secuencia hero + bloque editorial + CTA sobrio con más espacio de lectura.",
        "rationale_suffix": "Funciona cuando el producto necesita explicar bien su valor sin perder carácter.",
        "not_this": "No es la variante más agresiva ni la más pensada para escaneo operativo continuo.",
    },
    "technical": {
        "label": "Señal técnica",
        "concept_suffix": "con más semántica de estado, contraste y lectura de monitorización",
        "preview_copy": "La versión más precisa y orientada a lectura técnica del producto.",
        "preview_note": "Señal técnica",
        "density": "Media-alta, con bloques compactos, énfasis en estados y jerarquía de lectura rápida.",
        "tone_suffix": "Parece más precisa, instrumental y orientada a claridad de sistema.",
        "component": "Panel principal con estados, gráficas cortas y jerarquía clara de señales.",
        "rationale_suffix": "Conviene cuando el producto necesita reforzar control, estado y lectura inequívoca.",
        "not_this": "No busca calidez editorial ni silencio visual como primera capa de experiencia.",
    },
    "operational": {
        "label": "Producto operativo",
        "concept_suffix": "como una versión más utilizable en producto real, con foco en tarea y lectura rápida",
        "preview_copy": "La versión más aterrizada para uso diario y escaneo rápido.",
        "preview_note": "Producto operativo",
        "density": "Media, con equilibrio entre claridad, decisión y densidad suficiente para uso real.",
        "tone_suffix": "Se siente más de producto vivo que de manifiesto visual, manteniendo la familia elegida.",
        "component": "Resumen operativo con métricas clave, CTA contextual y jerarquía de escaneo muy clara.",
        "rationale_suffix": "Suele ser la opción más aterrizada para producto continuo y adopción amplia.",
        "not_this": "No convierte la dirección en una pieza puramente de marca o de storytelling.",
    },
    "minimal": {
        "label": "Producto limpio",
        "concept_suffix": "más limpia, enfocada y silenciosa, reduciendo ruido alrededor del sistema base",
        "preview_copy": "La versión más limpia, ligera y sencilla de ejecutar.",
        "preview_note": "Producto limpio",
        "density": "Aireada, con más espacio negativo, menos capas simultáneas y foco en lo esencial.",
        "tone_suffix": "Da una sensación más ligera, sofisticada y fácil de ejecutar a diario.",
        "component": "Hero de producto limpio con CTA dominante, prueba social y soporte mínimo.",
        "rationale_suffix": "Ayuda a mantener la familia elegida sin saturar la experiencia final.",
        "not_this": "No es la variante más expresiva ni la que lleva el gesto visual al límite.",
    },
    "balanced": {
        "label": "Equilibrio base",
        "concept_suffix": "en una clave más equilibrada, pensada para sostener marca y producto a la vez",
        "preview_copy": "La síntesis entre personalidad visual y facilidad de uso.",
        "preview_note": "Equilibrio base",
        "density": "Equilibrada, con suficiente aire para respirar y suficiente estructura para guiar.",
        "tone_suffix": "Se percibe más estable, versátil y sencilla de extender al resto del sistema.",
        "component": "Sección de valor con supporting copy, prueba social y CTA principal bien jerarquizado.",
        "rationale_suffix": "Es una buena síntesis entre personalidad y facilidad de ejecución.",
        "not_this": "No busca extremos visuales ni dramatizar cada bloque del producto.",
    },
}


def _build_variant_name(style_name: str, profile: Dict[str, str]) -> str:
    return f"{style_name} — {profile['label']}"


def _build_variant_concept(style_description: str, profile: Dict[str, str]) -> str:
    return f"{style_description} {profile['concept_suffix']}."


def _build_variant_tone(base_tone: str, profile: Dict[str, str]) -> str:
    return f"{base_tone} {profile['tone_suffix']}"


def _build_variant_rationale(base_when_to_use: str, profile: Dict[str, str]) -> str:
    return f"{base_when_to_use} {profile['rationale_suffix']}"


def _resolve_guided_selection(
    visual_path: str,
    *,
    style_id: Optional[str] = None,
    font_pairing_id: Optional[str] = None,
    palette_mode: Optional[str] = None,
) -> Dict[str, str]:
    if style_id and font_pairing_id and palette_mode:
        return {
            "style_id": style_id,
            "font_pairing_id": font_pairing_id,
            "palette_mode": palette_mode,
        }

    latest_choice = read_latest_style_choice(visual_path)
    parsed = parse_guided_choice((latest_choice or {}).get("choice"))
    if not parsed or parsed.get("stage") != "style-brief":
        raise ValueError(
            "No hay una selección guiada válida de sistema + tipografía + paleta todavía."
        )

    return {
        "style_id": parsed["style_id"],
        "font_pairing_id": parsed["font_pairing_id"],
        "palette_mode": parsed["palette_mode"],
    }


def build_guided_style_variants(
    *,
    style_id: str,
    font_pairing_id: str,
    palette_mode: str,
) -> List[Dict[str, Any]]:
    """Construye tres propuestas finales dentro de la misma familia elegida."""
    style = get_style_trend(style_id)
    font_pairing = resolve_font_pairing(style_id, pairing_id=font_pairing_id)
    palette_meta = resolve_palette_mode_meta(palette_mode)
    variant_flavors = STYLE_VARIANT_FLAVORS.get(style_id, ("balanced", "minimal", "editorial"))

    proposals: List[Dict[str, Any]] = []
    for choice, flavor in zip(("A", "B", "C"), variant_flavors):
        profile = VARIANT_PROFILES[flavor]
        proposal = build_style_catalog_proposal(
            style_id,
            choice=choice,
            palette_mode=palette_mode,
            font_pairing_id=font_pairing_id,
        )
        proposal["preview_flavor"] = flavor
        proposal["variant_id"] = flavor
        proposal["variant_label"] = profile["label"]
        proposal["preview_title"] = profile["label"]
        proposal["preview_copy"] = profile["preview_copy"]
        proposal["preview_note"] = profile["preview_note"]
        proposal["name"] = _build_variant_name(style["name"], profile)
        proposal["concept"] = _build_variant_concept(style["description"], profile)
        proposal["tone"] = _build_variant_tone(style["suggested_tone"], profile)
        proposal["spacing_density"] = profile["density"]
        proposal["sample_component"] = profile["component"]
        proposal["rationale"] = _build_variant_rationale(style["when_to_use"], profile)
        proposal["not_this_direction"] = [
            profile["not_this"],
            *list(style["anti_patterns"])[:1],
        ]
        proposal["context_signals"] = [
            f"Familia fijada por el usuario: {style['name']}.",
            f"Pairing fijado por el usuario: {font_pairing['label']} ({font_pairing['headings']} / {font_pairing['body']}).",
            f"Gama cromática fijada por el usuario: {palette_meta['label']}.",
            *list(style.get("visual_principles", []))[:2],
            f"Elementos firma del sistema: {', '.join(style.get('signature_elements', [])[:3])}.",
        ]
        proposal["prompt_seed"] = (
            f"{style.get('prompt_seed', '').strip()} "
            f"Mantén esta familia visual incluso cuando varíes la propuesta hacia '{profile['label']}'."
        ).strip()
        proposals.append(proposal)

    return proposals


def write_guided_style_options(
    visual_path: str,
    *,
    style_id: Optional[str] = None,
    font_pairing_id: Optional[str] = None,
    palette_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Escribe el sidecar y la pantalla final de tres variantes guiadas."""
    selection = _resolve_guided_selection(
        visual_path,
        style_id=style_id,
        font_pairing_id=font_pairing_id,
        palette_mode=palette_mode,
    )
    proposals = build_guided_style_variants(**selection)
    style = get_style_trend(selection["style_id"])
    font_pairing = resolve_font_pairing(selection["style_id"], pairing_id=selection["font_pairing_id"])
    palette_meta = resolve_palette_mode_meta(selection["palette_mode"])

    session_dir = resolve_visual_session_dir(visual_path)
    content_dir = os.path.join(session_dir, "content")
    os.makedirs(content_dir, exist_ok=True)
    proposals_path = os.path.join(content_dir, STYLE_VARIANTS_JSON_FILENAME)
    with open(proposals_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "guided_selection": selection,
                "proposals": proposals,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )

    html_result = write_style_options_html(
        visual_path,
        proposals_file=proposals_path,
        title=f"Elige la versión final de {style['name']}",
        subtitle=(
            f"Base fijada: {font_pairing['label']} + {palette_meta['label']}. "
            "Ahora sí: Selina te enseña tres versiones finales comparables dentro de esa misma familia."
        ),
    )

    return {
        "status": "ok",
        "style_id": selection["style_id"],
        "font_pairing_id": selection["font_pairing_id"],
        "palette_mode": selection["palette_mode"],
        "proposals_file": proposals_path,
        "html_path": html_result["html_path"],
        "choices": html_result["choices"],
    }
