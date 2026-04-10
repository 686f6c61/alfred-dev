#!/usr/bin/env python3
"""Renderizado de demos visuales y galeria del catalogo de Selina."""

from __future__ import annotations

import html
import os
from typing import Dict, List, Optional

from core.selina_style_catalog import (
    DEFAULT_STYLE_ID,
    get_palette_modes,
    get_style_catalog,
    get_style_trend,
    resolve_font_pairing,
    resolve_palette,
)
from core.selina_style_direction import resolve_visual_session_dir


STYLE_DEMO_GALLERY_FILENAME = "selina-style-gallery.html"

DEMO_CONTENT = {
    "eyebrow": "Selina / sandbox de sistemas de diseño",
    "headline": "Claude Code, pero con un sistema de diseño de verdad",
    "body": (
        "Una landing simple para comparar sistemas de diseño con el mismo contenido: "
        "19 agentes, 26 comandos, memoria local y quality gates con evidencia."
    ),
    "primary_cta": "Instalar Alfred Dev",
    "secondary_cta": "Ver vision tecnica",
    "meta": [
        ("19", "agentes"),
        ("26", "comandos"),
        ("61", "playbooks"),
        ("6", "flujos"),
    ],
    "feature_title": "Lo que cambia al trabajar con Alfred Dev",
    "features": [
        {
            "title": "Orquestacion con criterio",
            "body": "Alfred decide orden, agentes y gates en vez de dejar el flujo a prompts sueltos.",
        },
        {
            "title": "Memoria local persistente",
            "body": "Decisiones, commits y continuidad se quedan dentro del proyecto, no en una conversacion efimera.",
        },
        {
            "title": "Direccion visual antes del CSS",
            "body": "Selina fija el lenguaje visual antes de que architect o senior-dev diseñen componentes.",
        },
        {
            "title": "Entrega con evidencia",
            "body": "Los quality gates paran el avance si no hay pruebas, salida real y trazabilidad suficiente.",
        },
    ],
    "steps": [
        "Detecta stack y runtime del repo.",
        "Compone equipo y activa especialistas utiles.",
        "Ejecuta el flujo con fases, memoria y verificacion.",
    ],
}


def _escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _style_class(style_id: str) -> str:
    return style_id.replace("-", "_")


def _refs_markup(items: List[Dict[str, str]]) -> str:
    if not items:
        return '<span class="style-links__empty">Sin referencias fijadas: Selina define el sistema de diseño a partir del contexto.</span>'
    return "".join(
        f'<a href="{_escape(item["url"])}" target="_blank" rel="noreferrer">{_escape(item["label"])}</a>'
        for item in items
    )


def _fonts_markup(pairings: List[Dict[str, str]]) -> str:
    chips = []
    for pairing in pairings:
        chips.append(
            '<div class="font-chip">'
            f'<strong>{_escape(pairing["label"])}</strong>'
            f'<span>{_escape(pairing["headings"])} + {_escape(pairing["body"])}</span>'
            '<div class="font-chip__links">'
            f'<a href="{_escape(pairing["headings_specimen_url"])}" target="_blank" rel="noreferrer">Headings</a>'
            f'<a href="{_escape(pairing["body_specimen_url"])}" target="_blank" rel="noreferrer">Body</a>'
            '</div></div>'
        )
    return "".join(chips)


def _palette_mode_markup(mode_ids: List[str], recommended_id: str) -> str:
    modes_by_id = {entry["id"]: entry for entry in get_palette_modes()}
    items = []
    for mode_id in mode_ids:
        if mode_id not in modes_by_id:
            continue
        label = modes_by_id[mode_id]["label"]
        class_name = "palette-chip palette-chip--recommended" if mode_id == recommended_id else "palette-chip"
        items.append(f'<span class="{class_name}">{_escape(label)}</span>')
    return "".join(items)


