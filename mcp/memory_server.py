#!/usr/bin/env python3
"""
Servidor MCP stdio para la memoria persistente de Alfred Dev.

Implementa el protocolo Model Context Protocol sobre stdin/stdout usando
exclusivamente la biblioteca estandar de Python (json, sys, struct, logging).
El formato de transporte es JSON-RPC 2.0 con encabezados Content-Length,
identico al que usa LSP (Language Server Protocol).

El servidor expone quince herramientas que permiten a los agentes de Alfred
consultar, registrar y gestionar la base de datos de memoria del proyecto:

    Consulta (10 originales):
    - memory_search: busqueda textual con filtros temporales, por tags y estado.
    - memory_log_decision: registra una decision de diseno formal con etiquetas.
    - memory_log_commit: registra un commit con ficheros afectados.
    - memory_get_iteration: detalle de una iteracion (o la ultima).
    - memory_get_timeline: cronologia de eventos de una iteracion.
    - memory_stats: estadisticas generales de la memoria.
    - memory_record_decision / memory_record_iteration / memory_record_event / memory_record_commit
    - memory_link_commit: vincula un commit con una decision.
    - memory_get_decisions: listado filtrado de decisiones.

    Gestion (5 nuevas en v0.2.3):
    - memory_update_decision: actualiza estado y etiquetas de una decision.
    - memory_link_decisions: crea relaciones entre decisiones.
    - memory_health: validacion de integridad de la base de datos.
    - memory_export: exporta decisiones a Markdown (formato ADR).
    - memory_import: importa desde historial Git o ficheros ADR.

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
                "since": {
                    "type": "string",
                    "description": "Filtrar resultados posteriores a esta fecha (ISO 8601).",
                },
                "until": {
                    "type": "string",
                    "description": "Filtrar resultados anteriores a esta fecha (ISO 8601).",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filtrar decisiones que tengan alguna de estas etiquetas.",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "superseded", "deprecated"],
                    "description": "Filtrar decisiones por estado.",
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
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Etiquetas para clasificar la decision.",
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
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de ficheros afectados por el commit.",
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
    {
        "name": "memory_manage_iteration",
        "description": (
            "Gestiona el ciclo de vida de iteraciones: inicia una nueva "
            "o completa una existente. Util para que los agentes controlen "
            "el flujo sin depender del hook de captura automatica."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "complete"],
                    "description": (
                        "Accion a realizar: 'start' para iniciar una nueva "
                        "iteracion, 'complete' para cerrar una existente."
                    ),
                },
                "command": {
                    "type": "string",
                    "description": (
                        "Comando que origino la iteracion (ej. 'feature', 'fix'). "
                        "Solo requerido para action='start'."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Descripcion libre de la iteracion.",
                },
                "iteration_id": {
                    "type": "integer",
                    "description": (
                        "ID de la iteracion a completar. Solo para action='complete'. "
                        "Si se omite, se completa la iteracion activa."
                    ),
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "memory_log_event",
        "description": (
            "Registra un evento arbitrario en la cronologia de una iteracion. "
            "Util para trazar gates aprobadas, agentes ejecutados o hitos "
            "personalizados del flujo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": (
                        "Tipo de evento (ej. 'gate_approved', 'agent_executed', "
                        "'phase_completed', 'custom')."
                    ),
                },
                "phase": {
                    "type": "string",
                    "description": "Fase del flujo en la que ocurrio el evento.",
                },
                "payload": {
                    "type": "object",
                    "description": "Datos arbitrarios asociados al evento.",
                },
                "iteration_id": {
                    "type": "integer",
                    "description": (
                        "ID de la iteracion. Si se omite, se usa la activa."
                    ),
                },
            },
            "required": ["event_type"],
        },
    },
    {
        "name": "memory_get_decisions",
        "description": (
            "Lista las decisiones de diseno registradas en la memoria. "
            "Se pueden filtrar por iteracion. Util para el Bibliotecario "
            "y para generar informes de decisiones."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "iteration_id": {
                    "type": "integer",
                    "description": "Filtrar decisiones por ID de iteracion.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Numero maximo de decisiones (por defecto 50).",
                    "default": 50,
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filtrar decisiones por etiquetas.",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "superseded", "deprecated"],
                    "description": "Filtrar decisiones por estado.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "memory_purge",
        "description": (
            "Elimina eventos antiguos de la memoria. Las decisiones e "
            "iteraciones se conservan siempre; solo se purgan eventos "
            "anteriores a la ventana de retencion indicada."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "retention_days": {
                    "type": "integer",
                    "description": (
                        "Dias de retencion. Los eventos mas antiguos se eliminan."
                    ),
                },
            },
            "required": ["retention_days"],
        },
    },
    {
        "name": "memory_update_decision",
        "description": (
            "Actualiza el estado o las etiquetas de una decision existente. "
            "Permite marcar decisiones como superseded o deprecated, y "
            "anadir etiquetas para clasificarlas."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID de la decision a actualizar.",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "superseded", "deprecated"],
                    "description": "Nuevo estado de la decision.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Etiquetas a anadir a la decision.",
                },
            },
            "required": ["id"],
        },
    },
    {
        "name": "memory_link_decisions",
        "description": (
            "Crea una relacion entre dos decisiones. Permite documentar "
            "que una decision sustituye, depende, contradice o se "
            "relaciona con otra."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "integer",
                    "description": "ID de la decision origen.",
                },
                "target_id": {
                    "type": "integer",
                    "description": "ID de la decision destino.",
                },
                "link_type": {
                    "type": "string",
                    "enum": ["supersedes", "depends_on", "contradicts", "relates"],
                    "description": "Tipo de relacion.",
                },
            },
            "required": ["source_id", "target_id", "link_type"],
        },
    },
    {
        "name": "memory_health",
        "description": (
            "Valida la integridad de la base de datos de memoria. "
            "Comprueba version del esquema, sincronizacion FTS5, "
            "permisos del fichero y tamano de la BD."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "memory_export",
        "description": (
            "Exporta las decisiones del proyecto a un fichero Markdown "
            "con formato ADR-like. Incluye fecha, estado, etiquetas, "
            "contexto, decision, alternativas y justificacion."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": ["markdown"],
                    "description": "Formato de exportacion (por ahora solo markdown).",
                },
                "path": {
                    "type": "string",
                    "description": "Ruta del fichero de salida. Por defecto DECISIONS.md.",
                },
                "iteration_id": {
                    "type": "integer",
                    "description": "Exportar solo decisiones de esta iteracion.",
                },
            },
            "required": ["format"],
        },
    },
    {
        "name": "memory_import",
        "description": (
            "Importa datos en la memoria desde fuentes externas: "
            "historial de Git (commits) o ficheros ADR (decisiones)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": ["git", "adr"],
                    "description": "Fuente de importacion.",
                },
                "path": {
                    "type": "string",
                    "description": "Ruta del repositorio Git o directorio de ADRs.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Numero maximo de registros a importar (para git).",
                    "default": 100,
                },
            },
            "required": ["source"],
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
                "version": "0.3.1",
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
            # Si el handler devuelve {"error": ...}, marcamos isError para
            # que el consumidor MCP distinga errores de validacion de
            # resultados exitosos (protocolo MCP tools/call).
            is_error = isinstance(result, dict) and "error" in result
            return _make_response(request_id, {
                "content": [
                    {"type": "text", "text": text_content},
                ],
                "isError": is_error,
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
        since: Optional[str] = args.get("since")
        until: Optional[str] = args.get("until")
        tags: Optional[List[str]] = args.get("tags")
        status: Optional[str] = args.get("status")

        if not query.strip():
            return {"results": [], "message": "La consulta esta vacia."}

        results = db.search(
            query,
            limit=limit,
            iteration_id=iteration_id,
            since=since,
            until=until,
            tags=tags,
            status=status,
        )
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
            tags=args.get("tags"),
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
            files=args.get("files"),
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
        no especifica un ID concreto. Delega en el metodo publico de
        MemoryDB para mantener la encapsulacion.

        Args:
            db: instancia de MemoryDB abierta.

        Returns:
            Diccionario con la iteracion mas reciente, o None si no hay ninguna.
        """
        return db.get_latest_iteration()

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

    def _call_memory_manage_iteration(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gestiona el ciclo de vida de iteraciones.

        Soporta dos acciones: ``start`` para iniciar una nueva iteracion
        y ``complete`` para cerrar una existente. Si se intenta iniciar
        una iteracion cuando ya hay una activa, se devuelve un error.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``action`` (str, obligatorio), ``command`` (str),
                  ``description`` (str), ``iteration_id`` (int).

        Returns:
            Diccionario con el resultado de la operacion.
        """
        action: str = args.get("action", "")

        if action == "start":
            command: str = args.get("command", "")
            if not command:
                return {"error": "El campo 'command' es obligatorio para action='start'."}

            # Verificar que no hay iteracion activa
            active = db.get_active_iteration()
            if active is not None:
                return {
                    "error": (
                        f"Ya hay una iteracion activa (ID {active['id']}, "
                        f"comando '{active.get('command', '?')}'). "
                        f"Completala antes de iniciar una nueva."
                    ),
                    "active_iteration": active,
                }

            iteration_id = db.start_iteration(
                command=command,
                description=args.get("description"),
            )
            return {
                "iteration_id": iteration_id,
                "message": f"Iteracion {iteration_id} iniciada para '{command}'.",
            }

        elif action == "complete":
            iteration_id_param: Optional[int] = args.get("iteration_id")

            if iteration_id_param is None:
                active = db.get_active_iteration()
                if active is None:
                    return {"error": "No hay iteracion activa para completar."}
                iteration_id_param = active["id"]

            db.complete_iteration(iteration_id_param)
            return {
                "iteration_id": iteration_id_param,
                "message": f"Iteracion {iteration_id_param} completada.",
            }

        else:
            return {"error": f"Accion desconocida: '{action}'. Usa 'start' o 'complete'."}

    def _call_memory_log_event(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra un evento arbitrario en la cronologia de una iteracion.

        Los eventos se vinculan a una iteracion. Si no se proporciona
        ``iteration_id``, se usa la iteracion activa. Si no hay activa,
        se devuelve un error.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``event_type`` (str, obligatorio), ``phase`` (str),
                  ``payload`` (dict), ``iteration_id`` (int).

        Returns:
            Diccionario con el ID del evento registrado.
        """
        event_type: str = args.get("event_type", "")
        if not event_type:
            return {"error": "El campo 'event_type' es obligatorio."}

        iteration_id: Optional[int] = args.get("iteration_id")
        if iteration_id is None:
            active = db.get_active_iteration()
            if active is None:
                return {
                    "error": (
                        "No hay iteracion activa. Proporciona 'iteration_id' "
                        "o inicia una iteracion con memory_manage_iteration."
                    ),
                }
            iteration_id = active["id"]

        event_id = db.log_event(
            event_type=event_type,
            phase=args.get("phase"),
            payload=args.get("payload"),
            iteration_id=iteration_id,
        )

        return {
            "event_id": event_id,
            "iteration_id": iteration_id,
            "message": f"Evento '{event_type}' registrado con ID {event_id}.",
        }

    def _call_memory_get_decisions(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Lista las decisiones de diseno registradas en la memoria.

        Las decisiones se devuelven ordenadas de la mas reciente a la
        mas antigua. Se pueden filtrar por iteracion.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``iteration_id`` (int, opcional), ``limit`` (int).

        Returns:
            Diccionario con la lista de decisiones y metadatos.
        """
        iteration_id: Optional[int] = args.get("iteration_id")
        limit: int = args.get("limit", 50)
        tags: Optional[List[str]] = args.get("tags")
        status: Optional[str] = args.get("status")

        decisions = db.get_decisions(
            iteration_id=iteration_id,
            limit=limit,
            tags=tags,
            status=status,
        )

        return {
            "decisions": decisions,
            "total": len(decisions),
            "iteration_id": iteration_id,
        }

    def _call_memory_purge(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Elimina eventos antiguos de la memoria.

        Solo se purgan eventos: las decisiones e iteraciones se conservan
        siempre. El numero de dias de retencion determina el corte temporal.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``retention_days`` (int, obligatorio).

        Returns:
            Diccionario con el numero de eventos eliminados.
        """
        retention_days: Optional[int] = args.get("retention_days")

        if retention_days is None or retention_days < 1:
            return {
                "error": (
                    "El campo 'retention_days' es obligatorio y debe ser "
                    "un entero positivo."
                ),
            }

        purged = db.purge_old_events(retention_days)
        return {
            "purged_events": purged,
            "retention_days": retention_days,
            "message": (
                f"Eliminados {purged} eventos con mas de "
                f"{retention_days} dias de antigueedad."
            ),
        }

    def _call_memory_update_decision(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza el estado o las etiquetas de una decision existente.

        Permite marcar decisiones como ``superseded`` o ``deprecated`` y
        anadir etiquetas de clasificacion. Ambos cambios son opcionales y
        se aplican de forma independiente.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``id`` (int, obligatorio), ``status`` (str), ``tags`` (list[str]).

        Returns:
            Diccionario con confirmacion o error si falta el ID.
        """
        decision_id: Optional[int] = args.get("id")

        if decision_id is None:
            return {"error": "El campo 'id' es obligatorio."}

        new_status: Optional[str] = args.get("status")
        new_tags: Optional[List[str]] = args.get("tags")

        if new_status:
            try:
                db.update_decision_status(decision_id, new_status)
            except ValueError as exc:
                return {"error": str(exc)}

        if new_tags:
            db.add_decision_tags(decision_id, new_tags)

        return {
            "message": "Decision actualizada.",
            "id": decision_id,
        }

    def _call_memory_link_decisions(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea una relacion dirigida entre dos decisiones.

        Documenta que una decision sustituye, depende, contradice o se
        relaciona con otra. La operacion es idempotente: si la relacion
        ya existe, no se duplica.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``source_id`` (int), ``target_id`` (int), ``link_type`` (str).
                  Los tres campos son obligatorios.

        Returns:
            Diccionario con confirmacion o error si faltan campos.
        """
        source_id: Optional[int] = args.get("source_id")
        target_id: Optional[int] = args.get("target_id")
        link_type: Optional[str] = args.get("link_type")

        if source_id is None or target_id is None or link_type is None:
            return {
                "error": (
                    "Los campos 'source_id', 'target_id' y 'link_type' "
                    "son obligatorios."
                ),
            }

        db.link_decisions(source_id, target_id, link_type)

        return {
            "message": (
                f"Relacion '{link_type}' creada entre decision "
                f"{source_id} y {target_id}."
            ),
            "source_id": source_id,
            "target_id": target_id,
            "link_type": link_type,
        }

    def _call_memory_health(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valida la integridad de la base de datos de memoria.

        Delega en ``MemoryDB.check_health()`` y devuelve el resultado
        directamente, que incluye version del esquema, estado de FTS5,
        permisos y tamano del fichero.

        Args:
            db: instancia de MemoryDB abierta.
            args: sin parametros (se ignora).

        Returns:
            Diccionario con el informe de salud de la base de datos.
        """
        return db.check_health()

    def _call_memory_export(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exporta las decisiones a un fichero Markdown con formato ADR-like.

        Por ahora solo soporta el formato ``markdown``. El fichero de
        salida incluye fecha, estado, etiquetas, contexto, decision
        elegida, alternativas y justificacion de cada decision.

        Args:
            db: instancia de MemoryDB abierta.
            args: ``format`` (str, obligatorio), ``path`` (str),
                  ``iteration_id`` (int).

        Returns:
            Diccionario con el numero de decisiones exportadas, la ruta
            y el formato.
        """
        fmt: str = args.get("format", "")
        path: str = args.get("path", "DECISIONS.md")
        iteration_id: Optional[int] = args.get("iteration_id")

        if fmt != "markdown":
            return {
                "error": (
                    f"Formato no soportado: '{fmt}'. "
                    "Solo se admite 'markdown'."
                ),
            }

        count = db.export_decisions_markdown(path, iteration_id)

        return {
            "exported": count,
            "path": path,
            "format": fmt,
        }

    def _call_memory_import(
        self, db: MemoryDB, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Importa datos en la memoria desde fuentes externas.

        Soporta dos fuentes: ``git`` para importar el historial de commits
        de un repositorio, y ``adr`` para importar ficheros ADR como
        decisiones. La operacion es idempotente para commits (los SHA
        duplicados se ignoran).

        Args:
            db: instancia de MemoryDB abierta.
            args: ``source`` (str, obligatorio), ``path`` (str),
                  ``limit`` (int, solo para git).

        Returns:
            Diccionario con el numero de registros importados y la fuente.
        """
        source: str = args.get("source", "")
        path: Optional[str] = args.get("path")
        limit: int = args.get("limit", 100)

        if source == "git":
            repo_path = path or os.getcwd()
            count = db.import_git_history(repo_path, limit)
        elif source == "adr":
            adr_path = path or "docs/adr"
            count = db.import_adrs(adr_path)
        else:
            return {
                "error": (
                    f"Fuente no soportada: '{source}'. "
                    "Usa 'git' o 'adr'."
                ),
            }

        return {
            "imported": count,
            "source": source,
        }

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
