# Memoria persistente de decisiones -- diseno v1

**Fecha:** 2026-02-20
**Estado:** aprobado
**Version objetivo:** 0.2.0

---

## 1. Objetivo

Dotar al plugin Alfred Dev de memoria persistente por proyecto. El sistema conserva
decisiones, eventos del flujo de trabajo y metadatos de commits entre sesiones,
permitiendo trazabilidad completa (problema -> decision -> commit -> validacion)
sin depender de conversaciones efimeras ni diffs sin contexto.

La memoria es una capa lateral opcional que no modifica el core del plugin. Si no se
activa, el flujo sigue igual que hoy.

---

## 2. Decisiones de diseno

Estas decisiones se tomaron durante el brainstorming del 2026-02-20:

| Decision | Elegido | Alternativas descartadas | Rationale |
|----------|---------|--------------------------|-----------|
| Acceso a DB | API Python en `core/memory.py` + MCP server como interfaz | Bash + sqlite3, MCP directo sin core | Testabilidad (pytest) + experiencia nativa para agentes. Fallback via python3 -c si MCP no disponible. |
| Ubicacion DB | `.claude/alfred-memory.db` | `.alfred/memory.db`, `~/.claude/memory/<hash>.db` | Coherente con el ecosistema actual (.claude/alfred-dev.local.md, .claude/alfred-dev-state.json). Ya protegido por .gitignore. |
| Captura de datos | Hook automatico (eventos) + Alfred explicito (decisiones) | Solo orquestador, solo agente | Los hechos mecanicos se capturan solos (fiable). Las decisiones con juicio las registra quien tiene contexto (Alfred). Cero cambios en orchestrator.py. |
| Tipo de agente | Bibliotecario como agente opcional | Agente de nucleo, capacidad de Alfred | Prompt especializado para consultas. Si esta desactivado, cero overhead. Separacion de responsabilidades con Alfred. |
| MCP server | Proceso persistente stdio | Script bajo demanda | Claude Code gestiona el ciclo de vida. Conexion SQLite reutilizable durante la sesion. Patron estandar de MCP servers. |
| SonarQube | Excluido de v1 | Incluir tabla y logica | Esquema extensible para v2 pero sin implementacion ni tabla en v1. |

---

## 3. Arquitectura de componentes

### 3.1 Componentes nuevos

```
core/memory.py                API Python pura (sqlite3 stdlib)
  |
  +---> mcp/memory_server.py  MCP server stdio persistente
  |       (expone herramientas al agente)
  |
  +---> hooks/memory-capture.py  Hook PostToolUse/Write
  |       (captura automatica de eventos del flujo)
  |
  +---> session-start.sh         Modificacion minima
          (inyecta resumen de memoria al contexto)

agents/optional/librarian.md     Agente El Bibliotecario
```

### 3.2 Componentes existentes sin cambios

- `core/orchestrator.py` -- sin modificaciones
- `core/config_loader.py` -- solo se anade la seccion `memoria` a los defaults
- `agents/alfred.md` -- se anaden unas lineas al prompt para que sepa delegar al Bibliotecario
- `hooks/hooks.json` -- se registra el nuevo hook `memory-capture.py`

### 3.3 Flujo de datos

```
Usuario ejecuta /alfred feature "..."
  |
  v
Alfred crea sesion (orchestrator.save_state)
  |
  v
[Hook memory-capture.py] detecta escritura en alfred-dev-state.json
  |  -> memory.log_event(event_type="iteration_started", ...)
  |  -> memory.start_iteration(command, description)
  v
Alfred avanza fases, toma decisiones
  |
  +---> Alfred llama a memory_log_decision (MCP) cuando hay decision relevante
  |
  +---> [Hook memory-capture.py] registra phase_completed en cada avance
  |
  v
Iteracion completada
  |
  v
[Hook memory-capture.py] registra iteration_completed
  |
  v
Proxima sesion: session-start.sh inyecta resumen de memoria
```

---

## 4. Esquema de datos (v1)

SQLite con WAL activado. Versionado con campo `schema_version` en tabla `meta`.

### 4.1 Tabla `meta`

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| key | TEXT PK | Clave de configuracion |
| value | TEXT | Valor serializado |

Claves iniciales: `schema_version` (1), `fts_enabled` (0/1), `created_at`, `project_path`.

### 4.2 Tabla `iterations`

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | INTEGER PK | Autoincremental |
| command | TEXT NOT NULL | feature/fix/audit/ship/spike |
| description | TEXT | Descripcion del usuario |
| status | TEXT NOT NULL | active/completed/abandoned |
| started_at | TEXT NOT NULL | ISO 8601 UTC |
| completed_at | TEXT | NULL si activa |
| phases_completed | TEXT | JSON array |
| artifacts | TEXT | JSON array |