def _hero_art(style_id: str) -> str:
    if style_id == "maximalism-neo-retro":
        return (
            '<div class="hero-art__collage">'
            '<span class="sticker">NO AI SLOP</span>'
            '<span class="sticker sticker--alt">HUMAN ENERGY</span>'
            '<div class="blob blob--a"></div>'
            '<div class="blob blob--b"></div>'
            '<div class="frame frame--a"></div>'
            '<div class="frame frame--b"></div>'
            '</div>'
        )
    if style_id == "kinetic-typography":
        return (
            '<div class="hero-art__kinetic">'
            '<span>CLAUDE</span><span>CODE</span><span>WITH</span><span>TEAM</span>'
            '</div>'
        )
    if style_id == "interactive-3d-webgl":
        return (
            '<div class="hero-art__3d">'
            '<div class="cube cube--front"></div>'
            '<div class="cube cube--mid"></div>'
            '<div class="cube cube--back"></div>'
            '</div>'
        )
    if style_id == "glassmorphism-2":
        return (
            '<div class="hero-art__glass">'
            '<div class="glass-card glass-card--main"></div>'
            '<div class="glass-card glass-card--small"></div>'
            '<div class="glass-orb"></div>'
            '</div>'
        )
    if style_id == "dopamine-colors":
        return (
            '<div class="hero-art__dopamine">'
            '<div class="pill pill--a"></div>'
            '<div class="pill pill--b"></div>'
            '<div class="pill pill--c"></div>'
            '</div>'
        )
    if style_id == "nature-distilled":
        return (
            '<div class="hero-art__nature">'
            '<div class="leaf leaf--a"></div>'
            '<div class="leaf leaf--b"></div>'
            '<div class="leaf leaf--c"></div>'
            '</div>'
        )
    if style_id == "neo-brutalism":
        return (
            '<div class="hero-art__brutal">'
            '<div class="brutal-card brutal-card--a">GATE</div>'
            '<div class="brutal-card brutal-card--b">MEMORY</div>'
            '<div class="brutal-card brutal-card--c">TEAM</div>'
            '</div>'
        )
    if style_id == "ai-hyperminimalism":
        return (
            '<div class="hero-art__hyper">'
            '<div class="hyper-ring"></div>'
            '<div class="hyper-panel"></div>'
            '</div>'
        )
    if style_id == "narrative-scroll-gamification":
        return (
            '<div class="hero-art__story">'
            '<div class="story-step">01</div>'
            '<div class="story-line"></div>'
            '<div class="story-step">02</div>'
            '<div class="story-line"></div>'
            '<div class="story-step">03</div>'
            '</div>'
        )
    return (
        '<div class="hero-art__balanced">'
        '<div class="balanced-panel"></div>'
        '<div class="balanced-panel balanced-panel--alt"></div>'
        '</div>'
    )


def _hero_title_markup(style_id: str) -> str:
    if style_id == "kinetic-typography":
        return (
            '<h1 class="hero__title hero__title--kinetic">'
            '<span>ALFRED</span><span>DEV</span><span>PARA</span><span>EQUIPOS</span>'
            '</h1>'
        )
    if style_id == "maximalism-neo-retro":
        return (
            '<h1 class="hero__title hero__title--maxi">'
            'Un sistema serio<br>para equipos<br>que no quieren<br>parecer plantilla'
            '</h1>'
        )
    if style_id == "neo-brutalism":
        return (
            '<h1 class="hero__title hero__title--brutal">'
            'UN PLUGIN<br>CON CRITERIO<br>Y GOLPE VISUAL'
            '</h1>'
        )
    return f'<h1 class="hero__title">{_escape(DEMO_CONTENT["headline"])}</h1>'


def _feature_cards() -> str:
    return "".join(
        '<article class="feature-card">'
        f'<h3>{_escape(item["title"])}</h3>'
        f'<p>{_escape(item["body"])}</p>'
        '</article>'
        for item in DEMO_CONTENT["features"]
    )


def _steps_markup() -> str:
    return "".join(
        '<li>'
        f'<span class="step-index">0{index}</span>'
        f'<span>{_escape(item)}</span>'
        '</li>'
        for index, item in enumerate(DEMO_CONTENT["steps"], start=1)
    )


def _stats_markup() -> str:
    return "".join(
        '<div class="stat-pill">'
        f'<strong>{_escape(value)}</strong><span>{_escape(label)}</span>'
        '</div>'
        for value, label in DEMO_CONTENT["meta"]
    )


