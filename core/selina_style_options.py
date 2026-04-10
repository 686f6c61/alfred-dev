#!/usr/bin/env python3
"""Generacion canónica de style-options.html para Selina."""

from __future__ import annotations

import html
import os
from typing import Any, Dict, List, Optional

from core.selina_style_direction import (
    discover_proposals_file,
    load_style_proposals,
    resolve_visual_session_dir,
)


STYLE_OPTIONS_HTML_FILENAME = "style-options.html"


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _sentence(value: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""
    return text if text[-1] in ".!?" else f"{text}."


def _semantic_source_text(proposal: Dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            proposal.get("name", ""),
            proposal.get("concept", ""),
            proposal.get("tone", ""),
            proposal.get("rationale", ""),
            " ".join(item.get("role", "") for item in (proposal.get("palette") or [])),
            " ".join(proposal.get("context_signals", [])),
        ]
        if part
    ).lower()


def _matches_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _infer_option_flavor(proposal: Dict[str, Any]) -> str:
    text = _semantic_source_text(proposal)
    if _matches_any(text, ["editorial", "premium", "serif", "revista", "magazine", "lujo"]):
        return "editorial"
    if _matches_any(text, ["dashboard", "operativ", "metric", "analit", "control", "panel", "saas"]):
        return "operational"
    if _matches_any(text, ["minimal", "limpio", "airead", "sobrio", "claridad", "negativo"]):
        return "minimal"
    if _matches_any(text, ["vibrante", "oscuro", "espacial", "futur", "expresiv", "bold", "impacto"]):
        return "expressive"
    return "balanced"


def _extract_palette_values(proposal: Dict[str, Any]) -> List[str]:
    return [
        value
        for value in (item.get("value", "") for item in (proposal.get("palette") or []))
        if isinstance(value, str) and value.strip().startswith("#")
    ]


def _hex_to_rgba(color: str, alpha: float) -> str:
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return f"rgba(184, 92, 56, {alpha})"
    try:
        red = int(raw[0:2], 16)
        green = int(raw[2:4], 16)
        blue = int(raw[4:6], 16)
    except ValueError:
        return f"rgba(184, 92, 56, {alpha})"
    return f"rgba({red}, {green}, {blue}, {alpha})"


def _relative_luminance(color: str) -> float:
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return 1.0
    try:
        channels = [int(raw[idx:idx + 2], 16) / 255 for idx in range(0, 6, 2)]
    except ValueError:
        return 1.0

    def linearize(value: float) -> float:
        if value <= 0.03928:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = [linearize(channel) for channel in channels]
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _option_theme(proposal: Dict[str, Any], flavor: str) -> Dict[str, str]:
    defaults = {
        "editorial": {"accent": "#b85c38", "accent_alt": "#6f4633", "surface": "#f6ede3"},
        "operational": {"accent": "#2d6f7f", "accent_alt": "#1f4c56", "surface": "#eef5f7"},
        "minimal": {"accent": "#5f6c73", "accent_alt": "#364247", "surface": "#f1f3f2"},
        "expressive": {"accent": "#7b3256", "accent_alt": "#351d41", "surface": "#f4e7ef"},
        "balanced": {"accent": "#6c5a4d", "accent_alt": "#3d322c", "surface": "#f3eee8"},
    }[flavor]
    palette = _extract_palette_values(proposal)
    accent = palette[1] if len(palette) > 1 else (palette[0] if palette else defaults["accent"])
    surface = palette[0] if palette else defaults["surface"]
    accent_alt = palette[2] if len(palette) > 2 else defaults["accent_alt"]
    ink = "#fffaf5" if _relative_luminance(surface) < 0.28 else "#201714"
    muted = _hex_to_rgba(ink, 0.72 if ink.startswith("#fff") else 0.68)
    return {
        "accent": accent,
        "accent_soft": _hex_to_rgba(accent, 0.18),
        "accent_glow": _hex_to_rgba(accent, 0.3),
        "surface": surface,
        "surface_alt": _hex_to_rgba(accent_alt, 0.16),
        "ink": ink,
        "muted": muted,
    }