### 4.3 Tabla `decisions`

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | INTEGER PK | Autoincremental |
| iteration_id | INTEGER FK | -> iterations |
| title | TEXT NOT NULL | Titulo corto |
| context | TEXT | Problema que se resolvia |
| chosen | TEXT NOT NULL | Opcion elegida |
| alternatives | TEXT | JSON array de descartadas |
| rationale | TEXT | Justificacion |
| impact | TEXT | low/medium/high/critical |
| phase | TEXT | Fase del flujo |
| decided_at | TEXT NOT NULL | ISO 8601 UTC |

### 4.4 Tabla `commits`

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | INTEGER PK | Autoincremental |
| sha | TEXT UNIQUE NOT NULL | SHA del commit |
| message | TEXT | Mensaje |
| author | TEXT | Autor |
| files_changed | INTEGER | Ficheros modificados |
| insertions | INTEGER | Lineas anadidas |
| deletions | INTEGER | Lineas eliminadas |
| committed_at | TEXT NOT NULL | ISO 8601 UTC |
| iteration_id | INTEGER FK | -> iterations (nullable) |

### 4.5 Tabla `commit_links`

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| commit_id | INTEGER FK | -> commits |
| decision_id | INTEGER FK | -> decisions |
| link_type | TEXT | implements/reverts/relates |

PK compuesta: (commit_id, decision_id).

### 4.6 Tabla `events`

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | INTEGER PK | Autoincremental |
| iteration_id | INTEGER FK | -> iterations |
| event_type | TEXT NOT NULL | phase_completed/gate_passed/gate_failed/user_approved/... |
| phase | TEXT | Fase del evento |
| payload | TEXT | JSON con datos extra |
| created_at | TEXT NOT NULL | ISO 8601 UTC |

### 4.7 Tabla virtual `memory_fts` (solo si FTS5)

Indexa texto de `decisions` (title, context, chosen, rationale) y `commits` (message).
Se actualiza con triggers `AFTER INSERT` y `AFTER UPDATE`.
Si no hay FTS5, se usa `LIKE %termino%` como fallback.

### 4.8 Indices

- `idx_iterations_status` en `iterations(status)`
- `idx_decisions_iteration` en `decisions(iteration_id)`
- `idx_commits_iteration` en `commits(iteration_id)`
- `idx_events_iteration` en `events(iteration_id)`
- `idx_events_type` en `events(event_type)`

---

## 5. MCP server

### 5.1 Configuracion

Fichero `.claude-plugin/mcp.json`:

```json
{
  "mcpServers": {
    "alfred-memory": {
      "type": "stdio",
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/memory_server.py"],
      "env": {
        "ALFRED_MEMORY_DB": ".claude/alfred-memory.db"
      }
    }
  }
}
```

### 5.2 Herramientas expuestas

| Herramienta | Descripcion | Parametros |
|-------------|-------------|------------|
| `memory_search` | Busqueda textual en decisiones y commits | query, limit?, iteration_id? |
| `memory_log_decision` | Registra decision formal | title, context, chosen, alternatives?, rationale?, impact?, phase? |
| `memory_log_commit` | Registra commit y lo vincula | sha, message?, decision_ids?, iteration_id? |
| `memory_get_iteration` | Detalle de iteracion | id? (ultima si omitido) |
| `memory_get_timeline` | Cronologia de eventos | iteration_id |
| `memory_stats` | Estadisticas generales | (sin parametros) |

### 5.3 Ciclo de vida

Claude Code lanza el proceso al inicio de sesion y lo mantiene vivo. Al arrancar,
el server:
1. Resuelve la ruta de la DB (relativa al $PWD del proyecto)
2. Abre conexion SQLite con WAL
3. Ejecuta `ensure_schema()` (crea tablas si es primera vez, migra si esquema antiguo)
4. Ejecuta `detect_fts5()` y registra resultado en `meta`
5. Queda a la escucha de invocaciones MCP

---

## 6. Agente Bibliotecario

### 6.1 Perfil

| Campo | Valor |
|-------|-------|
| Nombre interno | `librarian` |
| Alias | El Bibliotecario |
| Modelo | sonnet |
| Color | Ambar/dorado |
| Tipo | Agente opcional |
| Herramientas | MCP memory_* + Read |

### 6.2 Reglas del prompt

- Siempre citar la fuente (ID de decision, SHA de commit, fecha, iteracion)
- Si hay ambiguedad, devolver top 3 resultados con explicacion del ranking
- Nunca responder sin consultar la DB primero
- Clasificar preguntas: decision (que/por que), implementacion (que commit), cronologia (cuando), estadistica (cuantas)

### 6.3 Personalidad

Archivista riguroso. Nivel de sarcasmo configurable con `personalidad.nivel_sarcasmo`.
En nivel 1: formal y preciso. En nivel 5: erudito que recuerda cuantas veces se ha
revertido la misma decision.

