# MCP y Memory UI

La memoria de Alfred Dev no se queda encerrada en SQLite. El plugin expone esa capa mediante un servidor MCP local y una interfaz web ligera que permiten consultar decisiones, commits, eventos y contexto operativo sin hablar directamente con la base de datos.

Las tres piezas forman un subsistema:

- `core/memory.py`: fuente de verdad de datos y reglas de persistencia;
- `mcp/memory_server.py`: adaptador MCP sobre stdio;
- `core/memory_ui_server.py`: servidor HTTP local para exploración visual.

---

## Servidor MCP

### Ubicación

- Código: `mcp/memory_server.py`
- Registro del servidor: `.claude-plugin/mcp.json`

### Función

El servidor MCP expone operaciones de memoria como herramientas accesibles desde Claude Code a través de stdio. No redefine la lógica de negocio: se apoya en `MemoryDB` y traduce entre el protocolo MCP y las funciones internas del plugin.

La separación es deliberada:

- `core/memory.py` decide cómo se persiste, se sanea y se consulta;
- `mcp/memory_server.py` decide cómo se publica esa capacidad al exterior.

### Qué aporta

- acceso estructurado a decisiones, commits y eventos;
- consultas sin abrir directamente SQLite;
- una frontera clara entre runtime interno y herramientas consumidoras.

---

## Memory UI local

### Entrada de usuario

El comando `/alfred-dev:memory-ui` prepara el contexto y delega en `python3 .claude/alfred-continuity.py memory-ui "$PWD"` para levantar la UI local.

### Implementación

La interfaz está servida por `core/memory_ui_server.py`. No es una SPA compleja ni depende de un framework frontend; es una UI ligera, orientada a consulta, que renderiza HTML/CSS/JS directamente desde el servidor.

### Qué muestra

La UI mezcla memoria persistente y contexto operativo:

- timeline de eventos;
- decisiones;
- commits;
- salud de memoria;
- resultados de búsqueda;
- contexto de `docs/project/`;
- señales del kanban operativo.

Esto es importante: no es solo un visor de base de datos. Es una proyección de memoria + estado operativo del proyecto.

---

## Búsqueda unificada

Una parte especialmente útil de la UI es la búsqueda. `core/memory_ui_server.py` delega en `core.continuity.search_project_context`, que cruza:

- resultados de SQLite;
- señales y documentos de `docs/project/`.

El resultado es una búsqueda contextual única, no dos búsquedas separadas pegadas sin criterio.

---

## Relación con la instalación

El instalador puede parchear `.claude-plugin/mcp.json` cuando `python3` no apunta a una versión compatible. Ese detalle es importante porque el subsistema MCP comparte la misma exigencia que hooks y core: Python 3.10+ real, no asumido.

Cuando el entorno no expone un `python3` válido por defecto, `install.sh` e `install.ps1` actualizan el runtime instalado para que el MCP use el intérprete correcto.

---

## Cobertura de tests

Aunque esta capa depende de protocolos de integración, no está “sin testear”. El repo ya incluye cobertura real en esta zona:

- `tests/test_memory_server.py`
- `tests/test_memory_ui.py`
- `tests/test_memory_ui_contract.py`
- `tests/test_visual_server.py`

Además, la mayor parte de la lógica de datos subyacente se verifica en `tests/test_memory.py` y `tests/test_memory_sync.py`.

---

## Cuándo tocar cada pieza

| Si quieres cambiar... | Empieza por... |
|---|---|
| Esquema o persistencia | `core/memory.py` |
| Sync de memoria a Markdown | `core/memory_sync.py` |
| Herramientas MCP expuestas | `mcp/memory_server.py` y `.claude-plugin/mcp.json` |
| UI local y endpoints HTTP | `core/memory_ui_server.py` |
| Comportamiento del comando | `commands/memory-ui.md` y `core/continuity.py` |

---

## Relación con otros documentos

- [memory.md](memory.md) cubre el modelo de memoria y SQLite.
- [operations.md](operations.md) explica cómo `docs/project/` y la capa operativa alimentan la UI.
- [installation.md](installation.md) documenta el parcheo de `mcp.json`.
