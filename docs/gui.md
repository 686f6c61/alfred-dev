# Dashboard GUI de Alfred Dev

> **Fase Alpha** -- Esta funcionalidad se encuentra en fase de desarrollo activo. La interfaz, el
> protocolo y las vistas pueden cambiar entre versiones menores sin garantia de compatibilidad hacia
> atras. El servidor y el frontend son completamente funcionales, pero se esperan mejoras y ajustes
> antes de considerarlos estables.

El dashboard es una aplicacion web local que ofrece una vista externa y persistente del estado del
proyecto. Su razon de existir es doble: por un lado, proporciona al desarrollador una interfaz
visual en tiempo real con la actividad de la sesion; por otro, actua como fuente de verdad
independiente de la memoria de Claude Code. Cuando Claude compacta el contexto y pierde informacion,
el dashboard --y la base de datos SQLite que lo sustenta-- siguen intactos.

A diferencia de los mensajes que aparecen en el terminal, el dashboard sobrevive a la compactacion,
a los reinicios de sesion y a cualquier interrupcion del CLI. Es la capa de observabilidad del
sistema Alfred Dev.

![Vista general del dashboard -- estado del proyecto](../site/screenshots/dashboard-estado.png)

---

## Arquitectura

El servidor es un unico proceso Python sin dependencias externas que asume tres responsabilidades:

| Capa | Puerto | Implementacion |
|------|--------|----------------|
| HTTP estatico | 7533 | `http.server.SimpleHTTPRequestHandler` (stdlib) |
| WebSocket RFC 6455 | 7534 | `gui.websocket` (implementacion propia) |
| SQLite watcher | -- | Polling cada 500 ms sobre `alfred-memory.db` |

El watcher sondea la base de datos comparando checkpoints (ultimo ID de evento, decision y commit).
Cuando detecta cambios, emite un mensaje `update` a todos los clientes conectados. Al conectarse,
cada cliente recibe un mensaje `init` con el estado completo para renderizar el dashboard sin
esperar al siguiente ciclo.

### Flujo de datos

```
Hooks de Claude Code           Servidor GUI              Navegador
       |                            |                        |
       |--- write SQLite ---------->|                        |
       |                            |--- poll cada 500ms --->|
       |                            |                        |
       |                            |<-- cambios detectados  |
       |                            |                        |
       |                            |--- WebSocket update -->|
       |                            |                        |
       |                            |<-- WebSocket action ---|
       |                            |--- write SQLite ------>|
       |                            |--- action_ack -------->|
```

Los hooks escriben en SQLite de forma asincrona; el servidor lee y propaga los cambios al navegador.
El navegador puede enviar acciones al servidor (marcar elementos, activar agentes) que el servidor
materializa en SQLite, cerrando el ciclo.

### Ficheros del modulo

| Fichero | Lineas | Responsabilidad |
|---------|--------|-----------------|
| `gui/server.py` | ~480 | Servidor HTTP, WebSocket, watcher SQLite, procesamiento de acciones |
| `gui/websocket.py` | ~175 | Implementacion RFC 6455: handshake, encode/decode de frames, opcodes |
| `gui/dashboard.html` | ~1600 | Frontend completo: HTML, CSS (dark mode) y JavaScript vanilla |

La decision de implementar WebSocket a mano (en lugar de usar `websockets` o `aiohttp`) responde
al principio de cero dependencias externas. El modulo `gui.websocket` cubre el subconjunto necesario
del RFC 6455: handshake HTTP Upgrade, frames de texto, ping/pong y close. No implementa
fragmentacion ni extensiones (innecesarias para JSON corto en localhost).

---

## Como funciona

### Arranque

El hook `session-start.sh` lanza el servidor como proceso en segundo plano al inicio de cada sesion:

```bash
PYTHONPATH="${PLUGIN_ROOT}" python3 "$GUI_SERVER" --db "$MEMORY_DB" &
```

El PID se guarda en `.claude/alfred-gui.pid`. Si hay una instancia anterior, se termina antes de
arrancar la nueva para evitar conflictos de puerto.

Si el servidor no puede arrancar (por ejemplo, Python no disponible o puerto ocupado), la sesion
continua con normalidad. Este es el comportamiento **fail-open**: la GUI es un complemento, no un
requisito. Los hooks siguen escribiendo en SQLite con independencia del estado del servidor.

### Parada

El hook `stop-hook.py` lee el fichero PID y envia `SIGTERM` al proceso del servidor al terminar la
sesion. El fichero PID se elimina a continuacion.

### Puertos alternativos

