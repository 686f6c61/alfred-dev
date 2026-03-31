#!/usr/bin/env python3
"""
Capa de sincronizacion SQLite a memoria nativa de Claude Code.

Proyecta los datos de ``alfred-memory.db`` a ficheros ``.md`` con el formato
nativo de Claude Code (frontmatter YAML con name/description/type + contenido).
SQLite es la fuente de verdad; los ficheros ``.md`` son proyecciones de lectura
que Claude carga automaticamente en cada conversacion.

La sincronizacion es unidireccional (SQLite -> .md) y nunca modifica la base
de datos. Los ficheros generados se identifican por la clave
``source: alfred-memory`` en su frontmatter, lo que permite distinguirlos de
las memorias escritas manualmente por el usuario.

Modo de uso:
    - Desde Python: instanciar ``MemorySync`` con una ``MemoryDB`` y un
      directorio de memoria, e invocar ``sync_all()`` o los metodos
      incrementales.
    - Desde shell: ``python3 core/memory_sync.py --action sync_all
      --project-dir /ruta/al/proyecto``.

Componentes principales:
    - ``resolve_memory_dir()``: localiza el directorio de memoria nativa.
    - ``MemorySync``: clase que orquesta la proyeccion de datos.

Politica de errores:
    Fail-open. Ningun error de escritura bloquea el flujo ni lanza excepciones
    al caller. Los problemas se registran en stderr con el prefijo
    ``[memory-sync]``.
"""

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Importacion condicional de MemoryDB para permitir uso standalone.
# Cuando se invoca como script (__main__), se importa despues de ajustar
# sys.path; cuando se importa como modulo, la importacion directa funciona.
try:
    from core.memory import MemoryDB
except ImportError:
    MemoryDB = None  # type: ignore[misc,assignment]

try:
    from core.memory_config import load_memory_config
except ImportError:
    load_memory_config = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Resolucion de rutas
# ---------------------------------------------------------------------------

