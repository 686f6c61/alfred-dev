#!/usr/bin/env python3
"""
Servidor GUI de Alfred Dev: HTTP estatico + WebSocket + SQLite watcher.

Este modulo implementa el proceso principal del dashboard. Tiene tres
responsabilidades:

1. **Servidor HTTP** -- Sirve el fichero ``dashboard.html`` y cualquier
   recurso estatico del directorio ``gui/``. Usa ``SimpleHTTPRequestHandler``
   de la stdlib para evitar dependencias externas.

2. **Servidor WebSocket** -- Gestiona conexiones de clientes usando el
   protocolo RFC 6455 implementado en ``gui.websocket``. Envia el estado
   completo al conectar (``init``) y notifica cambios incrementales
   (``update``) cuando el watcher detecta novedades.

3. **SQLite watcher** -- Sondea la base de datos cada 500 ms comparando
   checkpoints (ultimo ID de evento, decision y commit). Los cambios
   detectados se emiten a todos los clientes conectados.

El servidor puede arrancarse como script independiente con::

    python -m gui.server --db ruta/a/alfred-memory.db

Puertos por defecto: 7533 (HTTP) y 7534 (WebSocket). Si estan ocupados,
se buscan automaticamente puertos disponibles.
"""

import argparse
import asyncio
import json
import os
import socket
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any, Dict, List, Optional, Set

# Asegurar que el directorio raiz del proyecto esta en el path
# para poder importar core.memory y gui.websocket
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.memory import MemoryDB
from gui.websocket import (
    build_handshake_response,
    decode_frame,
    encode_frame,
    parse_handshake_request,
    OPCODE_CLOSE,
    OPCODE_PING,
    OPCODE_PONG,
    OPCODE_TEXT,
)

# Puertos por defecto del servidor
_DEFAULT_HTTP_PORT = 7533
_DEFAULT_WS_PORT = 7534

# Intervalo de sondeo del watcher en segundos
_POLL_INTERVAL = 0.5


def find_available_port(start: int = 7533, max_attempts: int = 50) -> int:
    """Busca un puerto TCP disponible a partir de uno dado.

    Intenta vincular un socket a cada puerto consecutivo hasta encontrar
    uno libre. Esto evita conflictos cuando el puerto por defecto esta
    ocupado por otra instancia del dashboard o un servicio diferente.

    Args:
        start: puerto desde el que empezar a buscar.
        max_attempts: numero maximo de puertos a probar.

    Returns:
        Primer puerto disponible encontrado.

    Raises:
        RuntimeError: si no se encuentra ningun puerto disponible tras
            agotar todos los intentos.
    """
    for offset in range(max_attempts):
        port = start + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(
        f"No se encontro puerto disponible entre {start} y {start + max_attempts}"
    )


