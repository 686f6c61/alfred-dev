---
description: "Abre o cierra la UI local de memoria: timeline, decisiones, grafo y búsqueda"
argument-hint: "[stop|cerrar]"
---

# /alfred-dev:memory-ui

Eres Alfred. Este comando existe para **abrir o cerrar la memoria del proyecto
en una UI gráfica local**, no para improvisar un análisis manual en el chat.

Argumento libre del usuario: $ARGUMENTS

## Semántica

- Sin argumento: abre o reutiliza la UI en `http://127.0.0.1`.
- `stop`, `cerrar` o `detener`: apaga el servidor local si está vivo.

Al terminar la sesión de Claude, `SessionEnd` detiene la UI si sigue en marcha.

## Protocolo

Paso 0: si `UserPromptSubmit` ya dejó la UI helper-first preparada en esta
misma sesión, consúmela ANTES de hacer nada más. Ejecuta este Bash
inmediatamente y, si devuelve texto, úsalo tal cual como respuesta final:

```bash
python3 .claude/alfred-continuity.py consume-prefetch "$PWD" --expected memory-ui
```

Si no devuelve nada o falla, continúa.

Después ejecuta inmediatamente el helper determinista:

```bash
python3 .claude/alfred-continuity.py memory-ui "$PWD" --raw "$ARGUMENTS"
```

El helper también acepta `--stop` como alias de `stop`/`cerrar`/`detener`.

Si el helper devuelve una respuesta válida, úsala tal cual como respuesta final
y no la reenvuelvas con más prosa. El helper ya deja visible la URL, el estado
de la UI o la confirmación de cierre.

Solo si el helper falla, cae al modo manual.

## Qué debe dejar visible la respuesta

Si se abre la UI:

- URL local abierta o reutilizada;
- que la fuente de verdad es `.claude/alfred-memory.db`;
- que la vista muestra overview, timeline, decisiones, grafo, commits y búsqueda;
- cómo cerrarla: `/alfred-dev:memory-ui stop`.

Si se cierra: confirmación de que el proceso se detuvo o de que no estaba en
ejecución.

## Reglas

- NO conviertas este comando en un informe textual largo.
- NO leas el SQLite “a mano” si el helper ha funcionado.
- NO abras un flujo multiagente.
- NO añadas una segunda explicación encima del Markdown que ya devuelve el helper.
- Si la memoria todavía está vacía, dilo claramente, pero abre igualmente la UI.
- NO uses `AskUserQuestion` como paso obligatorio.
