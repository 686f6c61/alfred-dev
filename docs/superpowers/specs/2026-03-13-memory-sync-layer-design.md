# Capa de sincronizacion SQLite a memoria nativa de Claude Code

## Resumen

Modulo que proyecta los datos de `alfred-memory.db` (SQLite) a ficheros `.md` con el formato nativo de Claude Code en `~/.claude/projects/<hash>/memory/`. SQLite es la fuente de verdad; los ficheros `.md` son proyecciones de lectura que Claude carga automaticamente en cada conversacion.

## Decisiones de diseno

| Decision | Opcion elegida | Alternativas descartadas |
|----------|---------------|--------------------------|
| Trigger de sincronizacion | Hibrido: regeneracion completa en session-start + incremental en cada escritura | Solo en escritura (riesgo de inconsistencia), solo en session-start (datos obsoletos) |
| Que se proyecta | Todo curado: decisiones activas + iteracion activa + ultimos commits + resumen narrativo | Solo decisiones (pierde contexto), decisiones + iteracion (pierde commits) |
| Organizacion de ficheros | Plano con prefijo `alfred-` en `memory/` | Subdirectorio `memory/alfred/` (anade profundidad innecesaria) |
| Ciclo de vida de decisiones | Archivo consolidado: activas en ficheros individuales, no activas en un unico `alfred-decisions-archived.md` | Borrar (pierde historial), mantener con marca (acumula ficheros) |

## Arquitectura

```
SQLite (fuente de verdad)
    |
    | lee
    v
MemorySync (proyector)
    |
    | escribe
    v
~/.claude/projects/<hash>/memory/
    alfred-decision-<id>.md
    alfred-decisions-archived.md
    alfred-iteration-active.md
    alfred-commits-recent.md
    alfred-summary.md
    MEMORY.md (seccion delimitada por marcadores)
```

## Componente central: MemorySync

### Interfaz publica

```python
class MemorySync:
    def __init__(self, db: MemoryDB, memory_dir: str): ...

    # Sincronizacion completa (session-start)
    def sync_all(self) -> SyncResult: ...

    # Sincronizacion incremental (post-escritura)
    def sync_decision(self, decision_id: int) -> None: ...
    def sync_iteration(self) -> None: ...
    def sync_commits(self, limit: int = 10) -> None: ...
    def sync_summary(self) -> None: ...

    # Gestion del indice
    def update_index(self) -> None: ...

    # Limpieza
    def cleanup_stale(self) -> list[str]: ...
```

### Resolucion de memory_dir

Busca en `~/.claude/projects/` un directorio cuyo nombre sea el path del proyecto actual con barras convertidas a guiones (convencion de Claude Code). Si no existe, lo crea.

## Formato de ficheros proyectados

### Decision activa (alfred-decision-<id>.md)

```markdown
---
name: "D#<id>: <titulo>"
description: "<chosen> -- decision de <phase> con impacto <impact>"
type: project
source: alfred-memory
source_id: <id>
---

## Contexto
<context>

## Opcion elegida
<chosen>

## Alternativas descartadas
- <alternativa 1>
- <alternativa 2>

## Razonamiento
<rationale>

**Impacto:** <impact> | **Fase:** <phase> | **Tags:** <tags> | **Fecha:** <decided_at>
```

### Decisiones archivadas (alfred-decisions-archived.md)

```markdown
---
name: "Decisiones archivadas de Alfred"
description: "Decisiones supersedidas o deprecadas -- contexto historico consultable"
type: project
source: alfred-memory
---

## D#<id> -- <titulo> (<status>)
**Elegida:** <chosen>
**Sustituida por:** D#<linked_id> (si aplica)
**Fecha:** <decided_at>

---
```

Formato condensado por decision. Sin contexto completo (para eso esta SQLite).

### Iteracion activa (alfred-iteration-active.md)

```markdown
---
name: "Iteracion activa: <command> #<id>"
description: "<description> -- fase actual: <fase>"
type: project
source: alfred-memory
---

**Comando:** <command>
**Descripcion:** <description>
**Estado:** activa desde <started_at>
**Fase actual:** <fase>

### Fases completadas
| Fase | Resultado | Fecha |
|------|-----------|-------|
| <nombre> | <resultado> | <fecha> |
```

Si no hay iteracion activa, el fichero no se genera o se borra.