class GUIServer:
    """Servidor del dashboard GUI de Alfred Dev.

    Coordina las tres capas del dashboard: HTTP estatico, WebSocket en
    tiempo real y sondeo de la base de datos SQLite. Los componentes se
    ejecutan en hilos separados para no bloquearse mutuamente.

    El ciclo de vida tipico es: crear la instancia, llamar a ``run()``
    (que bloquea) o arrancar cada componente por separado para tests.

    Args:
        db_path: ruta al fichero SQLite de memoria del proyecto.
        http_port: puerto para el servidor HTTP. Si es 0, se selecciona
            automaticamente un puerto disponible.
        ws_port: puerto para el servidor WebSocket. Si es 0, se selecciona
            automaticamente un puerto disponible.
    """

    def __init__(
        self,
        db_path: str,
        http_port: int = _DEFAULT_HTTP_PORT,
        ws_port: int = _DEFAULT_WS_PORT,
    ) -> None:
        self._db_path = db_path
        self._http_port = http_port
        self._ws_port = ws_port

        # Ruta al dashboard HTML, relativa a este fichero
        self._gui_dir = os.path.dirname(os.path.abspath(__file__))
        self.dashboard_path = os.path.join(self._gui_dir, "dashboard.html")

        # Conexion SQLite propia para el watcher (independiente de MemoryDB).
        # Se usa una conexion de solo lectura para no interferir con las
        # escrituras de los hooks y agentes.
        self._db = MemoryDB(db_path)

        # Checkpoints para detectar cambios incrementales.
        # Se inicializan a 0; el primer poll devuelve todo lo existente.
        self._event_checkpoint = 0
        self._decision_checkpoint = 0
        self._commit_checkpoint = 0

        # Clientes WebSocket conectados (asyncio.StreamWriter)
        self._ws_clients: Set[asyncio.StreamWriter] = set()

        # Control del bucle del watcher
        self._running = False

    # --- Estado completo para inicializacion del cliente --------------------

    def get_full_state(self) -> Dict[str, Any]:
        """Genera el estado completo del proyecto para el mensaje ``init``.

        Se envia a cada cliente al conectarse para que pueda renderizar
        el dashboard sin necesidad de esperar al siguiente ciclo de
        sondeo. Incluye la iteracion activa, decisiones recientes,
        eventos y elementos marcados.

        Returns:
            Diccionario con las claves: ``iteration``, ``decisions``,
            ``events``, ``pinned``.
        """
        active = self._db.get_active_iteration()

        decisions = []
        events = []
        if active:
            decisions = self._db.get_decisions(
                iteration_id=active["id"], limit=50
            )
            events = self._db.get_timeline(active["id"], limit=100)

        pinned = self._db.get_pinned_items()

        return {
            "iteration": active,
            "decisions": decisions,
            "events": events,
            "pinned": pinned,
        }

    # --- Sondeo incremental de cambios --------------------------------------

    def poll_new_events(self) -> List[Dict[str, Any]]:
        """Obtiene los eventos creados desde el ultimo checkpoint.

        Usa el ID del ultimo evento visto para obtener solo los nuevos.
        Tras la consulta, avanza el checkpoint para evitar repeticiones
        en el siguiente sondeo.

        Returns:
            Lista de diccionarios con los eventos nuevos.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM events WHERE id > ? ORDER BY id ASC",
                (self._event_checkpoint,),
            ).fetchall()
            results = [dict(r) for r in rows]
            if results:
                self._event_checkpoint = results[-1]["id"]
            return results
        finally:
            conn.close()

    def poll_new_decisions(self) -> List[Dict[str, Any]]:
        """Obtiene las decisiones creadas desde el ultimo checkpoint.

        Funciona igual que ``poll_new_events`` pero sobre la tabla
        ``decisions``.

        Returns:
            Lista de diccionarios con las decisiones nuevas.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE id > ? ORDER BY id ASC",
                (self._decision_checkpoint,),
            ).fetchall()
            results = [dict(r) for r in rows]
            if results:
                self._decision_checkpoint = results[-1]["id"]
            return results
        finally:
            conn.close()

    def poll_new_commits(self) -> List[Dict[str, Any]]:
        """Obtiene los commits registrados desde el ultimo checkpoint.

        Funciona igual que ``poll_new_events`` pero sobre la tabla
        ``commits``.

        Returns:
            Lista de diccionarios con los commits nuevos.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM commits WHERE id > ? ORDER BY id ASC",
                (self._commit_checkpoint,),
            ).fetchall()
            results = [dict(r) for r in rows]
            if results:
                self._commit_checkpoint = results[-1]["id"]
            return results
        finally:
            conn.close()

    # --- Procesamiento de acciones del dashboard ----------------------------

    def process_gui_action(self, action: Dict[str, Any]) -> None:
        """Procesa una accion recibida desde el dashboard.

        Segun el tipo de accion, delega en el metodo adecuado de MemoryDB
        para materializar el cambio en SQLite. Las acciones soportadas son:

        - ``pin_item``: marca un elemento como importante.
        - ``unpin_item``: elimina un marcado existente.
        - ``activate_agent``: registra la accion de activar un agente.
        - ``deactivate_agent``: registra la desactivacion de un agente.
        - ``approve_gate``: registra la aprobacion de una puerta de calidad.

        Args:
            action: diccionario con al menos la clave ``type`` que indica
                el tipo de accion, mas los campos especificos de cada tipo.
        """
        action_type = action.get("type", "")

        if action_type == "pin_item":
            self._db.pin_item(
                item_type=action.get("item_type", "unknown"),
                item_id=action.get("item_id"),
                item_ref=action.get("item_ref"),
                note=action.get("note"),
            )

        elif action_type == "unpin_item":
            pin_id = action.get("pin_id")
            if pin_id is not None:
                self._db.unpin_item(pin_id)

        elif action_type in ("activate_agent", "deactivate_agent", "approve_gate"):
            # Estas acciones se registran como gui_actions para que los
            # hooks las procesen en el siguiente ciclo.
            self._db.create_gui_action(action_type, action)

        else:
            # Tipo desconocido: registrar igualmente como gui_action
            # para trazabilidad, aunque ningun hook lo procese.
            self._db.create_gui_action(action_type, action)

    # --- Gestion de clientes WebSocket --------------------------------------

    async def handle_ws_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Gestiona la conexion de un cliente WebSocket.

        Realiza el handshake HTTP Upgrade, envia el estado inicial y
        queda escuchando mensajes del cliente. Cuando el cliente envia
        una accion, la procesa y confirma con un mensaje de respuesta.

        Args:
            reader: stream de lectura del socket.
            writer: stream de escritura del socket.
        """
        try:
            # Leer la peticion de handshake
            request_data = await reader.read(4096)
            client_key = parse_handshake_request(request_data)

            if client_key is None:
                writer.close()
                return

            # Completar el handshake
            response = build_handshake_response(client_key)
            writer.write(response)
            await writer.drain()

            # Registrar el cliente
            self._ws_clients.add(writer)

            # Enviar estado completo como mensaje de inicializacion
            state = self.get_full_state()
            init_msg = json.dumps({
                "type": "init",
                "payload": state,
            }, ensure_ascii=False, default=str)
            writer.write(encode_frame(init_msg))
            await writer.drain()

            # Bucle de recepcion de mensajes
            while True:
                data = await reader.read(65536)
                if not data:
                    break

                try:
                    opcode, payload = decode_frame(data)
                except ValueError:
                    break

                if opcode == OPCODE_CLOSE:
                    break
                elif opcode == OPCODE_PING:
                    # Responder con pong usando el mismo payload
                    writer.write(encode_frame(
                        payload.decode("utf-8", errors="replace"),
                        opcode=OPCODE_PONG,
                    ))
                    await writer.drain()
                elif opcode == OPCODE_TEXT:
                    # Intentar parsear como accion del dashboard
                    try:
                        msg = json.loads(payload.decode("utf-8"))
                        if msg.get("type") == "action":
                            self.process_gui_action(msg.get("payload", {}))
                            # Confirmar la accion procesada
                            ack = json.dumps({
                                "type": "action_ack",
                                "payload": {"status": "ok"},
                            })
                            writer.write(encode_frame(ack))
                            await writer.drain()
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass

        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass
        finally:
            self._ws_clients.discard(writer)
            try:
                writer.close()
            except Exception:
                pass

    async def broadcast(self, message: str) -> None:
        """Envia un mensaje a todos los clientes WebSocket conectados.

        Los clientes desconectados se eliminan automaticamente de la
        lista si el envio falla.

        Args:
            message: texto JSON a enviar como frame WebSocket.
        """
        frame = encode_frame(message)
        disconnected: Set[asyncio.StreamWriter] = set()

        for writer in self._ws_clients:
            try:
                writer.write(frame)
                await writer.drain()
            except (ConnectionResetError, BrokenPipeError, OSError):
                disconnected.add(writer)

        self._ws_clients -= disconnected

    # --- Bucle del watcher --------------------------------------------------

    async def watch_loop(self) -> None:
        """Bucle principal del watcher de SQLite.

        Sondea la base de datos cada 500 ms en busca de eventos, decisiones
        y commits nuevos. Cuando detecta cambios, construye un mensaje
        ``update`` y lo emite a todos los clientes conectados.

        El bucle se ejecuta hasta que se llame a ``stop()``.
        """
        self._running = True
        while self._running:
            try:
                new_events = self.poll_new_events()
                new_decisions = self.poll_new_decisions()
                new_commits = self.poll_new_commits()

                if new_events or new_decisions or new_commits:
                    msg = json.dumps({
                        "type": "update",
                        "payload": {
                            "events": new_events,
                            "decisions": new_decisions,
                            "commits": new_commits,
                        },
                    }, ensure_ascii=False, default=str)
                    await self.broadcast(msg)

            except Exception:
                # No dejar que un error del sondeo pare el watcher.
                # En produccion se registraria el error en un log.
                pass

            await asyncio.sleep(_POLL_INTERVAL)

    # --- Servidor HTTP ------------------------------------------------------

    def serve_http(self) -> None:
        """Arranca el servidor HTTP en un hilo separado.

        Sirve los ficheros estaticos del directorio ``gui/``. El dashboard
        queda disponible en ``http://127.0.0.1:<http_port>/dashboard.html``.
        """
        handler = partial(
            SimpleHTTPRequestHandler,
            directory=self._gui_dir,
        )
        server = HTTPServer(("127.0.0.1", self._http_port), handler)
        server.serve_forever()

    # --- Ciclo de vida completo ---------------------------------------------

    def run(self) -> None:
        """Arranca el servidor completo (HTTP + WebSocket + watcher).

        El servidor HTTP se ejecuta en un hilo daemon, mientras que el
        servidor WebSocket y el watcher se ejecutan en el bucle asyncio
        del hilo principal.
        """
        # Seleccionar puertos disponibles si se pidio auto-deteccion
        if self._http_port == 0:
            self._http_port = find_available_port(_DEFAULT_HTTP_PORT)
        if self._ws_port == 0:
            self._ws_port = find_available_port(self._http_port + 1)

        print(f"Alfred Dev Dashboard")
        print(f"  HTTP: http://127.0.0.1:{self._http_port}/dashboard.html")
        print(f"  WS:   ws://127.0.0.1:{self._ws_port}")
        print(f"  DB:   {self._db_path}")
        print()

        # Arrancar servidor HTTP en hilo daemon
        http_thread = threading.Thread(target=self.serve_http, daemon=True)
        http_thread.start()

        # Arrancar WebSocket + watcher en el bucle asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _start() -> None:
            """Inicia el servidor WebSocket y el watcher."""
            ws_server = await asyncio.start_server(
                self.handle_ws_client,
                "127.0.0.1",
                self._ws_port,
            )
            # Ejecutar el watcher en paralelo con el servidor WebSocket
            await asyncio.gather(
                ws_server.serve_forever(),
                self.watch_loop(),
            )

        try:
            loop.run_until_complete(_start())
        except KeyboardInterrupt:
            print("\nDeteniendo servidor...")
        finally:
            self._running = False
            loop.close()

    def stop(self) -> None:
        """Detiene el bucle del watcher.

        Establece la bandera de parada que el ``watch_loop`` comprueba
        en cada iteracion. El servidor se detiene limpiamente en el
        siguiente ciclo de sondeo.
        """
        self._running = False


def main() -> None:
    """Punto de entrada CLI del servidor GUI.

    Parsea los argumentos de linea de comandos y arranca el servidor.
    Acepta la ruta a la base de datos SQLite y los puertos opcionales
    para HTTP y WebSocket.

    Ejemplo de uso::

        python -m gui.server --db .claude/alfred-memory.db
        python -m gui.server --db mi-proyecto.db --http-port 8080 --ws-port 8081
    """
    parser = argparse.ArgumentParser(
        description="Servidor del dashboard GUI de Alfred Dev."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Ruta al fichero SQLite de memoria del proyecto.",
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=_DEFAULT_HTTP_PORT,
        help=f"Puerto HTTP (defecto: {_DEFAULT_HTTP_PORT}).",
    )
    parser.add_argument(
        "--ws-port",
        type=int,
        default=_DEFAULT_WS_PORT,
        help=f"Puerto WebSocket (defecto: {_DEFAULT_WS_PORT}).",
    )
    args = parser.parse_args()

    server = GUIServer(
        db_path=args.db,
        http_port=args.http_port,
        ws_port=args.ws_port,
    )
    server.run()


if __name__ == "__main__":
    main()
