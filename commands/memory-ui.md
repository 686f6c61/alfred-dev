---
description: "Abre una UI local en navegador con la memoria SQLite, timeline, decisiones, grafo y búsqueda"
---

# /alfred-dev:memory-ui

Eres Alfred. Este comando existe para **abrir la memoria del proyecto en una UI
gráfica local**, no para improvisar un análisis manual en el chat.

## Protocolo

Paso 0: si `UserPromptSubmit` ya dejó la UI helper-first preparada en esta
misma sesión, consúmela ANTES de hacer nada más. Ejecuta este Bash
inmediatamente y, si devuelve texto, úsalo tal cual como respuesta final:

```bash
python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected memory-ui
```

Si no devuelve nada o falla, continúa.

Si este comando solo va a abrir o reutilizar la UI, arma antes un bypass
transitorio del stop hook:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:memory-ui"
```

Después ejecuta inmediatamente el helper determinista:

```bash
python3 .claude/alfred-continuity.py memory-ui "$PWD"
```

Si el helper devuelve una URL válida:

- úsala como respuesta final;
- explica en una frase que la UI se abre en navegador y se refresca sola;
- no sigas explorando el repositorio.

Solo si el helper falla, cae al modo manual.

## Qué debe dejar visible la respuesta

- URL local abierta o reutilizada;
- que la fuente de verdad es `.claude/alfred-memory.db`;
- que la vista muestra overview, timeline, decisiones, grafo, commits y búsqueda.

## Reglas

- NO conviertas este comando en un informe textual largo.
- NO leas el SQLite “a mano” si el helper ha funcionado.
- NO abras un flujo multiagente.
- Si la memoria todavía está vacía, dilo claramente, pero abre igualmente la UI.
