---
description: "Busca texto en artefactos de SonIA y memoria SQLite del proyecto"
argument-hint: "Texto a buscar"
---

# /alfred-dev:search

Eres Alfred. Este comando es una búsqueda **determinista y rápida** sobre el
estado operativo del proyecto y su memoria persistente.

Consulta de búsqueda: $ARGUMENTS

## Protocolo

Si este comando solo va a mostrar resultados, arma antes un bypass transitorio
del stop hook:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:search"
```

Después ejecuta el helper:

```bash
python3 .claude/alfred-continuity.py search "$PWD" --raw "$ARGUMENTS"
```

Si devuelve resultados, úsalo como respuesta final y termina.

Solo si falla, cae al modo manual y busca en:

1. `docs/project/codebase-map.md`
2. `docs/project/current.md`
3. `docs/project/discovery.md`
4. `docs/project/progress.md`
5. `docs/project/traceability.md`
6. `docs/project/kanban/*.md`
7. `.claude/alfred-memory.db` si existe

## Reglas

- Si `$ARGUMENTS` está vacío, dilo claramente y no inventes una búsqueda.
- Prioriza coincidencias exactas o muy cercanas.
- Distingue entre resultados de artefactos y resultados de memoria SQLite.
- NO conviertas esto en un análisis largo.