def _demo_base_css(palette: Dict[str, str], headings: str, body: str) -> str:
    return f"""
      :root {{
        --surface: {palette['surface']};
        --surface-alt: {palette['surface_alt']};
        --ink: {palette['ink']};
        --muted: {palette['muted']};
        --accent: {palette['accent']};
        --accent-alt: {palette['accent_alt']};
        --line: rgba(17, 17, 17, 0.12);
        --shadow: 0 24px 80px rgba(17, 17, 17, 0.16);
        --font-display: "{headings}", system-ui, sans-serif;
        --font-body: "{body}", system-ui, sans-serif;
      }}

      * {{ box-sizing: border-box; }}

      html, body {{
        margin: 0;
        padding: 0;
        min-height: 100%;
      }}

      body {{
        font-family: var(--font-body);
        background: var(--surface);
        color: var(--ink);
      }}

      a {{
        color: inherit;
      }}

      .demo-shell {{
        max-width: 1440px;
        margin: 0 auto;
        padding: 28px;
      }}

      .topbar,
      .hero,
      .meta-strip,
      .content-grid,
      .cta-band {{
        border: 2px solid rgba(17, 17, 17, 0.16);
      }}

      .topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        padding: 18px 20px;
        background: rgba(255, 255, 255, 0.44);
        backdrop-filter: blur(12px);
      }}

      .topbar__brand {{
        display: flex;
        align-items: center;
        gap: 14px;
        flex-wrap: wrap;
      }}

      .brand-badge,
      .style-badge,
      .palette-chip,
      .style-card__tag {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        border: 1.5px solid rgba(17, 17, 17, 0.2);
        background: rgba(255, 255, 255, 0.56);
      }}

      .brand-badge {{
        background: var(--accent);
        color: #ffffff;
      }}

      .style-badge {{
        background: rgba(255, 255, 255, 0.68);
      }}

      .topbar__actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
        justify-content: flex-end;
      }}

      .topbar__actions a,
      .font-chip__links a,
      .style-links a,
      .gallery-card__links a {{
        text-underline-offset: 0.16em;
        text-decoration-thickness: 1.5px;
      }}

      .hero {{
        margin-top: 22px;
        padding: 28px;
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
        gap: 22px;
        background:
          radial-gradient(circle at top right, rgba(255,255,255,0.6), transparent 28rem),
          linear-gradient(180deg, rgba(255,255,255,0.42), rgba(255,255,255,0.12));
        overflow: hidden;
        position: relative;
      }}

      .hero::after {{
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background-image: linear-gradient(rgba(17,17,17,0.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(17,17,17,0.05) 1px, transparent 1px);
        background-size: 28px 28px;
        opacity: 0.18;
      }}

      .hero__copy,
      .hero__art {{
        position: relative;
        z-index: 1;
      }}

      .hero__eyebrow,
      .section-kicker {{
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
        color: var(--muted);
      }}

      .hero__title {{
        margin: 12px 0 0;
        font-family: var(--font-display);
        font-size: clamp(52px, 9vw, 104px);
        line-height: 0.92;
        letter-spacing: -0.06em;
      }}

      .hero__body {{
        max-width: 58ch;
        margin-top: 18px;
        font-size: 18px;
        line-height: 1.65;
        color: var(--muted);
      }}

      .hero__actions,
      .meta-strip,
      .style-links,
      .style-fonts,
      .palette-mode-list,
      .gallery-card__links {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
      }}

      .hero__actions {{
        margin-top: 24px;
      }}

      .hero__actions a {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 48px;
        padding: 0 18px;
        border-radius: 999px;
        border: 1.5px solid rgba(17, 17, 17, 0.18);
        text-decoration: none;
        font-weight: 700;
      }}

      .hero__actions a:first-child {{
        background: var(--accent);
        color: #ffffff;
      }}

      .hero__actions a:last-child {{
        background: rgba(255,255,255,0.55);
      }}

      .hero__art {{
        min-height: 440px;
        display: flex;
        align-items: center;
        justify-content: center;
      }}

      .meta-strip {{
        margin-top: 18px;
        padding: 16px 18px;
        background: rgba(255,255,255,0.48);
        align-items: center;
      }}

      .stat-pill {{
        display: grid;
        gap: 4px;
        min-width: 130px;
      }}

      .stat-pill strong {{
        font-family: var(--font-display);
        font-size: 28px;
        line-height: 0.9;
        letter-spacing: -0.05em;
      }}

      .stat-pill span {{
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
      }}

      .style-meta {{
        margin-top: 18px;
        display: grid;
        gap: 14px;
      }}

      .style-fonts {{
        gap: 14px;
      }}

      .font-chip {{
        display: grid;
        gap: 6px;
        min-width: 220px;
        padding: 14px 16px;
        background: rgba(255,255,255,0.46);
        border: 1.5px solid rgba(17,17,17,0.12);
      }}

      .font-chip strong {{
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}

      .font-chip span,
      .style-links__empty {{
        font-size: 14px;
        color: var(--muted);
      }}

      .font-chip__links {{
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        font-size: 13px;
      }}

      .content-grid {{
        margin-top: 18px;
        padding: 24px;
        display: grid;
        grid-template-columns: minmax(0, 1fr) 340px;
        gap: 20px;
        background: rgba(255,255,255,0.42);
      }}

      .feature-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
      }}

      .feature-card,
      .story-card {{
        padding: 18px;
        background: rgba(255,255,255,0.54);
        border: 1.5px solid rgba(17,17,17,0.12);
      }}

      .feature-card h3,
      .story-card h3 {{
        margin: 0 0 10px;
        font-family: var(--font-display);
        font-size: 24px;
        line-height: 1;
      }}

      .feature-card p,
      .story-card p {{
        margin: 0;
        line-height: 1.65;
        color: var(--muted);
      }}

      .story-rail {{
        display: grid;
        gap: 14px;
      }}

      .story-rail ul {{
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 14px;
      }}

      .story-rail li {{
        display: grid;
        grid-template-columns: 52px 1fr;
        gap: 12px;
        align-items: start;
      }}

      .step-index {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 52px;
        height: 52px;
        background: var(--accent);
        color: #ffffff;
        border-radius: 999px;
        font-family: var(--font-display);
        font-size: 22px;
      }}

      .cta-band {{
        margin-top: 18px;
        padding: 22px 24px;
        display: grid;
        gap: 10px;
        background: linear-gradient(120deg, rgba(255,255,255,0.52), rgba(255,255,255,0.24));
      }}

      .cta-band h2,
      .gallery-head h1,
      .gallery-card h2 {{
        margin: 0;
        font-family: var(--font-display);
        letter-spacing: -0.04em;
      }}

      .cta-band p,
      .gallery-head p,
      .gallery-card p {{
        margin: 0;
        line-height: 1.65;
        color: var(--muted);
      }}

      .gallery-body {{
        max-width: 1480px;
        margin: 0 auto;
        padding: 28px;
        background:
          radial-gradient(circle at top left, rgba(255,255,255,0.64), transparent 24rem),
          linear-gradient(180deg, var(--surface), rgba(255,255,255,0.86));
      }}

      .gallery-head {{
        padding: 26px;
        border: 1.5px solid rgba(17,17,17,0.14);
        background: rgba(255,255,255,0.58);
      }}

      .gallery-grid {{
        margin-top: 20px;
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
      }}

      .gallery-card {{
        padding: 20px;
        border: 1.5px solid rgba(17,17,17,0.14);
        background: rgba(255,255,255,0.58);
        display: grid;
        gap: 14px;
      }}

      .gallery-card__header {{
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: start;
      }}

      .gallery-card__meta {{
        display: grid;
        gap: 10px;
      }}

      .style-links,
      .gallery-card__links {{
        font-size: 14px;
      }}

      .palette-chip--recommended {{
        background: var(--accent);
        color: #ffffff;
      }}

      .hero-art__balanced,
      .hero-art__glass,
      .hero-art__3d,
      .hero-art__dopamine,
      .hero-art__nature,
      .hero-art__hyper,
      .hero-art__brutal,
      .hero-art__story,
      .hero-art__collage,
      .hero-art__kinetic {{
        width: min(100%, 420px);
        height: 100%;
      }}

      @media (max-width: 980px) {{
        .hero,
        .content-grid {{
          grid-template-columns: 1fr;
        }}

        .feature-grid,
        .gallery-grid {{
          grid-template-columns: 1fr;
        }}
      }}
    """


