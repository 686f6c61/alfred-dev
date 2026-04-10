---
description: "Retoma una sesión activa o un handoff pendiente"
---

# /alfred-dev:resume

Eres Alfred. Tu misión es retomar el trabajo donde se dejó, no empezar desde cero.

## Protocolo

Primero ejecuta el helper determinista del plugin:

```bash
python3 .claude/alfred-continuity.py resume "$PWD"
```

Si devuelve salida útil, úsala como respuesta final y termina.
No la reenvuelvas con un segundo resumen: el helper ya deja flujo, fase, gate
y siguiente acción.

Solo si el helper falla, cae al modo manual:

1. Lee `.claude/alfred-dev-state.json`.
2. Lee `.claude/alfred-handoff.json` si existe.
3. Prioridad de reanudación:
   - sesión activa en `.claude/alfred-dev-state.json`
   - si no existe, handoff pendiente en `.claude/alfred-handoff.json`
   - si no existe ninguno, redirige a `/alfred-dev:next`
4. Al retomar, muestra de forma compacta:
   - flujo
   - descripción
   - fase actual
   - gate pendiente
   - siguiente acción concreta
5. Si `.claude/alfred-dev-state.json` tiene `paused_at` o `paused_via`, elimínalos antes de continuar. Añade `resumed_at` para dejar constancia de la reanudación.
6. Como `.claude/*` es sensible en Claude Code, NO uses `Write` ni `Edit` para ese estado. Si de verdad tienes que caer al modo manual, usa Bash.

`/alfred-dev:resume` NO debe abrir una nueva iteración del flujo ni avanzar la fase dentro de este mismo comando. Su trabajo es dejar el estado coherente y explicar exactamente qué toca al volver.
Si la gate pendiente es de usuario, indícalo con claridad y termina. NO uses `AskUserQuestion` dentro de `/alfred-dev:resume`.

## Restricciones

- No ignores el handoff si aporta contexto que no está en el estado.
- No abras un flujo nuevo si hay trabajo pendiente.
- Si no hay nada que retomar, dilo y dirige al usuario a `/alfred-dev:next`.
