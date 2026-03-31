# Guía del servidor visual de Selina

Servidor local en navegador para mostrar opciones de estilo visual durante la fase
de dirección de estilo. Funciona como un visual companion con layout específico
a tres columnas.

## Cuándo usar el servidor visual

Siempre que Selina genere opciones de estilo. El servidor es la herramienta principal
de Selina — no es opcional dentro de su fase.

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
2. Escribe el HTML de opciones en `screen_dir/style-options.html` usando la clase `.style-grid`.
3. Informa al usuario: recuerda la URL, resume qué se muestra, pide que elija una opción.
4. En el siguiente turno: lee `STATE_DIR/events` (líneas JSON con los clics registrados).
5. Genera `docs/style-direction.md` con la opción elegida y sus detalles.
6. Escribe `waiting.html` en `screen_dir` para limpiar el navegador hasta la próxima acción.

## Estructura HTML de las opciones

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>Opciones de estilo</title>
  <link rel="stylesheet" href="/assets/style-viewer.css" />
</head>
<body>
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
  <script src="/assets/style-viewer.js"></script>
</body>
</html>
```

Cada `.style-option` debe incluir obligatoriamente `data-choice` con un identificador
único (letra, número o slug). El atributo es el que queda registrado en los eventos
al hacer clic.

## Formato de eventos

El archivo `STATE_DIR/events` contiene una línea JSON por evento, en orden cronológico:

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
