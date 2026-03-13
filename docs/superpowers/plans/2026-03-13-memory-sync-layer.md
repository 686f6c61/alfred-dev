# Capa de sincronizacion SQLite a memoria nativa - plan de implementacion

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Proyectar automaticamente los datos de `alfred-memory.db` a ficheros `.md` nativos de Claude Code para que las decisiones, iteraciones y commits sean visibles sin necesidad de MCP ni Bibliotecario.

**Architecture:** Nuevo modulo `core/memory_sync.py` con clase `MemorySync` que lee de `MemoryDB` y escribe ficheros `.md` con frontmatter YAML. Sincronizacion hibrida: regeneracion completa en session-start + incremental tras cada escritura a SQLite. Gestion segura de `MEMORY.md` via marcadores HTML.

**Tech Stack:** Python 3 stdlib (pathlib, re, json, os), MemoryDB existente, pytest para tests.

---

## Chunk 1: Modulo core/memory_sync.py - estructura base y resolucion de rutas

### Task 1: Resolucion de memory_dir y estructura base de MemorySync

**Files:**
- Create: `core/memory_sync.py`
- Create: `tests/test_memory_sync.py`

- [ ] **Step 1: Escribir el test de resolucion de memory_dir**

```python
# tests/test_memory_sync.py
"""Tests para la capa de sincronizacion SQLite -> memoria nativa."""

import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_env(tmp_path):
    """Crea un entorno temporal con DB de memoria y directorio de proyectos."""
    # Directorio del proyecto simulado
    project_dir = tmp_path / "mi-proyecto"
    project_dir.mkdir()

    # Directorio .claude con DB
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()

    # Directorio de memoria nativa de Claude Code
    # Simula ~/.claude/projects/<hash>/memory/
    projects_dir = tmp_path / ".claude" / "projects"
    memory_dir = projects_dir / "-mi-proyecto" / "memory"
    memory_dir.mkdir(parents=True)

    return {
        "project_dir": str(project_dir),
        "claude_dir": str(claude_dir),
        "projects_dir": str(projects_dir),
        "memory_dir": str(memory_dir),
        "db_path": str(claude_dir / "alfred-memory.db"),
    }


def test_resolve_memory_dir_existente(temp_env):
    """Encuentra el directorio de memoria cuando ya existe."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from core.memory_sync import resolve_memory_dir

    result = resolve_memory_dir(
        temp_env["project_dir"],
        temp_env["projects_dir"],
    )
    assert result is not None
    assert result.endswith("memory")
    assert os.path.isdir(result)


def test_resolve_memory_dir_no_existe(tmp_path):
    """Devuelve None si no existe el directorio de proyectos."""
    from core.memory_sync import resolve_memory_dir

    result = resolve_memory_dir(
        str(tmp_path / "proyecto-fantasma"),
        str(tmp_path / "no-existe"),
    )
    assert result is None
```