### Commits recientes (alfred-commits-recent.md)

```markdown
---
name: "Ultimos commits registrados"
description: "Los N commits mas recientes vinculados a iteraciones de Alfred"
type: project
source: alfred-memory
---

| SHA | Mensaje | Autor | Fecha | Ficheros |
|-----|---------|-------|-------|----------|
| <sha_corto> | <message> | <author> | <date> | <files_changed> |
```

Limite configurable, por defecto 10.

### Resumen narrativo (alfred-summary.md)

```markdown
---
name: "Resumen del proyecto (Alfred)"
description: "Estado actual del proyecto con estadisticas y decisiones clave"
type: project
source: alfred-memory
---

El proyecto tiene <N> decisiones activas y <M> archivadas.
La iteracion actual es "<command>: <description>", en fase de <fase>.
Se han registrado <K> commits en <J> iteraciones.

### Decisiones clave vigentes
- **D#<id> -- <titulo>:** <chosen_resumido>
```

Generado con plantillas y datos, no con IA.

## Gestion de MEMORY.md

El sincronizador gestiona un bloque delimitado por marcadores HTML:

```markdown
<!-- ALFRED-SYNC:START -->
## Memoria persistente (Alfred)

- [alfred-summary.md](alfred-summary.md) -- estado actual del proyecto
- [alfred-iteration-active.md](alfred-iteration-active.md) -- iteracion en curso
- [alfred-decision-<id>.md](alfred-decision-<id>.md) -- <titulo>
- [alfred-commits-recent.md](alfred-commits-recent.md) -- ultimos commits
- [alfred-decisions-archived.md](alfred-decisions-archived.md) -- decisiones historicas
<!-- ALFRED-SYNC:END -->
```

Reglas:
- Si los marcadores no existen, se anaden al final del fichero.
- Si MEMORY.md no existe, se crea con solo la seccion de Alfred.
- El contenido fuera de los marcadores NUNCA se modifica.

## Puntos de integracion

### Session-start (regeneracion completa)

En `session-start.sh`, despues de verificar que memoria esta habilitada:

```bash
python3 "$PLUGIN_ROOT/core/memory_sync.py" --action sync_all --project-dir "$PWD"
```

### PostToolUse (sincronizacion incremental)

En `activity-capture.py`, despues de cada escritura a SQLite:

- Tras `log_decision()`: sync_decision + sync_summary + update_index
- Tras `log_commit()`: sync_commits + sync_summary + update_index
- Tras `start/complete_iteration()`: sync_iteration + sync_summary + update_index

## Limpieza de ficheros huerfanos

`cleanup_stale()` compara ficheros `alfred-*.md` en disco contra IDs activos en SQLite:

- Fichero de decision cuyo ID ya no es `active` -> borrar (la decision esta en el archivo consolidado)
- Fichero de iteracion activa sin iteracion activa en DB -> borrar
- Ficheros sin `source: alfred-memory` en frontmatter -> nunca tocar

## Manejo de errores

Politica fail-open (igual que el resto de hooks de Alfred):

- No puede resolver memory_dir -> log warning, no sincroniza
- No puede escribir fichero -> log warning, continua con el siguiente
- MEMORY.md no existe -> lo crea
- Marcadores no existen -> los anade al final
- SQLite sin datos -> no genera ficheros, limpia los que hubiera
- Nunca lanza excepciones al caller

## Configuracion

Campos nuevos en `.claude/alfred-dev.local.md`:

```yaml
memoria:
  enabled: true
  sync_to_native: true        # proyectar a .md nativos (defecto: true si enabled)
  sync_commits_limit: 10      # commits recientes a proyectar
```

## Ficheros a crear o modificar

| Fichero | Accion | Contenido |
|---------|--------|-----------|
| core/memory_sync.py | Crear | Clase MemorySync completa |
| hooks/activity-capture.py | Modificar | Llamadas a sync incremental |
| hooks/session-start.sh | Modificar | Llamada a sync_all() |
| core/memory.py | No tocar | MemoryDB no cambia |
| mcp/memory_server.py | No tocar | MCP server no cambia |

## Restricciones

- Sincronizacion unidireccional: SQLite -> .md (nunca al reves)
- No toca ficheros .md sin `source: alfred-memory` en frontmatter
- No genera contenido con IA (plantillas + datos)
- No modifica el esquema de SQLite (cero migraciones)
