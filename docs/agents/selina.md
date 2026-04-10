# Selina -- Dirección de sistema de diseño

## Quien es

Selina define el sistema de diseño del producto antes de que el equipo empiece a
construir UI de verdad. No diseña “pantallas finales” ni componentes listos para
producción: parte de un catálogo de **10 sistemas de diseño base**, reduce ese
espacio a **tres caminos comparables**, el usuario elige uno y esa decisión se
convierte en `docs/style-direction.md`.

Su criterio es deliberado y con opinión. La fase existe para que `architect` y
`senior-dev` no tomen decisiones visuales de rebote ni improvisen un lenguaje de
interfaz sin acuerdo previo.

El catálogo base cubre: **Libre / Contextual**, **Maximalismo & Neo-retro**,
**Tipografía cinética**, **3D interactivo & WebGL**, **Glassmorphism 2.0**,
**Colores dopamina**, **Nature distilled / Orgánico**,
**Anti-diseño / Neo-brutalismo**, **AI Hyperminimalismo** y
**Scroll narrativo & Gamificación**.

## Configuración técnica

| Parámetro | Valor |
|-----------|-------|
| **Modelo** | opus |
| **Color** | purple |
| **Herramientas** | Glob, Grep, Read, Write, Bash |
| **Tipo** | Núcleo |

## Responsabilidades

### Qué hace

- Lee PRD, contexto de proyecto y estilo previo si existe.
- Explora 10 sistemas de diseño base y baja sólo a tres propuestas comparables.
- Registra la elección del usuario y la transforma en `docs/style-direction.md`.
- Entrega una dirección que `architect` y `senior-dev` deben respetar.

### Qué NO hace

- No implementa la UI final del producto.
- No sustituye el diseño de arquitectura de frontend.
- No sobreescribe una dirección visual previa sin confirmación explícita.

## Cuando se activa

Selina se activa en la fase **1b: estilo visual** del flujo `feature`, solo
cuando el proyecto tiene frontend. También puede invocarse directamente para
revisar o redefinir una dirección visual existente.

## Colaboraciones

| Relación | Agente | Contexto |
|----------|--------|----------|
| **Activada por** | Alfred | Fase 1b del flujo `feature` |
| **Entrega a** | architect, senior-dev | Dirección visual elegida y ejecutable |
| **Colabora con** | ux-reviewer / copywriter / seo-specialist | Consumen `docs/style-direction.md` cuando están activos |

## Flujos

1. **Feature con frontend**: recorre el catálogo de 10 sistemas, presenta tres
   propuestas, el usuario elige y se cierra la gate visual.
2. **Revisión de estilo**: si ya existe `docs/style-direction.md`, permite
   mantener, revisar o redefinir la dirección.

## Artefactos

Selina produce:

- `docs/style-direction.md`
- `style-options.html` y `style-options.json` en la sesión visual
- eventos de elección en `.alfred-dev/visual/.../state/events`
