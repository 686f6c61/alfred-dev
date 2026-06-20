# Referencia de comandos

Esta página documenta la superficie operativa real del plugin publicada en `.claude-plugin/plugin.json`. En la rama `main`, Alfred Dev expone **26 comandos**. Algunos lanzan flujos multiagente; otros son vistas operativas, utilidades de continuidad o integraciones especializadas.

La regla práctica es esta: si el trabajo requiere fases, gates y artefactos, usa un flujo. Si solo necesitas contexto, estado o una operación puntual, usa un comando operativo.

---

## Mapa rápido

| Grupo | Comandos |
|---|---|
| Orquestación y ayuda | `alfred`, `help`, `config`, `update` |
| Flujos de trabajo | `feature`, `quick`, `fix`, `spike`, `audit`, `ship` |
| Continuidad | `map-codebase`, `discuss`, `next`, `status`, `progress`, `pause`, `resume`, `verify` |
| Operación PM (SonIA) | `standup`, `blocked`, `in-progress`, `validate`, `search`, `sync-github` |
| Especializados | `memory-ui`, `lucius` |

---

## Orquestación y ayuda

### `/alfred-dev:alfred`

Entrada contextual del plugin. Decide si conviene mapear el repo, retomar una sesión, abrir un flujo completo o responder con una acción más pequeña. Es el comando correcto cuando el usuario todavía no sabe qué comando quiere, pero sí qué problema tiene.

### `/alfred-dev:help`

Resumen operativo de comandos, agentes y reglas de uso. Es la referencia rápida dentro de Claude Code.

### `/alfred-dev:config`

Configura el proyecto: autonomía, stack detectado, memoria, personalidad y activación de agentes opcionales. Es el primer comando recomendable al entrar en un repo nuevo.

### `/alfred-dev:update`

Comprueba si hay una versión más reciente del plugin y guía la actualización.

---

## Flujos de trabajo

### `/alfred-dev:feature <descripción>`

Flujo principal para desarrollar una funcionalidad. Puede recorrer hasta siete fases: producto, estilo visual condicional, arquitectura, desarrollo, calidad, documentación y entrega.

### `/alfred-dev:quick <descripción>`

Versión ligera para cambios pequeños o bien delimitados. Mantiene disciplina, pero con menos ceremonia que `feature`.

### `/alfred-dev:fix <descripción>`

Flujo orientado a bugs. Prioriza diagnóstico, corrección con TDD y validación final.

### `/alfred-dev:spike <tema>`

Investigación sin compromiso de implementación. Sirve para explorar una tecnología, patrón o alternativa antes de decidir.

### `/alfred-dev:audit`

Auditoría transversal del proyecto con foco en calidad, seguridad, arquitectura y documentación.

### `/alfred-dev:ship`

Comando de entrega y release. Reúne validación final, changelog, versionado y comprobaciones previas a producción.

---

## Continuidad

### `/alfred-dev:map-codebase`

Analiza un repo existente y deja artefactos de descubrimiento para trabajar en brownfield con contexto real. Es el mejor punto de entrada cuando el proyecto ya existe y nadie ha documentado su estado.

### `/alfred-dev:discuss <descripción>`

Refina una idea, una mejora o una fase concreta antes de abrir un flujo grande. Genera descubrimiento persistente.

### `/alfred-dev:next`

Dice cuál es el siguiente paso lógico según el estado actual del proyecto, la sesión activa y los artefactos disponibles.

### `/alfred-dev:status`

Muestra el estado de la sesión: fase actual, gates pendientes, fases completadas y señales útiles de continuidad.

### `/alfred-dev:progress`

Vista operativa más amplia del proyecto: progreso, bloqueos, trazabilidad, UAT y situación del trabajo en curso.

### `/alfred-dev:pause`

Pausa el trabajo actual y deja handoff persistente para retomarlo más tarde sin perder continuidad.

### `/alfred-dev:resume`

Recupera una sesión pausada usando el estado y el handoff guardados.

### `/alfred-dev:verify`

Separa la validación humana o UAT de la validación automática. Es el comando correcto cuando el código y los tests están, pero falta confirmación funcional.

---

## Operación PM y SonIA

### `/alfred-dev:standup`

Resumen breve y accionable del estado operativo del proyecto: qué está en curso, qué está bloqueado y qué toca después.

### `/alfred-dev:blocked`

Lista únicamente el trabajo bloqueado junto con su dependencia o causa visible.

### `/alfred-dev:in-progress`

Lista el trabajo actualmente en marcha.

### `/alfred-dev:validate`

Valida la integridad operativa del proyecto: duplicados, trazabilidad incompleta, evidencia ausente, UAT pendiente o desalineaciones del tablero local.

### `/alfred-dev:search <texto>`

Busca de forma unificada en artefactos operativos y memoria persistente.

### `/alfred-dev:sync-github [owner/repo]`

Sincroniza el tablero operativo local con GitHub Issues usando `gh`, manteniendo la fuente de verdad en local.

---

## Comandos especializados

### `/alfred-dev:memory-ui`

Abre una UI local para explorar la memoria SQLite del proyecto: timeline, decisiones, commits, búsqueda y salud de memoria.

### `/alfred-dev:lucius [directorio] [--scope X]`

Pide una segunda opinión técnica externa vía Codex CLI. Es una auditoría especializada, no un flujo de implementación.

---

## Cuándo usar cada uno

| Necesidad | Comando recomendado |
|---|---|
| No sabes por dónde empezar | `alfred` |
| Repo brownfield sin contexto | `map-codebase` |
| Idea aún inmadura | `discuss` |
| Nueva feature completa | `feature` |
| Cambio pequeño | `quick` |
| Bug concreto | `fix` |
| Investigación | `spike` |
| Estado operativo | `progress` o `standup` |
| Saber el siguiente paso | `next` |
| Retomar una sesión | `resume` |
| Validación humana | `verify` |
| Auditoría profunda | `audit` |
| Release | `ship` |
| Memoria histórica | `memory-ui` o `search` |
| Segunda opinión externa | `lucius` |

---

## Relación con la documentación

- La lógica de fases y gates está desarrollada en [flows.md](flows.md).
- La composición dinámica del equipo se explica en [configuration.md](configuration.md).
- La memoria persistente y la búsqueda se detallan en [memory.md](memory.md).
- La documentación de operación continua está en [operations.md](operations.md).