- [ ] **Step 2: Ejecutar test para verificar que falla**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python -m pytest tests/test_memory_sync.py -v`
Expected: FAIL con "ModuleNotFoundError" o "ImportError"

- [ ] **Step 3: Implementar resolve_memory_dir y esqueleto de MemorySync**

```python
# core/memory_sync.py
"""
Capa de sincronizacion SQLite a memoria nativa de Claude Code.

Proyecta los datos de alfred-memory.db a ficheros .md con el formato nativo
de Claude Code (frontmatter YAML con name/description/type + contenido).
SQLite es la fuente de verdad; los ficheros .md son proyecciones de lectura
que Claude carga automaticamente en cada conversacion.

La sincronizacion es unidireccional (SQLite -> .md) y nunca modifica la
base de datos. Los ficheros generados se identifican por la clave
``source: alfred-memory`` en su frontmatter, lo que permite distinguirlos
de las memorias escritas manualmente por el usuario.

Componentes principales:
    - resolve_memory_dir(): localiza el directorio de memoria nativa.
    - MemorySync: clase que orquesta la proyeccion de datos.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Importacion condicional de MemoryDB para permitir uso standalone
try:
    from core.memory import MemoryDB
except ImportError:
    MemoryDB = None  # type: ignore[misc,assignment]


# Marcadores que delimitan la seccion gestionada en MEMORY.md.
# El contenido entre estos marcadores se regenera en cada sincronizacion;
# todo lo que quede fuera nunca se modifica.
_SYNC_START = "<!-- ALFRED-SYNC:START -->"
_SYNC_END = "<!-- ALFRED-SYNC:END -->"

# Prefijo de los ficheros generados. Permite identificarlos para limpieza
# sin tener que leer el frontmatter de cada uno.
_FILE_PREFIX = "alfred-"

# Clave en el frontmatter YAML que identifica ficheros generados por
# este modulo. Solo se modifican/borran ficheros con esta clave.
_SOURCE_KEY = "alfred-memory"

# Prefijo para mensajes de log en stderr.
_LOG_PREFIX = "[memory-sync]"


def resolve_memory_dir(
    project_dir: str,
    projects_base: Optional[str] = None,
) -> Optional[str]:
    """
    Localiza el directorio de memoria nativa de Claude Code para un proyecto.

    Claude Code almacena la memoria de cada proyecto en un directorio cuyo
    nombre es el path absoluto del proyecto con las barras (/) sustituidas
    por guiones (-). Esta funcion busca ese directorio dentro de la base
    de proyectos de Claude Code.

    Args:
        project_dir: ruta absoluta del proyecto actual.
        projects_base: ruta al directorio ``~/.claude/projects/``. Si no se
            proporciona, se calcula a partir de ``$HOME``.

    Returns:
        Ruta absoluta al directorio ``memory/`` si existe, o None si no se
        encuentra el directorio del proyecto.
    """
    if projects_base is None:
        home = os.path.expanduser("~")
        projects_base = os.path.join(home, ".claude", "projects")

    if not os.path.isdir(projects_base):
        return None

    # Convencion de Claude Code: el path absoluto con / -> -
    # Ejemplo: /Users/foo/proyecto -> -Users-foo-proyecto
    normalized = project_dir.replace(os.sep, "-")
    if not normalized.startswith("-"):
        normalized = "-" + normalized

    # Buscar coincidencia en los directorios existentes
    try:
        entries = os.listdir(projects_base)
    except OSError:
        return None

    for entry in entries:
        if entry == normalized:
            memory_path = os.path.join(projects_base, entry, "memory")
            if os.path.isdir(memory_path):
                return memory_path

    return None


class MemorySync:
    """
    Proyecta datos de alfred-memory.db a ficheros .md nativos de Claude Code.

    Lee de una instancia de MemoryDB (sin modificarla) y escribe ficheros
    Markdown con frontmatter YAML en el directorio de memoria nativa. Los
    ficheros generados llevan ``source: alfred-memory`` en el frontmatter
    para distinguirlos de las memorias manuales del usuario.

    Politica de errores: fail-open. Ningun error de escritura bloquea el
    flujo ni lanza excepciones al caller. Los problemas se registran en
    stderr con el prefijo ``[memory-sync]``.

    Args:
        db: instancia de MemoryDB ya conectada (solo lectura).
        memory_dir: ruta absoluta al directorio ``memory/`` de Claude Code.
        commits_limit: numero maximo de commits recientes a proyectar.
    """

    def __init__(
        self,
        db: "MemoryDB",
        memory_dir: str,
        commits_limit: int = 10,
    ) -> None:
        self._db = db
        self._memory_dir = memory_dir
        self._commits_limit = commits_limit

    # --- Sincronizacion completa ---------------------------------------------

    def sync_all(self) -> Dict[str, Any]:
        """
        Regenera todas las proyecciones desde cero.

        Ejecuta la sincronizacion completa: decisiones activas, archivo de
        decisiones, iteracion activa, commits recientes, resumen narrativo
        e indice MEMORY.md. Limpia ficheros huerfanos al final.

        Returns:
            Diccionario con contadores de ficheros escritos, borrados y errores.
        """
        result = {"written": 0, "deleted": 0, "errors": 0}

        for method in (
            self._sync_decisions,
            self._sync_archived,
            self.sync_iteration,
            self.sync_commits,
            self.sync_summary,
        ):
            try:
                method()
                result["written"] += 1
            except Exception as e:
                _log(f"Error en {method.__name__}: {e}")
                result["errors"] += 1

        deleted = self.cleanup_stale()
        result["deleted"] = len(deleted)

        try:
            self.update_index()
        except Exception as e:
            _log(f"Error actualizando indice: {e}")
            result["errors"] += 1

        return result

    # --- Sincronizacion incremental ------------------------------------------

    def sync_decision(self, decision_id: int) -> None:
        """
        Proyecta una decision individual.

        Si la decision es activa, genera/actualiza su fichero individual.
        Si no es activa, la elimina del fichero individual y regenera el
        archivo consolidado.

        Args:
            decision_id: ID de la decision a sincronizar.
        """
        decisions = self._db.get_decisions(limit=1000)
        decision = None
        for d in decisions:
            if d["id"] == decision_id:
                decision = d
                break

        if decision is None:
            return

        if decision.get("status", "active") == "active":
            self._write_decision_file(decision)
        else:
            # Borrar fichero individual si existia
            path = self._decision_path(decision_id)
            _safe_delete(path)
            # Regenerar archivo consolidado
            self._sync_archived()

    def sync_iteration(self) -> None:
        """Proyecta el estado de la iteracion activa."""
        active = self._db.get_active_iteration()
        path = os.path.join(self._memory_dir, "alfred-iteration-active.md")

        if active is None:
            _safe_delete(path)
            return

        # Obtener fases completadas desde eventos
        events = self._db.get_timeline(active["id"])
        phases = []
        for ev in events:
            if ev.get("event_type") == "phase_completed":
                payload_raw = ev.get("payload")
                if payload_raw:
                    try:
                        payload = (
                            json.loads(payload_raw)
                            if isinstance(payload_raw, str)
                            else payload_raw
                        )
                        phases.append({
                            "nombre": payload.get("fase", ""),
                            "resultado": payload.get("resultado", ""),
                            "fecha": payload.get(
                                "completada_en",
                                ev.get("created_at", "")[:10],
                            ),
                        })
                    except (json.JSONDecodeError, AttributeError):
                        pass

        # Determinar fase actual
        fase_actual = "en curso"
        if phases:
            fase_actual = f"tras {phases[-1]['nombre']}"

        command = active.get("command", "desconocido")
        description = active.get("description", "")
        started = active.get("started_at", "")[:10]

        content = _frontmatter(
            name=f"Iteracion activa: {command} #{active['id']}",
            description=f"{description} -- fase actual: {fase_actual}",
        )
        content += f"\n**Comando:** {command}\n"
        content += f"**Descripcion:** {description}\n"
        content += f"**Estado:** activa desde {started}\n"
        content += f"**Fase actual:** {fase_actual}\n"

        if phases:
            content += "\n### Fases completadas\n\n"
            content += "| Fase | Resultado | Fecha |\n"
            content += "|------|-----------|-------|\n"
            for p in phases:
                content += f"| {p['nombre']} | {p['resultado']} | {p['fecha']} |\n"

        _safe_write(path, content)

    def sync_commits(self, limit: Optional[int] = None) -> None:
        """
        Proyecta los commits mas recientes.

        Args:
            limit: numero de commits a proyectar. Si no se especifica,
                usa el valor configurado en el constructor.
        """
        if limit is None:
            limit = self._commits_limit

        path = os.path.join(self._memory_dir, "alfred-commits-recent.md")

        # Obtener commits recientes via SQL directo (MemoryDB no tiene
        # un metodo get_commits con limit global, asi que usamos la conexion)
        try:
            rows = self._db._conn.execute(
                "SELECT sha, message, author, files_changed, committed_at "
                "FROM commits ORDER BY committed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        except Exception:
            rows = []

        if not rows:
            _safe_delete(path)
            return

        content = _frontmatter(
            name="Ultimos commits registrados",
            description=f"Los {limit} commits mas recientes vinculados a iteraciones de Alfred",
        )
        content += "\n| SHA | Mensaje | Autor | Fecha | Ficheros |\n"
        content += "|-----|---------|-------|-------|----------|\n"
        for row in rows:
            sha_short = row["sha"][:7] if row["sha"] else "?"
            msg = row["message"] or ""
            author = row["author"] or ""
            date = (row["committed_at"] or "")[:10]
            files = row["files_changed"] or 0
            content += f"| {sha_short} | {msg} | {author} | {date} | {files} |\n"

        _safe_write(path, content)

    def sync_summary(self) -> None:
        """Genera el fichero de resumen narrativo con estadisticas y decisiones clave."""
        path = os.path.join(self._memory_dir, "alfred-summary.md")
        stats = self._db.get_stats()

        total_decisions = stats.get("total_decisions", 0)
        total_commits = stats.get("total_commits", 0)
        total_iterations = stats.get("total_iterations", 0)

        # Contar decisiones activas y archivadas
        active_decisions = self._db.get_decisions(status="active", limit=1000)
        n_active = len(active_decisions)
        n_archived = total_decisions - n_active

        content = _frontmatter(
            name="Resumen del proyecto (Alfred)",
            description="Estado actual del proyecto con estadisticas y decisiones clave",
        )

        content += f"\nEl proyecto tiene {n_active} decisiones activas"
        if n_archived > 0:
            content += f" y {n_archived} archivadas"
        content += ".\n"

        # Iteracion activa
        active_iter = self._db.get_active_iteration()
        if active_iter:
            cmd = active_iter.get("command", "?")
            desc = active_iter.get("description", "")
            content += (
                f'La iteracion actual es "{cmd}: {desc}".\n'
            )

        content += (
            f"Se han registrado {total_commits} commits "
            f"en {total_iterations} iteraciones.\n"
        )

        # Decisiones clave
        if active_decisions:
            content += "\n### Decisiones clave vigentes\n\n"
            for d in active_decisions[:10]:
                title = d.get("title", "sin titulo")
                chosen = d.get("chosen", "")
                # Truncar chosen a 80 chars para el resumen
                if len(chosen) > 80:
                    chosen = chosen[:77] + "..."
                content += f"- **D#{d['id']} -- {title}:** {chosen}\n"

        _safe_write(path, content)

    # --- Gestion del indice --------------------------------------------------

    def update_index(self) -> None:
        """
        Actualiza la seccion delimitada de MEMORY.md con los ficheros proyectados.

        Busca los marcadores ALFRED-SYNC:START/END en MEMORY.md y reescribe
        solo el contenido entre ellos. Si no existen, los anade al final.
        Si MEMORY.md no existe, lo crea con la seccion de Alfred.
        """
        memory_md = os.path.join(self._memory_dir, "MEMORY.md")

        # Construir el bloque de sincronizacion
        lines = [_SYNC_START, "## Memoria persistente (Alfred)", ""]
        alfred_files = self._list_alfred_files()

        for filename, description in alfred_files:
            lines.append(f"- [{filename}]({filename}) -- {description}")

        lines.append(_SYNC_END)
        sync_block = "\n".join(lines) + "\n"

        # Leer MEMORY.md existente o crear nuevo
        existing = ""
        if os.path.isfile(memory_md):
            try:
                with open(memory_md, "r", encoding="utf-8") as f:
                    existing = f.read()
            except OSError:
                pass

        if _SYNC_START in existing and _SYNC_END in existing:
            # Reemplazar bloque existente
            pattern = re.compile(
                re.escape(_SYNC_START) + r".*?" + re.escape(_SYNC_END),
                re.DOTALL,
            )
            updated = pattern.sub(sync_block.strip(), existing)
        elif existing:
            # Anadir al final
            updated = existing.rstrip() + "\n\n" + sync_block
        else:
            # MEMORY.md no existe: crear con seccion Alfred
            updated = sync_block

        _safe_write(memory_md, updated)

    # --- Limpieza ------------------------------------------------------------

    def cleanup_stale(self) -> List[str]:
        """
        Elimina ficheros alfred-*.md que ya no corresponden a datos activos.

        Compara los ficheros con prefijo alfred- en disco contra los IDs
        activos en SQLite. Solo elimina ficheros con ``source: alfred-memory``
        en el frontmatter.

        Returns:
            Lista de rutas de ficheros eliminados.
        """
        deleted: List[str] = []
        active_ids = set()
        for d in self._db.get_decisions(status="active", limit=1000):
            active_ids.add(d["id"])

        try:
            entries = os.listdir(self._memory_dir)
        except OSError:
            return deleted

        for entry in entries:
            if not entry.startswith(_FILE_PREFIX):
                continue
            if entry == "MEMORY.md":
                continue

            full_path = os.path.join(self._memory_dir, entry)

            # Solo tocar ficheros que nosotros generamos
            if not _is_alfred_file(full_path):
                continue

            # Ficheros de decision: comprobar si el ID sigue activo
            if entry.startswith("alfred-decision-") and entry != "alfred-decisions-archived.md":
                try:
                    # Extraer ID del nombre: alfred-decision-14.md -> 14
                    id_str = entry.replace("alfred-decision-", "").replace(".md", "")
                    decision_id = int(id_str)
                    if decision_id not in active_ids:
                        _safe_delete(full_path)
                        deleted.append(full_path)
                except (ValueError, IndexError):
                    pass
                continue

            # Fichero de iteracion activa: comprobar si hay iteracion activa
            if entry == "alfred-iteration-active.md":
                if self._db.get_active_iteration() is None:
                    _safe_delete(full_path)
                    deleted.append(full_path)

        return deleted

    # --- Metodos privados ----------------------------------------------------

    def _sync_decisions(self) -> None:
        """Genera ficheros individuales para cada decision activa."""
        decisions = self._db.get_decisions(status="active", limit=1000)
        for d in decisions:
            self._write_decision_file(d)

    def _sync_archived(self) -> None:
        """Genera el fichero consolidado de decisiones archivadas."""
        path = os.path.join(self._memory_dir, "alfred-decisions-archived.md")

        # Obtener decisiones no activas
        all_decisions = self._db.get_decisions(limit=1000)
        archived = [d for d in all_decisions if d.get("status") != "active"]

        if not archived:
            _safe_delete(path)
            return

        content = _frontmatter(
            name="Decisiones archivadas de Alfred",
            description="Decisiones supersedidas o deprecadas -- contexto historico consultable",
        )

        for d in archived:
            title = d.get("title", "sin titulo")
            status = d.get("status", "?")
            chosen = d.get("chosen", "")
            date = (d.get("decided_at") or "")[:10]
            content += f"\n## D#{d['id']} -- {title} ({status})\n\n"
            content += f"**Elegida:** {chosen}\n"

            # Buscar si hay una decision que la sustituye
            links = self._db.get_decision_links(d["id"])
            for link in links:
                if link.get("link_type") == "supersedes" and link.get("source_id") != d["id"]:
                    content += f"**Sustituida por:** D#{link['source_id']}\n"
                    break

            content += f"**Fecha:** {date}\n\n---\n"

        _safe_write(path, content)

    def _write_decision_file(self, decision: Dict[str, Any]) -> None:
        """Escribe un fichero .md para una decision individual."""
        path = self._decision_path(decision["id"])

        impact = decision.get("impact", "")
        phase = decision.get("phase", "")
        chosen = decision.get("chosen", "")

        desc_parts = [chosen]
        if phase:
            desc_parts.append(f"decision de {phase}")
        if impact:
            desc_parts.append(f"con impacto {impact}")

        content = _frontmatter(
            name=f"D#{decision['id']}: {decision.get('title', 'sin titulo')}",
            description=" -- ".join(desc_parts),
            source_id=decision["id"],
        )

        # Contexto
        context = decision.get("context")
        if context:
            content += f"\n## Contexto\n\n{context}\n"

        # Opcion elegida
        content += f"\n## Opcion elegida\n\n{chosen}\n"

        # Alternativas
        alt_raw = decision.get("alternatives")
        if alt_raw:
            try:
                alts = json.loads(alt_raw) if isinstance(alt_raw, str) else alt_raw
                if alts:
                    content += "\n## Alternativas descartadas\n\n"
                    for alt in alts:
                        content += f"- {alt}\n"
            except (json.JSONDecodeError, TypeError):
                pass

        # Razonamiento
        rationale = decision.get("rationale")
        if rationale:
            content += f"\n## Razonamiento\n\n{rationale}\n"

        # Metadatos
        tags_raw = decision.get("tags", "[]")
        try:
            tags = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
            tags_str = ", ".join(tags) if tags else ""
        except (json.JSONDecodeError, TypeError):
            tags_str = ""

        date = (decision.get("decided_at") or "")[:10]
        meta_parts = []
        if impact:
            meta_parts.append(f"**Impacto:** {impact}")
        if phase:
            meta_parts.append(f"**Fase:** {phase}")
        if tags_str:
            meta_parts.append(f"**Tags:** {tags_str}")
        meta_parts.append(f"**Fecha:** {date}")

        content += "\n" + " | ".join(meta_parts) + "\n"

        _safe_write(path, content)

    def _decision_path(self, decision_id: int) -> str:
        """Devuelve la ruta del fichero .md para una decision."""
        return os.path.join(
            self._memory_dir, f"alfred-decision-{decision_id}.md"
        )

    def _list_alfred_files(self) -> List[Tuple[str, str]]:
        """
        Lista los ficheros alfred-*.md con su descripcion para el indice.

        Returns:
            Lista de tuplas (nombre_fichero, descripcion) ordenada:
            resumen primero, iteracion, decisiones, commits, archivo.
        """
        result: List[Tuple[str, str]] = []

        # Orden fijo para ficheros conocidos
        order = [
            ("alfred-summary.md", "estado actual del proyecto"),
            ("alfred-iteration-active.md", "iteracion en curso"),
        ]

        for filename, desc in order:
            if os.path.isfile(os.path.join(self._memory_dir, filename)):
                result.append((filename, desc))

        # Decisiones activas (orden por ID)
        decision_files = []
        try:
            for entry in sorted(os.listdir(self._memory_dir)):
                if entry.startswith("alfred-decision-") and entry != "alfred-decisions-archived.md":
                    # Leer titulo del frontmatter
                    full = os.path.join(self._memory_dir, entry)
                    title = _read_frontmatter_field(full, "name") or entry
                    decision_files.append((entry, title))
        except OSError:
            pass
        result.extend(decision_files)

        # Commits
        commits_file = "alfred-commits-recent.md"
        if os.path.isfile(os.path.join(self._memory_dir, commits_file)):
            result.append((commits_file, "ultimos commits"))

        # Archivo de decisiones
        archived_file = "alfred-decisions-archived.md"
        if os.path.isfile(os.path.join(self._memory_dir, archived_file)):
            n = _count_archived(os.path.join(self._memory_dir, archived_file))
            result.append((archived_file, f"{n} decisiones historicas"))

        return result


# ---------------------------------------------------------------------------
# Funciones auxiliares (nivel de modulo)
# ---------------------------------------------------------------------------

def _frontmatter(
    name: str,
    description: str,
    source_id: Optional[int] = None,
) -> str:
    """Genera el bloque de frontmatter YAML para un fichero de memoria nativa."""
    lines = [
        "---",
        f'name: "{name}"',
        f'description: "{description}"',
        "type: project",
        f"source: {_SOURCE_KEY}",
    ]
    if source_id is not None:
        lines.append(f"source_id: {source_id}")
    lines.append("---\n")
    return "\n".join(lines)


def _safe_write(path: str, content: str) -> bool:
    """Escribe un fichero de forma segura, sin lanzar excepciones."""
    try:
        parent = os.path.dirname(path)
        os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except OSError as e:
        _log(f"No se pudo escribir {path}: {e}")
        return False


def _safe_delete(path: str) -> bool:
    """Elimina un fichero de forma segura, sin lanzar excepciones."""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except OSError as e:
        _log(f"No se pudo eliminar {path}: {e}")
    return False


def _is_alfred_file(path: str) -> bool:
    """Comprueba si un fichero fue generado por este modulo."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            # Leer solo las primeras 10 lineas para buscar el frontmatter
            for i, line in enumerate(f):
                if i > 10:
                    break
                if f"source: {_SOURCE_KEY}" in line:
                    return True
    except OSError:
        pass
    return False


