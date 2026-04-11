#!/usr/bin/env python3
"""Pantallas guiadas para seleccionar sistema visual en Selina."""

from __future__ import annotations

import html
import os
from typing import Any, Dict, List, Optional

from core.selina_style_catalog import (
    get_palette_modes,
    get_style_catalog,
    get_style_trend,
    resolve_font_pairing,
    resolve_palette,
    resolve_palette_mode_meta,
)
from core.selina_style_direction import resolve_visual_session_dir


STYLE_SELECTOR_HTML_FILENAME = "style-selector.html"
STYLE_BRIEF_HTML_FILENAME = "style-brief.html"

STYLE_CHOICE_PREFIX = "style"
STYLE_BRIEF_PREFIX = "brief"


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _palette_markup(palette: Dict[str, str]) -> str:
    order = ("surface", "surface_alt", "accent", "accent_alt")
    chips = []
    for key in order:
        value = palette.get(key)
        if not value:
            continue
        chips.append(
            '<span class="selector-swatch">'
            f'<span class="selector-swatch__dot" style="background:{_escape(value)};"></span>'
            f"<span>{_escape(value)}</span>"
            "</span>"
        )
    return '<div class="selector-palette">' + "".join(chips) + "</div>"


def _pairing_list_markup(pairings: List[Dict[str, str]]) -> str:
    items = []
    for pairing in pairings:
        items.append(
            '<div class="selector-pairing">'
            f'<strong>{_escape(pairing["label"])}</strong>'
            f"<span>{_escape(pairing['headings'])} / {_escape(pairing['body'])}</span>"
            "</div>"
        )
    return '<div class="selector-pairings">' + "".join(items) + "</div>"


def _palette_mode_list_markup(mode_ids: List[str], recommended_id: str) -> str:
    meta_by_id = {entry["id"]: entry for entry in get_palette_modes()}
    items = []
    for mode_id in mode_ids:
        meta = meta_by_id.get(mode_id)
        if not meta:
            continue
        classes = "style-badge"
        if mode_id != recommended_id:
            classes += " style-badge--soft"
        items.append(f'<span class="{classes}">{_escape(meta["label"])}</span>')
    return '<div class="style-badges selector-badges">' + "".join(items) + "</div>"


def _references_markup(references: List[Dict[str, str]]) -> str:
    if not references:
        return ""
    links = []
    for item in references[:3]:
        links.append(
            f'<a class="style-link" href="{_escape(item["url"])}" target="_blank" rel="noreferrer">{_escape(item["label"])}</a>'
        )
    return '<div class="style-links selector-links">' + "".join(links) + "</div>"


def _selector_css() -> str:
    return """
<style>
  .selector-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  .selector-card {
    min-height: 100%;
  }

  .selector-card .style-preview {
    min-height: 184px;
    padding: 1.15rem;
    display: grid;
    align-content: start;
    gap: 0.7rem;
  }

  .selector-card .style-meta {
    display: grid;
    gap: 0.75rem;
  }

  .selector-title {
    font-family: var(--font-display);
    font-size: 1.32rem;
    line-height: 1.02;
    color: var(--option-ink);
    max-width: 12ch;
  }

  .selector-summary,
  .selector-description,
  .selector-copy,
  .selector-note {
    font-size: 0.84rem;
    line-height: 1.55;
    color: var(--option-muted);
  }

  .selector-description {
    margin-top: 0.15rem;
  }

  .selector-badges {
    margin: 0;
  }

  .selector-palette {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
  }

  .selector-swatch {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.68rem;
    color: var(--option-muted);
    font-family: "SF Mono", "IBM Plex Mono", "Fira Code", monospace;
  }

  .selector-swatch__dot {
    width: 14px;
    height: 14px;
    border-radius: 999px;
    border: 1px solid rgba(17, 17, 17, 0.1);
  }

  .selector-pairings {
    display: grid;
    gap: 0.55rem;
  }

  .selector-pairing {
    display: grid;
    gap: 0.14rem;
    padding: 0.65rem 0.72rem;
    border-radius: 16px;
    border: 1px solid rgba(17, 17, 17, 0.08);
    background: rgba(255, 255, 255, 0.48);
  }

  .selector-pairing strong {
    color: var(--option-ink);
    font-size: 0.76rem;
  }

  .selector-pairing span {
    font-size: 0.74rem;
    color: var(--option-muted);
  }

  .selector-action {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 36px;
    padding: 0 0.9rem;
    border-radius: 999px;
    background: var(--option-accent-soft);
    color: var(--option-accent);
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  .selector-step {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--option-accent);
    font-weight: 700;
  }

  .selector-screen-rail {
    margin-bottom: 1rem;
    max-width: 72ch;
    color: var(--text-secondary);
    font-size: 0.92rem;
  }

  .selector-screen-rail strong {
    color: var(--text);
  }

  .selector-brief-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
  }

  .selector-brief-card .style-preview {
    min-height: 160px;
  }

  .selector-brief-topline {
    display: flex;
    justify-content: space-between;
    gap: 0.7rem;
    align-items: center;
    font-size: 0.72rem;
    color: var(--option-muted);
  }

  .selector-brief-topline strong {
    color: var(--option-ink);
    font-size: 0.75rem;
  }
</style>
"""


