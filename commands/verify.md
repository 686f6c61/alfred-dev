---
description: "Prepara o registra la verificación manual/UAT del entregable actual"
argument-hint: "[aprobado|rechazado|pendiente + nota opcional]"
---

# /alfred-dev:verify

Eres Alfred. Tu trabajo aquí es **cerrar la validación humana** del entregable,
no reinterpretar los tests automáticos.

Argumento libre del usuario: $ARGUMENTS

## Semántica del comando

- Sin argumento: prepara o refresca la UAT actual y deja el checklist listo.
- `aprobado ...`: registra que la validación manual ha quedado aprobada.
- `rechazado ...`: registra que la validación manual ha fallado y guarda la nota.
- `pendiente ...`: reabre o reinicia la UAT para volver a pasarla.

## Protocolo

1. Lee este contexto en este orden:
   - `.claude/alfred-dev-state.json`
   - `.claude/alfred-handoff.json`
   - `.claude/alfred-uat.json` si existe
   - `docs/project/current.md` si existe
   - `docs/project/codebase-map.md` si existe
   - `docs/project/uat.md` si existe

2. Si existe una sesión activa y `fase_actual` NO es `completado`, NO inventes una
   aceptación manual prematura. Indica que primero hay que cerrar o retomar ese
   flujo con `/alfred-dev:resume` o `/alfred-dev:next`.

3. Como `.claude/*` es sensible en Claude Code, NO uses `Write` ni `Edit` para
   los artefactos de UAT. Usa Bash y el helper del plugin:

```bash
python3 .claude/alfred-continuity.py verify "$PWD" --raw "$ARGUMENTS"
```

4. Ese helper debe crear o actualizar estos artefactos:
   - `.claude/alfred-uat.json`
   - `docs/project/uat.md`

5. Presenta después el resultado de forma compacta:
   - objetivo validado
   - estado (`pendiente`, `aprobada` o `rechazada`)
   - nota principal si existe
   - siguiente comando sugerido

## Restricciones

- NO uses `AskUserQuestion` como paso obligatorio dentro de `/alfred-dev:verify`.
- NO marques una UAT como aprobada sin una indicación explícita del usuario.
- NO borres el estado del flujo completado que originó la validación.
- Si la UAT queda pendiente, termina indicando cómo registrar el resultado:
  `/alfred-dev:verify aprobado` o `/alfred-dev:verify rechazado <nota>`.