def _read_frontmatter_field(path: str, field: str) -> Optional[str]:
    """Lee un campo del frontmatter YAML de un fichero."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            in_frontmatter = False
            for line in f:
                stripped = line.strip()
                if stripped == "---":
                    if in_frontmatter:
                        break
                    in_frontmatter = True
                    continue
                if in_frontmatter and stripped.startswith(f"{field}:"):
                    value = stripped[len(field) + 1:].strip()
                    # Quitar comillas
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    return value
    except OSError:
        pass
    return None


def _count_archived(path: str) -> int:
    """Cuenta las decisiones en el fichero de archivo consolidado."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content.count("## D#")
    except OSError:
        return 0


def _log(msg: str) -> None:
    """Imprime un mensaje de aviso en stderr."""
    import sys
    print(f"{_LOG_PREFIX} {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Punto de entrada CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """Permite invocar la sincronizacion desde shell (session-start.sh)."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Sincroniza memoria SQLite a ficheros .md nativos"
    )
    parser.add_argument("--action", required=True, choices=["sync_all"])
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--commits-limit", type=int, default=10)
    args = parser.parse_args()

    # Resolver rutas
    db_path = os.path.join(args.project_dir, ".claude", "alfred-memory.db")
    if not os.path.isfile(db_path):
        sys.exit(0)

    memory_dir = resolve_memory_dir(args.project_dir)
    if memory_dir is None:
        print(
            f"{_LOG_PREFIX} No se encontro directorio de memoria nativa",
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from memory import MemoryDB

        db = MemoryDB(db_path)
        sync = MemorySync(db, memory_dir, commits_limit=args.commits_limit)

        if args.action == "sync_all":
            result = sync.sync_all()
            print(
                f"{_LOG_PREFIX} sync_all: "
                f"{result['written']} escritos, "
                f"{result['deleted']} borrados, "
                f"{result['errors']} errores",
                file=sys.stderr,
            )

        db.close()
    except Exception as e:
        print(f"{_LOG_PREFIX} Error: {e}", file=sys.stderr)
        sys.exit(0)  # fail-open
```

- [ ] **Step 4: Ejecutar tests para verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python -m pytest tests/test_memory_sync.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred"
git add core/memory_sync.py tests/test_memory_sync.py
git commit -m "feat: modulo base memory_sync con resolucion de rutas"
```

---

### Task 2: Tests de proyeccion de decisiones

**Files:**
- Modify: `tests/test_memory_sync.py`
- (core/memory_sync.py ya creado en Task 1)

- [ ] **Step 1: Escribir tests de proyeccion de decisiones**

```python
# Anadir a tests/test_memory_sync.py

@pytest.fixture
def sync_env(temp_env):
    """Crea un entorno con MemoryDB poblada y MemorySync listo."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from core.memory import MemoryDB
    from core.memory_sync import MemorySync

    db = MemoryDB(temp_env["db_path"])

    # Crear iteracion y decisiones de prueba
    iter_id = db.start_iteration(command="feature", description="Sistema de cache")

    d1_id = db.log_decision(
        title="Cache con Redis",
        chosen="Redis por latencia sub-ms",
        context="Necesitamos cache para reducir latencia",
        alternatives=["Memcached", "Cache en memoria"],
        rationale="Redis ofrece TTL nativo y persistencia opcional",
        impact="high",
        phase="arquitectura",
        tags=["cache", "infra"],
        iteration_id=iter_id,
    )

    d2_id = db.log_decision(
        title="Autenticacion con sesiones",
        chosen="Sesiones server-side",
        context="Requisitos de compliance",
        alternatives=["JWT"],
        rationale="Compliance exige revocacion inmediata",
        impact="critical",
        phase="arquitectura",
        tags=["auth", "security"],
        iteration_id=iter_id,
    )

    sync = MemorySync(db, temp_env["memory_dir"])

    return {
        **temp_env,
        "db": db,
        "sync": sync,
        "iter_id": iter_id,
        "d1_id": d1_id,
        "d2_id": d2_id,
    }


def test_sync_decision_genera_fichero(sync_env):
    """sync_decision genera un fichero .md con frontmatter correcto."""
    sync = sync_env["sync"]
    d1_id = sync_env["d1_id"]

    sync.sync_decision(d1_id)

    path = os.path.join(sync_env["memory_dir"], f"alfred-decision-{d1_id}.md")
    assert os.path.isfile(path)

    with open(path, "r") as f:
        content = f.read()

    assert "source: alfred-memory" in content
    assert f"source_id: {d1_id}" in content
    assert "Cache con Redis" in content
    assert "Redis por latencia sub-ms" in content
    assert "Memcached" in content


def test_sync_decision_archivada_no_genera_fichero(sync_env):
    """Una decision supersedida no genera fichero individual."""
    db = sync_env["db"]
    sync = sync_env["sync"]
    d1_id = sync_env["d1_id"]

    db.update_decision_status(d1_id, "superseded")
    sync.sync_decision(d1_id)

    path = os.path.join(sync_env["memory_dir"], f"alfred-decision-{d1_id}.md")
    assert not os.path.isfile(path)

    # Pero si debe estar en el archivo consolidado
    archived = os.path.join(sync_env["memory_dir"], "alfred-decisions-archived.md")
    assert os.path.isfile(archived)
    with open(archived, "r") as f:
        content = f.read()
    assert f"D#{d1_id}" in content
    assert "superseded" in content


def test_sync_all_genera_todos_los_ficheros(sync_env):
    """sync_all genera todos los ficheros esperados."""
    sync = sync_env["sync"]

    result = sync.sync_all()

    assert result["errors"] == 0
    assert result["written"] > 0

    memory_dir = sync_env["memory_dir"]
    assert os.path.isfile(os.path.join(memory_dir, "alfred-summary.md"))
    assert os.path.isfile(os.path.join(memory_dir, "alfred-iteration-active.md"))
    assert os.path.isfile(os.path.join(memory_dir, f"alfred-decision-{sync_env['d1_id']}.md"))
    assert os.path.isfile(os.path.join(memory_dir, f"alfred-decision-{sync_env['d2_id']}.md"))


def test_update_index_con_marcadores(sync_env):
    """update_index gestiona la seccion delimitada en MEMORY.md."""
    sync = sync_env["sync"]
    memory_dir = sync_env["memory_dir"]

    # Crear MEMORY.md con contenido manual previo
    memory_md = os.path.join(memory_dir, "MEMORY.md")
    with open(memory_md, "w") as f:
        f.write("# Mi proyecto\n\nContenido manual que no debe tocarse.\n")

    # Sincronizar todo
    sync.sync_all()

    with open(memory_md, "r") as f:
        content = f.read()

    # El contenido manual debe seguir intacto
    assert "Contenido manual que no debe tocarse." in content
    # Los marcadores deben existir
    assert "<!-- ALFRED-SYNC:START -->" in content
    assert "<!-- ALFRED-SYNC:END -->" in content
    # Los ficheros alfred deben estar referenciados
    assert "alfred-summary.md" in content


def test_update_index_reemplaza_bloque_existente(sync_env):
    """Una segunda sincronizacion reemplaza el bloque, no lo duplica."""
    sync = sync_env["sync"]
    memory_dir = sync_env["memory_dir"]
    memory_md = os.path.join(memory_dir, "MEMORY.md")

    # Primera sync
    sync.sync_all()
    # Segunda sync
    sync.sync_all()

    with open(memory_md, "r") as f:
        content = f.read()

    assert content.count("<!-- ALFRED-SYNC:START -->") == 1
    assert content.count("<!-- ALFRED-SYNC:END -->") == 1


def test_cleanup_stale_borra_huerfanos(sync_env):
    """cleanup_stale elimina ficheros de decisiones ya no activas."""
    sync = sync_env["sync"]
    db = sync_env["db"]
    memory_dir = sync_env["memory_dir"]
    d1_id = sync_env["d1_id"]

    # Sincronizar todo (genera ficheros para d1 y d2)
    sync.sync_all()
    assert os.path.isfile(os.path.join(memory_dir, f"alfred-decision-{d1_id}.md"))

    # Marcar d1 como superseded
    db.update_decision_status(d1_id, "superseded")

    # Limpiar
    deleted = sync.cleanup_stale()

    # El fichero de d1 debe haber sido borrado
    assert not os.path.isfile(os.path.join(memory_dir, f"alfred-decision-{d1_id}.md"))
    assert len(deleted) == 1


def test_cleanup_no_toca_ficheros_manuales(sync_env):
    """cleanup_stale no borra ficheros sin source: alfred-memory."""
    sync = sync_env["sync"]
    memory_dir = sync_env["memory_dir"]

    # Crear un fichero manual con prefijo alfred-
    manual = os.path.join(memory_dir, "alfred-notas-personales.md")
    with open(manual, "w") as f:
        f.write("Mis notas sobre el proyecto.\n")

    deleted = sync.cleanup_stale()
    assert os.path.isfile(manual)
    assert manual not in deleted
```

- [ ] **Step 2: Ejecutar tests para verificar que pasan**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python -m pytest tests/test_memory_sync.py -v`
Expected: PASS (todos los tests)

- [ ] **Step 3: Commit**

```bash
cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred"
git add tests/test_memory_sync.py
git commit -m "test: tests de proyeccion de decisiones, indice y limpieza"
```

---

## Chunk 2: Integracion con hooks existentes

### Task 3: Integrar sync incremental en activity-capture.py

**Files:**
- Modify: `hooks/activity-capture.py` (lineas 194-227 para _open_db, lineas 311-460 para _process_state y _capture_git_commit)

- [ ] **Step 1: Anadir funcion auxiliar _sync_after para sincronizacion incremental**

Anadir al final de la seccion de funciones auxiliares de `hooks/activity-capture.py` (despues de `_read_file_safe`, antes de `_build_dispatcher_table`):

```python
def _try_sync(db, action: str, **kwargs) -> None:
    """Ejecuta una sincronizacion incremental si esta habilitada.

    Intenta proyectar los cambios a ficheros .md nativos de Claude Code.
    Si falla, continua silenciosamente (fail-open).

    Args:
        db: instancia de MemoryDB.
        action: tipo de sincronizacion (decision, iteration, commits).
        **kwargs: argumentos adicionales para el metodo de sync.
    """
    try:
        from core.memory_sync import MemorySync, resolve_memory_dir

        memory_dir = resolve_memory_dir(os.getcwd())
        if memory_dir is None:
            return

        sync = MemorySync(db, memory_dir)

        if action == "decision":
            sync.sync_decision(kwargs.get("decision_id", 0))
        elif action == "iteration":
            sync.sync_iteration()
        elif action == "commits":
            sync.sync_commits()

        sync.sync_summary()
        sync.update_index()
    except Exception as e:
        print(
            f"{_LOG_PREFIX} Aviso: sync incremental fallida: {e}",
            file=sys.stderr,
        )
```

- [ ] **Step 2: Inyectar llamadas a _try_sync en _process_state**

En `hooks/activity-capture.py`, despues de `db.start_iteration(...)` (linea ~345):

```python
        _try_sync(db, "iteration")
```

Despues de `db.complete_iteration(iteration_id)` (linea ~397):

```python
        _try_sync(db, "iteration")
```

- [ ] **Step 3: Inyectar llamada a _try_sync en _capture_git_commit**

En `hooks/activity-capture.py`, despues de `db.log_commit(...)` (linea ~444):

```python
    _try_sync(db, "commits")
```

- [ ] **Step 4: Ejecutar tests existentes para verificar que no se ha roto nada**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python -m pytest tests/ -v --tb=short`
Expected: PASS (todos los tests)

- [ ] **Step 5: Commit**

```bash
cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred"
git add hooks/activity-capture.py
git commit -m "feat: sincronizacion incremental en activity-capture"
```

---

### Task 4: Integrar sync_all en session-start.sh

**Files:**
- Modify: `hooks/session-start.sh` (despues de la seccion de asegurar BD, ~linea 248)

- [ ] **Step 1: Anadir llamada a sync_all en session-start.sh**

Insertar despues del bloque "Asegurar iteracion activa para el dashboard" (linea ~248) y antes de "Memoria persistente del proyecto" (linea ~250):

```bash
# --- Sincronizacion de memoria a ficheros nativos de Claude Code ---
#
# Proyecta las decisiones, iteraciones y commits de la DB a ficheros .md
# en el directorio de memoria nativa (~/.claude/projects/<hash>/memory/).
# Esto permite que Claude acceda a la memoria del proyecto sin necesidad
# de invocar herramientas MCP ni al Bibliotecario.

if [[ -f "$MEMORY_DB" ]]; then
  PYTHONPATH="${PLUGIN_ROOT}" python3 "${PLUGIN_ROOT}/core/memory_sync.py" \
    --action sync_all \
    --project-dir "$PROJECT_DIR" 2>/dev/null || true
fi
```

- [ ] **Step 2: Verificar que session-start.sh sigue funcionando**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && bash hooks/session-start.sh 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if 'hookSpecificOutput' in d else 'FAIL')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred"
git add hooks/session-start.sh
git commit -m "feat: sincronizacion completa al inicio de sesion"
```

---

### Task 5: Anadir configuracion sync_to_native

**Files:**
- Modify: `hooks/activity-capture.py` (_try_sync debe comprobar la config)
- Modify: `hooks/session-start.sh` (comprobar config antes de sync_all)
- Modify: `core/memory_sync.py` (anadir lectura de config)

- [ ] **Step 1: Anadir lectura de sync_to_native en _try_sync**

En `hooks/activity-capture.py`, al principio de `_try_sync()`:

```python
    # Comprobar si la sincronizacion nativa esta habilitada
    config_path = os.path.join(os.getcwd(), ".claude", "alfred-dev.local.md")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()
        # sync_to_native: false desactiva explicitamente
        if re.search(r"sync_to_native:\s*false", config_content):
            return
    except (OSError, FileNotFoundError):
        pass
