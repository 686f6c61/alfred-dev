# Mapa del repositorio

Esta página explica dónde vive cada subsistema del plugin y qué documento usar para entenderlo. La idea es reducir el tiempo de orientación: abrir el directorio correcto primero y no perderse entre prompts, core Python, hooks, memoria, scripts visuales y tests.

La rama `main` documentada aquí corresponde al plugin. La landing pública vive en la rama `Alfred-Astro` y queda fuera de este mapa salvo cuando una release exige alinear contenido entre ambas.

---

## Vista de alto nivel

| Ruta | Qué contiene | Estado documental |
|---|---|---|
| `agents/` | Prompts de los 19 agentes publicados | Bien cubierto en `docs/agents/` |
| `commands/` | Slash commands del plugin | Cubierto ahora en [commands.md](commands.md) |
| `core/` | Runtime Python: orquestación, memoria, configuración, Selina | Cubierto por temas; faltan páginas por subsistema |
| `hooks/` | Hooks del ciclo de vida y guards | Cubierto en `hooks.md` |
| `mcp/` | Servidor MCP de memoria | Cobertura insuficiente |
| `skills/` | Catálogo de 62 skills por dominio | Cubierto en `skills.md` |
| `tests/` | Suite de tests y contratos | Cubierto en `testing.md`, con margen de mejora |
| `visual/` | Scripts visuales de Selina y servidor local | Cubierto en [visual.md](visual.md) |
| `templates/` | Plantillas de artefactos y salidas | Sin página propia |
| `.github/workflows/` | Automatización CI/release | Sin página propia |

---

## Directorios clave

### `agents/`

Aquí viven los prompts fuente que Claude Code descubre desde el directorio `agents/`. Desde 0.6.0 todos los agentes publicados están en `agents/*.md`; la diferencia entre núcleo y opcionales se documenta en sus fichas y en el motor de personalidad, no mediante un subdirectorio `agents/optional/`.

La documentación humana equivalente está en `docs/agents/`. Si cambias un agente fuente, conviene revisar su ficha en `docs/agents/` y cualquier mención en `docs/README.md`, `docs/personality.md` o `docs/flows.md`.

### `commands/`

Contiene los prompts de todos los slash commands. Hay dos tipos:

- comandos de flujo, como `feature.md`, `fix.md`, `ship.md`;
- comandos operativos, como `progress.md`, `validate.md`, `search.md`, `memory-ui.md`.

Si una release añade o elimina un comando, hay que alinear cuatro superficies:

1. `commands/`;
2. `.claude-plugin/plugin.json`;
3. `README.md`;
4. `docs/commands.md`.

### `core/`

Es la lógica ejecutable principal del plugin. Los módulos más importantes hoy son:

- `orchestrator.py`: flujos, fases, gates y persistencia de sesión;
- `config_loader.py`: detección de stack, carga de configuración y sugerencias;
- `personality.py`: catálogo de personalidad y metadatos de agentes;
- `memory.py`, `memory_sync.py`, `memory_ui_server.py`: memoria persistente, sync nativo y UI;
- `optional_agents.py`: composición dinámica del equipo;
- `selina_*`: runtime visual de Selina.

La mayor parte del valor técnico del plugin está aquí, pero `docs/` todavía lo cubre más por temas funcionales que por mapa de módulos.

### `hooks/`

Aquí viven los scripts conectados al ciclo de vida de Claude Code. El manifiesto canónico es `hooks/hooks.json`. Los hooks aplican seguridad, continuidad, captura de actividad, quality gates y memoria.

Cuando cambias un hook, revisa:

1. `hooks/hooks.json`;
2. la implementación del script;
3. sus tests;
4. `docs/hooks.md` si cambia el comportamiento observable.

### `mcp/`

Contiene el servidor MCP local de memoria (`memory_server.py`). Aunque la memoria ya está documentada conceptualmente, esta capa merece una página específica porque es la frontera de integración con herramientas externas.

### `visual/`

Scripts y helpers del companion visual de Selina. Aquí viven el servidor local, las plantillas HTML y los generadores de pantallas/variantes. La referencia técnica está en [visual.md](visual.md).

### `tests/`

La suite mezcla:

- tests unitarios del core;
- tests de contratos para prompts y superficie pública;
- tests de hooks;
- tests de memoria, UI y servidor;
- tests de helpers visuales.

La documentación de testing existía, pero necesitaba ponerse al día con esta cobertura real.

---

## Cómo orientarse según la tarea

| Si vas a tocar... | Empieza por... | Después revisa... |
|---|---|---|
| Un flujo | `commands/*.md` | `core/orchestrator.py`, `docs/flows.md` |
| Un agente | `agents/*.md` | `docs/agents/`, `core/personality.py` |
| Configuración | `core/config_loader.py` | `docs/configuration.md` |
| Memoria | `core/memory.py` | `core/memory_sync.py`, `mcp/memory_server.py`, `docs/memory.md` |
| Hooks | `hooks/hooks.json` | el script concreto, sus tests y `docs/hooks.md` |
| Selina | `core/selina_*` y `visual/scripts/` | `agents/selina.md`, `docs/agents/selina.md`, `docs/visual.md` |
| Tests/contratos | `tests/` | `docs/testing.md` |

---

## Deriva documental a vigilar

En este repo hay cuatro zonas con más riesgo de drift:

- **contadores públicos**: número de comandos, agentes, skills, hooks;
- **superficie publicada**: `.claude-plugin/plugin.json` y marketplace;
- **versionado**: README, docs, instaladores, tests de consistencia;
- **prompts operativos**: commands y agents, que cambian rápido.

Cuando una release toca cualquiera de esas zonas, `docs/` debe revisarse en la misma PR.
