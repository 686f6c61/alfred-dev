#!/usr/bin/env python3
"""Catalogo canonico de direcciones visuales para Selina."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_STYLE_ID = "free-default"

PALETTE_MODE_CATALOG: Tuple[Dict[str, str], ...] = (
    {
        "id": "recommended",
        "label": "Recomendada",
        "description": "La paleta principal que mejor expresa esa familia visual.",
    },
    {
        "id": "pastel",
        "label": "Pastel",
        "description": "Version suave, luminosa y mas amable de la familia.",
    },
    {
        "id": "solid",
        "label": "Solidos",
        "description": "Color con mayor peso visual y contraste mas directo.",
    },
    {
        "id": "monochrome",
        "label": "Monocromatica",
        "description": "Escala contenida para productos que necesitan foco y disciplina.",
    },
    {
        "id": "earth",
        "label": "Tierra",
        "description": "Base organica, calida y menos tecnologica.",
    },
    {
        "id": "dopamine",
        "label": "Dopamina",
        "description": "Version energica y muy visible pensada para impacto inmediato.",
    },
)


def _specimen_url(font_name: str) -> str:
    return f"https://fonts.google.com/specimen/{font_name.replace(' ', '+')}"


def _css_url(*families: str) -> str:
    family_query = "&".join(
        f"family={family.replace(' ', '+')}:wght@400;500;700" for family in families
    )
    return f"https://fonts.googleapis.com/css2?{family_query}&display=swap"


def _reference(label: str, url: str) -> Dict[str, str]:
    return {"label": label, "url": url}


def _font_pairing(
    pairing_id: str,
    label: str,
    headings: str,
    body: str,
    *,
    notes: str,
) -> Dict[str, str]:
    return {
        "id": pairing_id,
        "label": label,
        "headings": headings,
        "body": body,
        "notes": notes,
        "headings_specimen_url": _specimen_url(headings),
        "body_specimen_url": _specimen_url(body),
        "css_url": _css_url(headings, body),
        "source": "google-fonts",
    }


def _palette(
    surface: str,
    surface_alt: str,
    ink: str,
    muted: str,
    accent: str,
    accent_alt: str,
) -> Dict[str, str]:
    return {
        "surface": surface,
        "surface_alt": surface_alt,
        "ink": ink,
        "muted": muted,
        "accent": accent,
        "accent_alt": accent_alt,
    }


STYLE_CATALOG: Tuple[Dict[str, Any], ...] = (
    {
        "id": DEFAULT_STYLE_ID,
        "name": "Libre / Contextual",
        "summary": "Selina trabaja como hasta ahora y decide la direccion a partir del producto, sin casar el proyecto con una tendencia previa.",
        "description": "Modo sin sistema de diseño prefijado. Sirve cuando la mejor respuesta sale del PRD, del usuario y del contexto real del producto.",
        "when_to_use": "Conviene cuando quieres criterio visual sin imponer una corriente concreta desde el principio.",
        "anti_patterns": [
            "No obliga a parecer una marca de tendencia si el producto pide otra cosa.",
            "No convierte la fase visual en una votacion de moodboards sin contexto.",
        ],
        "context_signals": [
            "Producto con necesidades mixtas o todavia poco definidas.",
            "Equipo que quiere que Selina parta del problema antes que de la estetica.",
        ],
        "references": [],
        "palette_modes": ["recommended", "pastel", "solid", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#f4efe9", "#e8e0d7", "#181311", "#6f635c", "#2f6fed", "#12284c"),
            "pastel": _palette("#f6f2ec", "#eed8de", "#1d1715", "#796c66", "#d8a7c4", "#88b5ff"),
            "solid": _palette("#f1ece5", "#e1d4c7", "#171210", "#655852", "#1847c9", "#0f1d40"),
            "monochrome": _palette("#f2efeb", "#e4dfd8", "#141414", "#666666", "#4a4a4a", "#272727"),
        },
        "font_pairings": (
            _font_pairing(
                "contextual-sans",
                "Contextual Sans",
                "Space Grotesk",
                "Inter",
                notes="Pareja neutral para que el sistema lo marque el producto, no la tipografía.",
            ),
            _font_pairing(
                "contextual-editorial",
                "Contextual Editorial",
                "Fraunces",
                "DM Sans",
                notes="Cuando el producto pide mas criterio o un tono mas curado.",
            ),
        ),
        "suggested_density": "Equilibrada, con foco en lectura clara y jerarquia entendible.",
        "suggested_tone": "Flexible, contemporaneo y guiado por el producto.",
        "suggested_component": "Hero claro con propuesta de valor, prueba social y CTA principal.",
    },
    {
        "id": "maximalism-neo-retro",
        "name": "Maximalismo & Neo-retro",
        "summary": "Capas, texturas, saturacion y caos controlado con sabor editorial y humano.",
        "description": "Direccion rica en color, contraste y grafica. Funciona cuando la marca puede permitirse ruido expresivo y caracter inmediato.",
        "when_to_use": "Encaja bien cuando el producto necesita personalidad alta, memoria visual y una sensacion humana nada esteril.",
        "anti_patterns": [
            "No es la mejor opcion para entornos de monitorizacion densa o backoffice serio.",
            "No conviene si la lectura rapida y la contencion visual son prioridad absoluta.",
        ],
        "context_signals": [
            "Marca con tono expresivo o cultural.",
            "Necesidad de diferenciarse de interfaces SaaS genericas.",
        ],
        "references": [
            _reference("Vacation", "https://www.vacation.inc"),
            _reference("Wix Trends 2026", "https://www.wix.com/blog/web-design-trends"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "dopamine"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#f7cf44", "#ff8a65", "#1d1020", "#61474f", "#ff4268", "#2f1ec9"),
            "pastel": _palette("#f8e9a8", "#f6c7bb", "#201417", "#705d62", "#f28bb2", "#b39df6"),
            "solid": _palette("#ffcd00", "#ff6b35", "#170d14", "#5b4d52", "#ff1f63", "#3c27ff"),
            "dopamine": _palette("#ffe75b", "#ff6fa3", "#160d22", "#59496c", "#ff275e", "#19a7ff"),
        },
        "font_pairings": (
            _font_pairing(
                "maxi-retro",
                "Retro editorial",
                "Bricolage Grotesque",
                "Newsreader",
                notes="Titulares con gesto y cuerpo con una lectura mas de revista.",
            ),
            _font_pairing(
                "maxi-saturated",
                "Saturado y humano",
                "Archivo Black",
                "DM Sans",
                notes="Mas impacto directo y menos nostalgia refinada.",
            ),
        ),
        "suggested_density": "Media-alta, con capas visibles, ritmo rapido y bloques que se pisan con intencion.",
        "suggested_tone": "Expresivo, humano y con sentido de cultura visual.",
        "suggested_component": "Hero apilado con stickers, cards inclinadas y CTA protagonista.",
    },
    {
        "id": "kinetic-typography",
        "name": "Tipografia cinetica",
        "summary": "El texto domina la experiencia: gigantesco, dramatizado y pensado como gesto visual.",
        "description": "Direccion centrada en titulares y ritmo tipografico. La tipografia deja de ser soporte y pasa a ser estructura.",
        "when_to_use": "Muy buena cuando el mensaje comercial o narrativo es mas fuerte que el recurso grafico y necesita gobernar la pagina.",
        "anti_patterns": [
            "No es ideal si el producto depende de mucha explicacion secundaria por encima del claim principal.",
            "No conviene si la marca necesita discrecion o una voz corporativa clasica.",
        ],
        "context_signals": [
            "Proyecto con claims fuertes o posicionamiento muy claro.",
            "Necesidad de convertir titulares y scroll en experiencia.",
        ],
        "references": [
            _reference("Grog Shop", "https://grog.shop"),
            _reference("Made by Analogue", "https://www.madebyanalogue.com"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#fbf6ef", "#efe4d6", "#111111", "#5a524b", "#111111", "#ef5338"),
            "pastel": _palette("#fbf4ef", "#f1d5dc", "#141111", "#746966", "#ea8aa2", "#7cb6ff"),
            "solid": _palette("#f8efe6", "#e9d4c1", "#121212", "#62574d", "#121212", "#ff4b2b"),
            "monochrome": _palette("#f3f3f3", "#d9d9d9", "#0f0f0f", "#5e5e5e", "#121212", "#303030"),
        },
        "font_pairings": (
            _font_pairing(
                "kinetic-core",
                "Kinetic Core",
                "Archivo Black",
                "Space Grotesk",
                notes="Titulares enormes y cuerpo sobrio que no compite con ellos.",
            ),
            _font_pairing(
                "kinetic-editorial",
                "Kinetic Editorial",
                "Syne",
                "IBM Plex Sans",
                notes="Mas gesto organico y menos dureza geométrica.",
            ),
        ),
        "suggested_density": "Media, con titulares dominantes y mucho contraste entre escalas.",
        "suggested_tone": "Directo, energico y performativo.",
        "suggested_component": "Hero de texto gigante con palabras en tension y CTA secundario discreto.",
    },
    {
        "id": "interactive-3d-webgl",
        "name": "3D interactivo & WebGL",
        "summary": "Volumen, profundidad y objetos como parte del mensaje del producto.",
        "description": "Direccion pensada para productos que necesitan objeto, espacio o demostracion visual inmersiva antes de explicar con detalle.",
        "when_to_use": "Encaja cuando la experiencia o el producto ganan muchisimo si se perciben como objeto manipulable o entorno inmersivo.",
        "anti_patterns": [
            "No conviene para landings donde el peso de la conversion depende de lectura inmediata y coste visual bajo.",
            "No es la mejor primera opcion si el equipo no puede sostener una capa visual ambiciosa.",
        ],
        "context_signals": [
            "Producto con componente espacial, visual o tangible.",
            "Necesidad de crear profundidad y sensacion de exploracion.",
        ],
        "references": [
            _reference("Nike", "https://www.nike.com"),
            _reference("Spline", "https://spline.design"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#eef2ff", "#dfe5ff", "#111827", "#546179", "#4f46e5", "#0ea5e9"),
            "pastel": _palette("#f2f4ff", "#e1e7ff", "#152033", "#687487", "#9aa7ff", "#87d2ff"),
            "solid": _palette("#e8eeff", "#d5e0ff", "#0f172a", "#4f5a72", "#4338ca", "#0284c7"),
            "monochrome": _palette("#f2f4f7", "#dde2e8", "#111827", "#667085", "#1f2937", "#475467"),
        },
        "font_pairings": (
            _font_pairing(
                "3d-core",
                "Immersive Sans",
                "Sora",
                "Inter",
                notes="Tecnologica sin caer en ciencia ficcion barata.",
            ),
            _font_pairing(
                "3d-product",
                "Product Spatial",
                "Outfit",
                "Manrope",
                notes="Mas suave y comercial para producto moderno.",
            ),
        ),
        "suggested_density": "Media, con foco en un objeto o escena hero de mucha presencia.",
        "suggested_tone": "Inmersivo, ambicioso y muy visual.",
        "suggested_component": "Hero con objeto 3D protagonista y panel lateral con mensaje y CTA.",
    },
    {
        "id": "glassmorphism-2",
        "name": "Glassmorphism 2.0",
        "summary": "Paneles translúcidos, profundidad contenida y una interfaz con capas suaves y maduras.",
        "description": "Version mas sobria del glassmorphism. Menos truco de moda y mas sistema con capas claras, blur, luz y profundidad.",
        "when_to_use": "Funciona cuando el producto quiere verse avanzado y pulido sin entrar en brutalismo ni minimalismo extremo.",
        "anti_patterns": [
            "No encaja si la marca necesita crudeza, friccion o sensacion industrial.",
            "No es la mejor opcion cuando el contexto pide maxima robustez tipografica y cero ornamento.",
        ],
        "context_signals": [
            "Producto digital con vocacion premium.",
            "Necesidad de capas, estado y profundidad con tacto contemporaneo.",
        ],
        "references": [
            _reference("Apple HIG", "https://developer.apple.com/design/human-interface-guidelines"),
            _reference("UX Collective", "https://uxdesign.cc/the-most-popular-experience-design-trends-of-2026-3ca85c8a3e3d"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#edf4ff", "#d9e8ff", "#0f172a", "#526176", "#7c9cff", "#c36bff"),
            "pastel": _palette("#f4f7ff", "#e6defc", "#172033", "#67748c", "#b4c4ff", "#d4b6ff"),
            "solid": _palette("#e7f0ff", "#d7e5ff", "#0b1326", "#4b5a73", "#5a7fff", "#a855f7"),
            "monochrome": _palette("#f3f4f6", "#e2e5ea", "#111827", "#667085", "#475467", "#98a2b3"),
        },
        "font_pairings": (
            _font_pairing(
                "glass-premium",
                "Liquid Premium",
                "Sora",
                "Manrope",
                notes="Suave, pulida y con aire premium de producto moderno.",
            ),
            _font_pairing(
                "glass-ui",
                "UI Translucida",
                "Outfit",
                "Plus Jakarta Sans",
                notes="Mas interfaz y menos identidad editorial.",
            ),
        ),
        "suggested_density": "Media, con bloques flotantes, separaciones limpias y jerarquia de capas.",
        "suggested_tone": "Pulido, premium y tecnologico sin agresividad.",
        "suggested_component": "Panel de hero con tarjetas translúcidas, trust bar y CTA nítido.",
    },
    {
        "id": "dopamine-colors",
        "name": "Colores dopamina",
        "summary": "Saturacion alta, energia inmediata y una UI que busca respuesta emocional rapida.",
        "description": "Direccion colorista, juvenil y de impacto. La marca entra primero por color, luego por estructura.",
        "when_to_use": "Muy buena cuando la marca necesita alegria, energia, visibilidad y no teme parecer claramente no-corporativa.",
        "anti_patterns": [
            "No conviene para contextos regulatorios, B2B sobrio o productos que piden confianza silenciosa.",
            "No es la opcion adecuada si la accesibilidad cromatica no se cuida con disciplina.",
        ],
        "context_signals": [
            "Marca juvenil o con tono muy visible.",
            "Necesidad de generar energia e inmediatez emocional.",
        ],
        "references": [
            _reference("Lush", "https://www.lush.com"),
            _reference("Starface", "https://www.starface.world"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "dopamine"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#fff46a", "#ffb800", "#161019", "#5d5267", "#ff4fa3", "#2266ff"),
            "pastel": _palette("#fff8b3", "#ffd6ea", "#1a1520", "#685f71", "#ff9ecb", "#9ebcff"),
            "solid": _palette("#ffe500", "#ff9900", "#120d19", "#5a4e66", "#ff2f92", "#1f5dff"),
            "dopamine": _palette("#f9ff57", "#ff7a00", "#0f0a18", "#564b63", "#ff2478", "#00a6ff"),
        },
        "font_pairings": (
            _font_pairing(
                "dopamine-pop",
                "Pop Saturado",
                "Bungee",
                "DM Sans",
                notes="Fuerte presencia de marca y cuerpo muy legible.",
            ),
            _font_pairing(
                "dopamine-clean",
                "Energia legible",
                "Syne",
                "Work Sans",
                notes="Mas facil de sostener a largo plazo sin perder energia.",
            ),
        ),
        "suggested_density": "Media-alta, con bloques claros, cromatismo protagonista y ritmo rapido.",
        "suggested_tone": "Energetico, visible y muy emocional.",
        "suggested_component": "Hero con claim corto, CTA vibrante y mosaico de beneficios muy cromatico.",
    },
    {
        "id": "nature-distilled",
        "name": "Nature distilled / Organico",
        "summary": "Tonos tierra, curvas suaves y una interfaz que respira calidez y autenticidad.",
        "description": "Direccion organica y calmada. Menos grid duro, mas asimetria controlada, calidez y tactilidad.",
        "when_to_use": "Encaja cuando el producto necesita confianza humana, sostenibilidad, calma o una marca menos sintetica.",
        "anti_patterns": [
            "No es la mejor via para productos puramente tecnicos o extremadamente operativos.",
            "No conviene si el objetivo es tension grafica, agresividad comercial o sensacion industrial.",
        ],
        "context_signals": [
            "Marca con tono humano y autentico.",
            "Necesidad de transmitir sostenibilidad, calma o proximidad.",
        ],
        "references": [
            _reference("Gormley & Gamble", "https://www.gormleyandgamble.com"),
            _reference("Elementor Trends", "https://elementor.com/blog/web-design-trends-2026/"),
        ],
        "palette_modes": ["recommended", "pastel", "earth", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#efe6d8", "#d7c4aa", "#1f1a17", "#695f57", "#8c6a42", "#5f7b5c"),
            "pastel": _palette("#f5efe5", "#e8d8c6", "#201a17", "#766a61", "#c3a385", "#a8c2a4"),
            "earth": _palette("#e8dccb", "#ccb18c", "#1f1814", "#6a5c4c", "#9b6b3a", "#5b7850"),
            "monochrome": _palette("#f1ece6", "#ddd4c8", "#181614", "#68615a", "#5f5750", "#2a2623"),
        },
        "font_pairings": (
            _font_pairing(
                "nature-warm",
                "Calidez organica",
                "Fraunces",
                "Work Sans",
                notes="Serif con textura y sans funcional para equilibrio humano.",
            ),
            _font_pairing(
                "nature-soft",
                "Editorial calmado",
                "Cormorant Garamond",
                "Manrope",
                notes="Mas sensorial y editorial para marcas cuidadas.",
            ),
        ),
        "suggested_density": "Aireada, con secciones fluidas y jerarquia calmada.",
        "suggested_tone": "Humano, sereno y tangible.",
        "suggested_component": "Hero organico con fotografia o mancha suave, valor y CTA contenido.",
    },
    {
        "id": "neo-brutalism",
        "name": "Anti-diseno / Neo-brutalismo",
        "summary": "Bordes duros, sombras negras, grid roto e imperfeccion controlada con mucha personalidad.",
        "description": "Direccion de alto contraste formal. Parece humana, anti-corporativa y claramente no sintetica.",
        "when_to_use": "Funciona muy bien cuando la marca quiere tension, ironia, friccion visual y una identidad dificil de confundir.",
        "anti_patterns": [
            "No conviene si el producto necesita elegancia silenciosa o sofisticacion premium pulida.",
            "No es buena primera opcion para dashboards muy densos o productos de adopcion ultraconservadora.",
        ],
        "context_signals": [
            "Marca con voz propia y baja tolerancia a parecer generica.",
            "Necesidad de presencia fuerte con recursos visuales simples.",
        ],
        "references": [
            _reference("Brutalist Websites", "https://www.brutalistwebsites.com"),
            _reference("WannaThis Trends", "https://wannathis.one/blog/web-design-trends-2026"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#f7f0e8", "#efc6d2", "#111111", "#4b4b4b", "#111111", "#bfd4f4"),
            "pastel": _palette("#f7f0e8", "#f3d1a9", "#111111", "#4f4f4f", "#111111", "#cfc6ee"),
            "solid": _palette("#fff0b3", "#ff6b6b", "#111111", "#525252", "#111111", "#4d96ff"),
            "monochrome": _palette("#f4f4f4", "#dadada", "#101010", "#5f5f5f", "#111111", "#373737"),
        },
        "font_pairings": (
            _font_pairing(
                "brutal-core",
                "Brutal Core",
                "Archivo Black",
                "IBM Plex Mono",
                notes="Titular mazazo y cuerpo con tono de sistema o terminal.",
            ),
            _font_pairing(
                "brutal-readable",
                "Brutal legible",
                "Archivo Black",
                "Space Grotesk",
                notes="Mantiene energia brutalista con lectura menos seca.",
            ),
        ),
        "suggested_density": "Media, con cajas duras, jerarquia violenta y dominancia de titulares.",
        "suggested_tone": "Directo, ironico y deliberadamente no pulido.",
        "suggested_component": "Hero de cajas desplazadas, tags torcidas y CTA con sombra brutal.",
    },
    {
        "id": "ai-hyperminimalism",
        "name": "AI Hyperminimalismo",
        "summary": "Luz, gradientes suaves, mucho aire y tecnologia elegante sin ruido.",
        "description": "Direccion limpia y muy contenida. La sofisticacion sale de la composicion, la tipografia y el microdetalle, no del ornamento.",
        "when_to_use": "Muy adecuada para productos de IA, tooling premium o marcas que quieren claridad y altura sin caer en vacio corporativo.",
        "anti_patterns": [
            "No es la mejor opcion si la marca necesita excentricidad o identidad muy rugosa.",
            "No conviene si el producto pide caos expresivo o una energia muy comercial.",
        ],
        "context_signals": [
            "Producto con posicionamiento tecnico-premium.",
            "Necesidad de mucha claridad, orden y sofisticacion contenida.",
        ],
        "references": [
            _reference("OpenAI", "https://openai.com"),
            _reference("ElevenLabs", "https://elevenlabs.io"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#f7f9fc", "#ecf1f8", "#101828", "#667085", "#7c8cff", "#86d2ff"),
            "pastel": _palette("#fafbff", "#eff2fb", "#111827", "#6b7280", "#b3bcff", "#b6e6ff"),
            "solid": _palette("#f5f7fb", "#e8eef8", "#0f172a", "#5b667d", "#6475ff", "#54b8ff"),
            "monochrome": _palette("#f8fafc", "#e2e8f0", "#0f172a", "#64748b", "#334155", "#94a3b8"),
        },
        "font_pairings": (
            _font_pairing(
                "hyperminimal-core",
                "Hyperminimal Core",
                "Manrope",
                "Inter",
                notes="Muy limpio, actual y alineado con tooling premium.",
            ),
            _font_pairing(
                "hyperminimal-soft",
                "Soft Precision",
                "Sora",
                "Public Sans",
                notes="Un punto mas editorial sin perder limpieza.",
            ),
        ),
        "suggested_density": "Aireada, con mucho espacio negativo y jerarquia de bajo ruido.",
        "suggested_tone": "Preciso, elegante y seguro.",
        "suggested_component": "Hero limpio con gradiente, chips suaves y CTA principal muy nítido.",
    },
    {
        "id": "narrative-scroll-gamification",
        "name": "Scroll narrativo & Gamificacion",
        "summary": "La landing se recorre como una historia: progreso, etapas y ritmo secuencial.",
        "description": "Direccion para paginas que convierten mejor cuando se entienden como recorrido guiado y no como mosaico estatico.",
        "when_to_use": "Conveniente cuando el producto necesita educar, crear progresion mental o traducir complejidad en una secuencia clara.",
        "anti_patterns": [
            "No es ideal si la visita debe resolverlo todo en un vistazo muy corto.",
            "No conviene si la marca necesita una sola impresion hero sin narrativa posterior.",
        ],
        "context_signals": [
            "Producto con onboarding, fases o historia clara.",
            "Necesidad de convertir scroll en explicacion progresiva.",
        ],
        "references": [
            _reference("Stripe", "https://www.stripe.com"),
            _reference("Duolingo", "https://www.duolingo.com"),
        ],
        "palette_modes": ["recommended", "pastel", "solid", "monochrome"],
        "recommended_palette_mode": "recommended",
        "palettes": {
            "recommended": _palette("#f5f7fb", "#dbe7ff", "#111827", "#667085", "#2f6fed", "#16b364"),
            "pastel": _palette("#f8f9ff", "#e5eefc", "#162032", "#6a768e", "#9ab8ff", "#9ee2bb"),
            "solid": _palette("#f2f6ff", "#d5e0ff", "#0f172a", "#55637a", "#1d4ed8", "#12b76a"),
            "monochrome": _palette("#f8fafc", "#e2e8f0", "#0f172a", "#64748b", "#334155", "#94a3b8"),
        },
        "font_pairings": (
            _font_pairing(
                "narrative-flow",
                "Narrative Flow",
                "Syne",
                "Space Grotesk",
                notes="Marca el ritmo del scroll sin perder tono de producto serio.",
            ),
            _font_pairing(
                "narrative-product",
                "Product Journey",
                "Sora",
                "Manrope",
                notes="Mas producto moderno y menos gesto editorial.",
            ),
        ),
        "suggested_density": "Media, con secciones secuenciales, rails de progreso y momentos bien pautados.",
        "suggested_tone": "Guiado, claro y con sensacion de avance.",
        "suggested_component": "Hero de entrada con rail de pasos, beneficios por etapas y CTA final de progreso.",
    },
)


STYLE_CATALOG_BY_ID: Dict[str, Dict[str, Any]] = {
    entry["id"]: entry for entry in STYLE_CATALOG
}

PALETTE_MODE_BY_ID: Dict[str, Dict[str, str]] = {
    entry["id"]: entry for entry in PALETTE_MODE_CATALOG
}


def get_style_catalog() -> List[Dict[str, Any]]:
    """Devuelve el catalogo completo de familias visuales."""
    return [deepcopy(entry) for entry in STYLE_CATALOG]


def get_style_trend(style_id: str) -> Dict[str, Any]:
    """Devuelve una familia visual canonica por id."""
    normalized_id = str(style_id or "").strip()
    if normalized_id not in STYLE_CATALOG_BY_ID:
        raise KeyError(f"Estilo de Selina desconocido: {normalized_id}")
    return deepcopy(STYLE_CATALOG_BY_ID[normalized_id])


def get_palette_modes() -> List[Dict[str, str]]:
    """Lista canonica de modos de paleta."""
    return [deepcopy(entry) for entry in PALETTE_MODE_CATALOG]


def resolve_palette(style_id: str, palette_mode: Optional[str] = None) -> Tuple[Dict[str, str], str]:
    """Resuelve la paleta real a usar para una familia visual."""
    style = get_style_trend(style_id)
    requested_mode = str(palette_mode or style["recommended_palette_mode"]).strip() or "recommended"
    palette_map = style["palettes"]

    if requested_mode in palette_map:
        return deepcopy(palette_map[requested_mode]), requested_mode

    fallback_mode = style["recommended_palette_mode"]
    return deepcopy(palette_map[fallback_mode]), fallback_mode


def resolve_font_pairing(
    style_id: str,
    *,
    pairing_id: Optional[str] = None,
    custom_google_fonts_url: Optional[str] = None,
    custom_headings: Optional[str] = None,
    custom_body: Optional[str] = None,
) -> Dict[str, str]:
    """Devuelve el pairing tipografico activo para una familia visual."""
    if custom_google_fonts_url:
        headings = str(custom_headings or custom_body or "Custom Headings").strip()
        body = str(custom_body or custom_headings or "Custom Body").strip()
        return {
            "id": "custom-google-fonts",
            "label": "Custom Google Fonts",
            "headings": headings,
            "body": body,
            "notes": "URL proporcionada por el usuario para imponer la familia tipografica.",
            "headings_specimen_url": custom_google_fonts_url,
            "body_specimen_url": custom_google_fonts_url,
            "css_url": custom_google_fonts_url,
            "source": "custom-google-fonts",
            "custom_url": custom_google_fonts_url,
        }

    style = get_style_trend(style_id)
    pairings = list(style["font_pairings"])
    if pairing_id:
        for pairing in pairings:
            if pairing["id"] == pairing_id:
                return deepcopy(pairing)
    return deepcopy(pairings[0])


def _palette_to_roles(palette: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {"role": "surface", "value": palette["surface"]},
        {"role": "surface_alt", "value": palette["surface_alt"]},
        {"role": "accent", "value": palette["accent"]},
        {"role": "accent_alt", "value": palette["accent_alt"]},
        {"role": "ink", "value": palette["ink"]},
        {"role": "muted", "value": palette["muted"]},
    ]


def _palette_to_tokens(palette: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {"name": "color.bg.surface", "value": palette["surface"]},
        {"name": "color.bg.surface_alt", "value": palette["surface_alt"]},
        {"name": "color.text.primary", "value": palette["ink"]},
        {"name": "color.text.muted", "value": palette["muted"]},
        {"name": "color.brand.primary", "value": palette["accent"]},
        {"name": "color.brand.secondary", "value": palette["accent_alt"]},
    ]


def build_style_catalog_proposal(
    style_id: str,
    *,
    choice: str,
    palette_mode: Optional[str] = None,
    font_pairing_id: Optional[str] = None,
    custom_google_fonts_url: Optional[str] = None,
    custom_headings: Optional[str] = None,
    custom_body: Optional[str] = None,
) -> Dict[str, Any]:
    """Construye una propuesta de Selina a partir del catalogo."""
    style = get_style_trend(style_id)
    palette, resolved_palette_mode = resolve_palette(style_id, palette_mode)
    font_pairing = resolve_font_pairing(
        style_id,
        pairing_id=font_pairing_id,
        custom_google_fonts_url=custom_google_fonts_url,
        custom_headings=custom_headings,
        custom_body=custom_body,
    )

    return {
        "choice": str(choice).strip(),
        "name": style["name"],
        "concept": style["description"],
        "style_family": style["id"],
        "style_family_label": style["name"],
        "palette_mode": resolved_palette_mode,
        "palette": _palette_to_roles(palette),
        "typography": {
            "headings": font_pairing["headings"],
            "body": font_pairing["body"],
            "scale": "14 / 18 / 24 / 40 / 72",
            "notes": font_pairing["notes"],
            "headings_url": font_pairing["headings_specimen_url"],
            "body_url": font_pairing["body_specimen_url"],
            "css_url": font_pairing["css_url"],
            "source": font_pairing["source"],
            "custom_url": font_pairing.get("custom_url", ""),
        },
        "spacing_density": style["suggested_density"],
        "tone": style["suggested_tone"],
        "sample_component": style["suggested_component"],
        "rationale": style["when_to_use"],
        "not_this_direction": list(style["anti_patterns"]),
        "context_signals": list(style["context_signals"]),
        "reference_urls": [deepcopy(item) for item in style["references"]],
        "tokens": _palette_to_tokens(palette),
    }