def _demo_variant_css(style_id: str) -> str:
    if style_id == "maximalism-neo-retro":
        return """
          body.demo--maximalism_neo_retro {
            background:
              radial-gradient(circle at 10% 15%, rgba(255, 66, 104, 0.24), transparent 18rem),
              radial-gradient(circle at 90% 8%, rgba(47, 30, 201, 0.18), transparent 16rem),
              linear-gradient(180deg, #fff1b8 0%, var(--surface) 56%, #fff7df 100%);
          }

          body.demo--maximalism_neo_retro .topbar,
          body.demo--maximalism_neo_retro .hero,
          body.demo--maximalism_neo_retro .content-grid,
          body.demo--maximalism_neo_retro .cta-band,
          body.demo--maximalism_neo_retro .meta-strip,
          body.demo--maximalism_neo_retro .feature-card {
            border-width: 3px;
            border-color: rgba(29, 16, 32, 0.24);
            box-shadow: 10px 10px 0 rgba(29, 16, 32, 0.18);
          }

          .hero-art__collage {
            position: relative;
          }

          .sticker {
            position: absolute;
            padding: 10px 14px;
            background: #111111;
            color: #ffffff;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.08em;
            transform: rotate(-7deg);
          }

          .sticker--alt {
            right: 10px;
            top: 42px;
            background: var(--accent-alt);
            transform: rotate(6deg);
          }

          .blob, .frame {
            position: absolute;
            inset: auto;
          }

          .blob {
            border-radius: 32% 68% 61% 39% / 46% 38% 62% 54%;
            opacity: 0.92;
          }

          .blob--a {
            width: 220px;
            height: 220px;
            background: var(--accent);
            top: 110px;
            left: 24px;
          }

          .blob--b {
            width: 180px;
            height: 180px;
            background: var(--accent-alt);
            bottom: 36px;
            right: 24px;
          }

          .frame {
            border: 5px solid #111111;
            background: rgba(255,255,255,0.24);
          }

          .frame--a {
            width: 180px;
            height: 240px;
            top: 76px;
            right: 64px;
            transform: rotate(-9deg);
          }

          .frame--b {
            width: 140px;
            height: 160px;
            bottom: 10px;
            left: 84px;
            transform: rotate(11deg);
          }
        """
    if style_id == "kinetic-typography":
        return """
          body.demo--kinetic_typography .hero__title--kinetic {
            display: grid;
            gap: 0;
            font-size: clamp(56px, 11vw, 136px);
          }

          body.demo--kinetic_typography .hero__title--kinetic span:nth-child(2) {
            margin-left: 8%;
          }

          body.demo--kinetic_typography .hero__title--kinetic span:nth-child(3) {
            margin-left: 24%;
            color: var(--accent-alt);
            transform: rotate(-2deg);
          }

          body.demo--kinetic_typography .hero__title--kinetic span:nth-child(4) {
            margin-left: 6%;
            color: var(--accent);
          }

          .hero-art__kinetic {
            display: grid;
            align-content: center;
            gap: 10px;
            font-family: var(--font-display);
            font-size: clamp(42px, 8vw, 90px);
            line-height: 0.88;
            letter-spacing: -0.08em;
            text-transform: uppercase;
          }

          .hero-art__kinetic span:nth-child(odd) {
            transform: translateX(8%);
          }

          .hero-art__kinetic span:nth-child(even) {
            color: var(--accent-alt);
            transform: translateX(-6%) rotate(-4deg);
          }
        """
    if style_id == "interactive-3d-webgl":
        return """
          body.demo--interactive_3d_webgl .hero {
            background:
              radial-gradient(circle at 70% 20%, rgba(79, 70, 229, 0.22), transparent 18rem),
              linear-gradient(180deg, rgba(255,255,255,0.56), rgba(255,255,255,0.18));
          }

          .hero-art__3d {
            position: relative;
            perspective: 1000px;
          }

          .cube {
            position: absolute;
            inset: 0;
            margin: auto;
            width: 220px;
            height: 220px;
            border-radius: 28px;
            background: linear-gradient(140deg, rgba(255,255,255,0.94), rgba(79, 70, 229, 0.24));
            border: 1px solid rgba(17,17,17,0.08);
            box-shadow: 0 30px 80px rgba(79, 70, 229, 0.24);
          }

          .cube--front { transform: rotateX(56deg) rotateZ(-24deg) translateZ(40px); }
          .cube--mid { transform: rotateX(56deg) rotateZ(-24deg) translateY(-26px) scale(0.88); }
          .cube--back { transform: rotateX(56deg) rotateZ(-24deg) translateY(26px) scale(0.78); opacity: 0.54; }
        """
    if style_id == "glassmorphism-2":
        return """
          body.demo--glassmorphism_2 {
            background:
              radial-gradient(circle at 15% 15%, rgba(195, 107, 255, 0.28), transparent 18rem),
              radial-gradient(circle at 85% 15%, rgba(124, 156, 255, 0.22), transparent 18rem),
              linear-gradient(180deg, #eef2ff 0%, var(--surface) 46%, #f7f3ff 100%);
          }

          body.demo--glassmorphism_2 .topbar,
          body.demo--glassmorphism_2 .hero,
          body.demo--glassmorphism_2 .content-grid,
          body.demo--glassmorphism_2 .cta-band,
          body.demo--glassmorphism_2 .feature-card,
          body.demo--glassmorphism_2 .font-chip {
            background: rgba(255,255,255,0.26);
            backdrop-filter: blur(22px);
            border-color: rgba(255,255,255,0.38);
          }

          .hero-art__glass {
            position: relative;
          }

          .glass-card,
          .glass-orb {
            position: absolute;
            border-radius: 32px;
            backdrop-filter: blur(18px);
            border: 1px solid rgba(255,255,255,0.38);
            background: linear-gradient(180deg, rgba(255,255,255,0.5), rgba(255,255,255,0.14));
          }

          .glass-card--main {
            width: 260px;
            height: 320px;
            top: 36px;
            left: 42px;
          }

          .glass-card--small {
            width: 180px;
            height: 180px;
            right: 20px;
            bottom: 28px;
          }

          .glass-orb {
            width: 120px;
            height: 120px;
            right: 36px;
            top: 32px;
            border-radius: 999px;
          }
        """
    if style_id == "dopamine-colors":
        return """
          body.demo--dopamine_colors {
            background:
              radial-gradient(circle at 8% 12%, rgba(255, 79, 163, 0.26), transparent 18rem),
              radial-gradient(circle at 90% 8%, rgba(34, 102, 255, 0.2), transparent 16rem),
              linear-gradient(180deg, #fffaa5 0%, var(--surface) 60%, #fff0b6 100%);
          }

          .hero-art__dopamine {
            position: relative;
          }

          .pill {
            position: absolute;
            border-radius: 999px;
            box-shadow: 0 20px 50px rgba(17, 17, 17, 0.12);
          }

          .pill--a {
            width: 260px;
            height: 96px;
            top: 76px;
            left: 24px;
            background: var(--accent);
            transform: rotate(-12deg);
          }

          .pill--b {
            width: 190px;
            height: 72px;
            top: 170px;
            right: 28px;
            background: var(--accent-alt);
            transform: rotate(9deg);
          }

          .pill--c {
            width: 210px;
            height: 210px;
            bottom: 24px;
            left: 100px;
            background: rgba(255,255,255,0.54);
          }
        """
    if style_id == "nature-distilled":
        return """
          body.demo--nature_distilled {
            background:
              radial-gradient(circle at 12% 12%, rgba(95, 123, 92, 0.18), transparent 18rem),
              linear-gradient(180deg, #f4ecdf 0%, var(--surface) 52%, #efe5d6 100%);
          }

          body.demo--nature_distilled .hero,
          body.demo--nature_distilled .content-grid,
          body.demo--nature_distilled .cta-band,
          body.demo--nature_distilled .feature-card,
          body.demo--nature_distilled .font-chip {
            border-radius: 36px;
          }

          .hero-art__nature {
            position: relative;
          }

          .leaf {
            position: absolute;
            border-radius: 58% 42% 68% 32% / 50% 38% 62% 50%;
            background: linear-gradient(140deg, rgba(255,255,255,0.72), rgba(95,123,92,0.42));
          }

          .leaf--a {
            width: 220px;
            height: 280px;
            left: 18px;
            top: 68px;
            transform: rotate(-10deg);
          }

          .leaf--b {
            width: 160px;
            height: 200px;
            right: 26px;
            top: 48px;
            transform: rotate(18deg);
          }

          .leaf--c {
            width: 140px;
            height: 170px;
            right: 86px;
            bottom: 28px;
            transform: rotate(-18deg);
          }
        """
    if style_id == "neo-brutalism":
        return """
          body.demo--neo_brutalism {
            background: var(--surface);
          }

          body.demo--neo_brutalism .topbar,
          body.demo--neo_brutalism .hero,
          body.demo--neo_brutalism .meta-strip,
          body.demo--neo_brutalism .content-grid,
          body.demo--neo_brutalism .cta-band,
          body.demo--neo_brutalism .feature-card,
          body.demo--neo_brutalism .font-chip,
          body.demo--neo_brutalism .brand-badge,
          body.demo--neo_brutalism .style-badge,
          body.demo--neo_brutalism .palette-chip {
            border: 4px solid #111111;
            border-radius: 0;
            box-shadow: 10px 10px 0 rgba(17, 17, 17, 0.22);
          }

          body.demo--neo_brutalism .hero__title--brutal {
            font-size: clamp(58px, 10vw, 112px);
            text-transform: uppercase;
          }

          .hero-art__brutal {
            position: relative;
          }

          .brutal-card {
            position: absolute;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 200px;
            height: 110px;
            background: #f7f0e8;
            border: 4px solid #111111;
            box-shadow: 8px 8px 0 rgba(17,17,17,0.24);
            font-family: var(--font-display);
            font-size: 30px;
          }

          .brutal-card--a { top: 52px; left: 30px; transform: rotate(-8deg); }
          .brutal-card--b { top: 170px; right: 28px; background: var(--surface-alt); transform: rotate(5deg); }
          .brutal-card--c { bottom: 30px; left: 98px; background: var(--accent-alt); color: #ffffff; transform: rotate(-4deg); }
        """
    if style_id == "ai-hyperminimalism":
        return """
          body.demo--ai_hyperminimalism {
            background:
              radial-gradient(circle at 20% 12%, rgba(134, 210, 255, 0.2), transparent 18rem),
              radial-gradient(circle at 86% 12%, rgba(124, 140, 255, 0.18), transparent 18rem),
              linear-gradient(180deg, #ffffff 0%, var(--surface) 56%, #f8fbff 100%);
          }

          body.demo--ai_hyperminimalism .topbar,
          body.demo--ai_hyperminimalism .hero,
          body.demo--ai_hyperminimalism .meta-strip,
          body.demo--ai_hyperminimalism .content-grid,
          body.demo--ai_hyperminimalism .cta-band,
          body.demo--ai_hyperminimalism .feature-card,
          body.demo--ai_hyperminimalism .font-chip {
            border-radius: 28px;
            border-color: rgba(15, 23, 42, 0.08);
          }

          .hero-art__hyper {
            position: relative;
          }

          .hyper-ring {
            position: absolute;
            inset: 0;
            margin: auto;
            width: 260px;
            height: 260px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(255,255,255,0.8), rgba(124,140,255,0.14));
            border: 1px solid rgba(255,255,255,0.9);
            box-shadow: 0 36px 100px rgba(124, 140, 255, 0.18);
          }

          .hyper-panel {
            position: absolute;
            inset: auto 32px 36px 32px;
            height: 96px;
            border-radius: 22px;
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(15,23,42,0.08);
            backdrop-filter: blur(14px);
          }
        """
    if style_id == "narrative-scroll-gamification":
        return """
          body.demo--narrative_scroll_gamification .content-grid {
            grid-template-columns: minmax(0, 1.05fr) 360px;
          }

          .hero-art__story {
            display: grid;
            align-content: center;
            justify-items: center;
            gap: 8px;
          }

          .story-step {
            width: 84px;
            height: 84px;
            border-radius: 999px;
            background: var(--accent);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-display);
            font-size: 28px;
            box-shadow: 0 18px 40px rgba(47, 111, 237, 0.24);
          }

          .story-line {
            width: 4px;
            height: 54px;
            background: linear-gradient(180deg, var(--accent), var(--accent-alt));
          }
        """
    return """
      body.demo--free_default .hero,
      body.demo--free_default .content-grid,
      body.demo--free_default .cta-band {
        border-radius: 24px;
      }

      .hero-art__balanced {
        position: relative;
      }

      .balanced-panel {
        position: absolute;
        inset: auto;
        width: 230px;
        height: 180px;
        top: 90px;
        left: 46px;
        border-radius: 26px;
        background: linear-gradient(140deg, rgba(255,255,255,0.92), rgba(47,111,237,0.18));
      }

      .balanced-panel--alt {
        width: 180px;
        height: 140px;
        right: 36px;
        bottom: 38px;
        background: linear-gradient(140deg, rgba(255,255,255,0.76), rgba(18,40,76,0.18));
      }
    """


