---
description: "Valida la integridad operativa de SonIA: kanban, trazabilidad, UAT y sync local"
---

# /alfred-dev:validate

Eres Alfred. Este comando debe decir si el **estado operativo del proyecto**
está sano o si hay huecos visibles en SonIA.

## Protocolo

Si solo vas a devolver el informe de validación, arma primero un bypass
transitorio del stop hook:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:validate"
```

Después ejecuta el helper determinista:

```bash
python3 .claude/alfred-continuity.py validate "$PWD"
```

Si devuelve salida válida, úsala como respuesta final y termina.
No añadas una segunda capa de resumen encima del veredicto del helper: el helper
ya deja `Resumen`, `Checks`, `Avisos`, `Errores` y siguiente paso.

Solo si el helper falla, cae al modo manual y valida:

1. `docs/project/kanban/*.md`
2. `docs/project/traceability.md`
3. `docs/project/progress.md`
4. `.claude/alfred-uat.json`
5. `.claude/alfred-github-sync.json` si existe

## Qué debe comprobar

- tareas duplicadas o sin ID;
- tareas en `done` sin evidencia clara;
- tareas en `blocked` sin motivo o dependencia;
- huecos visibles entre kanban y trazabilidad;
- UAT pendiente cuando debería estar cerrada;
- huecos visibles en el sync local con GitHub si existe.

## Reglas

- NO uses `AskUserQuestion`.
- NO corrijas artefactos desde `/alfred-dev:validate`; solo valida y recomienda.
- El veredicto debe ser claro: aprobado, aprobado con avisos o rechazado.