def encode_style_choice(style_id: str) -> str:
    """Codifica una elección de familia visual."""
    normalized_style_id = str(style_id or "").strip()
    return f"{STYLE_CHOICE_PREFIX}::{normalized_style_id}"


def encode_style_brief_choice(style_id: str, font_pairing_id: str, palette_mode: str) -> str:
    """Codifica una elección completa de familia + pairing + paleta."""
    normalized_style_id = str(style_id or "").strip()
    normalized_pairing_id = str(font_pairing_id or "").strip()
    normalized_palette_mode = str(palette_mode or "").strip()
    return (
        f"{STYLE_BRIEF_PREFIX}::"
        f"{normalized_style_id}::"
        f"{normalized_pairing_id}::"
        f"{normalized_palette_mode}"
    )


def parse_guided_choice(choice: Any) -> Optional[Dict[str, str]]:
    """Decodifica una elección del flujo guiado de Selina."""
    text = str(choice or "").strip()
    if not text:
        return None

    parts = text.split("::")
    if len(parts) == 2 and parts[0] == STYLE_CHOICE_PREFIX and parts[1]:
        return {
            "stage": "style-family",
            "style_id": parts[1],
        }

    if (
        len(parts) == 4
        and parts[0] == STYLE_BRIEF_PREFIX
        and parts[1]
        and parts[2]
        and parts[3]
    ):
        return {
            "stage": "style-brief",
            "style_id": parts[1],
            "font_pairing_id": parts[2],
            "palette_mode": parts[3],
        }

    return None