def resolve_memory_dir(
    project_dir: str,
    projects_base: Optional[str] = None,
) -> Optional[str]:
    """
    Localiza el directorio de memoria nativa de Claude Code para un proyecto.

    Claude Code almacena la memoria de cada proyecto en un directorio cuyo
    nombre es el path absoluto del proyecto con las barras (``/``) sustituidas
    por guiones (``-``). Esta funcion busca ese directorio dentro de la base
    de proyectos de Claude Code.

    Args:
        project_dir: ruta absoluta del proyecto actual.
        projects_base: ruta al directorio ``~/.claude/projects/``. Si no se
            proporciona, se calcula a partir de ``$HOME``.

    Returns:
        Ruta absoluta al directorio ``memory/``. Si el directorio del
        proyecto o el subdirectorio ``memory/`` no existen, se crean
        automaticamente. Devuelve ``None`` solo si la creacion falla.
    """
    if projects_base is None:
        home = os.path.expanduser("~")
        projects_base = os.path.join(home, ".claude", "projects")

    # Convencion de Claude Code: el path absoluto con / -> -
    # Ejemplo: /Users/foo/proyecto -> -Users-foo-proyecto
    normalized = project_dir.replace(os.sep, "-")
    if not normalized.startswith("-"):
        normalized = "-" + normalized

    memory_path = os.path.join(projects_base, normalized, "memory")

    # Crear la ruta completa si no existe. Esto cubre tres escenarios:
    # 1. ~/.claude/projects/ no existe (proyecto nuevo sin memorias)
    # 2. El directorio del proyecto existe pero sin memory/
    # 3. Todo existe (caso habitual, makedirs no hace nada)
    try:
        os.makedirs(memory_path, exist_ok=True)
        return memory_path
    except OSError as e:
        _log(f"No se pudo crear el directorio de memoria nativa: {e}")
        return None


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class MemorySync:
    """
    Proyecta datos de ``alfred-memory.db`` a ficheros ``.md`` nativos.

    Lee de una instancia de ``MemoryDB`` (sin modificarla) y escribe ficheros
    Markdown con frontmatter YAML en el directorio de memoria nativa. Los
    ficheros generados llevan ``source: alfred-memory`` en el frontmatter
    para distinguirlos de las memorias manuales del usuario.

    Politica de errores: fail-open. Ningun error de escritura bloquea el
    flujo ni lanza excepciones al caller. Los problemas se registran en
    stderr con el prefijo ``[memory-sync]``.

    Args:
        db: instancia de ``MemoryDB`` ya conectada (solo lectura).
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
            Diccionario con contadores de ficheros escritos, borrados y
            errores encontrados durante la sincronizacion.
        """
        result: Dict[str, Any] = {"synced": 0, "deleted": 0, "errors": 0}

        for method in (
            self._sync_decisions,
            self._sync_archived,
            self.sync_iteration,
            self.sync_commits,
            self.sync_summary,
        ):
            try:
                method()
                result["synced"] += 1
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

        Si la decision es activa, genera o actualiza su fichero individual.
        Si no es activa, la elimina del fichero individual y regenera el
        archivo consolidado de decisiones archivadas.

        Args:
            decision_id: ID de la decision a sincronizar.
        """
        decision = self._db.get_decision(decision_id)

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
        """Proyecta el estado de la iteracion activa.

        Si hay una iteracion activa en la DB, genera un fichero con el
        comando, descripcion, fase actual y tabla de fases completadas.
        Si no hay iteracion activa, elimina el fichero si existia.
        """
        active = self._db.get_active_iteration()
        path = os.path.join(self._memory_dir, "alfred-iteration-active.md")

        if active is None:
            _safe_delete(path)
            return

        # Obtener fases completadas desde los eventos de la iteracion
        events = self._db.get_timeline(active["id"])
        phases: List[Dict[str, str]] = []
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

        # Determinar fase actual para la descripcion
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
                content += (
                    f"| {p['nombre']} | {p['resultado']} | {p['fecha']} |\n"
                )

        _safe_write(path, content)

    def sync_commits(self, limit: Optional[int] = None) -> None:
        """
        Proyecta los commits mas recientes a un fichero de tabla.

        Args:
            limit: numero de commits a proyectar. Si no se especifica,
                usa el valor configurado en el constructor.
        """
        if limit is None:
            limit = self._commits_limit

        path = os.path.join(self._memory_dir, "alfred-commits-recent.md")

        # Obtener commits recientes via SQL directo. MemoryDB no expone
        # un metodo get_commits con limite global, asi que accedemos a
        # la conexion interna. Esto acopla al esquema, pero evita anadir
        # un metodo nuevo a MemoryDB solo para esta proyeccion.
        try:
            rows = self._db.get_commits(limit=limit)
        except Exception as e:
            _log(f"Error accediendo a commits: {e}")
            rows = []

        if not rows:
            _safe_delete(path)
            return

        content = _frontmatter(
            name="Ultimos commits registrados",
            description=(
                f"Los {limit} commits mas recientes vinculados "
                f"a iteraciones de Alfred"
            ),
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
        """Genera el fichero de resumen narrativo con estadisticas y decisiones clave.

        El contenido se construye a partir de plantillas y datos reales de
        la DB, sin generacion con IA. Incluye contadores de decisiones,
        commits e iteraciones, y lista las decisiones activas mas
        relevantes.
        """
        path = os.path.join(self._memory_dir, "alfred-summary.md")
        stats = self._db.get_stats()

        total_decisions = stats.get("total_decisions", 0)
        total_commits = stats.get("total_commits", 0)
        total_iterations = stats.get("total_iterations", 0)

        # Contar decisiones activas vs archivadas
        active_decisions = list(
            self._db.iter_decisions(status="active", batch_size=500)
        )
        n_active = len(active_decisions)
        n_archived = total_decisions - n_active

        content = _frontmatter(
            name="Resumen del proyecto (Alfred)",
            description=(
                "Estado actual del proyecto con estadisticas "
                "y decisiones clave"
            ),
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
            content += f'La iteracion actual es "{cmd}: {desc}".\n'

        content += (
            f"Se han registrado {total_commits} commits "
            f"en {total_iterations} iteraciones.\n"
        )

        # Decisiones clave (hasta 10)
        if active_decisions:
            content += "\n### Decisiones clave vigentes\n\n"
            for d in active_decisions[:10]:
                title = d.get("title", "sin titulo")
                chosen = d.get("chosen", "")
                if len(chosen) > 80:
                    chosen = chosen[:77] + "..."
                content += f"- **D#{d['id']} -- {title}:** {chosen}\n"

        _safe_write(path, content)

    # --- Gestion del indice --------------------------------------------------

    def update_index(self) -> None:
        """
        Actualiza la seccion delimitada de MEMORY.md.

        Busca los marcadores ``ALFRED-SYNC:START/END`` en MEMORY.md y
        reescribe solo el contenido entre ellos. Si no existen, los anade
        al final del fichero. Si MEMORY.md no existe, lo crea con la
        seccion de Alfred.
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

        start_pos = existing.find(_SYNC_START)
        end_pos = existing.find(_SYNC_END)

        if start_pos != -1 and end_pos != -1 and start_pos < end_pos:
            # Reemplazar bloque existente (marcadores en orden correcto)
            updated = (
                existing[:start_pos]
                + sync_block.strip()
                + existing[end_pos + len(_SYNC_END):]
            )
        elif start_pos != -1 or end_pos != -1:
            # Marcadores huerfanos o en orden invertido: eliminarlos y
            # anadir el bloque limpio al final para evitar corrupcion
            cleaned = existing.replace(_SYNC_START, "").replace(_SYNC_END, "")
            updated = cleaned.rstrip() + "\n\n" + sync_block
        elif existing:
            # Anadir al final
            updated = existing.rstrip() + "\n\n" + sync_block
        else:
            # MEMORY.md no existe: crear con seccion de Alfred
            updated = sync_block

        _safe_write(memory_md, updated)

    # --- Limpieza ------------------------------------------------------------

    def cleanup_stale(self) -> List[str]:
        """
        Elimina ficheros ``alfred-*.md`` que ya no corresponden a datos activos.

        Compara los ficheros con prefijo ``alfred-`` en disco contra los IDs
        activos en SQLite. Solo elimina ficheros con ``source: alfred-memory``
        en el frontmatter para no tocar memorias manuales.

        Returns:
            Lista de rutas de ficheros eliminados.
        """
        deleted: List[str] = []
        active_ids = {
            decision["id"]
            for decision in self._db.iter_decisions(
                status="active",
                batch_size=500,
            )
        }

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
            if (
                entry.startswith("alfred-decision-")
                and entry != "alfred-decisions-archived.md"
            ):
                try:
                    id_str = entry.replace(
                        "alfred-decision-", ""
                    ).replace(".md", "")
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
        for d in self._db.iter_decisions(status="active", batch_size=500):
            self._write_decision_file(d)

    def _sync_archived(self) -> None:
        """Genera el fichero consolidado de decisiones archivadas."""
        path = os.path.join(
            self._memory_dir, "alfred-decisions-archived.md"
        )

        # Obtener decisiones no activas
        all_decisions = list(self._db.iter_decisions(batch_size=500))
        archived = [
            d for d in all_decisions if d.get("status") != "active"
        ]

        if not archived:
            _safe_delete(path)
            return

        content = _frontmatter(
            name="Decisiones archivadas de Alfred",
            description=(
                "Decisiones supersedidas o deprecadas -- "
                "contexto historico consultable"
            ),
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
                if (
                    link.get("link_type") == "supersedes"
                    and link.get("source_id") != d["id"]
                ):
                    content += f"**Sustituida por:** D#{link['source_id']}\n"
                    break

            content += f"**Fecha:** {date}\n\n---\n"

        _safe_write(path, content)

    def _write_decision_file(self, decision: Dict[str, Any]) -> None:
        """Escribe un fichero .md individual para una decision activa."""
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
            name=(
                f"D#{decision['id']}: "
                f"{decision.get('title', 'sin titulo')}"
            ),
            description=" -- ".join(desc_parts),
            source_id=decision["id"],
        )

        # Contexto
        context = decision.get("context")
        if context:
            content += f"\n## Contexto\n\n{context}\n"

        # Opcion elegida
        content += f"\n## Opcion elegida\n\n{chosen}\n"

        # Alternativas descartadas
        alt_raw = decision.get("alternatives")
        if alt_raw:
            try:
                alts = (
                    json.loads(alt_raw)
                    if isinstance(alt_raw, str)
                    else alt_raw
                )
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

        # Metadatos en linea final
        tags_raw = decision.get("tags", "[]")
        try:
            tags = (
                json.loads(tags_raw)
                if isinstance(tags_raw, str)
                else tags_raw
            )
            tags_str = ", ".join(tags) if tags else ""
        except (json.JSONDecodeError, TypeError):
            tags_str = ""

        date = (decision.get("decided_at") or "")[:10]
        meta_parts: List[str] = []
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
            Lista de tuplas ``(nombre_fichero, descripcion)`` ordenada:
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

        # Decisiones activas (ordenadas por nombre de fichero)
        try:
            for entry in sorted(os.listdir(self._memory_dir)):
                if (
                    entry.startswith("alfred-decision-")
                    and entry != "alfred-decisions-archived.md"
                ):
                    full = os.path.join(self._memory_dir, entry)
                    title = _read_frontmatter_field(full, "name") or entry
                    result.append((entry, title))
        except OSError:
            pass

        # Commits recientes
        commits_file = "alfred-commits-recent.md"
        if os.path.isfile(os.path.join(self._memory_dir, commits_file)):
            result.append((commits_file, "ultimos commits"))

        # Archivo de decisiones
        archived_file = "alfred-decisions-archived.md"
        if os.path.isfile(os.path.join(self._memory_dir, archived_file)):
            n = _count_archived(
                os.path.join(self._memory_dir, archived_file)
            )
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
    """
    Genera el bloque de frontmatter YAML para un fichero de memoria nativa.

    El formato sigue la convencion de Claude Code: campos ``name``,
    ``description`` y ``type`` son obligatorios. Los campos ``source``
    y ``source_id`` son propios de Alfred para identificar ficheros
    generados automaticamente.

    Args:
        name: nombre visible de la memoria.
        description: descripcion breve (usada para decidir relevancia).
        source_id: ID de la entidad en SQLite, si aplica.

    Returns:
        Bloque de frontmatter YAML completo con delimitadores ``---``.
    """
    # Escapar comillas dobles en name y description para YAML valido
    name = name.replace('"', '\\"')
    description = description.replace('"', '\\"')

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
    """
    Escribe un fichero de forma segura, sin lanzar excepciones.

    Crea los directorios padre si no existen. Si la escritura falla por
    cualquier razon (permisos, disco lleno, etc.), registra un aviso en
    stderr y devuelve ``False``.

    Args:
        path: ruta absoluta del fichero a escribir.
        content: contenido completo del fichero.

    Returns:
        ``True`` si la escritura fue exitosa, ``False`` en caso contrario.
    """
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
    """
    Elimina un fichero de forma segura, sin lanzar excepciones.

    Args:
        path: ruta absoluta del fichero a eliminar.

    Returns:
        ``True`` si el fichero fue eliminado, ``False`` si no existia
        o no se pudo eliminar.
    """
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except OSError as e:
        _log(f"No se pudo eliminar {path}: {e}")
    return False


