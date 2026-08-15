---
description: "Ejecuta SonIA Sync: refleja el tablero local en GitHub Issues usando gh CLI"
argument-hint: "[owner/repo opcional]"
disable-model-invocation: true
allowed-tools: Bash(python3 .claude/alfred-continuity.py *), Bash(gh *), Read, Write
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

Ejecuta inmediatamente el helper determinista:

```bash
python3 .claude/alfred-continuity.py sync-github "$PWD" --raw "$ARGUMENTS"
```

Si el helper devuelve salida válida:

- úsala como respuesta final y termina;
- entiende que ya ha escrito `.claude/alfred-github-sync.json` y `docs/project/github-sync.md`;
- asume que también puede haber retirado issues Alfred previamente sincronizados si ya no existen en SonIA local;
- conserva visibles `focus`, `source`, `command`, `directive` y `reason` si el helper los expone;
- en `claude -p` o auditoría headless, mantén el cierre en menos de 12 líneas;
- no añadas bloques `Insight`, tablas, explicación pedagógica ni lecturas adicionales;
- no sigas explorando, no rehagas el sync a mano y no añadas una segunda narración por encima del resumen del helper.

Solo si el helper falla o `gh` no está listo, cae al modo manual. En manual:

1. verifica `gh --version` y `gh auth status`;
2. detecta el repo desde `origin` o usa `$ARGUMENTS` si trae `owner/repo`;
3. lee `docs/project/kanban/backlog.md`, `in-progress.md`, `done.md`, `blocked.md`;
4. usa GitHub Issues como espejo colaborativo de SonIA Sync, no como fuente de verdad principal.

## Reglas

- NO uses `AskUserQuestion` por defecto.
- Si falta `gh` o autenticación, informa claramente y no finjas el sync.
- No borres issues ajenos a Alfred.
- Si una tarea Alfred ya no existe en el tablero local, el espejo remoto debe retirarla o cerrarla sin tocar issues ajenos.
- Mantén la verdad local en `docs/project/` y `.claude/`.
