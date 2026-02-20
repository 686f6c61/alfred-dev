#!/usr/bin/env python3
"""
Servidor MCP stdio para la memoria persistente de Alfred Dev.

Implementa el protocolo Model Context Protocol sobre stdin/stdout usando
exclusivamente la biblioteca estandar de Python (json, sys, struct, logging).
El formato de transporte es JSON-RPC 2.0 con encabezados Content-Length,
identico al que usa LSP (Language Server Protocol).

El servidor expone seis herramientas que permiten a los agentes de Alfred
consultar y registrar informacion en la base de datos de memoria del proyecto:

    - memory_search: busqueda textual en decisiones y commits.
    - memory_log_decision: registra una decision de diseno formal.
    - memory_log_commit: registra un commit y lo vincula a decisiones.
    - memory_get_iteration: detalle de una iteracion (o la ultima).
    - memory_get_timeline: cronologia de eventos de una iteracion.
    - memory_stats: estadisticas generales de la memoria.

Ciclo de vida:
    Claude Code lanza este proceso al inicio de sesion y lo mantiene vivo.
    Al arrancar, el servidor resuelve la ruta de la DB relativa al directorio
    de trabajo (``$PWD/.claude/alfred-memory.db``), abre la conexion, asegura
    el esquema y queda a la escucha de invocaciones MCP por stdin.

Seguridad:
    La sanitizacion de secretos la realiza MemoryDB internamente. Este servidor
    se limita a pasar los parametros recibidos a la API de core/memory.py.

Uso:
    No esta pensado para ejecutarse manualmente. Claude Code lo gestiona a
    traves de la configuracion en ``.claude-plugin/mcp.json``.
"""

import json
import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Configuracion de logging
# ---------------------------------------------------------------------------
# Los logs van a stderr para no interferir con el protocolo MCP que viaja
# por stdout. Nivel DEBUG para facilitar diagnostico durante desarrollo.

logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="[alfred-memory] %(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
_log = logging.getLogger("alfred-memory")

# ---------------------------------------------------------------------------
# Importacion de MemoryDB
# ---------------------------------------------------------------------------
# El servidor necesita importar core.memory, que vive en la raiz del plugin.
# Se anade al sys.path la raiz del plugin (el directorio padre de mcp/).

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

from core.memory import MemoryDB  # noqa: E402


# ---------------------------------------------------------------------------
# Definicion de herramientas
# ---------------------------------------------------------------------------
# Cada herramienta se describe con name, description e inputSchema (JSON
# Schema draft-07). El servidor devuelve esta lista cuando recibe el metodo
# ``tools/list`` y la usa para despachar en ``tools/call``.