def _is_alfred_file(path: str) -> bool:
    """
    Comprueba si un fichero fue generado por este modulo.

    Busca la clave ``source: alfred-memory`` en las primeras 10 lineas
    del fichero (zona del frontmatter).

    Args:
        path: ruta absoluta del fichero a comprobar.

    Returns:
        ``True`` si el fichero contiene la marca de origen de Alfred.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 10:
                    break
                if f"source: {_SOURCE_KEY}" in line:
                    return True
    except OSError:
        pass
    return False


def _read_frontmatter_field(path: str, field: str) -> Optional[str]:
    """
    Lee un campo del frontmatter YAML de un fichero.

    Parseo ligero sin dependencias externas: busca el patron
    ``campo: valor`` dentro de los delimitadores ``---``.

    Args:
        path: ruta absoluta del fichero.
        field: nombre del campo a leer.

    Returns:
        Valor del campo (sin comillas) o ``None`` si no se encuentra.
    """
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
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    return value
    except OSError:
        pass
    return None


def _count_archived(path: str) -> int:
    """
    Cuenta las decisiones en el fichero de archivo consolidado.

    Busca encabezados con el patron ``## D#`` que marcan cada decision
    archivada.

    Args:
        path: ruta al fichero ``alfred-decisions-archived.md``.

    Returns:
        Numero de decisiones encontradas.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content.count("## D#")
    except OSError:
        return 0


