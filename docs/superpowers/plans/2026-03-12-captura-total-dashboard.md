# Captura total y dashboard humanizado -- plan de implementacion

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development
> (if subagents available) or superpowers:executing-plans to implement this plan.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir la DB de memoria en fuente de verdad completa de toda la
actividad del plugin (prompts, contenido de ficheros, salida de comandos) y
humanizar el dashboard para que muestre texto legible en vez de JSON crudo.

**Architecture:** Un hook centralizado (`activity-capture.py`) reemplaza a
`memory-capture.py` y `commit-capture.py`, capturando todos los eventos con
contenido completo y un `summary` en lenguaje natural. La DB se migra a schema
v4 con columnas `summary` y `content`. El dashboard se simplifica: muestra
summaries, elimina el panel de agentes, y carga el content bajo demanda.

**Tech Stack:** Python 3.10+ stdlib (sqlite3, json, re, os), HTML/JS vanilla.

**Spec:** `docs/superpowers/specs/2026-03-12-captura-total-dashboard-design.md`

---

## Estructura de ficheros

| Accion | Fichero | Responsabilidad |
|--------|---------|-----------------|
| Crear | `hooks/activity-capture.py` | Dispatcher centralizado de captura |
| Crear | `tests/test_activity_capture.py` | Tests del dispatcher |
| Modificar | `core/memory.py:41,58-97,776-821` | Schema v4 + log_event con summary/content |
| Modificar | `hooks/hooks.json` | Reorganizar hooks para activity-capture |
| Modificar | `gui/server.py:182-250,434-515` | Accion get_content + excluir content de init |
| Modificar | `gui/dashboard.html` | Timeline humanizada + eliminar panel agentes |
| Eliminar | `hooks/memory-capture.py` | Absorbido por activity-capture |
| Eliminar | `hooks/commit-capture.py` | Absorbido por activity-capture |
| Modificar | `tests/test_memory_capture.py` | Adaptar o eliminar (cubierto por test_activity_capture) |
| Modificar | `tests/test_commit_capture.py` | Adaptar o eliminar (cubierto por test_activity_capture) |

---

## Chunk 1: DB y core

### Tarea 1: Migrar schema a v4 (summary + content)

**Files:**
- Modify: `core/memory.py:41,58-97`
- Test: `tests/test_memory.py` (o test existente de migraciones)

- [ ] **Paso 1: Incrementar _SCHEMA_VERSION a 4 y anadir migracion**

En `core/memory.py`, cambiar:

```python
_SCHEMA_VERSION = 4
```

Anadir la migracion 3 -> 4 en `_MIGRATIONS`:

```python
3: [
    # v3 -> v4: columnas summary y content para captura total
    "ALTER TABLE events ADD COLUMN summary TEXT",
    "ALTER TABLE events ADD COLUMN content TEXT",
],
```

- [ ] **Paso 2: Actualizar CREATE TABLE events en _SCHEMA_SQL**

Anadir las dos columnas al final de la definicion de la tabla `events`:

```sql
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id  INTEGER REFERENCES iterations(id),
    event_type    TEXT    NOT NULL,
    phase         TEXT,
    payload       TEXT,
    summary       TEXT,
    content       TEXT,
    created_at    TEXT    NOT NULL
);
```

- [ ] **Paso 3: Verificar migracion con test manual**

```bash
cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred"
python3 -c "
import sys; sys.path.insert(0, '.')
from core.memory import MemoryDB
db = MemoryDB('.claude/alfred-memory.db')
# Verificar que las columnas existen
cols = [r[1] for r in db._conn.execute('PRAGMA table_info(events)').fetchall()]
assert 'summary' in cols, 'Falta columna summary'
assert 'content' in cols, 'Falta columna content'
print('Migracion OK: summary y content presentes')
db.close()
"
```

- [ ] **Paso 4: Ejecutar tests completos**

```bash
python3 -m pytest tests/ -v
```

