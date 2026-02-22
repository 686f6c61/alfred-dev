#!/usr/bin/env python3
"""
Implementacion manual del protocolo WebSocket (RFC 6455).

Cubre el handshake HTTP Upgrade, el framing de mensajes de texto y los
frames de control (ping, pong, close). Disenado para uso local con un
numero reducido de conexiones (dashboard de Alfred Dev).

No implementa:
    - Fragmentacion de mensajes (no necesaria para JSON corto).
    - Extensiones (permessage-deflate, etc.).
    - Subprotocolos.

Referencia: https://datatracker.ietf.org/doc/html/rfc6455
"""

import base64
import hashlib
import struct
from typing import Optional, Tuple

# GUID magico definido por el RFC 6455 para el handshake
_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Opcodes de frames WebSocket (RFC 6455, seccion 5.2)
OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


def build_accept_key(client_key: str) -> str:
    """Genera la clave Sec-WebSocket-Accept para el handshake.

    Concatena la clave del cliente con el GUID magico del RFC,
    calcula el SHA-1 y lo devuelve codificado en base64.

    Args:
        client_key: valor del header Sec-WebSocket-Key del cliente.

    Returns:
        Valor para el header Sec-WebSocket-Accept de la respuesta.
    """
    raw = client_key.strip() + _WS_GUID
    sha1 = hashlib.sha1(raw.encode("utf-8")).digest()
    return base64.b64encode(sha1).decode("utf-8")


def build_handshake_response(client_key: str) -> bytes:
    """Construye la respuesta HTTP 101 para completar el handshake.

    Args:
        client_key: valor del header Sec-WebSocket-Key.

    Returns:
        Respuesta HTTP completa como bytes, lista para enviar por socket.
    """
    accept = build_accept_key(client_key)
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "\r\n"
    )
    return response.encode("utf-8")


def encode_frame(data: str, opcode: int = OPCODE_TEXT) -> bytes:
    """Codifica un mensaje como frame WebSocket (servidor a cliente, sin mascara).

    Soporta payloads de hasta 65535 bytes con el campo de longitud de 2 bytes.
    Para mensajes mas grandes (>65535) usa el campo de 8 bytes.

    Args:
        data: texto a enviar.
        opcode: opcode del frame (OPCODE_TEXT, OPCODE_CLOSE, etc.).

    Returns:
        Frame WebSocket como bytes.
    """
    payload = data.encode("utf-8") if isinstance(data, str) else data
    length = len(payload)

    header = bytes([0x80 | opcode])

    if length < 126:
        header += bytes([length])
    elif length < 65536:
        header += bytes([126]) + struct.pack("!H", length)
    else:
        header += bytes([127]) + struct.pack("!Q", length)

    return header + payload


def decode_frame(data: bytes) -> Tuple[int, bytes]:
    """Decodifica un frame WebSocket (puede venir con o sin mascara).

    Los frames de cliente a servidor siempre llevan mascara (RFC 6455,
    seccion 5.3). Los de servidor a cliente no.

    Args:
        data: bytes crudos del frame.

    Returns:
        Tupla (opcode, payload) donde payload son los bytes del mensaje.

    Raises:
        ValueError: si el frame es demasiado corto o malformado.
    """
    if len(data) < 2:
        raise ValueError("Frame demasiado corto")

    opcode = data[0] & 0x0F

    masked = bool(data[1] & 0x80)
    length = data[1] & 0x7F
    offset = 2

    if length == 126:
        if len(data) < 4:
            raise ValueError("Frame incompleto (longitud 2 bytes)")
        length = struct.unpack("!H", data[2:4])[0]
        offset = 4
    elif length == 127:
        if len(data) < 10:
            raise ValueError("Frame incompleto (longitud 8 bytes)")
        length = struct.unpack("!Q", data[2:10])[0]
        offset = 10

    mask_key = None
    if masked:
        if len(data) < offset + 4:
            raise ValueError("Frame incompleto (mascara)")
        mask_key = data[offset : offset + 4]
        offset += 4

    payload = data[offset : offset + length]

    if mask_key:
        payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

    return opcode, payload


def parse_handshake_request(data: bytes) -> Optional[str]:
    """Extrae la clave Sec-WebSocket-Key de una peticion HTTP de upgrade.

    Busca el header Sec-WebSocket-Key en la peticion HTTP del cliente.
    Si no lo encuentra o la peticion no es un upgrade WebSocket, devuelve None.

    Args:
        data: peticion HTTP completa como bytes.

    Returns:
        Valor del header Sec-WebSocket-Key, o None si no es un upgrade.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None

    if "Upgrade: websocket" not in text and "upgrade: websocket" not in text:
        return None

    for line in text.split("\r\n"):
        lower = line.lower()
        if lower.startswith("sec-websocket-key:"):
            return line.split(":", 1)[1].strip()

    return None