def _option_style_attr(theme: Dict[str, str]) -> str:
    style = "; ".join(
        [
            f"--option-accent: {theme['accent']}",
            f"--option-accent-soft: {theme['accent_soft']}",
            f"--option-accent-glow: {theme['accent_glow']}",
            f"--option-surface: {theme['surface']}",
            f"--option-surface-alt: {theme['surface_alt']}",
            f"--option-ink: {theme['ink']}",
            f"--option-muted: {theme['muted']}",
        ]
    )
    return _escape(style)


def _preview_background(proposal: Dict[str, Any]) -> str:
    palette = proposal.get("palette") or []
    if palette:
        return palette[0].get("value") or "rgba(128, 128, 128, 0.08)"
    return "rgba(128, 128, 128, 0.08)"


def _palette_markup(palette: List[Dict[str, str]]) -> str:
    if not palette:
        return ""

    items = []
    for item in palette[:4]:
        value = _escape(item.get("value", ""))
        role = _escape(item.get("role", ""))
        items.append(
            '<div class="palette-dot">'
            f'<span class="dot" style="background:{value};" title="{role}: {value}"></span>'
            f'<span class="hex">{value}</span>'
            "</div>"
        )
    return '<div class="palette">' + "".join(items) + "</div>"


def _reference_links_markup(reference_urls: List[Dict[str, str]]) -> str:
    if not reference_urls:
        return ""

    links = []
    for item in reference_urls[:3]:
        label = _escape(item.get("label", "Referencia"))
        url = _escape(item.get("url", ""))
        if not url:
            continue
        links.append(
            f'<a class="style-link" href="{url}" target="_blank" rel="noreferrer">{label}</a>'
        )
    if not links:
        return ""
    return '<div class="style-links">' + "".join(links) + "</div>"


def _typography_links_markup(typography: Dict[str, str]) -> str:
    links = []
    if typography.get("headings_url"):
        links.append(
            f'<a class="style-link" href="{_escape(typography["headings_url"])}" target="_blank" rel="noreferrer">Headings</a>'
        )
    if typography.get("body_url"):
        links.append(
            f'<a class="style-link" href="{_escape(typography["body_url"])}" target="_blank" rel="noreferrer">Body</a>'
        )
    if typography.get("custom_url"):
        links.append(
            f'<a class="style-link" href="{_escape(typography["custom_url"])}" target="_blank" rel="noreferrer">Custom</a>'
        )
    if not links:
        return ""
    return '<div class="style-links style-links--fonts">' + "".join(links) + "</div>"


def _typography_summary(proposal: Dict[str, Any]) -> str:
    typography = proposal.get("typography") or {}
    parts = []
    if typography.get("headings"):
        parts.append(f"Titulares: {typography['headings']}")
    if typography.get("body"):
        parts.append(f"Cuerpo: {typography['body']}")
    if typography.get("scale"):
        parts.append(f"Escala: {typography['scale']}")
    return " · ".join(parts)


def _context_summary(proposal: Dict[str, Any]) -> str:
    return (
        proposal.get("concept")
        or proposal.get("rationale")
        or ((proposal.get("context_signals") or [None])[0])
        or ""
    )


def _preview_editorial(proposal: Dict[str, Any]) -> str:
    return (
        '<div class="preview-editorial">'
        '<div class="mock-nav"><span></span><span></span><span></span></div>'
        '<p class="preview-kicker">Edicion visual</p>'
        '<div class="mock-hero preview-hero preview-hero--editorial">'
        f"<h4>{_escape(proposal.get('concept') or proposal.get('name') or 'Direccion visual')}</h4>"
        f"<p>{_escape(proposal.get('tone') or 'Calma, criterio y jerarquia')}</p>"
        '<span class="mock-button">Leer propuesta</span>'
        "</div>"
        '<div class="preview-lines"><span></span><span></span><span></span></div>'
        "</div>"
    )