Esperado: todos los tests pasan (las columnas nuevas tienen DEFAULT NULL).

---

### Tarea 2: Ampliar log_event para aceptar summary y content

**Files:**
- Modify: `core/memory.py:776-821`

- [ ] **Paso 1: Anadir parametros summary y content a log_event**

```python
def log_event(
    self,
    event_type: str,
    phase: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    summary: Optional[str] = None,
    content: Optional[str] = None,
    iteration_id: Optional[int] = None,
) -> int:
```

- [ ] **Paso 2: Sanitizar y persistir los nuevos campos**

Actualizar el INSERT para incluir summary y content:

```python
# Sanitizar summary y content
sanitized_summary = sanitize_content(summary) if summary else None
sanitized_content = sanitize_content(content) if content else None

cursor = self._conn.execute(
    "INSERT INTO events "
    "(iteration_id, event_type, phase, payload, summary, content, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)",
    (iteration_id, event_type, phase, payload_json,
     sanitized_summary, sanitized_content, now),
)
```

- [ ] **Paso 3: Indexar content en FTS si esta habilitado**

Despues del INSERT, si `self._fts_enabled` y `sanitized_content`:

```python
if self._fts_enabled and sanitized_content:
    self._conn.execute(
        "INSERT INTO memory_fts (source_type, source_id, content) "
        "VALUES (?, ?, ?)",
        ("event", cursor.lastrowid, sanitized_content),
    )
```

- [ ] **Paso 4: Ejecutar tests**

```bash
python3 -m pytest tests/ -v
```

---

## Chunk 2: Hook centralizado

### Tarea 3: Crear activity-capture.py

**Files:**
- Create: `hooks/activity-capture.py`

- [ ] **Paso 1: Crear el esqueleto con main() y dispatcher**

```python
#!/usr/bin/env python3
"""
Hook centralizado de captura de actividad para la memoria de Alfred Dev.

Registra en la base de datos de memoria TODA la actividad relevante de la
sesion: ficheros escritos/editados (con contenido completo), comandos Bash
(con salida completa), prompts del usuario, compactaciones de contexto y
cierres de sesion.

Cada evento se guarda con tres niveles de detalle:
    - summary: texto legible en lenguaje natural para el dashboard.
    - payload: metadatos estructurados (JSON) para filtrado y busqueda.
    - content: contenido completo sin truncar para consulta bajo demanda.
"""

import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, Optional, Tuple
```

El main() lee stdin, identifica el tipo de hook por el JSON de entrada, y
despacha al metodo correspondiente:

```python
def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[activity-capture] Aviso: entrada invalida: {e}", file=sys.stderr)
        sys.exit(0)

    if not _is_memory_enabled():
        sys.exit(0)

    # Determinar tipo de evento por la estructura del JSON
    hook_event = data.get("hook_event_name", "")
    tool_name = data.get("tool_name", "")

    dispatcher = _DISPATCHERS.get(hook_event) or _DISPATCHERS.get(tool_name)
    if dispatcher is None:
        sys.exit(0)

    db = _open_db()
    if db is None:
        sys.exit(0)

    try:
        dispatcher(db, data)
    except Exception as e:
        print(f"[activity-capture] Aviso: {e}", file=sys.stderr)
    finally:
        db.close()

    sys.exit(0)
```

- [ ] **Paso 2: Implementar _dispatch_write**

Captura el contenido completo del fichero escrito. Si es state.json, ejecuta
ademas la logica de fases (migrada de memory-capture.py).

