# Captura total y dashboard humanizado

**Fecha:** 2026-03-12
**Estado:** aprobado

## Contexto

La DB de memoria de Alfred Dev (`alfred-memory.db`) debe ser la fuente de verdad
completa de toda la actividad del plugin. El contexto del modelo es limitado y los
compactings pierden informacion. La DB no tiene esa limitacion: es local, crece lo
que necesite y no se purga.

El dashboard es la visualizacion de esa DB. Debe mostrar informacion legible para
humanos, no JSON crudo.

## Decisiones de diseno

| Decision | Eleccion | Alternativas descartadas |
|----------|----------|--------------------------|
| Nivel de captura | Todo: prompts, contenido completo, stdout | Solo metadatos; metadatos + resumen |
| Inteligencia de presentacion | Hook inteligente (genera summary) | Dashboard inteligente (interpreta tipos) |
| Limite de tamano de DB | Sin limite, crece libremente | Retencion temporal; truncamiento por evento |
| Prompts del usuario | Se capturan via UserPromptSubmit | No capturar |
| Panel de agentes | Se elimina del dashboard | Mostrar con actividad aproximada |
| Arquitectura de hooks | Dispatcher unico (activity-capture.py) | Hooks independientes por evento |

## Arquitectura

### Hook centralizado: `hooks/activity-capture.py`

Un unico fichero que reemplaza a `memory-capture.py` y `commit-capture.py`. Se
registra en `hooks.json` para todos los eventos relevantes.

#### Eventos capturados

| Hook de Claude Code | event_type en DB | Contenido capturado |
|---------------------|-----------------|---------------------|
| PostToolUse Write | file_written | Ruta, extension, contenido completo |
| PostToolUse Edit | file_edited | Ruta, extension, old_string + new_string |
| PostToolUse Bash | command_executed | Comando, exit code, stdout + stderr completos |
| PostToolUse Bash (git commit) | command_executed + log_commit() | Anterior + metadatos enriquecidos |
| UserPromptSubmit | user_prompt | Texto completo del prompt |
| PreCompact | context_compacted | Timestamp de la compactacion |
| Stop | session_ended | Cierre de sesion |
| PostToolUse Write (state.json) | iteration_started / phase_completed / iteration_completed | Logica de fases existente |

#### Estructura interna

```
activity-capture.py
  main()                    -- lee stdin, determina evento, despacha
  _dispatch_write(data)     -- captura Write completo + logica state.json
  _dispatch_edit(data)      -- captura Edit completo
  _dispatch_bash(data)      -- captura Bash completo + enriquecimiento git
  _dispatch_prompt(data)    -- captura prompt del usuario
  _dispatch_compact(data)   -- marca perdida de contexto
  _dispatch_stop(data)      -- cierra sesion
  _generate_summary(...)    -- genera resumen en lenguaje natural
  _is_memory_enabled()      -- comprobacion unica
  _is_excluded_path()       -- exclusion de ficheros internos
  _open_db()                -- apertura de DB una sola vez
```

#### Generacion de summary

Cada dispatcher genera un `summary` en castellano natural:

- ``"Escrito src/auth/login.py (47 lineas, Python)"``
- ``"Editado core/memory.py: reemplazadas 3 lineas en _search_fts"``
- ``"Ejecutado: npm install -- exit 0, 423 paquetes anadidos"``
- ``"Commit: feat: login con OAuth2 -- 4 ficheros"``
- ``"Prompt: por que falla el login cuando el email tiene +"``
- ``"Contexto compactado -- los mensajes anteriores se han resumido"``

### Ficheros eliminados

- `hooks/memory-capture.py` -- absorbido por activity-capture.py
- `hooks/commit-capture.py` -- absorbido por activity-capture.py

### hooks.json

Se reorganiza para que activity-capture.py cubra todos los eventos:

- PostToolUse Write|Edit -> activity-capture.py
- PostToolUse Bash -> activity-capture.py (antes de quality-gate)
- UserPromptSubmit -> activity-capture.py (nuevo)
- PreCompact -> activity-capture.py (junto a memory-compact.py)
- Stop -> activity-capture.py (junto a stop-hook.py)

Los hooks de seguridad (secret-guard, dangerous-command-guard, sensitive-read-guard)
y los de calidad (quality-gate, dependency-watch, spelling-guard) no cambian.

## Cambios en la DB

### Nuevas columnas en `events`

```sql
ALTER TABLE events ADD COLUMN summary TEXT;
ALTER TABLE events ADD COLUMN content TEXT;
```

| Columna | Proposito | Ejemplo |
|---------|-----------|---------|
| summary | Texto legible para el dashboard | "Editado core/memory.py: 3 lineas" |
| payload | Metadatos estructurados (JSON) | {"file":"core/memory.py", "exit_code":0} |
| content | Contenido completo sin truncar | old_string, new_string, stdout, prompt... |

### Migracion

- _SCHEMA_VERSION se incrementa a 4
- ALTER TABLE para las dos columnas nuevas
- Eventos existentes quedan con summary=NULL, content=NULL (fallback a payload)
- El campo content se indexa en memory_fts para busqueda textual

## Dashboard

### Timeline humanizada

Cada evento muestra:

1. Icono por tipo (fichero, terminal, prompt, commit, sistema)
2. Summary como texto principal
3. Timestamp relativo
4. Boton expandir para ver content completo

### Panel de agentes

Se elimina. No se puede dar informacion fiable sobre la actividad de agentes
con los hooks disponibles.

### Filtros actualizados

- Todos
- Ficheros (file_written + file_edited)
- Comandos (command_executed)
- Prompts (user_prompt)
- Decisiones
- Commits
- Sistema (session_*, context_compacted, phase_*, iteration_*)

### Carga bajo demanda del content

El content no se envia en el init ni en los updates del WebSocket. Solo se
carga cuando el usuario expande un evento:

1. Click en expandir -> envio {"action":"get_content","event_id":N}
2. Servidor consulta SELECT content FROM events WHERE id = N
3. Respuesta {"type":"content","event_id":N,"content":"..."}
4. Dashboard renderiza en un pre con scroll

## Tests

- Tests de activity-capture.py: cada dispatcher, generacion de summary,
  exclusion de rutas, deteccion de comandos triviales
- Tests de migracion: schema v3 -> v4 sin perdida de datos
- Tests del WebSocket: accion get_content
