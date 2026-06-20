# Runtime visual de Selina

`visual/` pertenece al plugin de la rama `main`. No es la web publica de
Alfred Dev; esa vive en la rama `Alfred-Astro`. Esta carpeta contiene el
companion visual local que usa Selina durante la fase `estilo_visual` del flujo
`/alfred-dev:feature`, solo cuando el proyecto tiene frontend.

El objetivo del runtime visual es sacar una decision de direccion visual del
terminal y llevarla a una pantalla local: Selina genera propuestas HTML, el
usuario elige una en el navegador, el servidor registra el clic y despues el
plugin escribe `docs/style-direction.md` como artefacto estable para architect y
senior-dev.

## Flujo operativo

1. Selina arranca `visual/scripts/start-server.sh --project-dir "$PWD"`.
2. El script crea una sesion privada en `.alfred-dev/visual/<pid>-<timestamp>/`
   con dos subdirectorios: `content/` y `state/`.
3. `visual/scripts/server.cjs` sirve el HTML mas reciente de `content/` en una
   URL local `http://127.0.0.1:<puerto>`.
4. Los generadores Python escriben pantallas en `content/` y sidecars JSON en
   `state/`.
5. El navegador registra la eleccion por WebSocket o, si falla, por `POST
   /events`.
6. `visual/scripts/read-choice.py` lee la ultima eleccion valida desde
   `state/events`.
7. `visual/scripts/write-style-direction.py` genera `docs/style-direction.md`.
8. `visual/scripts/stop-server.sh <session_dir>` detiene el servidor y limpia
   sesiones temporales bajo `/tmp`.

## Scripts

| Script | Funcion |
|---|---|
| `start-server.sh` | Arranca el servidor visual en foreground o background y devuelve JSON con `url`, `session_dir`, `screen_dir` y `state_dir`. |
| `stop-server.sh` | Detiene solo el proceso visual esperado, evitando matar PIDs ajenos cuando queda un PID file stale. |
| `server.cjs` | Servidor HTTP + WebSocket sin dependencias externas. Sirve pantallas, recarga al cambiar HTML y registra eventos. |
| `helper.js` | Cliente inyectado en la pagina: conecta WebSocket, captura clics y usa fallback HTTP. |
| `frame-template.html` | Marco HTML compartido para fragmentos generados por Selina. |
| `write-style-demo-gallery.py` | Genera una galeria de sistemas visuales base para alinear criterio. |
| `write-style-selector.py` | Genera la pantalla guiada de familia visual y la segunda pantalla de tipografia + paleta. |
| `write-guided-style-options.py` | Genera tres variantes finales desde la seleccion guiada. |
| `write-style-options.py` | Genera una pantalla de tres propuestas desde un sidecar manual. |
| `read-choice.py` | Lee la ultima eleccion valida, incluyendo elecciones guiadas. |
| `write-style-direction.py` | Escribe el artefacto final `docs/style-direction.md`. |

## Contrato de eventos

El servidor persiste un evento por linea en `state/events`. La forma canonica es:

```json
{
  "source": "user-event",
  "type": "click",
  "choice": "A",
  "label": "Editorial calido",
  "element": ".style-option",
  "ts": "2026-06-20T15:00:00.000Z",
  "timestamp": "2026-06-20T15:00:00.000Z"
}
```

`choice` debe ser una cadena no vacia. `label` y `element` se normalizan con
limites de tamano para evitar que una pagina local escriba eventos enormes o
mal formados.

## Seguridad y limites

El servidor se disena para uso local y efimero, no como servicio publico:

- escucha por defecto en `127.0.0.1`;
- crea sesiones con permisos privados mediante `umask 077`;
- limita `POST /events` a 64 KiB;
- valida `Sec-WebSocket-Version`, `Sec-WebSocket-Key`, `Upgrade` y `Connection`;
- acepta WebSocket solo desde origins loopback esperados;
- sirve ficheros de `content/` con `realpath` para bloquear path traversal y
  symlinks fuera de la sesion;
- aplica `Cache-Control: no-store`, `X-Content-Type-Options: nosniff` y
  `X-Frame-Options: DENY`;
- apaga el servidor por inactividad tras 30 minutos;
- detiene el proceso si el proceso propietario desaparece.

## Pruebas

Los contratos principales viven en:

- `tests/test_visual_server.py`: ciclo de vida HTTP/WS, eventos, reload,
  path traversal y hardening.
- `tests/test_visual_scripts.py`: wrappers shell, PID files, permisos y cierre
  seguro.
- `tests/test_visual_helper.py`: cliente inyectado, cola WebSocket y fallback
  HTTP.
- `tests/test_selina_style_*.py`: generadores de galeria, selector, opciones,
  variantes y artefacto `docs/style-direction.md`.

Antes de publicar una release, `scripts/release_audit.py` tambien comprueba que
`npm pack --dry-run --json` incluye `visual/scripts/`; si esos scripts no viajan
en el paquete, Selina queda rota aunque funcione desde el worktree.
