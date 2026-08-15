# Referencia de comandos

Esta página documenta la superficie publicada en `.claude-plugin/plugin.json`: **18 comandos**. `next` y `search` quedan como helpers internos, no como slash commands.

La continuidad pública es `/alfred-dev:alfred`, `/alfred-dev:progress` y `/alfred-dev:retomar`.

---

## Mapa rápido

| Grupo | Comandos |
|---|---|
| Orquestación | `alfred`, `ajustes`, `update` |
| Flujos | `feature`, `quick`, `fix`, `spike`, `audit`, `ship` |
| Continuidad | `progress`, `retomar`, `pause`, `map-codebase`, `discuss` |
| Operación | `uat`, `sync-github`, `memory-ui`, `lucius` |

---

## Orquestación y ayuda

### `/alfred-dev:alfred`

Entrada contextual del plugin. Decide si conviene mapear el repo, retomar una sesión, abrir un flujo completo o responder con una acción más pequeña. Es el comando correcto cuando el usuario todavía no sabe qué comando quiere, pero sí qué problema tiene.

### `/alfred-dev:ajustes`

Configura el proyecto: autonomía, stack detectado, memoria, personalidad y el único opcional (Lucius). Es el primer comando recomendable al entrar en un repo nuevo. No ofrece el catálogo 0.6.

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

### `/alfred-dev:progress`

Vista operativa del proyecto: progreso, bloqueos, trazabilidad, UAT y situación del trabajo en curso. Absorbé status, standup, blocked, in-progress y validate.

### `/alfred-dev:pause`

Pausa el trabajo actual y deja handoff persistente para retomarlo más tarde sin perder continuidad.

### `/alfred-dev:retomar`

Recupera una sesión pausada usando el estado y el handoff guardados.

### `/alfred-dev:uat`

Separa la validación humana o UAT de la validación automática. Es el comando correcto cuando el código y los tests están, pero falta confirmación funcional.

---

## Operación

`next` y `search` existen como helpers internos (`commands/next.md`, `commands/search.md`) y no se publican en `plugin.json`.

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
| Estado operativo | `progress` |
| Saber el siguiente paso | `progress` o el helper interno `next` |
| Retomar una sesión | `retomar` |
| Validación humana | `uat` |
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
