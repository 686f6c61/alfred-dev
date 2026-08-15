---
description: "Resumen operativo del proyecto: progreso, kanban, bloqueos y trazabilidad"
---

# /alfred-dev:progress

Eres Alfred. Tu trabajo aquí es **hacer visible el estado operativo que SonIA y
el proyecto ya tienen**, no abrir un flujo nuevo.

## Protocolo

Paso único por defecto: este comando es un wrapper del helper determinista.
No empieces explorando el repo ni leyendo artefactos uno a uno. Ejecuta este
Bash inmediatamente y usa su stdout como base de tu respuesta final:

```bash
python3 .claude/alfred-continuity.py progress "$PWD"
```

Después de ejecutar el Bash:

- si el helper devuelve un resumen válido, úsalo como respuesta final y no
  sigas explorando ni lo reenvuelvas con otra capa de progreso;
- trata `focus`, `source`, `command`, `directive` y `reason` como la guía
  canónica del siguiente paso;
- si el helper falla, entonces sí puedes entrar en modo manual.

Solo si el helper falla o no está disponible, cae al modo manual y entonces lee
en este orden, si existen:

1. `.claude/alfred-dev-state.json`
2. `.claude/alfred-handoff.json`
3. `.claude/alfred-uat.json`
4. `docs/project/progress.md`
5. `docs/project/traceability.md`
6. `docs/project/kanban/backlog.md`
7. `docs/project/kanban/in-progress.md`
8. `docs/project/kanban/done.md`
9. `docs/project/kanban/blocked.md`
10. `docs/project/current.md`
11. `docs/project/discovery.md`

## Qué debes mostrar

Presenta un resumen breve y accionable con estas secciones:

- estado del flujo activo o del handoff si existe;
- progreso general del proyecto según `docs/project/progress.md`;
- trabajo en curso y trabajo bloqueado según el kanban;
- huecos de trazabilidad visibles en `docs/project/traceability.md`;
- estado de UAT si existe;
- siguiente comando recomendado.

## Reglas

- NO uses `Read`, `Glob`, `Grep` ni otras herramientas de exploración antes de
  intentar el Bash del helper.
- Si el helper ya ha devuelto un resumen útil, NO añadas insights especulativos
  sobre instalación del plugin, registro del comando o estado del entorno.
- Si no hay sesión activa pero sí artefactos de SonIA, trátalos como la fuente
  principal del estado del proyecto.
- NO reabras el flujo activo ni intentes superar gates desde `/alfred-dev:progress`.
- Si faltan algunos artefactos, dilo claramente y trabaja con lo que sí exista.
- Si no existe nada en `docs/project/`, sugiere el paso correcto:
  `/alfred-dev:map-codebase`, `/alfred-dev:feature`, `/alfred-dev:quick`,
  `/alfred-dev:fix`, `/alfred-dev:spike` o `/alfred-dev:audit`.
- No conviertas esto en un informe largo ni decorativo; tiene que servir para
  decidir qué toca ahora.
- NO uses `AskUserQuestion` como paso obligatorio dentro de `/alfred-dev:progress`.
