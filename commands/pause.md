---
description: "Pausa el trabajo actual y deja un handoff explícito"
---

# /alfred-dev:pause

Eres Alfred. Vas a pausar la sesión actual sin perder el hilo.

## Protocolo

1. Lee `.claude/alfred-dev-state.json`.
2. Si no existe o la sesión ya está completada, dilo con claridad y NO inventes un handoff.
3. Si existe una sesión activa:
   - resume comando, descripción, fase actual y fases completadas
   - identifica la gate pendiente
   - identifica el siguiente paso concreto para retomar

4. Escribe estos artefactos:
   - `.claude/alfred-handoff.json`
   - `docs/project/handoff.md`
   - actualiza `.claude/alfred-dev-state.json` añadiendo `paused_at` y `paused_via: "/alfred-dev:pause"`

5. El handoff debe incluir como mínimo:
   - flujo activo
   - descripción
   - fase actual y número
   - fases completadas
   - gate pendiente
   - artefactos registrados
   - comando de retorno `/alfred-dev:resume`
   - siguiente acción concreta al volver

6. Como `.claude/*` es sensible en Claude Code, NO uses `Write` ni `Edit` para esos ficheros. Usa Bash y el helper del plugin:

```bash
python3 .claude/alfred-continuity.py pause "$PWD"
```

## Restricciones

- NO marques la sesión como completada.
- NO borres `.claude/alfred-dev-state.json`.
- NO hagas un handoff vacío o genérico.
- Cierra con una confirmación breve indicando dónde quedó guardado el handoff.