def render_style_demo_document(
    style_id: str,
    *,
    palette_mode: Optional[str] = None,
    font_pairing_id: Optional[str] = None,
    custom_google_fonts_url: Optional[str] = None,
    custom_headings: Optional[str] = None,
    custom_body: Optional[str] = None,
) -> str:
    """Renderiza una landing simple de demo para un sistema de diseño."""
    style = get_style_trend(style_id)
    palette, resolved_palette_mode = resolve_palette(style_id, palette_mode)
    pairing = resolve_font_pairing(
        style_id,
        pairing_id=font_pairing_id,
        custom_google_fonts_url=custom_google_fonts_url,
        custom_headings=custom_headings,
        custom_body=custom_body,
    )

    reference_markup = _refs_markup(style["references"])
    palette_markup = _palette_mode_markup(style["palette_modes"], style["recommended_palette_mode"])
    feature_cards = _feature_cards()
    steps = _steps_markup()
    stats = _stats_markup()
    title_markup = _hero_title_markup(style_id)
    hero_art_markup = _hero_art(style_id)
    google_fonts = pairing.get("css_url", "")
    custom_url = pairing.get("custom_url", "")
    google_fonts_link = (
        f'<link rel="preconnect" href="https://fonts.googleapis.com">'
        f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link href="{_escape(google_fonts)}" rel="stylesheet">'
        if google_fonts
        else ""
    )
    custom_note = (
        f'<p class="section-kicker">URL tipografica custom: <a href="{_escape(custom_url)}" target="_blank" rel="noreferrer">{_escape(custom_url)}</a></p>'
        if custom_url
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_escape(style["name"])} — Demo de sistema de diseño de Selina</title>
  {google_fonts_link}
  <style>
    {_demo_base_css(palette, pairing["headings"], pairing["body"])}
    {_demo_variant_css(style_id)}
  </style>