_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "memory_search",
        "description": (
            "Busca en la memoria del proyecto (decisiones y commits) por texto. "
            "Usa FTS5 si esta disponible, o LIKE como fallback."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termino de busqueda textual.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Numero maximo de resultados (por defecto 20).",
                    "default": 20,
                },
                "iteration_id": {
                    "type": "integer",
                    "description": "Filtrar resultados por ID de iteracion.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_log_decision",
        "description": (
            "Registra una decision de diseno formal en la memoria del proyecto. "
            "Se vincula automaticamente a la iteracion activa si no se indica otra."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titulo corto de la decision.",
                },
                "chosen": {
                    "type": "string",
                    "description": "Opcion elegida.",
                },
                "context": {
                    "type": "string",
                    "description": "Problema o situacion que se resolvia.",
                },
                "alternatives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Opciones descartadas.",
                },
                "rationale": {
                    "type": "string",
                    "description": "Justificacion de la eleccion.",
                },
                "impact": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Nivel de impacto de la decision.",
                },
                "phase": {
                    "type": "string",
                    "description": "Fase del flujo en la que se tomo.",
                },
            },
            "required": ["title", "chosen"],
        },
    },
    {
        "name": "memory_log_commit",
        "description": (
            "Registra un commit en la memoria y opcionalmente lo vincula a "
            "decisiones previas. Si el SHA ya existe se ignora (idempotente)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sha": {
                    "type": "string",
                    "description": "Hash SHA del commit.",
                },
                "message": {
                    "type": "string",
                    "description": "Mensaje del commit.",
                },
                "decision_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": (
                        "IDs de decisiones a vincular con este commit."
                    ),
                },
                "iteration_id": {
                    "type": "integer",
                    "description": (
                        "ID de iteracion. Si se omite, se usa la activa."
                    ),
                },
            },
            "required": ["sha"],
        },
    },
    {
        "name": "memory_get_iteration",
        "description": (
            "Obtiene los datos completos de una iteracion. Si no se indica "
            "ID, devuelve la iteracion activa o la mas reciente."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": (
                        "ID de la iteracion. Si se omite, devuelve la activa "
                        "o la ultima registrada."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "memory_get_timeline",
        "description": (
            "Obtiene la cronologia completa de eventos de una iteracion, "
            "ordenados de mas antiguo a mas reciente."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "iteration_id": {
                    "type": "integer",
                    "description": "ID de la iteracion cuya cronologia consultar.",
                },
            },
            "required": ["iteration_id"],
        },
    },
    {
        "name": "memory_stats",
        "description": (
            "Devuelve estadisticas generales de la memoria del proyecto: "
            "contadores de iteraciones, decisiones, commits, eventos, modo "
            "de busqueda y metadatos."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# Mapa de nombre a indice para acceso rapido en tools/call
_TOOL_NAMES = {t["name"] for t in _TOOLS}


# ---------------------------------------------------------------------------
# Transporte JSON-RPC sobre stdio
# ---------------------------------------------------------------------------


def _read_message() -> Optional[Dict[str, Any]]:
    """
    Lee un mensaje JSON-RPC de stdin con encabezado Content-Length.

    El formato es identico al de LSP:
        Content-Length: <N>\\r\\n
        \\r\\n
        <N bytes de JSON>

    Returns:
        Diccionario con el mensaje parseado, o None si stdin se cierra.

    Raises:
        ValueError: si el encabezado no tiene el formato esperado.
    """
    # Leer encabezados hasta encontrar la linea vacia
    content_length: Optional[int] = None

    while True:
        line = sys.stdin.buffer.readline()

        # Si stdin se cierra, terminar
        if not line:
            return None

        # Decodificar la linea como ASCII (los encabezados son ASCII puro)
        line_str = line.decode("ascii").strip()

        # Linea vacia marca el fin de los encabezados
        if line_str == "":
            if content_length is not None:
                break
            # Si aun no tenemos Content-Length, seguir leyendo
            # (puede haber lineas vacias espurias al inicio)
            continue

        # Parsear encabezado Content-Length
        if line_str.lower().startswith("content-length:"):
            try:
                content_length = int(line_str.split(":", 1)[1].strip())
            except (ValueError, IndexError) as exc:
                raise ValueError(
                    f"Encabezado Content-Length malformado: {line_str!r}"
                ) from exc
        # Ignorar otros encabezados (ej. Content-Type)

    # Leer el cuerpo exacto
    body = sys.stdin.buffer.read(content_length)
    if len(body) < content_length:
        _log.warning(
            "Cuerpo truncado: esperados %d bytes, recibidos %d",
            content_length,
            len(body),
        )
        return None

    return json.loads(body.decode("utf-8"))


def _write_message(msg: Dict[str, Any]) -> None:
    """
    Escribe un mensaje JSON-RPC a stdout con encabezado Content-Length.

    Args:
        msg: diccionario con el mensaje JSON-RPC a enviar.
    """
    body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()


def _make_response(request_id: Any, result: Any) -> Dict[str, Any]:
    """
    Construye una respuesta JSON-RPC 2.0 exitosa.

    Args:
        request_id: el ID del request original.
        result: datos del resultado.

    Returns:
        Diccionario con la respuesta formateada.
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _make_error(
    request_id: Any,
    code: int,
    message: str,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Construye una respuesta JSON-RPC 2.0 de error.

    Codigos de error estandar:
        -32700  Parse error
        -32600  Invalid Request
        -32601  Method not found
        -32602  Invalid params
        -32603  Internal error

    Args:
        request_id: el ID del request original (puede ser None).
        code: codigo numerico del error.
        message: descripcion legible del error.
        data: datos adicionales opcionales.

    Returns:
        Diccionario con la respuesta de error formateada.
    """
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error,
    }


# ---------------------------------------------------------------------------
# Servidor MCP
# ---------------------------------------------------------------------------


class MemoryMCPServer:
    """
    Servidor MCP stdio para la memoria persistente de Alfred Dev.

    Gestiona el ciclo de vida de la conexion con la base de datos SQLite
    y despacha los mensajes JSON-RPC recibidos por stdin a los handlers
    correspondientes. Las respuestas se escriben por stdout en el mismo
    formato Content-Length + JSON-RPC.

    El servidor soporta cuatro metodos del protocolo MCP:
        - ``initialize``: negociacion de capacidades.
        - ``notifications/initialized``: confirmacion del cliente.
        - ``tools/list``: listado de herramientas disponibles.
        - ``tools/call``: invocacion de una herramienta concreta.

    Args:
        db_path: ruta al fichero SQLite de la memoria. Si no existe, se crea
                 automaticamente con el esquema completo.
        retention_days: dias de retencion para la purga de eventos antiguos.
                        Si es 0 o negativo, no se ejecuta la purga.
    """

    def __init__(self, db_path: str, retention_days: int = 365) -> None:
        self._db: Optional[MemoryDB] = None
        self._db_path = db_path
        self._retention_days = retention_days
        self._initialized = False

    def _ensure_db(self) -> MemoryDB:
        """
        Abre la conexion con la DB de forma perezosa.

        La apertura se difiere hasta que realmente se necesita para evitar
        crear la DB si el cliente nunca invoca herramientas (por ejemplo,
        si solo hace initialize + shutdown).

        Returns:
            Instancia de MemoryDB lista para operar.

        Raises:
            RuntimeError: si la ruta de la DB no es accesible.
        """
        if self._db is not None:
            return self._db

        _log.info("Abriendo base de datos en: %s", self._db_path)
        try:
            self._db = MemoryDB(self._db_path)
        except Exception as exc:
            _log.error("Error al abrir la base de datos: %s", exc)
            raise RuntimeError(
                f"No se pudo abrir la base de datos: {exc}"
            ) from exc

        # Purgar eventos antiguos si procede
        if self._retention_days > 0:
            try:
                purged = self._db.purge_old_events(self._retention_days)
                if purged > 0:
                    _log.info(
                        "Purgados %d eventos con mas de %d dias",
                        purged,
                        self._retention_days,
                    )
            except Exception as exc:
                _log.warning("Error en purga de eventos: %s", exc)

        return self._db

    # --- Handlers de protocolo MCP -----------------------------------------

    def _handle_initialize(
        self, request_id: Any, _params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Responde al metodo ``initialize`` con la informacion del servidor.

        Devuelve el nombre, la version y las capacidades soportadas. En este
        caso, el servidor solo expone herramientas (``tools``).
        """
        self._initialized = True
        _log.info("Inicializacion solicitada por el cliente")
        return _make_response(request_id, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "alfred-memory",
                "version": "0.2.0",
            },
            "capabilities": {
                "tools": {},
            },
        })

    def _handle_tools_list(
        self, request_id: Any, _params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Responde al metodo ``tools/list`` con el catalogo de herramientas.

        Cada herramienta incluye su nombre, descripcion y el JSON Schema
        de sus parametros de entrada.
        """
        _log.debug("Listado de herramientas solicitado")
        return _make_response(request_id, {"tools": _TOOLS})

    def _handle_tools_call(
        self, request_id: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Despacha una invocacion de herramienta al metodo correspondiente.

        Valida que la herramienta exista, abre la DB si es necesario y
        delega la ejecucion al metodo ``_call_<nombre_herramienta>``.
        El resultado se serializa como JSON y se devuelve en un bloque
        ``content`` con tipo ``text``.

        Args:
            request_id: ID del request JSON-RPC.
            params: debe contener ``name`` (str) y opcionalmente ``arguments`` (dict).

        Returns:
            Respuesta JSON-RPC con el resultado o un error.
        """
        tool_name: str = params.get("name", "")
        arguments: Dict[str, Any] = params.get("arguments", {})

        _log.info("Invocacion de herramienta: %s", tool_name)
        _log.debug("Argumentos: %s", arguments)

        if tool_name not in _TOOL_NAMES:
            return _make_error(
                request_id,
                -32602,
                f"Herramienta desconocida: {tool_name}",
            )

        # Abrir la DB si aun no esta abierta
        try:
            db = self._ensure_db()
        except RuntimeError as exc:
            return _make_error(
                request_id,
                -32603,
                str(exc),
            )

        # Despachar al handler concreto
        handler_name = f"_call_{tool_name}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            return _make_error(
                request_id,
                -32603,
                f"Handler no implementado para: {tool_name}",
            )

        try:
            result = handler(db, arguments)
            text_content = json.dumps(result, ensure_ascii=False, indent=2)
            return _make_response(request_id, {
                "content": [
                    {"type": "text", "text": text_content},
                ],
            })
        except Exception as exc:
            _log.error(
                "Error ejecutando %s: %s\n%s",
                tool_name,
                exc,
                traceback.format_exc(),
            )
            return _make_error(
                request_id,
                -32603,
                f"Error en {tool_name}: {exc}",
            )

    # --- Implementacion de cada herramienta --------------------------------

    def _call_memory_search(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una busqueda textual en decisiones y commits.

        La busqueda aprovecha FTS5 si esta disponible en el entorno SQLite;
        en caso contrario, utiliza LIKE como fallback transparente.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``query`` (str, obligatorio), ``limit`` (int), ``iteration_id`` (int).

        Returns:
            Diccionario con la lista de resultados y metadatos de la busqueda.
        """
        query: str = args.get("query", "")
        limit: int = args.get("limit", 20)
        iteration_id: Optional[int] = args.get("iteration_id")

        if not query.strip():
            return {"results": [], "message": "La consulta esta vacia."}

        results = db.search(query, limit=limit, iteration_id=iteration_id)
        return {
            "results": results,
            "total": len(results),
            "query": query,
            "fts_enabled": db.fts_enabled,
        }

    def _call_memory_log_decision(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra una decision de diseno en la memoria.

        Los campos ``title`` y ``chosen`` son obligatorios. El resto son
        opcionales y enriquecen la trazabilidad de la decision.

        Args:
            db: instancia de MemoryDB abierta.
            args: parametros de la decision segun el inputSchema.

        Returns:
            Diccionario con el ID de la decision creada y confirmacion.
        """
        title: str = args.get("title", "")
        chosen: str = args.get("chosen", "")

        if not title or not chosen:
            return {"error": "Los campos 'title' y 'chosen' son obligatorios."}

        decision_id = db.log_decision(
            title=title,
            chosen=chosen,
            context=args.get("context"),
            alternatives=args.get("alternatives"),
            rationale=args.get("rationale"),
            impact=args.get("impact"),
            phase=args.get("phase"),
        )

        return {
            "decision_id": decision_id,
            "message": f"Decision registrada con ID {decision_id}.",
        }

    def _call_memory_log_commit(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra un commit y opcionalmente lo vincula a decisiones.

        Si el SHA ya existe en la base de datos, la operacion se ignora
        (idempotencia). Las vinculaciones con decisiones se crean como
        enlaces de tipo ``implements``.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``sha`` (str, obligatorio), ``message`` (str),
                  ``decision_ids`` (list[int]), ``iteration_id`` (int).

        Returns:
            Diccionario con el resultado del registro.
        """
        sha: str = args.get("sha", "")

        if not sha:
            return {"error": "El campo 'sha' es obligatorio."}

        commit_id = db.log_commit(
            sha=sha,
            message=args.get("message"),
            iteration_id=args.get("iteration_id"),
        )

        # Vincular con decisiones si se proporcionaron
        decision_ids: List[int] = args.get("decision_ids", [])
        linked: List[int] = []

        if commit_id is not None and decision_ids:
            for did in decision_ids:
                try:
                    db.link_commit_decision(commit_id, did)
                    linked.append(did)
                except Exception as exc:
                    _log.warning(
                        "No se pudo vincular commit %d con decision %d: %s",
                        commit_id,
                        did,
                        exc,
                    )

        if commit_id is None:
            return {
                "commit_id": None,
                "message": f"El commit {sha[:8]} ya existia. Ignorado.",
                "duplicate": True,
            }

        return {
            "commit_id": commit_id,
            "message": f"Commit {sha[:8]} registrado con ID {commit_id}.",
            "linked_decisions": linked,
        }

    def _call_memory_get_iteration(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Obtiene los datos completos de una iteracion.

        Si no se proporciona un ID, intenta devolver la iteracion activa.
        Si no hay activa, devuelve la mas reciente (mayor ID).

        Args:
            db: instancia de MemoryDB abierta.
            args: ``id`` (int, opcional).

        Returns:
            Diccionario con los datos de la iteracion o un mensaje si no existe.
        """
        iteration_id: Optional[int] = args.get("id")

        if iteration_id is not None:
            iteration = db.get_iteration(iteration_id)
        else:
            # Intentar la activa primero, si no la ultima
            iteration = db.get_active_iteration()
            if iteration is None:
                # Buscar la mas reciente por ID descendente
                stats = db.get_stats()
                total = stats.get("total_iterations", 0)
                if total > 0:
                    # Obtener la de mayor ID mediante busqueda directa
                    iteration = self._get_latest_iteration(db)

        if iteration is None:
            return {"iteration": None, "message": "No hay iteraciones registradas."}

        # Enriquecer con decisiones de esa iteracion
        decisions = db.get_decisions(iteration_id=iteration["id"], limit=50)

        return {
            "iteration": iteration,
            "decisions": decisions,
            "total_decisions": len(decisions),
        }

    @staticmethod
    def _get_latest_iteration(db: MemoryDB) -> Optional[Dict[str, Any]]:
        """
        Obtiene la iteracion mas reciente de la base de datos.

        Se usa como fallback cuando no hay iteracion activa y el usuario
        no especifica un ID concreto.

        Args:
            db: instancia de MemoryDB abierta.

        Returns:
            Diccionario con la iteracion mas reciente, o None si no hay ninguna.
        """
        # Acceso directo a la conexion para una consulta que MemoryDB
        # no expone directamente como metodo publico
        row = db._conn.execute(
            "SELECT * FROM iterations ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def _call_memory_get_timeline(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Obtiene la cronologia de eventos de una iteracion.

        Los eventos se devuelven ordenados cronologicamente (del mas antiguo
        al mas reciente), permitiendo reconstruir la secuencia completa del
        flujo de trabajo.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``iteration_id`` (int, obligatorio).

        Returns:
            Diccionario con la lista de eventos y metadatos.
        """
        iteration_id: Optional[int] = args.get("iteration_id")

        if iteration_id is None:
            return {"error": "El campo 'iteration_id' es obligatorio."}

        events = db.get_timeline(iteration_id)
        return {
            "iteration_id": iteration_id,
            "events": events,
            "total": len(events),
        }

    def _call_memory_stats(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Devuelve estadisticas generales de la memoria del proyecto.

        Incluye contadores de cada tipo de registro, el modo de busqueda
        activo (FTS5 o LIKE), la version del esquema y la fecha de creacion.

        Args:
            db: instancia de MemoryDB abierta.
            args: sin parametros (se ignora).

        Returns:
            Diccionario con todas las estadisticas.
        """
        stats = db.get_stats()
        stats["fts_enabled"] = db.fts_enabled
        stats["db_path"] = self._db_path
        return stats

    # --- Bucle principal ---------------------------------------------------

    def run(self) -> None:
        """
        Bucle principal del servidor MCP.

        Lee mensajes JSON-RPC de stdin, los despacha al handler apropiado
        y escribe las respuestas en stdout. El bucle termina cuando stdin
        se cierra (fin del proceso padre) o cuando se recibe una senal
        de terminacion.

        Las notificaciones (mensajes sin ``id``) se procesan pero no generan
        respuesta, conforme al protocolo JSON-RPC 2.0.
        """
        _log.info("Servidor MCP alfred-memory iniciado")
        _log.info("DB path: %s", self._db_path)

        try:
            while True:
                try:
                    message = _read_message()
                except ValueError as exc:
                    _log.error("Error leyendo mensaje: %s", exc)
                    # Intentar enviar error de parse si es posible
                    _write_message(_make_error(None, -32700, str(exc)))
                    continue
                except Exception as exc:
                    _log.error(
                        "Error inesperado leyendo stdin: %s\n%s",
                        exc,
                        traceback.format_exc(),
                    )
                    break

                # stdin cerrado: el proceso padre termino
                if message is None:
                    _log.info("Stdin cerrado. Terminando servidor.")
                    break

                _log.debug("Mensaje recibido: %s", json.dumps(message)[:200])

                # Extraer campos del mensaje JSON-RPC
                method: str = message.get("method", "")
                request_id = message.get("id")
                params: Dict[str, Any] = message.get("params", {})

                # Las notificaciones no tienen id y no requieren respuesta
                is_notification = request_id is None

                # Despachar segun el metodo
                response: Optional[Dict[str, Any]] = None

                if method == "initialize":
                    response = self._handle_initialize(request_id, params)

                elif method == "notifications/initialized":
                    # Notificacion de confirmacion del cliente. No requiere
                    # respuesta segun el protocolo.
                    _log.info("Cliente confirma inicializacion")

                elif method == "tools/list":
                    response = self._handle_tools_list(request_id, params)

                elif method == "tools/call":
                    response = self._handle_tools_call(request_id, params)

                elif method == "ping":
                    # Metodo de heartbeat: responder con un objeto vacio
                    response = _make_response(request_id, {})

                else:
                    # Metodo desconocido: si es una peticion con id, devolver
                    # error. Si es notificacion, ignorar silenciosamente.
                    if not is_notification:
                        response = _make_error(
                            request_id,
                            -32601,
                            f"Metodo no soportado: {method}",
                        )
                    else:
                        _log.debug(
                            "Notificacion ignorada: %s", method
                        )

                # Enviar respuesta solo si es una peticion (tiene id)
                if response is not None and not is_notification:
                    _write_message(response)
                    _log.debug(
                        "Respuesta enviada para id=%s", request_id
                    )

        except KeyboardInterrupt:
            _log.info("Interrupcion recibida. Cerrando servidor.")
        finally:
            if self._db is not None:
                _log.info("Cerrando conexion con la base de datos")
                self._db.close()

        _log.info("Servidor MCP alfred-memory finalizado")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Punto de entrada del servidor MCP.

    Resuelve la ruta de la base de datos relativa al directorio de trabajo
    actual (donde Claude Code ejecuta el proceso) y arranca el bucle
    principal del servidor.
    """
    # La DB vive en el directorio .claude/ del proyecto donde se ejecuta
    # Claude Code, no en el directorio del plugin.
    db_path = os.path.join(os.getcwd(), ".claude", "alfred-memory.db")

    # Dias de retencion configurables via variable de entorno (fallback 365)
    retention_str = os.environ.get("ALFRED_MEMORY_RETENTION_DAYS", "365")
    try:
        retention_days = int(retention_str)
    except ValueError:
        retention_days = 365

    server = MemoryMCPServer(db_path=db_path, retention_days=retention_days)
    server.run()


if __name__ == "__main__":
    main()