```python
def _dispatch_write(db, data: dict) -> None:
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path or _is_excluded_path(file_path):
        return

    project_dir = os.getcwd()
    rel_path = _relative_path(file_path, project_dir)
    _, ext = os.path.splitext(file_path)
    ext_clean = ext.lstrip(".") if ext else ""

    # Leer contenido completo del fichero recien escrito
    file_content = _read_file_safe(file_path)
    line_count = file_content.count("\n") if file_content else 0

    summary = f"Escrito {rel_path} ({line_count} lineas, {ext_clean or 'sin extension'})"

    db.log_event(
        event_type="file_written",
        summary=summary,
        payload={"file": rel_path, "extension": ext_clean, "lines": line_count},
        content=file_content,
    )

    # Logica especifica de state.json
    if file_path.endswith("alfred-dev-state.json"):
        _process_state(db, file_path)
```

- [ ] **Paso 3: Implementar _dispatch_edit**

```python
def _dispatch_edit(db, data: dict) -> None:
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path or _is_excluded_path(file_path):
        return

    rel_path = _relative_path(file_path, os.getcwd())
    _, ext = os.path.splitext(file_path)
    ext_clean = ext.lstrip(".") if ext else ""

    old_string = tool_input.get("old_string", "")
    new_string = tool_input.get("new_string", "")
    old_lines = old_string.count("\n") + 1 if old_string else 0
    new_lines = new_string.count("\n") + 1 if new_string else 0

    summary = f"Editado {rel_path}: {old_lines} lineas reemplazadas por {new_lines}"

    # El content guarda el diff completo (old + new)
    content = f"--- old ---\n{old_string}\n--- new ---\n{new_string}"

    db.log_event(
        event_type="file_edited",
        summary=summary,
        payload={"file": rel_path, "extension": ext_clean,
                 "old_lines": old_lines, "new_lines": new_lines},
        content=content,
    )
```

- [ ] **Paso 4: Implementar _dispatch_bash**

```python
_GIT_COMMIT_RE = re.compile(r"(?:^|&&|\|\||;)\s*git\s+commit\b")

_TRIVIAL_COMMANDS = frozenset({
    "ls", "pwd", "cd", "echo", "cat", "head", "tail", "less", "more",
    "wc", "whoami", "date", "which", "where", "type", "file", "true",
    "false", "clear", "history", "env", "printenv", "set", "export",
    "alias", "unalias", "source", ".", "test", "[",
})

def _dispatch_bash(db, data: dict) -> None:
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", {})

    command = tool_input.get("command", "")
    if not command or _is_trivial_command(command):
        return

    exit_code = tool_result.get("exit_code")
    stdout = tool_result.get("stdout", "") or tool_result.get("output", "")
    stderr = tool_result.get("stderr", "")

    # Generar summary legible
    cmd_short = command[:80] + "..." if len(command) > 80 else command
    exit_str = f"exit {exit_code}" if exit_code is not None else "sin exit code"
    # Extraer primera linea significativa del stdout para el summary
    first_line = _first_meaningful_line(stdout)
    summary_parts = [f"Ejecutado: {cmd_short} -- {exit_str}"]
    if first_line:
        summary_parts.append(first_line)
    summary = ", ".join(summary_parts)

    # Content: stdout + stderr completos
    content_parts = []
    if stdout:
        content_parts.append(f"--- stdout ---\n{stdout}")
    if stderr:
        content_parts.append(f"--- stderr ---\n{stderr}")
    content = "\n".join(content_parts) if content_parts else None

    db.log_event(
        event_type="command_executed",
        summary=summary,
        payload={"command": command, "exit_code": exit_code},
        content=content,
    )

    # Enriquecimiento git commit
    if _GIT_COMMIT_RE.search(command) and exit_code == 0:
        _capture_git_commit(db)
```

- [ ] **Paso 5: Implementar _dispatch_prompt**

```python
def _dispatch_prompt(db, data: dict) -> None:
    # UserPromptSubmit envia el texto del prompt en el campo "prompt"
    prompt_text = data.get("prompt", "") or data.get("content", "")
    if not prompt_text:
        return

    # Summary: primera linea truncada a 100 chars
    first_line = prompt_text.split("\n")[0][:100]
    summary = f"Prompt: {first_line}"
    if len(prompt_text) > len(first_line):
        summary += "..."

    db.log_event(
        event_type="user_prompt",
        summary=summary,
        payload={"length": len(prompt_text)},
        content=prompt_text,
    )
```