### 6.4 Integracion con Alfred

Alfred delega al Bibliotecario cuando:
- El usuario hace preguntas historicas
- Al inicio de un flujo feature/fix, para contextualizar con decisiones previas relacionadas

Se consigue anadiendo instrucciones al prompt de Alfred, sin tocar codigo.

---

## 7. Activacion y onboarding

### 7.1 Configuracion en alfred-dev.local.md

```yaml
memoria:
  enabled: true
  capture_decisions: true
  capture_commits: true
  retention_days: 365
  search_mode: auto    # auto | fts5 | basic
```

### 7.2 Flujo de onboarding

1. Usuario activa `memoria.enabled: true` via `/alfred config`
2. Siguiente sesion: `session-start.sh` detecta config pero no DB
3. Alfred ve el mensaje e invoca `memory_stats` (que crea la DB)
4. MCP server crea esquema, detecta FTS5, informa resultado
5. Alfred comunica al usuario el estado (modo, capacidades)

### 7.3 Matriz de decision

| SQLite | FTS5 | Resultado |
|--------|------|-----------|
| Si | Si | Modo completo: FTS5 + todas las tablas |
| Si | No | Modo basico: LIKE + todas las tablas (aviso) |
| No | - | Error + guia de instalacion |

### 7.4 Desactivacion

`memoria.enabled: false` desactiva captura, consultas y agente. La DB se mantiene
intacta. Borrado manual si el usuario lo desea.

---

## 8. Seguridad y gobierno

### 8.1 Sanitizacion

`sanitize_content()` en `core/memory.py` aplica los mismos regex de `secret-guard.sh`
antes de persistir texto. Patrones detectados se reemplazan por `[REDACTED:<tipo>]`.

Campos sanitizados: `decisions.context`, `decisions.chosen`, `decisions.rationale`,
`decisions.alternatives`, `commits.message`, `events.payload`.

### 8.2 Retencion

- Eventos: se purgan tras `retention_days` al arrancar el MCP server
- Decisiones e iteraciones: no se purgan (alto valor)
- Commits: no se purgan (necesarios para trazabilidad)
- Borrado completo: manual por el usuario

### 8.3 Integridad

- Transacciones explicitas (`BEGIN IMMEDIATE ... COMMIT`)
- WAL activado
- Foreign keys activadas (`PRAGMA foreign_keys = ON`)
- Permisos del fichero: 0600

### 8.4 Aviso de .gitignore

Si `.claude/` no esta en `.gitignore`, `session-start.sh` emite un aviso al contexto.

---

## 9. Fases de implementacion

### Fase 1: base operativa
- `core/memory.py` con MemoryDB, esquema, migraciones, sanitizacion
- `mcp/memory_server.py` con las 6 herramientas
- `hooks/memory-capture.py` para captura automatica de eventos
- `agents/optional/librarian.md` con prompt completo
- Modificacion de `session-start.sh` para inyeccion de contexto
- Configuracion en `config_loader.py` (seccion `memoria`)
- Tests unitarios en `tests/test_memory.py`

### Fase 2: trazabilidad con commits
- Captura de metadatos de commits
- Tabla `commit_links` funcional
- Vinculacion automatica commit -> iteracion activa
- Vinculacion explicita commit -> decision via Alfred

### Fase 3: optimizaciones y SonarQube (futura)
- Tabla `sonar_snapshots` y captura de metricas
- Comparacion entre iteraciones
- Reportes automaticos y metricas de aprendizaje

---

## 10. Criterios de aceptacion (v1)

1. **Respuesta con evidencia**: preguntar "que decidimos sobre X" devuelve registros
   verificables (ID, fecha, iteracion), no inferencias.
2. **Localizacion de commits**: encontrar commits por tema funcional, no solo por
   mensaje literal.
3. **Degradacion sin FTS5**: el sistema funciona en modo basico si FTS5 no esta disponible.
4. **Cero impacto desactivado**: con `memoria.enabled: false`, el flujo actual no cambia.
5. **Onboarding automatico**: la primera sesion con memoria activa configura todo sin
   intervencion manual mas alla de activar la opcion.
6. **Sanitizacion efectiva**: ningun secreto se persiste en la DB.

---

## 11. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Ruido en captura | Media | Media | Esquema minimo estricto, captura solo en eventos relevantes |
| Crecimiento descontrolado de DB | Baja | Media | Retencion configurable, purga de eventos, indices |
| Entorno sin SQLite | Baja | Alta | Onboarding con deteccion real y guia de instalacion |
| Respuestas incorrectas por ranking | Media | Baja | Exigir evidencia, devolver multiples candidatos |
| MCP server no soportado por version de Claude Code | Baja | Alta | Fallback via python3 -c para consultas basicas |