</head>
<body class="demo demo--{_escape(_style_class(style_id))}">
  <div class="demo-shell">
    <header class="topbar">
      <div class="topbar__brand">
        <span class="brand-badge">SELINA</span>
        <span class="style-badge">{_escape(style["name"])}</span>
        <span class="style-badge">{_escape(resolved_palette_mode)}</span>
      </div>
      <div class="topbar__actions">
        <a href="{_escape(pairing['headings_specimen_url'])}" target="_blank" rel="noreferrer">{_escape(pairing['headings'])}</a>
        <a href="{_escape(pairing['body_specimen_url'])}" target="_blank" rel="noreferrer">{_escape(pairing['body'])}</a>
      </div>
    </header>

    <section class="hero">
      <div class="hero__copy">
        <p class="hero__eyebrow">{_escape(DEMO_CONTENT["eyebrow"])}</p>
        {title_markup}
        <p class="hero__body">{_escape(DEMO_CONTENT["body"])}</p>
        <div class="hero__actions">
          <a href="#cta">{_escape(DEMO_CONTENT["primary_cta"])}</a>
          <a href="#features">{_escape(DEMO_CONTENT["secondary_cta"])}</a>
        </div>
        <div class="style-meta">
          <div class="style-links">{reference_markup}</div>
          <div class="palette-mode-list">{palette_markup}</div>
          <div class="style-fonts">{_fonts_markup([pairing])}</div>
          {custom_note}
        </div>
      </div>
      <div class="hero__art">{hero_art_markup}</div>
    </section>

    <section class="meta-strip">
      {stats}
    </section>

    <section class="content-grid" id="features">
      <div>
        <p class="section-kicker">{_escape(style["summary"])}</p>
        <h2>{_escape(DEMO_CONTENT["feature_title"])}</h2>
        <div class="feature-grid">{feature_cards}</div>
      </div>
      <aside class="story-rail">
        <p class="section-kicker">Ruta que explica el producto</p>
        <ul>{steps}</ul>
      </aside>
    </section>

    <section class="cta-band" id="cta">
      <p class="section-kicker">{_escape(style["description"])}</p>
      <h2>{_escape(style["when_to_use"])}</h2>
      <p>Esta demo no pretende cerrar diseño final. Sirve para validar si este sistema de diseño merece pasar a la siguiente ronda de Selina.</p>
    </section>
  </div>