- [ ] **Paso 6: Implementar _dispatch_compact y _dispatch_stop**

```python
def _dispatch_compact(db, data: dict) -> None:
    summary = "Contexto compactado -- los mensajes anteriores se han resumido"
    db.log_event(
        event_type="context_compacted",
        summary=summary,
        payload={"source": "PreCompact"},
    )

def _dispatch_stop(db, data: dict) -> None:
    summary = "Sesion finalizada"
    db.log_event(
        event_type="session_ended",
        summary=summary,
        payload={"source": "Stop"},
    )
    # Cerrar iteracion activa si existe
    active = db.get_active_iteration()
    if active:
        db.complete_iteration(active["id"])
```

- [ ] **Paso 7: Implementar funciones auxiliares**

Funciones reutilizadas: `_is_memory_enabled`, `_is_excluded_path`,
`_is_trivial_command`, `_open_db`, `_relative_path`, `_read_file_safe`,
`_first_meaningful_line`, `_process_state` (migrada de memory-capture.py),
`_capture_git_commit` (migrada de commit-capture.py).

La tabla de dispatcher:

```python
_DISPATCHERS = {
    "Write": _dispatch_write,
    "Edit": _dispatch_edit,
    "Bash": _dispatch_bash,
    "UserPromptSubmit": _dispatch_prompt,
    "PreCompact": _dispatch_compact,
    "Stop": _dispatch_stop,
}
```

- [ ] **Paso 8: Verificar sintaxis**

```bash
python3 -c "import py_compile; py_compile.compile('hooks/activity-capture.py', doraise=True)"
```

---

### Tarea 4: Tests de activity-capture.py

**Files:**
- Create: `tests/test_activity_capture.py`

- [ ] **Paso 1: Tests de _is_excluded_path**

Cubrir: .claude/, .git/, node_modules/, __pycache__, .venv/, ficheros normales.
(Migrar los tests existentes de test_memory_capture.py::TestIsExcludedPath)

- [ ] **Paso 2: Tests de _is_trivial_command**

Cubrir: ls, pwd, cd, echo, cat, head, npm install, git push, python3, docker,
variables de entorno, rutas absolutas.
(Migrar los tests existentes de test_commit_capture.py::TestIsTrivialCommand)

- [ ] **Paso 3: Tests de _dispatch_write**

Cubrir: fichero normal genera file_written con summary legible y content completo;
fichero excluido no genera evento; state.json genera evento + logica de fases.

- [ ] **Paso 4: Tests de _dispatch_edit**

Cubrir: edit genera file_edited con old/new en content; summary contiene lineas.

- [ ] **Paso 5: Tests de _dispatch_bash**

Cubrir: comando relevante genera command_executed con stdout completo en content;
comando trivial no genera evento; git commit genera log_commit adicional.

- [ ] **Paso 6: Tests de _dispatch_prompt**

Cubrir: prompt se guarda completo en content; summary trunca a primera linea.

- [ ] **Paso 7: Tests de _dispatch_compact y _dispatch_stop**

Cubrir: compact genera context_compacted; stop cierra iteracion activa.

- [ ] **Paso 8: Ejecutar tests completos**

```bash
python3 -m pytest tests/ -v
```

---

### Tarea 5: Reorganizar hooks.json y eliminar hooks obsoletos

**Files:**
- Modify: `hooks/hooks.json`
- Delete: `hooks/memory-capture.py`
- Delete: `hooks/commit-capture.py`
- Modify: `tests/test_memory_capture.py` -> eliminar o redirigir
- Modify: `tests/test_commit_capture.py` -> eliminar o redirigir

- [ ] **Paso 1: Actualizar hooks.json**