Si el puerto 7533 esta ocupado, `find_available_port()` busca el siguiente disponible hasta un
maximo de 50 intentos. El puerto WebSocket se busca a partir del puerto HTTP encontrado + 1. Los
puertos reales se imprimen en stderr al arrancar el servidor.

---

## Protocolo WebSocket

La comunicacion entre el navegador y el servidor usa un protocolo JSON sobre WebSocket con cuatro
tipos de mensaje. Todos los mensajes siguen la misma estructura: un objeto con las claves `type`
(cadena que identifica el tipo) y `payload` (contenido especifico del mensaje).

### Conexion y handshake

El cliente se conecta al puerto WebSocket (por defecto 7534) con una peticion HTTP Upgrade estandar.
El servidor responde con `101 Switching Protocols` usando la clave `Sec-WebSocket-Accept` calculada
segun el RFC 6455 (SHA-1 del nonce + GUID magico, codificado en base64).

### Mensaje `init` (servidor -> cliente)

Se envia inmediatamente tras completar el handshake. Contiene el estado completo del proyecto para
que el cliente pueda renderizar todas las vistas sin esperar al siguiente ciclo de sondeo.

```json
{
  "type": "init",
  "payload": {
    "iteration": {
      "id": 1,
      "command": "feature",
      "description": "Implementar sistema de autenticacion OAuth2",
      "current_phase": "desarrollo",
      "started_at": "2026-02-22T10:00:00.000Z",
      "status": "active"
    },
    "decisions": [
      {
        "id": 1,
        "title": "Usar JWT con refresh tokens",
        "rationale": "...",
        "phase": "arquitectura",
        "status": "active",
        "tags": "seguridad,auth",
        "created_at": "2026-02-22T10:15:00.000Z"
      }
    ],
    "events": [
      {
        "id": 1,
        "event_type": "phase_start",
        "payload": "{\"phase\": \"desarrollo\"}",
        "created_at": "2026-02-22T10:30:00.000Z"
      }
    ],
    "commits": [
      {
        "id": 1,
        "sha": "a1b2c3d",
        "message": "feat: anadir middleware de autenticacion",
        "author": "usuario",
        "files_changed": "src/auth/middleware.py,tests/test_auth.py",
        "created_at": "2026-02-22T11:00:00.000Z"
      }
    ],
    "pinned": [
      {
        "id": 1,
        "item_type": "decision",
        "item_id": 1,
        "note": "Critica para la fase de seguridad",
        "pinned_by": "user",
        "created_at": "2026-02-22T10:20:00.000Z"
      }
    ]
  }
}
```

Los campos de `payload` pueden ser listas vacias si no hay datos. `iteration` es `null` cuando no
hay ninguna iteracion activa.

### Mensaje `update` (servidor -> cliente)

Se emite cada vez que el watcher detecta cambios en SQLite (ciclo de 500 ms). Solo incluye los
elementos nuevos desde el ultimo checkpoint, no el estado completo.

```json
{
  "type": "update",
  "payload": {
    "events": [],
    "decisions": [
      {
        "id": 2,
        "title": "Patron repositorio para acceso a datos",
        "rationale": "...",
        "phase": "arquitectura"
      }
    ],
    "commits": []
  }
}
```

El cliente fusiona los datos incrementales con su estado local. Las listas vacias indican que no hay
novedades en esa tabla.

### Mensaje `action` (cliente -> servidor)

El navegador envia acciones para modificar el estado de SQLite. Todas siguen la misma estructura
envolvente; el campo `payload.type` determina que accion ejecutar.

```json
{
  "type": "action",
  "payload": {
    "type": "pin_item",
    "item_type": "decision",
    "item_id": 1,
    "note": "Decisión clave para el sprint"
  }
}
```

Acciones soportadas:

| `payload.type` | Campos adicionales | Efecto |
|----------------|-------------------|--------|
| `pin_item` | `item_type`, `item_id`, `item_ref`, `note` | Marca un elemento como importante en la tabla `pinned_items` |
| `unpin_item` | `pin_id` | Elimina un marcado existente |
| `activate_agent` | `agent` (ID del agente) | Registra la activacion en `gui_actions` para que los hooks la procesen |
| `deactivate_agent` | `agent` (ID del agente) | Registra la desactivacion en `gui_actions` |
| `approve_gate` | Datos de la gate | Registra la aprobacion en `gui_actions` |

Las acciones desconocidas se registran igualmente en `gui_actions` para trazabilidad.

### Mensaje `action_ack` (servidor -> cliente)

