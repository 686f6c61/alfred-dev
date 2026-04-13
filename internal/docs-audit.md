# Auditoría de la documentación

Esta auditoría contrasta `docs/` contra el estado real de la rama `main` del plugin. El objetivo no es reescribir por gusto, sino detectar tres cosas con precisión: qué está bien cubierto, qué falta por documentar y qué partes ya tienen drift respecto al código.

La conclusión principal es clara: `docs/` tenía una base bastante mejor de lo que parecía, pero estaba descompensada. La cobertura de arquitectura, agentes, skills, memoria, hooks e instalación era amplia; en cambio, faltaban páginas de primer nivel para la superficie operativa real del plugin (comandos, mapa del repo, SonIA/continuidad, MCP/Memory UI, release/contribución). Además, había varios puntos donde la narrativa ya no reflejaba bien la suite de tests ni la ubicación real de ciertos artefactos.

---

## Resumen ejecutivo

### Lo que ya estaba bien cubierto

- **Agentes:** `docs/agents/` ya cubría los **19 agentes publicados** del plugin. No faltaban fichas de agentes en la rama `main`.
- **Arquitectura base:** `architecture.md`, `flows.md`, `memory.md`, `configuration.md`, `installation.md` y `personality.md` daban una visión técnica suficientemente profunda para entender el runtime.
- **Skills y hooks:** ya existían páginas específicas y con bastante contexto conceptual.
- **Testing:** había una página extensa y la suite real del repo ya era amplia.

### Lo que faltaba de verdad

- **Referencia de comandos:** el plugin publica **26 comandos** en `.claude-plugin/plugin.json`, pero `docs/` no tenía una página dedicada a esa superficie.
- **Mapa del repositorio:** faltaba una vista de alto nivel que conectara `agents/`, `commands/`, `core/`, `hooks/`, `mcp/`, `visual/`, `tests/` y `templates/` con sus documentos.
- **Operación continua / SonIA:** había mucho comportamiento real alrededor de `docs/project/`, continuidad, handoff, kanban y vistas operativas, pero no existía una página técnica dedicada.
- **MCP y Memory UI:** la memoria estaba documentada, pero no la capa de servidor MCP ni la UI local como subsistemas propios.
- **Contribución y releases:** faltaba una guía clara para mantener el plugin, actualizar versión, validar contratos y publicar.

### Drift factual detectado

- `docs/hooks.md` decía que los hooks se declaraban en `hooks.json` en la raíz o en `.claude-plugin`; el manifiesto real está en `hooks/hooks.json`.
- `docs/testing.md` presentaba la capa de commands/agentes/MCP como prácticamente no testeada o solo verificable en uso real, pero el repo ya incluía tests de contratos, tests del servidor MCP y tests de superficie pública.

---

## Plan recomendado

### Fase 1. Ordenar la entrada a `docs/`

- Actualizar `docs/README.md` como índice canónico.
- Añadir `commands.md`.
- Añadir `repository.md`.
- Mantener esta auditoría fuera de `docs/`, como documento interno.

### Fase 2. Corregir drift factual

- Corregir `hooks.md` para que refleje `hooks/hooks.json`.
- Corregir `testing.md` para reconocer la cobertura actual.
- Revisar tablas, contadores y claims sensibles a versión.

### Fase 3. Cubrir la operación real del plugin

- Añadir una página para **SonIA, continuidad y artefactos operativos**.
- Añadir una página para **MCP + Memory UI**.
- Añadir una guía de **contribución/release**.

### Fase 4. Profundidad por subsistema

- Selina como subsistema visual (`visual/` + `core/selina_*`).
- Contratos de superficie pública (`plugin.json`, marketplace, versión, tests de contrato).
- Plantillas y flujos internos de documentación/reports.