def _preview_operational(proposal: Dict[str, Any]) -> str:
    return (
        '<div class="preview-dashboard">'
        '<div class="preview-metrics">'
        '<div class="preview-stat"><strong>72%</strong><span>Adopcion</span></div>'
        '<div class="preview-stat"><strong>4.2</strong><span>Foco</span></div>'
        "</div>"
        '<div class="mock-card preview-card preview-card--wide">'
        f"<h5>{_escape(proposal.get('sample_component') or 'Panel de control')}</h5>"
        f"<p>{_escape(_context_summary(proposal))}</p>"
        "</div>"
        '<div class="preview-bar-group"><span></span><span></span><span></span></div>'
        "</div>"
    )


def _preview_minimal(proposal: Dict[str, Any]) -> str:
    return (
        '<div class="preview-minimal">'
        '<div class="preview-minimal-frame"></div>'
        '<div class="mock-hero preview-hero preview-hero--minimal">'
        f"<h4>{_escape(proposal.get('concept') or proposal.get('name') or 'Direccion visual')}</h4>"
        f"<p>{_escape(proposal.get('tone') or 'Sobrio y enfocado')}</p>"
        '<span class="mock-button">Continuar</span>'
        "</div>"
        '<div class="preview-balance-line"></div>'
        "</div>"
    )


def _preview_expressive(proposal: Dict[str, Any]) -> str:
    return (
        '<div class="preview-expressive">'
        '<div class="preview-badge">Impacto</div>'
        '<div class="mock-hero preview-hero preview-hero--expressive">'
        f"<h4>{_escape(proposal.get('concept') or proposal.get('name') or 'Direccion visual')}</h4>"
        f"<p>{_escape(proposal.get('tone') or 'Expresivo y memorable')}</p>"
        '<span class="mock-button">Ver identidad</span>'
        "</div>"
        '<div class="preview-stack">'
        '<div class="preview-panel"></div><div class="preview-panel preview-panel--alt"></div>'
        "</div>"
        "</div>"
    )


def _preview_balanced(proposal: Dict[str, Any]) -> str:
    return (
        '<div class="preview-balanced">'
        '<div class="mock-nav"><span></span><span></span><span></span></div>'
        '<div class="mock-hero preview-hero">'
        f"<h4>{_escape(proposal.get('concept') or proposal.get('name') or 'Direccion visual')}</h4>"
        f"<p>{_escape(proposal.get('tone') or 'Equilibrio y claridad')}</p>"
        '<span class="mock-button">CTA principal</span>'
        "</div>"
        '<div class="mock-card preview-card">'
        f"<h5>{_escape(proposal.get('sample_component') or 'Componente de referencia')}</h5>"
        f"<p>{_escape(_context_summary(proposal))}</p>"
        "</div>"
        "</div>"
    )


def _preview_markup(proposal: Dict[str, Any], flavor: str) -> str:
    tone = _escape(proposal.get("tone") or "Direccion visual por concretar")
    preview_layout = {
        "editorial": _preview_editorial,
        "operational": _preview_operational,
        "minimal": _preview_minimal,
        "expressive": _preview_expressive,
        "balanced": _preview_balanced,
    }[flavor](proposal)
    return (
        f'<div class="style-preview style-preview--{flavor}" style="background:{_escape(_preview_background(proposal))};">'
        f'<div class="preview-tone-note">{tone}</div>'
        f"{preview_layout}"
        "</div>"
    )