Confirmacion de que una accion se ha procesado correctamente.

```json
{
  "type": "action_ack",
  "payload": {
    "status": "ok"
  }
}
```

### Reconexion automatica

El cliente implementa reconexion con backoff exponencial. Cuando la conexion WebSocket se pierde:

1. Primer intento inmediato tras 1 segundo.
2. Si falla, duplica el intervalo: 2s, 4s, 8s, 16s.
3. Tope maximo en 30 segundos entre intentos.
4. Al reconectar, el servidor envia `init` con el estado completo actualizado.

Durante la desconexion, el indicador de estado en la cabecera del dashboard cambia a naranja
parpadeante. Al reconectar vuelve a verde fijo.

---

## Vistas disponibles

El dashboard tiene 7 vistas accesibles desde la barra lateral izquierda. Cada vista se renderiza
a partir del objeto `state` global que el cliente mantiene en memoria, actualizandolo con cada
mensaje `init` o `update` recibido por WebSocket.

### Estado (Dashboard)

![Vista de estado del proyecto](../site/screenshots/dashboard-estado.png)

La vista principal muestra un resumen ejecutivo de la iteracion activa. Incluye:

- **Cabecera:** nombre del proyecto, tipo de iteracion (feature, fix, spike...) con su ID, y fase
  activa actual.
- **Tarjetas de metricas:** contadores de decisiones, eventos, commits y elementos marcados.
- **Progreso de gates:** barra visual con las fases completadas y la fase activa.
- **Agente activo:** indica que agente esta trabajando en ese momento.
- **Marcados recientes:** lista de los ultimos elementos marcados como importantes.

### Timeline

![Timeline de eventos del proyecto](../site/screenshots/dashboard-timeline.png)

Cronologia completa de eventos de la iteracion activa en orden cronologico inverso (mas reciente
primero). Cada evento muestra su tipo, timestamp humanizado (hace X minutos/horas) y el payload
relevante.

Los eventos se agrupan visualmente por tipo con iconos y colores diferenciados:

- **phase_start / phase_end:** transiciones de fase (verde).
- **agent_start / agent_end:** activaciones de agentes (azul).
- **gate_result:** resultados de quality gates (amarillo/rojo segun veredicto).
- **decision:** registro de decisiones tecnicas (cyan).
- **commit:** commits capturados automaticamente (gris).

### Decisiones

![Tabla de decisiones tecnicas](../site/screenshots/dashboard-decisiones.png)

Tabla ordenable con todas las decisiones tecnicas y arquitectonicas registradas en la iteracion.
Cada fila muestra el titulo, la fase en la que se tomo, el estado (`active`, `superseded`,
`deprecated`), las etiquetas y la fecha.

La vista incluye un campo de busqueda textual que filtra en tiempo real sobre titulo y razonamiento.
Las decisiones marcadas como importantes aparecen resaltadas con un indicador visual.

### Agentes

![Cuadricula de los 15 agentes de Alfred Dev](../site/screenshots/dashboard-agentes.png)

Cuadricula con los 15 agentes del sistema (8 de nucleo + 7 opcionales). Cada tarjeta muestra:

- **Icono de 2 letras:** identificador visual del agente (AL, AR, PO, SD...).
- **Nombre y rol:** descripcion breve de la responsabilidad del agente.
- **Estado:** activo (verde), inactivo (gris) u opcional desactivado (tenue).
- **Toggle:** boton para activar o desactivar agentes opcionales desde el propio dashboard.

Los agentes de nucleo siempre aparecen activos y no se pueden desactivar. Los opcionales reflejan
la configuracion del fichero `.claude/alfred-dev.local.md` y se pueden modificar en tiempo real
desde esta vista.

### Memoria

![Explorador de memoria persistente](../site/screenshots/dashboard-memoria.png)

Explorador directo de la base de datos SQLite con pestanas por tabla: decisiones, eventos, commits
e iteraciones. Cada pestana muestra una tabla con todas las filas de la tabla correspondiente,
ordenadas por ID descendente.

La vista incluye busqueda textual sobre el contenido de las filas. Es util para depuracion y para
verificar que los hooks estan capturando eventos correctamente.

### Commits

![Historial de commits del proyecto](../site/screenshots/dashboard-commits.png)

Historial de commits registrados en la iteracion activa. Cada entrada muestra:

- **SHA abreviado:** los primeros 7 caracteres del hash del commit.
- **Mensaje:** descripcion del commit.
- **Autor:** nombre del autor del commit.
- **Ficheros afectados:** lista de ficheros modificados.
- **Timestamp:** fecha y hora del commit.

