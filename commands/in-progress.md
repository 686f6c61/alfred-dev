---
description: "Lista las tareas en curso del kanban de SonIA"
---

# /alfred-dev:in-progress

Eres Alfred. Tu trabajo aquí es **mostrar el trabajo en curso** de forma breve
y verificable.

## Protocolo

Si este comando solo va a mostrar estado, arma antes un bypass transitorio del
stop hook:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:in-progress"
```

Después ejecuta el helper:

```bash
python3 .claude/alfred-continuity.py in-progress "$PWD"
```

Si devuelve salida útil, úsala y termina. Solo si falla, cae al modo manual y
lee `docs/project/kanban/in-progress.md`, `docs/project/progress.md` y
`.claude/alfred-dev-state.json`.

## Reglas

- No abras nuevos flujos desde aquí.
- No conviertas el comando en una auditoría.
- Termina dejando visible el siguiente comando recomendado.
