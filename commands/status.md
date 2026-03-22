---
description: "Muestra el estado de la sesión activa de Alfred Dev"
---

# Estado de la sesión

Lee estos artefactos en este orden:

1. `.claude/alfred-dev-state.json`
2. `.claude/alfred-handoff.json`
3. `.claude/alfred-uat.json` si existe
4. `docs/project/discovery.md` si existe
5. `docs/project/current.md` si existe
6. `docs/project/progress.md` si existe
7. `docs/project/traceability.md` si existe
8. `docs/project/kanban/in-progress.md` si existe
9. `docs/project/kanban/blocked.md` si existe
10. `docs/project/uat.md` si existe

Si hay una sesión activa y este comando solo va a informar, antes de cerrar
arma un bypass transitorio del stop hook para que la respuesta termine limpia
en Claude Code CLI:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:status"
```

Si no existe `.claude/alfred-dev-state.json`, informa de que no hay sesión activa y, si hay handoff, preséntalo como trabajo pendiente recuperable. Si existe `docs/project/discovery.md`, úsalo para resumir el refinado actual y el siguiente comando recomendado. Si existen artefactos de SonIA en `docs/project/`, úsalos para resumir el estado operativo y sugiere `/alfred-dev:progress` cuando sea la vista más útil. Si existe UAT pendiente o rechazada, muéstrala como siguiente foco operativo.

Si existe, presenta:
- Comando activo y descripción
- Fase actual y número de fase
- Fases completadas con timestamps y artefactos generados
- Gates pendientes o fallidas
- Estado del refinado en `docs/project/discovery.md` si existe
- Estado de verificación manual/UAT si existe
- Dependencias nuevas añadidas
- Hallazgos de seguridad
- Notas acumuladas
- Resumen de progreso/kanban/trazabilidad si existe
- Siguiente paso recomendado (incluye el comando exacto si está claro)

No reabras el flujo ni intentes superar gates desde `/alfred-dev:status`.

Presenta la información de forma legible con tablas y formato claro.
