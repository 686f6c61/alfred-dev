---
name: style-direction
description: "Abrir y operar el companion visual de Selina para elegir una direccion de estilo en proyectos con interfaz. Skill manual: levanta un servidor local y escribe artefactos visuales."
disable-model-invocation: true
---

# Guía del servidor visual de Selina

Servidor local en navegador para mostrar sistemas de diseño y opciones visuales
durante la fase de dirección de estilo. Funciona como un visual companion para
enseñar el catálogo base de Selina, dejar que el usuario fije familia +
tipografía + gama de color y cerrar después una ronda final de tres columnas.

## Cuándo usar el servidor visual

Siempre que Selina genere opciones de estilo. El servidor es la herramienta principal
de Selina: sirve tanto para enseñar la galería de 10 sistemas de diseño base como
para el nuevo flujo guiado de selección y la ronda final de 3 propuestas comparables.

## Arrancar sesión

```bash
visual/scripts/start-server.sh --project-dir /ruta/al/proyecto
```

Respuesta JSON esperada:

```json
{
  "type": "server-started",
  "port": 7432,
  "url": "http://localhost:7432",
  "screen_dir": "/ruta/al/proyecto/.alfred-dev/visual/<pid-timestamp>/content",
  "state_dir": "/ruta/al/proyecto/.alfred-dev/visual/<pid-timestamp>/state",
  "state": "ready"
}
```

Guarda `screen_dir` (directorio donde escribir los HTML de opciones) y `state_dir`
(directorio donde leer eventos de clic y verificar estado del servidor).

El fichero `state_dir/server-info` contiene el mismo JSON emitido en el arranque.
Léelo para comprobar que el servidor sigue activo antes de cada operación.

Indica al usuario que abra la URL en el navegador.

## El ciclo

1. Comprueba que el servidor sigue activo leyendo `STATE_DIR/server-info`.
2. Si aporta contexto, genera primero la galería del catálogo con `python3 visual/scripts/write-style-demo-gallery.py --visual-path "$STATE_DIR"`.
3. Flujo guiado recomendado:
   - `python3 visual/scripts/write-style-selector.py --visual-path "$STATE_DIR"` para elegir el sistema base.
   - lee la elección con `python3 visual/scripts/read-choice.py "$STATE_DIR"`.
   - `python3 visual/scripts/write-style-selector.py --visual-path "$STATE_DIR" --style-id "<style_id>"` para que el usuario elija tipografía + paleta.
   - vuelve a leer la elección con `python3 visual/scripts/read-choice.py "$STATE_DIR"`.
   - `python3 visual/scripts/write-guided-style-options.py --visual-path "$STATE_DIR"` para generar automáticamente la ronda final de 3 variantes a partir de esa selección.
4. Flujo directo alternativo: si ya tienes las tres propuestas decididas, genera `screen_dir/style-options.html` con `python3 visual/scripts/write-style-options.py --visual-path "$STATE_DIR"`. Si necesitas escribirlo a mano, usa la clase `.style-grid`.
5. El sidecar JSON final debe vivir en `screen_dir/style-options.json` para poder generar luego el artefacto final sin reinterpretar la pantalla.
6. Informa al usuario: recuerda la URL, resume qué se muestra, pide que elija una opción.
7. En el siguiente turno: lee la elección final con `python3 visual/scripts/read-choice.py "$STATE_DIR"` o, si lo prefieres, inspecciona `STATE_DIR/events` directamente.
8. Genera `docs/style-direction.md` con `python3 visual/scripts/write-style-direction.py --project-dir "$PWD" --visual-path "$STATE_DIR"` o, si necesitas control manual, escribe el artefacto tú misma usando el sidecar JSON.
9. Escribe `waiting.html` en `screen_dir` para limpiar el navegador hasta la próxima acción.

## Sidecar JSON recomendado

Para que el artefacto final salga con buen nivel, intenta que cada propuesta incluya al
menos:

- `choice`
- `name`
- `concept` o `description`
- `palette`
- `typography`
- `spacing_density` o `layout_density`
- `tone` o `mood`
- `sample_component` o `component_example`
- `visual_principles` o `design_principles`
- `layout_grammar` o `composition_grammar`
- `surface_treatment` o `materiality`
- `shape_language`
- `motion_language`
- `signature_elements` o `visual_motifs`
- `implementation_guardrails` o `guardrails`
- `prompt_seed` o `design_prompt`
- `rationale` o `why`
- `not_this_direction` o `anti_patterns`
- `context_signals`, `audience` o `constraints`

El writer canónico tolera sidecars incompletos y alias razonables, pero cuanto más
específica sea la propuesta, menos genérica será la dirección final.

### Regla crítica del flujo guiado

Si el usuario ya ha fijado **familia + tipografía + paleta**, las tres variantes finales
deben seguir perteneciendo a ese mismo sistema. Lo que puede cambiar entre `A / B / C`
es la composición, la jerarquía o el grado de expresividad, pero no la gramática base
del sistema elegido.

Cuando generes sidecars manuales:

- reutiliza la `prompt_seed` del sistema como semilla principal
- arrastra siempre `visual_principles`, `layout_grammar` y `signature_elements`
- usa `implementation_guardrails` para evitar que la variante se desvíe hacia otra familia
- no mezcles referencias de una tendencia distinta solo para “hacerla más bonita”