Reemplazar las entradas de memory-capture.py y commit-capture.py por
activity-capture.py. Anadir entradas para UserPromptSubmit, PreCompact y Stop.

- [ ] **Paso 2: Eliminar hooks/memory-capture.py y hooks/commit-capture.py**

- [ ] **Paso 3: Eliminar o redirigir tests obsoletos**

Los tests de test_memory_capture.py::TestProcessState se migran a
test_activity_capture.py. Los ficheros de test antiguos se eliminan.

- [ ] **Paso 4: Ejecutar tests completos**

```bash
python3 -m pytest tests/ -v
```

---

## Chunk 3: Dashboard

### Tarea 6: Servidor -- accion get_content y excluir content de init/update

**Files:**
- Modify: `gui/server.py:182-250` (get_full_state)
- Modify: `gui/server.py:434-515` (handle_ws_client)

- [ ] **Paso 1: Excluir content de get_full_state**

En las queries de eventos dentro de `get_full_state()`, seleccionar todas las
columnas excepto `content`. Anadir `summary` al resultado.

- [ ] **Paso 2: Excluir content de las queries del watcher**

En `watch_loop()`, las queries incrementales tampoco deben incluir `content`.

- [ ] **Paso 3: Implementar accion get_content en handle_ws_client**

Cuando el cliente envia `{"action":"get_content","event_id":N}`:

```python
if action == "get_content":
    event_id = msg_data.get("event_id")
    row = self._poll_conn.execute(
        "SELECT content FROM events WHERE id = ?", (event_id,)
    ).fetchone()
    content = row[0] if row else None
    response = json.dumps({
        "type": "content",
        "event_id": event_id,
        "content": content,
    })
    writer.write(encode_frame(response))
    await writer.drain()
```

- [ ] **Paso 4: Verificar sintaxis**

```bash
python3 -c "import py_compile; py_compile.compile('gui/server.py', doraise=True)"
```

---

### Tarea 7: Dashboard HTML -- timeline humanizada

**Files:**
- Modify: `gui/dashboard.html`

- [ ] **Paso 1: Eliminar panel de agentes**

Eliminar la seccion completa del panel de agentes (HTML + JS + CSS asociado).
Eliminar el boton/tab de "Agentes" de la navegacion.

- [ ] **Paso 2: Humanizar timeline**

Modificar la funcion de renderizado de eventos para:
- Mostrar `summary` como texto principal (fallback a `event_type` si no hay summary)
- Mostrar icono segun event_type: fichero, terminal, prompt, commit, sistema
- Anadir boton [v] que expanda/colapse el content
- Al expandir, enviar peticion get_content por WebSocket y renderizar en un pre

- [ ] **Paso 3: Actualizar filtros**

Reemplazar los filtros actuales por:
- Todos / Ficheros / Comandos / Prompts / Decisiones / Commits / Sistema

- [ ] **Paso 4: Humanizar panel de memoria**

En la tabla del explorador, mostrar `summary` como columna principal en vez
del `payload` JSON. El payload y content quedan en el detalle expandible.

- [ ] **Paso 5: Verificar visualmente**

Abrir el dashboard en el navegador y comprobar que:
- La timeline muestra texto legible
- Los filtros funcionan
- El boton de expandir carga el content
- No hay panel de agentes

---

### Tarea 8: Verificacion final

- [ ] **Paso 1: Ejecutar suite completa de tests**

```bash
python3 -m pytest tests/ -v
```

- [ ] **Paso 2: Probar flujo end-to-end**

Arrancar servidor GUI, hacer Write/Edit/Bash y verificar que:
- Los eventos aparecen con summary legible en la timeline
- El content se carga al expandir
- Los prompts se capturan (si UserPromptSubmit funciona)

- [ ] **Paso 3: Limpiar evento test_event de la DB**

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('.claude/alfred-memory.db')
conn.execute(\"DELETE FROM events WHERE event_type = 'test_event'\")
conn.commit()
conn.close()
"
```
