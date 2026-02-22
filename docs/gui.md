# Dashboard GUI de Alfred Dev

El dashboard es una aplicacion web local que ofrece una vista externa y persistente del estado del
proyecto. Su razón de existir es doble: por un lado, proporciona al desarrollador una interfaz
visual en tiempo real con la actividad de la sesion; por otro, actua como fuente de verdad
independiente de la memoria de Claude Code. Cuando Claude compacta el contexto y pierde informacion,
el dashboard —y la base de datos SQLite que lo sustenta— siguen intactos.

A diferencia de los mensajes que aparecen en el terminal, el dashboard sobrevive a la compactacion,
a los reinicios de sesion y a cualquier interrupcion del CLI. Es la capa de observabilidad del
sistema Alfred Dev.

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

Flujo de datos:

```
Claude Code --[hooks]--> SQLite <--[read/write]--> gui/server.py --[WebSocket]--> Navegador
```

Los hooks escriben en SQLite de forma asíncrona; el servidor lee y propaga los cambios al navegador.
El navegador puede enviar acciones al servidor (marcar elementos, activar agentes) que el servidor
materializa en SQLite, cerrando el ciclo.

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

## Vistas disponibles

El dashboard tiene 7 vistas accesibles desde la barra lateral:

| Vista | Descripcion |
|-------|-------------|
| **Dashboard** | Resumen del estado actual: iteracion activa, fase, agentes, metricas y elementos marcados recientes. |
| **Timeline** | Cronologia de eventos de la iteracion activa, en orden cronologico inverso. |
| **Decisiones** | Tabla ordenable de decisiones tecnicas y arquitectonicas con busqueda textual. |
| **Agentes** | Tarjetas por agente con su estado (activo/inactivo) y un toggle para activar o desactivar. |
| **Memoria** | Explorador de la base de datos SQLite con busqueda sobre decisiones y eventos. |
| **Commits** | Historial de commits vinculados al proyecto y a las decisiones correspondientes. |
| **Marcados** | Elementos marcados manualmente o por el sistema, agrupados por tipo. |

Cuando no hay ninguna iteracion activa, las vistas de Timeline y Decisiones muestran los datos de
la iteracion mas reciente para que el historial siga siendo consultable.

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

## Solucion de problemas

| Escenario | Comportamiento |
|-----------|----------------|
| Puerto 7533 ocupado | El servidor busca automaticamente puertos alternativos (7534, 7535...). Los puertos reales se imprimen en stderr al arrancar. |
| Servidor caido durante la sesion | Los hooks siguen escribiendo en SQLite. El navegador muestra el indicador de reconexion (punto naranja parpadeante) y reintenta la conexion WebSocket. Cuando el servidor vuelve, el navegador recibe el estado completo. |
| Sin iteracion activa | Las vistas muestran el historial de la ultima iteracion cerrada. El dashboard indica que no hay sesion activa en curso. |
| Multiples pestanas abiertas | Todas las pestanas reciben los mismos mensajes WebSocket simultaneamente. El estado es identico en todas porque se lee de la misma fuente SQLite. |
| Instancia anterior no terminada | `session-start.sh` lee el PID guardado, envia SIGTERM y arranca una instancia nueva. Si el proceso ya no existe, ignora el error y continua. |

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

3. Añadir el elemento de seccion HTML en el area de contenido principal:

```html
<section id="view-mi-vista" class="view">
  <div class="view-header">
    <div class="view-title">Mi vista</div>
    <div class="view-subtitle">Descripcion breve</div>
  </div>
</section>
```

4. Añadir la entrada al sidebar con un icono SVG y el atributo `data-view`:

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

---

## Arranque manual

Para arrancar el servidor fuera de una sesion de Claude Code:

```bash
python -m gui.server --db .claude/alfred-memory.db
python -m gui.server --db mi-proyecto.db --http-port 8080 --ws-port 8081
```

El dashboard queda disponible en `http://127.0.0.1:7533/dashboard.html`.