## Writer canónico de opciones

El helper recomendado es:

```bash
python3 visual/scripts/write-style-options.py --visual-path "$STATE_DIR"
```

Este script:

- autodetecta `style-options.json`
- normaliza aliases comunes del sidecar
- escribe un fragmento HTML compatible con el servidor real
- evita depender de assets externos que no existen en el repo

Si necesitas personalizar el copy de cabecera, acepta `--title` y `--subtitle`.

## Selector guiado de sistema + tipografía + paleta

Selina ya puede trabajar en tres pasos naturales:

1. **Sistema base** — `python3 visual/scripts/write-style-selector.py --visual-path "$STATE_DIR"`
2. **Tipografía + paleta** — `python3 visual/scripts/write-style-selector.py --visual-path "$STATE_DIR" --style-id "<style_id>"`
3. **Tres variantes finales** — `python3 visual/scripts/write-guided-style-options.py --visual-path "$STATE_DIR"`

`read-choice.py` sigue siendo el lector canónico entre pasos. Si la elección
pertenece al flujo guiado, devolverá además `parsed_choice` con `stage`,
`style_id`, `font_pairing_id` y `palette_mode`.

## Estructura HTML de las opciones

El servidor ya envuelve fragmentos HTML en su frame propio e inyecta `helper.js`, así
que no hace falta escribir un documento completo ni enlazar assets extra. Este es el
formato recomendado:

```html
<section class="style-screen">
  <div class="style-screen-header">
    <p class="style-screen-kicker">Selina propone</p>
    <h1>Selecciona una dirección visual</h1>
    <p class="style-screen-subtitle">Elige la propuesta que mejor encaja con el producto.</p>
  </div>
  <div class="style-grid">

    <div class="style-option" data-choice="A">
      <div class="style-preview" style="background:#1a1a2e;">
        <span class="style-letter">A</span>
      </div>
      <div class="style-meta">
        <h2>Oscuro espacial</h2>
        <p>Contraste alto, tipografía sans-serif, sensación tecnológica.</p>
        <div class="palette">
          <span class="swatch" style="background:#1a1a2e;" title="#1a1a2e"></span>
          <span class="swatch" style="background:#e94560;" title="#e94560"></span>
          <span class="swatch" style="background:#ffffff;" title="#ffffff"></span>
        </div>
      </div>
    </div>

    <div class="style-option" data-choice="B">
      <div class="style-preview" style="background:#f5f0e8;">
        <span class="style-letter">B</span>
      </div>
      <div class="style-meta">
        <h2>Editorial cálido</h2>
        <p>Tonos crema, serif clásico, aire de revista de lujo.</p>
        <div class="palette">
          <span class="swatch" style="background:#f5f0e8;" title="#f5f0e8"></span>
          <span class="swatch" style="background:#c8a96e;" title="#c8a96e"></span>
          <span class="swatch" style="background:#2c2c2c;" title="#2c2c2c"></span>
        </div>
      </div>
    </div>

    <div class="style-option" data-choice="C">
      <div class="style-preview" style="background:#0d7377;">
        <span class="style-letter">C</span>
      </div>
      <div class="style-meta">
        <h2>Minimalismo vibrante</h2>
        <p>Verde azulado saturado, mucho espacio negativo, tipografía condensada.</p>
        <div class="palette">
          <span class="swatch" style="background:#0d7377;" title="#0d7377"></span>
          <span class="swatch" style="background:#14ffec;" title="#14ffec"></span>
          <span class="swatch" style="background:#f8f8f8;" title="#f8f8f8"></span>
        </div>
      </div>
    </div>

  </div>
</section>
```

Cada `.style-option` debe incluir obligatoriamente `data-choice` con un identificador
único (letra, número o slug). El atributo es el que queda registrado en los eventos
al hacer clic.

## Formato de eventos

El archivo `STATE_DIR/events` contiene una línea JSON por evento, en orden cronológico.
La forma canónica actual es:

```jsonl
{"source":"user-event","type":"click","choice":"A","label":"Oscuro espacial","element":".style-option","ts":"2026-03-31T10:14:02Z","timestamp":"2026-03-31T10:14:02Z"}
{"source":"user-event","type":"click","choice":"A","label":"Oscuro espacial","element":".style-option","ts":"2026-03-31T10:14:05Z","timestamp":"2026-03-31T10:14:05Z"}
```

El lector canónico `visual/scripts/read-choice.py` también acepta el formato legacy anterior:

```jsonl
{"ts":"2026-03-31T10:14:02Z","type":"click","choice":"A","element":".style-option"}
{"ts":"2026-03-31T10:14:05Z","type":"click","choice":"A","element":".style-option"}
```

El último clic con `type: "click"` sobre un `.style-option` se considera la elección
definitiva del usuario. Si hay varios clics sobre la misma opción, se interpreta como
confirmación. Si hay clics sobre opciones distintas, prevalece el más reciente.

## Parar servidor

```bash
visual/scripts/stop-server.sh <session_dir>
```

`session_dir` es el directorio de sesión devuelto por `start-server.sh`, o bien el
padre común de `screen_dir` y `state_dir`. El script detiene el proceso y limpia los
archivos temporales de la sesión.
