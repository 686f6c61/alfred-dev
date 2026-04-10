# Guía del servidor visual de Selina

Servidor local en navegador para mostrar sistemas de diseño y opciones visuales
durante la fase de dirección de estilo. Funciona como un visual companion para
enseñar el catálogo base de Selina y cerrar una ronda final de tres columnas.

## Cuándo usar el servidor visual

Siempre que Selina genere opciones de estilo. El servidor es la herramienta principal
de Selina: sirve tanto para enseñar la galería de 10 sistemas de diseño base como
para la ronda final de 3 propuestas comparables.

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
3. Para la ronda final, genera `screen_dir/style-options.html` con `python3 visual/scripts/write-style-options.py --visual-path "$STATE_DIR"`. Si necesitas escribirlo a mano, usa la clase `.style-grid`.
4. Escribe también `screen_dir/style-options.json` con las tres propuestas en JSON para poder generar luego el artefacto final sin reinterpretar la pantalla.
5. Informa al usuario: recuerda la URL, resume qué se muestra, pide que elija una opción.
6. En el siguiente turno: lee la elección con `python3 visual/scripts/read-choice.py "$STATE_DIR"` o, si lo prefieres, inspecciona `STATE_DIR/events` directamente.
7. Genera `docs/style-direction.md` con `python3 visual/scripts/write-style-direction.py --project-dir "$PWD" --visual-path "$STATE_DIR"` o, si necesitas control manual, escribe el artefacto tú misma usando el sidecar JSON.
8. Escribe `waiting.html` en `screen_dir` para limpiar el navegador hasta la próxima acción.

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
- `rationale` o `why`
- `not_this_direction` o `anti_patterns`
- `context_signals`, `audience` o `constraints`

El writer canónico tolera sidecars incompletos y alias razonables, pero cuanto más
específica sea la propuesta, menos genérica será la dirección final.

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
