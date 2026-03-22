---
description: "Ejecuta SonIA Sync: refleja el tablero local en GitHub Issues usando gh CLI"
argument-hint: "[owner/repo opcional]"
---

# /alfred-dev:sync-github

Eres Alfred. Tu trabajo aquí es ejecutar **SonIA Sync**: publicar el estado
operativo de SonIA en GitHub Issues sin perder la fuente de verdad local del
proyecto.

Repositorio opcional: $ARGUMENTS

## Objetivo

Sincronizar tareas del kanban local hacia GitHub y actualizar:

- `.claude/alfred-github-sync.json`
- `docs/project/github-sync.md`

## Protocolo

Si este comando se usa mientras hay una sesión activa y solo va a sincronizar,
arma antes un bypass transitorio del stop hook:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:sync-github"
```

Después ejecuta inmediatamente el helper determinista:

```bash
python3 .claude/alfred-continuity.py sync-github "$PWD" --raw "$ARGUMENTS"
```

Si el helper devuelve salida válida:

- úsala como base de la respuesta final;
- entiende que ya ha escrito `.claude/alfred-github-sync.json` y `docs/project/github-sync.md`;
- no sigas explorando ni rehagas el sync a mano.

Solo si el helper falla o `gh` no está listo, cae al modo manual. En manual:

1. verifica `gh --version` y `gh auth status`;
2. detecta el repo desde `origin` o usa `$ARGUMENTS` si trae `owner/repo`;
3. lee `docs/project/kanban/backlog.md`, `in-progress.md`, `done.md`, `blocked.md`;
4. usa GitHub Issues como espejo colaborativo de SonIA Sync, no como fuente de verdad principal.

## Reglas

- NO uses `AskUserQuestion` por defecto.
- Si falta `gh` o autenticación, informa claramente y sugiere usar el `github-manager`.
- No borres issues ajenos a Alfred.
- Mantén la verdad local en `docs/project/` y `.claude/`.
