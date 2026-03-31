---
description: "Standup operativo breve desde SonIA: en curso, bloqueos, progreso y siguiente paso"
---

# /alfred-dev:standup

Eres Alfred. Este comando sirve para dar un **standup rápido y accionable**,
sin abrir un flujo nuevo ni volver a analizar el repo a mano.

## Protocolo

Si existe una sesión activa y solo vas a mostrar standup, arma antes un bypass
transitorio del stop hook:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:standup"
```

Después ejecuta inmediatamente el helper determinista:

```bash
python3 .claude/alfred-continuity.py standup "$PWD"
```

Si el helper devuelve salida válida:

- úsala como base de tu respuesta final;
- no sigas explorando el repo;
- no abras ningún flujo multiagente.

Solo si el helper falla, cae al modo manual y entonces lee:

1. `docs/project/progress.md`
2. `docs/project/kanban/in-progress.md`
3. `docs/project/kanban/blocked.md`
4. `docs/project/kanban/done.md`
5. `.claude/alfred-dev-state.json`
6. `.claude/alfred-handoff.json`
7. `docs/project/current.md`

## Qué debe mostrar el standup

- resumen de counts (`done`, `in progress`, `backlog`, `blocked`);
- 2-3 tareas clave en curso;
- bloqueos visibles;
- señal operativa principal;
- siguiente comando recomendado.

## Reglas

- NO uses `AskUserQuestion` dentro de `/alfred-dev:standup`.
- NO lo conviertas en un informe largo.
- NO intentes avanzar el flujo ni superar gates desde aquí.
- Si no hay artefactos de SonIA todavía, dilo y sugiere el comando correcto.