</body>
</html>
"""


def render_style_gallery_html(title: Optional[str] = None, subtitle: Optional[str] = None) -> str:
    """Renderiza una galería navegable del catálogo de sistemas de diseño."""
    catalog = get_style_catalog()
    title_text = title or "Atlas de sistemas de diseño de Selina"
    subtitle_text = subtitle or (
        "Catálogo de sistemas de diseño para explorar direcciones comparables antes de que Selina "
        "proponga las tres opciones finales de una fase real."
    )

    card_markup = []
    for entry in catalog:
        pairings = list(entry["font_pairings"])
        refs = _refs_markup(entry["references"])
        palette_chips = _palette_mode_markup(entry["palette_modes"], entry["recommended_palette_mode"])
        demo_href = f"/files/demos/{entry['id']}.html"
        card_markup.append(
            '<article class="gallery-card">'
            '<div class="gallery-card__header">'
            f'<div class="gallery-card__meta"><span class="style-card__tag">{_escape(entry["name"])}</span>'
            f'<h2>{_escape(entry["name"])}</h2></div>'
            f'<a href="{_escape(demo_href)}">Abrir demo</a>'
            '</div>'
            f'<p>{_escape(entry["summary"])}</p>'
            f'<div class="palette-mode-list">{palette_chips}</div>'
            f'<div class="style-links">{refs}</div>'
            f'<div class="style-fonts">{_fonts_markup(pairings)}</div>'
            '<div class="gallery-card__links">'
            f'<a href="{_escape(demo_href)}">Sistema de diseño base</a>'
            '</div></article>'
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_escape(title_text)}</title>
  <style>
    {_demo_base_css(
        {
            "surface": "#f4efe9",
            "surface_alt": "#e7ddd1",
            "ink": "#161311",
            "muted": "#675d57",
            "accent": "#1b63ff",
            "accent_alt": "#111111",
        },
        "Space Grotesk",
        "Inter",
    )}
  </style>
</head>
<body>
  <div class="gallery-body">
    <section class="gallery-head">
      <p class="section-kicker">Selina / catálogo de sistemas de diseño</p>
      <h1>{_escape(title_text)}</h1>
      <p>{_escape(subtitle_text)}</p>
      <p>Regla operativa: el catálogo puede tener muchos sistemas de diseño base, pero la fase real de Selina sigue cerrando con tres propuestas comparables, no con diez opciones a la vez.</p>
    </section>
    <section class="gallery-grid">
      {"".join(card_markup)}
    </section>
  </div>
</body>
</html>
"""


def write_style_demo_gallery(
    visual_path: str,
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Dict[str, object]:
    """Escribe una galeria y una demo simple por estilo dentro de una sesion visual."""
    session_dir = resolve_visual_session_dir(visual_path)
    content_dir = os.path.join(session_dir, "content")
    demos_dir = os.path.join(content_dir, "demos")
    os.makedirs(demos_dir, exist_ok=True)

    demo_paths: List[str] = []
    for entry in get_style_catalog():
        demo_path = os.path.join(demos_dir, f"{entry['id']}.html")
        with open(demo_path, "w", encoding="utf-8") as fh:
            fh.write(render_style_demo_document(entry["id"]))
        demo_paths.append(demo_path)

    gallery_path = os.path.join(content_dir, STYLE_DEMO_GALLERY_FILENAME)
    with open(gallery_path, "w", encoding="utf-8") as fh:
        fh.write(render_style_gallery_html(title=title, subtitle=subtitle))

    return {
        "status": "ok",
        "gallery_path": gallery_path,
        "demo_paths": demo_paths,
        "style_count": len(demo_paths),
        "default_style_id": DEFAULT_STYLE_ID,
    }