def _render_option_card(proposal: Dict[str, Any]) -> str:
    flavor = _infer_option_flavor(proposal)
    theme = _option_theme(proposal, flavor)
    choice = _escape(proposal.get("choice", ""))
    name = _escape(proposal.get("name", choice))
    concept = _escape(_sentence(proposal.get("concept") or ""))
    typography = _escape(_typography_summary(proposal))
    tone = _escape(_sentence(proposal.get("tone") or ""))
    density = _escape(_sentence(proposal.get("spacing_density") or ""))
    sample_component = _escape(_sentence(proposal.get("sample_component") or ""))
    style_family = _escape(proposal.get("style_family_label") or proposal.get("style_family") or "")
    palette_mode = _escape(proposal.get("palette_mode") or "")
    typography_data = proposal.get("typography") or {}

    meta_lines = []
    if style_family or palette_mode:
        badges = []
        if style_family:
            badges.append(f'<span class="style-badge">{style_family}</span>')
        if palette_mode:
            badges.append(f'<span class="style-badge style-badge--soft">{palette_mode}</span>')
        meta_lines.append('<div class="style-badges">' + "".join(badges) + "</div>")
    if concept:
        meta_lines.append(f'<p class="style-description">{concept}</p>')
    palette_markup = _palette_markup(proposal.get("palette") or [])
    if palette_markup:
        meta_lines.append(palette_markup)
    if typography:
        meta_lines.append(f'<p class="style-typo"><strong>Tipografia:</strong> {typography}</p>')
    if tone:
        meta_lines.append(f'<p class="style-tone"><strong>Tono:</strong> {tone}</p>')
    if density:
        meta_lines.append(f'<p class="style-tone"><strong>Densidad:</strong> {density}</p>')
    if sample_component:
        meta_lines.append(f'<p class="style-sample"><strong>Componente:</strong> {sample_component}</p>')
    reference_links = _reference_links_markup(proposal.get("reference_urls") or [])
    if reference_links:
        meta_lines.append(reference_links)
    typography_links = _typography_links_markup(typography_data)
    if typography_links:
        meta_lines.append(typography_links)

    return (
        f'<div class="style-option style-option--{flavor}" data-choice="{choice}" style="{_option_style_attr(theme)}">'
        f'<span class="style-letter">{choice}</span>'
        f"{_preview_markup(proposal, flavor)}"
        '<div class="style-meta">'
        f'<h2 class="style-name">{name}</h2>'
        + "".join(meta_lines)
        + "</div></div>"
    )


def render_style_options_html(
    proposals: List[Dict[str, Any]],
    *,
    title: str = "Selecciona una direccion visual",
    subtitle: str = "Elige la propuesta que mejor encaja con el producto. Tu clic queda registrado automaticamente.",
) -> str:
    """Renderiza el fragmento HTML canónico de las opciones de Selina."""
    cards = [_render_option_card(proposal) for proposal in proposals]
    return (
        '<section class="style-screen">'
        '<div class="style-screen-header">'
        f"<p class=\"style-screen-kicker\">Selina propone</p>"
        f"<h1>{_escape(title)}</h1>"
        f"<p class=\"style-screen-subtitle\">{_escape(subtitle)}</p>"
        "</div>"
        '<div class="style-grid">'
        + "".join(cards)
        + "</div></section>"
    )


def build_style_options_payload(
    visual_path: str,
    *,
    proposals_file: Optional[str] = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Dict[str, Any]:
    """Carga propuestas normalizadas y genera el HTML listo para escribir."""
    proposals_path = proposals_file or discover_proposals_file(visual_path)
    if not proposals_path:
        raise ValueError("No se ha encontrado ningun fichero de propuestas de Selina.")

    proposals = list(load_style_proposals(proposals_path).values())
    if not proposals:
        raise ValueError("El sidecar de propuestas existe pero no contiene opciones validas.")

    html_fragment = render_style_options_html(
        proposals,
        title=title or "Selecciona una direccion visual",
        subtitle=subtitle
        or "Elige la propuesta que mejor encaja con el producto. Tu clic queda registrado automaticamente.",
    )

    return {
        "visual_session_dir": resolve_visual_session_dir(visual_path),
        "proposals_file": proposals_path,
        "choices": [proposal["choice"] for proposal in proposals],
        "html": html_fragment,
    }


def write_style_options_html(
    visual_path: str,
    *,
    proposals_file: Optional[str] = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Dict[str, Any]:
    """Escribe style-options.html en la sesion visual de Selina."""
    payload = build_style_options_payload(
        visual_path,
        proposals_file=proposals_file,
        title=title,
        subtitle=subtitle,
    )
    content_dir = os.path.join(payload["visual_session_dir"], "content")
    os.makedirs(content_dir, exist_ok=True)
    html_path = os.path.join(content_dir, STYLE_OPTIONS_HTML_FILENAME)
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(payload["html"])

    return {
        "status": "ok",
        "html_path": html_path,
        "proposals_file": payload["proposals_file"],
        "choices": payload["choices"],
    }