Los commits se capturan automaticamente por el hook `commit-capture.py` cada vez que detecta una
ejecucion de `git commit` en el terminal de Claude Code.

### Marcados

![Elementos marcados como importantes](../site/screenshots/dashboard-marcados.png)

Lista de todos los elementos marcados como importantes, agrupados por tipo (decision, evento,
commit, accion). Cada marcado muestra el tipo del elemento, su referencia, la nota asociada,
quien lo marco (usuario o sistema) y la fecha.

Los marcados automaticos --generados por transiciones de fase o decisiones de alto impacto-- se
distinguen con la etiqueta `(auto)`. Los marcados manuales muestran la nota que el usuario
introdujo al marcarlos.

---

## Marcado de elementos

El marcado es el mecanismo principal de memoria permanente del sistema. Un elemento marcado
(«pinned») es cualquier evento, decision, commit o accion que se considera suficientemente
importante como para sobrevivir a la compactacion del contexto.

### Marcado manual

Desde cualquier vista, el usuario puede marcar un elemento pulsando el boton de marcado que aparece
al pasar el cursor sobre una fila. El formulario solicita una nota opcional que documenta por que
ese elemento es relevante.

### Marcado automatico

El sistema marca automaticamente los elementos cuando se cumplen dos condiciones:

- Cambio de fase dentro de un flujo (gate superada).
- Registro de una decision de alto impacto (tipo `architecture` o `security`).

Los elementos marcados automaticamente se distinguen con la etiqueta `(auto)` en la vista Marcados.

### Por que importa el marcado

Los elementos marcados tienen una doble funcion. En primer lugar, aparecen resaltados en todas las
vistas para que el desarrollador identifique rapida y visualmente lo mas relevante. En segundo lugar,
el hook `memory-compact.py` los inyecta como contexto protegido cuando Claude Code compacta la
sesion, garantizando que las decisiones criticas y los hitos del proyecto no se pierdan.

---

## Recuperacion de sesion

Cuando Claude Code compacta el historial de la conversacion, ejecuta el hook `memory-compact.py`
(evento `PreCompact`). Este hook:

1. Lee la iteracion activa de SQLite.
2. Obtiene las decisiones criticas (hasta 10 de la iteracion activa).
3. Obtiene todos los elementos marcados.
4. Obtiene las acciones pendientes del dashboard que aun no han sido procesadas.
5. Construye un bloque de texto estructurado y lo devuelve como `additionalContext`.

Claude Code inyecta ese bloque en el contexto compactado, de modo que cuando la sesion se reanuda,
el modelo dispone de las decisiones y el estado relevante del proyecto sin necesidad de releer la
conversacion completa.

El formato del contexto inyectado es:

```
## Decisiones criticas de la sesion (protegidas contra compactacion)

- [2026-02-10] **Eleccion de ORM**: SQLAlchemy 2.x con migraciones Alembic
- [2026-02-15] **Estrategia de autenticacion**: JWT con refresh tokens en httpOnly cookies

## Elementos marcados por el usuario

- [decision] arch-001: Patron repositorio para acceso a datos (auto)
- [event] gate-fase3: Gate de desarrollo superada

## Acciones pendientes desde el dashboard

- activate_agent: {"agent": "performance-engineer"}
```

---

## Tablas SQLite del dashboard

El dashboard utiliza dos tablas adicionales que se crean durante la migracion del esquema v3
(ejecutada automaticamente por `core/memory.py`):

### `gui_actions`

Almacena acciones enviadas desde el navegador que deben ser procesadas por los hooks en el
siguiente ciclo. Funciona como cola de mensajes entre el dashboard y los hooks.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| `id` | INTEGER PK | Identificador autoincremental |
| `action_type` | TEXT | Tipo de accion (`activate_agent`, `deactivate_agent`, `approve_gate`) |
| `payload` | TEXT | JSON con los datos completos de la accion |
| `status` | TEXT | Estado de procesamiento (`pending`, `processed`, `failed`) |
| `created_at` | TEXT | Timestamp ISO 8601 |
| `processed_at` | TEXT | Timestamp de procesamiento (null si pendiente) |

### `pinned_items`

