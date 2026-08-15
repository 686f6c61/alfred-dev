---
name: memory
description: This skill should be used when the user asks to record a design decision, search past project decisions, inspect the Alfred memory timeline, or work with the alfred-memory MCP server. Use it to call the namespaced MCP tools instead of inventing history.
---

# Memoria persistente de Alfred

Registrar y consultar decisiones del proyecto a través del servidor MCP `alfred-memory`. No inventar historial. Si la herramienta no está disponible, decirlo y no simular resultados.

## Nombres reales de las tools

Claude Code expone las tools del plugin con prefijo MCP. Usar estos nombres, no los cortos:

- `mcp__plugin_alfred-dev_alfred-memory__memory_search`
- `mcp__plugin_alfred-dev_alfred-memory__memory_get_decisions`
- `mcp__plugin_alfred-dev_alfred-memory__memory_get_iteration`
- `mcp__plugin_alfred-dev_alfred-memory__memory_get_timeline`
- `mcp__plugin_alfred-dev_alfred-memory__memory_stats`
- `mcp__plugin_alfred-dev_alfred-memory__memory_log_decision`
- `mcp__plugin_alfred-dev_alfred-memory__memory_update_decision`
- `mcp__plugin_alfred-dev_alfred-memory__memory_link_decisions`
- `mcp__plugin_alfred-dev_alfred-memory__memory_health`

Si el runtime muestra un prefijo distinto, usar el que aparezca en la lista de tools, siempre del servidor `alfred-memory`.

## Qué se escribe y qué no

Sí: decisiones de diseño, resultado de gates, handoffs, UAT y commits hechos en una sesión de Alfred.

No: historial antiguo de Git, cada Read/Glob/Grep, consejos operativos ni kanban vacío.

Llamar a `memory_log_decision` solo cuando haya una elección real de diseño, seguridad o entrega. No registrar cada edit. Si la decisión es de arquitectura o compliance, el Markdown vivo (`docs/adr/`, `docs/project/compliance.md`) es lo que lee un humano; la memoria no lo sustituye.

Campos mínimos: título, contexto, alternativas descartadas, justificación, etiquetas.

## Consulta

Para "por qué decidimos X" o "qué hicimos la última vez": `memory_search` o `memory_get_decisions` con el término y, si aplica, rango o tags.

Si no hay filas, responder que no hay registros. No inferir.

No existe el agente `librarian`. Esta skill y `/alfred-dev:memory-ui` son la vía de consulta histórica.

## UI

La vista gráfica es `/alfred-dev:memory-ui`. Esta skill no arranca el servidor HTTP. Para cerrarla: `/alfred-dev:memory-ui stop`. Al terminar la sesión de Claude se detiene sola.