```

- [ ] **Step 2: Anadir comprobacion en session-start.sh**

Envolver la llamada a sync_all con una comprobacion:

```bash
if [[ -f "$MEMORY_DB" ]]; then
  # Comprobar si sync_to_native esta desactivado
  SYNC_DISABLED=$(python3 -c "
import re, sys
try:
    with open(sys.argv[1], 'r') as f:
        content = f.read()
    if re.search(r'sync_to_native:\s*false', content):
        print('yes')
except Exception:
    pass
" "$CONFIG_FILE" 2>/dev/null) || SYNC_DISABLED=""

  if [[ "$SYNC_DISABLED" != "yes" ]]; then
    PYTHONPATH="${PLUGIN_ROOT}" python3 "${PLUGIN_ROOT}/core/memory_sync.py" \
      --action sync_all \
      --project-dir "$PROJECT_DIR" 2>/dev/null || true
  fi
fi
```

- [ ] **Step 3: Actualizar la plantilla de config por defecto en session-start.sh**

En la plantilla que crea `.claude/alfred-dev.local.md` (~linea 170), anadir:

```yaml
memoria:
  enabled: true
  sync_to_native: true
  sync_commits_limit: 10
  capture_decisions: true
  capture_commits: true
  retention_days: 365
```

- [ ] **Step 4: Ejecutar todos los tests**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python -m pytest tests/ -v --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred"
git add hooks/activity-capture.py hooks/session-start.sh
git commit -m "feat: configuracion sync_to_native para sincronizacion nativa"
```

---

## Chunk 3: Test de integracion end-to-end

### Task 6: Test de integracion del flujo completo

**Files:**
- Modify: `tests/test_memory_sync.py`

- [ ] **Step 1: Escribir test de integracion end-to-end**

```python
# Anadir a tests/test_memory_sync.py

def test_flujo_completo_e2e(tmp_path):
    """Test end-to-end: crea datos en SQLite y verifica proyeccion completa."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from core.memory import MemoryDB
    from core.memory_sync import MemorySync

    # Setup
    db_path = str(tmp_path / ".claude" / "alfred-memory.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    memory_dir = str(tmp_path / "memory")
    os.makedirs(memory_dir, exist_ok=True)

    # MEMORY.md preexistente con contenido manual
    memory_md = os.path.join(memory_dir, "MEMORY.md")
    with open(memory_md, "w") as f:
        f.write("# Proyecto de prueba\n\nNotas manuales del usuario.\n")

    db = MemoryDB(db_path)
    sync = MemorySync(db, memory_dir)

    # 1. Crear iteracion con decisiones
    iter_id = db.start_iteration(command="feature", description="E2E test")
    d1 = db.log_decision(
        title="Framework web",
        chosen="FastAPI",
        alternatives=["Flask", "Django"],
        rationale="Rendimiento y tipado nativo",
        impact="high",
        phase="arquitectura",
        tags=["backend"],
    )
    d2 = db.log_decision(
        title="Base de datos",
        chosen="PostgreSQL",
        impact="critical",
        phase="arquitectura",
    )
    db.log_commit(sha="abc1234567890", message="feat: setup inicial", author="dev")

    # 2. Sync completo
    result = sync.sync_all()
    assert result["errors"] == 0

    # 3. Verificar ficheros generados
    assert os.path.isfile(os.path.join(memory_dir, f"alfred-decision-{d1}.md"))
    assert os.path.isfile(os.path.join(memory_dir, f"alfred-decision-{d2}.md"))
    assert os.path.isfile(os.path.join(memory_dir, "alfred-summary.md"))
    assert os.path.isfile(os.path.join(memory_dir, "alfred-iteration-active.md"))
    assert os.path.isfile(os.path.join(memory_dir, "alfred-commits-recent.md"))

    # 4. Verificar MEMORY.md mantiene contenido manual
    with open(memory_md, "r") as f:
        index = f.read()
    assert "Notas manuales del usuario." in index
    assert "<!-- ALFRED-SYNC:START -->" in index
    assert "alfred-summary.md" in index

    # 5. Verificar resumen tiene datos correctos
    with open(os.path.join(memory_dir, "alfred-summary.md"), "r") as f:
        summary = f.read()
    assert "2 decisiones activas" in summary
    assert "Framework web" in summary
    assert "PostgreSQL" in summary

    # 6. Archivar una decision y re-sync
    db.update_decision_status(d1, "superseded")
    sync.sync_decision(d1)
    sync.sync_summary()
    sync.update_index()

    # El fichero individual debe desaparecer
    assert not os.path.isfile(os.path.join(memory_dir, f"alfred-decision-{d1}.md"))
    # Pero debe estar en el archivo consolidado
    archived = os.path.join(memory_dir, "alfred-decisions-archived.md")
    assert os.path.isfile(archived)
    with open(archived, "r") as f:
        arch_content = f.read()
    assert "Framework web" in arch_content
    assert "superseded" in arch_content

    # 7. Verificar que el resumen se actualizo
    with open(os.path.join(memory_dir, "alfred-summary.md"), "r") as f:
        summary2 = f.read()
    assert "1 decisiones activas" in summary2

    db.close()
```

- [ ] **Step 2: Ejecutar el test e2e**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python -m pytest tests/test_memory_sync.py::test_flujo_completo_e2e -v`
Expected: PASS

- [ ] **Step 3: Ejecutar suite completa**

Run: `cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred" && python -m pytest tests/ -v --tb=short`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd "/Users/00b/Documents/Claude Code/Plugin-Claude/Alfred"
git add tests/test_memory_sync.py
git commit -m "test: integracion end-to-end del flujo de sincronizacion"
```

---

## Resumen de tareas

| Task | Descripcion | Ficheros | Dependencias |
|------|-------------|----------|-------------|
| 1 | Modulo base memory_sync.py + resolve_memory_dir | core/memory_sync.py, tests/test_memory_sync.py | ninguna |
| 2 | Tests de proyeccion de decisiones, indice y limpieza | tests/test_memory_sync.py | Task 1 |
| 3 | Sync incremental en activity-capture.py | hooks/activity-capture.py | Task 1 |
| 4 | Sync completo en session-start.sh | hooks/session-start.sh | Task 1 |
| 5 | Configuracion sync_to_native | hooks/activity-capture.py, hooks/session-start.sh | Task 3, Task 4 |
| 6 | Test de integracion e2e | tests/test_memory_sync.py | Task 1, Task 2 |