Almacena elementos marcados como importantes por el usuario o por el sistema.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| `id` | INTEGER PK | Identificador autoincremental |
| `item_type` | TEXT | Tipo del elemento (`decision`, `event`, `commit`, `action`) |
| `item_id` | INTEGER | ID del elemento en su tabla de origen |
| `item_ref` | TEXT | Referencia legible (`D#42`, `C#a1b2c3d`) |
| `note` | TEXT | Nota explicativa del usuario |
| `priority` | INTEGER | Prioridad (1 = alta, 2 = media, 3 = baja). Por defecto 2 |
| `pinned_by` | TEXT | Quien lo marco (`user`, `system`) |
| `created_at` | TEXT | Timestamp ISO 8601 |

---

## Solucion de problemas

| Escenario | Comportamiento |
|-----------|----------------|
| Puerto 7533 ocupado | El servidor busca automaticamente puertos alternativos (7534, 7535...). Los puertos reales se imprimen en stderr al arrancar. |
| Servidor caido durante la sesion | Los hooks siguen escribiendo en SQLite. El navegador muestra el indicador de reconexion (punto naranja parpadeante) y reintenta la conexion WebSocket con backoff exponencial. Cuando el servidor vuelve, el navegador recibe el estado completo via mensaje `init`. |
| Sin iteracion activa | Las vistas muestran el historial de la ultima iteracion cerrada. El dashboard indica que no hay sesion activa en curso. |
| Multiples pestanas abiertas | Todas las pestanas reciben los mismos mensajes WebSocket simultaneamente. El estado es identico en todas porque se lee de la misma fuente SQLite. |
| Instancia anterior no terminada | `session-start.sh` lee el PID guardado, envia SIGTERM y arranca una instancia nueva. Si el proceso ya no existe, ignora el error y continua. |
| Base de datos bloqueada | SQLite con modo WAL permite lecturas concurrentes. El servidor usa una conexion de solo lectura para el polling, separada de la conexion de escritura para acciones del dashboard. |
| El dashboard no muestra datos nuevos | Verificar que los hooks estan activos (`/alfred status`) y que la base de datos existe en `.claude/alfred-memory.db`. Usar la vista Memoria para inspeccionar directamente las tablas. |

---

## Desarrollo

### Anadir una vista nueva

Una vista nueva requiere cuatro cambios en `dashboard.html`:

1. Crear la funcion de renderizado que construya el HTML a partir del objeto `state` global y
   lo inserte en el elemento correspondiente.

2. Registrar el caso en la funcion `renderCurrentView()`:

```javascript
case 'mi-vista': renderMiVista(); break;
```

3. Anadir el elemento de seccion HTML en el area de contenido principal:

```html
<section id="view-mi-vista" class="view">
  <div class="view-header">
    <div class="view-title">Mi vista</div>
    <div class="view-subtitle">Descripcion breve</div>
  </div>
</section>
```

4. Anadir la entrada al sidebar con un icono SVG y el atributo `data-view`:

```html
<div class="nav-item" data-view="mi-vista">
  <!-- icono SVG 16x16 -->
  Mi vista
</div>
```

### Anadir una accion nueva

Las acciones son mensajes que el navegador envia al servidor para modificar el estado de SQLite.
El protocolo es siempre el mismo: el navegador envia `{ type: "action", payload: {...} }` y el
servidor responde con `action_ack`.

1. Registrar el handler en `server.py` dentro de `process_gui_action()`:

```python
elif action_type == "mi_accion":
    self._db.mi_metodo(action.get("parametro"))
```

2. Implementar el metodo correspondiente en `core/memory.py` para que interactue con SQLite.

3. Enviar el mensaje desde el navegador:

```javascript
ws.send(JSON.stringify({
  type: 'action',
  payload: { type: 'mi_accion', parametro: valor }
}));
```

El watcher detectara el cambio en SQLite en el siguiente ciclo de 500 ms y lo propagara a todos los
clientes conectados mediante un mensaje `update`.

### Anadir un campo al protocolo WebSocket

Si es necesario incluir mas datos en los mensajes `init` o `update`:

1. Anadir la consulta SQL en el metodo correspondiente de `server.py` (`get_full_state()` para
   `init`, o `poll_new_*()` para `update`).

2. Incluir el resultado en el diccionario `payload` del mensaje.

3. En el frontend, actualizar la funcion de procesamiento (`processInit()` o `processUpdate()`)
   para que almacene los nuevos datos en el objeto `state` global.

4. Actualizar las funciones de renderizado que deban mostrar los datos nuevos.

---

## Arranque manual

Para arrancar el servidor fuera de una sesion de Claude Code:

```bash
python -m gui.server --db .claude/alfred-memory.db
python -m gui.server --db mi-proyecto.db --http-port 8080 --ws-port 8081
```

El dashboard queda disponible en `http://127.0.0.1:7533/dashboard.html`.