def render_style_selector_html(
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> str:
    """Renderiza la primera pantalla: elegir familia visual base."""
    cards = []
    for entry in get_style_catalog():
        palette, _ = resolve_palette(entry["id"], entry["recommended_palette_mode"])
        card_style = (
            f"--option-accent: {_escape(palette['accent'])}; "
            f"--option-accent-soft: {_escape(palette['accent'])}22; "
            f"--option-surface: {_escape(palette['surface'])}; "
            f"--option-surface-alt: {_escape(palette['surface_alt'])}cc;"
        )
        cards.append(
            f'<article class="style-option selector-card" data-choice="{_escape(encode_style_choice(entry["id"]))}" '
            f'data-label="{_escape(entry["name"])}" style="{card_style}">'
            '<div class="style-preview">'
            '<p class="selector-step">Paso 1 · Sistema base</p>'
            f'<h2 class="selector-title">{_escape(entry["name"])}</h2>'
            f'<p class="selector-summary">{_escape(entry["summary"])}</p>'
            f"{_palette_markup(palette)}"
            "</div>"
            '<div class="style-meta">'
            f'<p class="selector-description">{_escape(entry["description"])}</p>'
            f"{_palette_mode_list_markup(list(entry['palette_modes']), entry['recommended_palette_mode'])}"
            f"{_pairing_list_markup(list(entry['font_pairings']))}"
            f"{_references_markup(list(entry['references']))}"
            '<span class="selector-action">Elegir este sistema</span>'
            "</div></article>"
        )

    title_text = title or "Elige el sistema de diseño base"
    subtitle_text = subtitle or (
        "Aquí no eliges la versión final todavía. Primero decides la familia visual "
        "que mejor encaja con el producto; después Selina te dejará escoger "
        "tipografía y gama de color dentro de esa familia."
    )
    return (
        _selector_css()
        + '<section class="style-screen">'
        '<div class="style-screen-header">'
        '<p class="style-screen-kicker">Selina / paso 1</p>'
        f"<h1>{_escape(title_text)}</h1>"
        f'<p class="style-screen-subtitle">{_escape(subtitle_text)}</p>'
        '</div>'
        '<p class="selector-screen-rail"><strong>Qué estás viendo:</strong> cada sistema ya enseña sus pairings tipográficos, '
        'modos de paleta y referencias para que no elijas a ciegas.</p>'
        '<div class="selector-grid">'
        + "".join(cards)
        + "</div></section>"
    )


def render_style_brief_selector_html(
    style_id: str,
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> str:
    """Renderiza la segunda pantalla: elegir pairing tipográfico y paleta."""
    style = get_style_trend(style_id)
    cards = []
    for pairing in list(style["font_pairings"]):
        for palette_mode in list(style["palette_modes"]):
            palette, resolved_palette_mode = resolve_palette(style_id, palette_mode)
            palette_meta = resolve_palette_mode_meta(resolved_palette_mode)
            label = f"{pairing['label']} · {palette_meta['label']}"
            choice = encode_style_brief_choice(style_id, pairing["id"], resolved_palette_mode)
            cards.append(
                f'<article class="style-option selector-card selector-brief-card" data-choice="{_escape(choice)}" '
                f'data-label="{_escape(label)}" '
                f'style="--option-accent: {_escape(palette["accent"])}; --option-accent-soft: {_escape(palette["accent"])}22; '
                f'--option-surface: {_escape(palette["surface"])}; --option-surface-alt: {_escape(palette["surface_alt"])}cc;">'
                '<div class="style-preview">'
                '<p class="selector-step">Paso 2 · Tipografía + paleta</p>'
                '<div class="selector-brief-topline">'
                f'<strong>{_escape(pairing["label"])}</strong>'
                f'<span>{_escape(palette_meta["label"])}</span>'
                "</div>"
                f'<h2 class="selector-title">{_escape(style["name"])}</h2>'
                f'<p class="selector-summary">{_escape(pairing["headings"])} / {_escape(pairing["body"])}</p>'
                f"{_palette_markup(palette)}"
                "</div>"
                '<div class="style-meta">'
                f'<p class="selector-copy">{_escape(pairing["notes"])}</p>'
                f'<p class="selector-note">{_escape(palette_meta["description"])}</p>'
                '<span class="selector-action">Usar esta combinación</span>'
                "</div></article>"
            )

    title_text = title or f"Elige tipografía y paleta para {style['name']}"
    subtitle_text = subtitle or (
        "Selina mantendrá esta familia visual y, con esta combinación concreta, "
        "te devolverá tres versiones finales comparables antes de cerrar la dirección."
    )
    return (
        _selector_css()
        + '<section class="style-screen">'
        '<div class="style-screen-header">'
        '<p class="style-screen-kicker">Selina / paso 2</p>'
        f"<h1>{_escape(title_text)}</h1>"
        f'<p class="style-screen-subtitle">{_escape(subtitle_text)}</p>'
        '</div>'
        '<p class="selector-screen-rail"><strong>Regla:</strong> aquí ya no cambias de sistema. '
        'Solo fijas la voz tipográfica y la gama cromática que usará la ronda final.</p>'
        '<div class="selector-brief-grid">'
        + "".join(cards)
        + "</div></section>"
    )


def write_style_selector_html(
    visual_path: str,
    *,
    style_id: Optional[str] = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Dict[str, Any]:
    """Escribe la pantalla guiada correspondiente en la sesión visual."""
    session_dir = resolve_visual_session_dir(visual_path)
    content_dir = os.path.join(session_dir, "content")
    os.makedirs(content_dir, exist_ok=True)

    if style_id:
        html = render_style_brief_selector_html(style_id, title=title, subtitle=subtitle)
        html_filename = STYLE_BRIEF_HTML_FILENAME
        stage = "style-brief"
        style = get_style_trend(style_id)
        choices = [
            encode_style_brief_choice(style_id, pairing["id"], palette_mode)
            for pairing in list(style["font_pairings"])
            for palette_mode in list(style["palette_modes"])
        ]
    else:
        html = render_style_selector_html(title=title, subtitle=subtitle)
        html_filename = STYLE_SELECTOR_HTML_FILENAME
        stage = "style-family"
        choices = [encode_style_choice(entry["id"]) for entry in get_style_catalog()]

    html_path = os.path.join(content_dir, html_filename)
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    return {
        "status": "ok",
        "stage": stage,
        "html_path": html_path,
        "choices": choices,
        "style_id": style_id or "",
    }
