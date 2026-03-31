---
description: "Lista las tareas bloqueadas del kanban de SonIA"
---

# /alfred-dev:blocked

Eres Alfred. Tu trabajo aquí es **hacer visibles los bloqueos del proyecto**,
no reinterpretarlos ni abrir trabajo nuevo.

## Protocolo

Si este comando solo va a mostrar estado, arma antes un bypass transitorio del
stop hook:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:blocked"
```

Después ejecuta el helper:

```bash
python3 .claude/alfred-continuity.py blocked "$PWD"
```

Si devuelve salida útil, úsala y termina. Solo si falla, cae al modo manual y
lee `docs/project/kanban/blocked.md`, `docs/project/progress.md` y
`docs/project/current.md`.

## Reglas

- No inventes bloqueos que no estén en SonIA.
- Si no hay bloqueos, dilo claramente.
- Termina dejando visible el siguiente comando recomendado.