def _log(msg: str) -> None:
    """Imprime un mensaje de aviso en stderr con prefijo identificativo."""
    print(f"{_LOG_PREFIX} {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Punto de entrada CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """Permite invocar la sincronizacion desde shell (session-start.sh).

    Uso::

        python3 core/memory_sync.py --action sync_all --project-dir /ruta

    El proceso sale siempre con codigo 0 (fail-open) para no bloquear
    el arranque de sesion si algo falla.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Sincroniza memoria SQLite a ficheros .md nativos"
    )
    parser.add_argument(
        "--action", required=True, choices=["sync_all"],
        help="Accion a ejecutar",
    )
    parser.add_argument(
        "--project-dir", required=True,
        help="Ruta absoluta del directorio del proyecto",
    )
    parser.add_argument(
        "--commits-limit", type=int, default=10,
        help="Numero de commits recientes a proyectar",
    )
    args = parser.parse_args()

    # Resolver rutas
    db_path = os.path.join(args.project_dir, ".claude", "alfred-memory.db")
    if not os.path.isfile(db_path):
        sys.exit(0)

    memory_dir = resolve_memory_dir(args.project_dir)
    if memory_dir is None:
        _log("No se encontro directorio de memoria nativa")
        sys.exit(0)

    try:
        # Ajustar sys.path para importar MemoryDB cuando se ejecuta standalone
        core_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(core_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        from core.memory import MemoryDB as _MemoryDB

        commits_limit = args.commits_limit
        if load_memory_config is not None:
            project_config = load_memory_config(args.project_dir)
            configured_limit = project_config.get("sync_commits_limit")
            if isinstance(configured_limit, int) and configured_limit > 0:
                commits_limit = configured_limit

        db = _MemoryDB(db_path)
        sync = MemorySync(db, memory_dir, commits_limit=commits_limit)

        if args.action == "sync_all":
            result = sync.sync_all()
            _log(
                f"sync_all: {result['synced']} bloques sincronizados, "
                f"{result['deleted']} borrados, "
                f"{result['errors']} errores"
            )

        db.close()
    except Exception as e:
        _log(f"Error: {e}")
        sys.exit(0)  # fail-open: nunca bloquear el arranque
