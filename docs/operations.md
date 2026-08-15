# Operación continua y artefactos de proyecto

Alfred Dev no solo ejecuta flujos. También mantiene un estado operativo persistente del proyecto para que la sesión actual, la siguiente sesión y otros comandos compartan contexto estable. Esa capa vive sobre dos zonas complementarias:

- `.claude/`, que guarda estado de sesión, memoria SQLite, handoff y configuración local;
- `docs/project/`, que guarda artefactos legibles para humanos y comandos operativos.

La idea es simple: los flujos multiagente producen trabajo; la capa de continuidad lo deja visible, resumible y retomable sin depender de recordar la conversación exacta.

---

## Las dos fuentes operativas

### `.claude/`

Aquí viven los artefactos de runtime y control:

- `.claude/alfred-dev-state.json`: estado activo del flujo;
- `.claude/alfred-handoff.json`: handoff estructurado para pausa y reanudación;
- `.claude/alfred-memory.db`: memoria persistente SQLite;
- `.claude/alfred-dev.local.md`: configuración local del proyecto.

Estos ficheros son la fuente de verdad para el runtime.

### `docs/project/`

Aquí viven las proyecciones Markdown que ayudan al usuario y a los comandos a orientarse sin abrir JSON ni SQLite:

- `discovery.md`: refinado previo o preguntas abiertas;
- `current.md`: estado operativo resumido;
- `codebase-map.md`: mapa brownfield del repo;
- `progress.md`: resumen de progreso y foco actual;
- `traceability.md`: trazabilidad entre trabajo, evidencia y estado;
- `uat.md`: validación manual / UAT;
- `handoff.md`: handoff legible;
- `github-sync.md`: estado y resultado del sync con GitHub;
- `kanban/backlog.md`, `kanban/in-progress.md`, `kanban/blocked.md`, `kanban/done.md`: tablero operativo.

---

## Comandos que alimentan esta capa

| Comando | Qué deja o consume |
|---|---|
| `alfred` | Decide si mapear, retomar, abrir un flujo o responder en corto |
| `map-codebase` | Siembra `docs/project/codebase-map.md` y contexto brownfield |
| `discuss` | Siembra o actualiza `docs/project/discovery.md` |
| `progress` | Resume `progress.md`, trazabilidad, kanban y UAT. Absorbe standup, blocked, in-progress y validate |
| `pause` | Genera `.claude/alfred-handoff.json` y `docs/project/handoff.md` |
| `retomar` | Reanuda una sesión pausada y resuelve el handoff |
| `uat` | Crea o actualiza la UAT del último entregable |
| `sync-github` | Refleja el tablero local en GitHub Issues |
| `memory-ui` | Expone memoria y artefactos operativos en una UI local |

`next` y `search` existen como helpers internos (`commands/next.md`, `commands/search.md`) y no se publican en `plugin.json`. El runtime de continuidad (`core/continuity.py`) sigue implementando resume/verify/standup para esos helpers y para `progress`.

---

## Tablero operativo

No hay agente `project-manager`. El kanban y la trazabilidad los escribe el runtime (`core/continuity.py`): snapshots, Markdown, validación de artefactos, siguiente paso y sync con GitHub.

Esa capa deja visible:

- qué está en backlog;
- qué está en curso;
- qué está bloqueado;
- qué está hecho;
- qué UAT queda pendiente;
- qué huecos de trazabilidad siguen abiertos.

---

## Handoff, pausa y reanudación

El handoff existe para que una sesión pueda detenerse sin perder el hilo técnico. Cuando el usuario ejecuta `pause`, Alfred:

1. lee el estado actual del flujo;
2. construye un resumen de fase, gates, artefactos y siguiente paso;
3. lo guarda en JSON para el runtime y en Markdown para lectura humana.

Cuando el usuario ejecuta `retomar`, el plugin:

1. carga el handoff pendiente;
2. recupera el comando y la fase;
3. marca el handoff como resuelto;
4. devuelve una instrucción de reanudación consistente.

Esto evita dos fallos frecuentes en entornos CLI:

- reabrir trabajo sin recordar la última fase real;
- inventar contexto que el sistema sí conocía, pero no había resumido bien.

---

## UAT y validación manual

Alfred separa expresamente la evidencia automática de la validación humana. Los tests pueden estar verdes y, aun así, faltar confirmación funcional. Por eso `uat` mantiene una pieza propia de estado:

- `pending`: falta revisar el entregable;
- `approved`: la validación humana está cerrada;
- `rejected`: el cambio vuelve a retrabajo o bloqueo.

La UAT afecta a la capa operativa y a los informes de sesión. Un flujo puede estar completado a nivel de runtime y seguir “pendiente de UAT” a nivel de operación real.

---

## Sync con GitHub

`sync-github` no convierte GitHub en la fuente de verdad. Hace lo contrario: proyecta el tablero local en GitHub Issues cuando el proyecto lo necesita.

El flujo esperado es:

1. el estado operativo se mantiene en `docs/project/` y `.claude/`;
2. `progress` comprueba consistencia local;
3. `sync-github` refleja esa realidad en GitHub usando `gh`;
4. `github-sync.md` deja rastro de la sincronización.

Esta decisión evita que el proyecto dependa por completo de una integración remota para conservar su contexto operativo.

---

## Relación con otros documentos

- [commands.md](commands.md) resume qué hace cada comando.
- [memory.md](memory.md) explica la memoria persistente.
- [repository.md](repository.md) ubica esta capa dentro del repo.
- [testing.md](testing.md) cubre los tests y contratos asociados.
