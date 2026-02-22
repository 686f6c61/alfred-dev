#!/usr/bin/env python3
"""Tests para la implementacion manual del protocolo WebSocket RFC 6455."""

import base64
import hashlib
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.websocket import (
    build_accept_key,
    encode_frame,
    decode_frame,
    OPCODE_TEXT,
    OPCODE_CLOSE,
    OPCODE_PING,
    OPCODE_PONG,
)


class TestWebSocketHandshake(unittest.TestCase):
    """Tests del handshake WebSocket."""

    def test_accept_key_rfc_example(self):
        """Verifica el ejemplo del RFC 6455 seccion 4.2.2."""
        client_key = "dGhlIHNhbXBsZSBub25jZQ=="
        expected = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
        self.assertEqual(build_accept_key(client_key), expected)

    def test_accept_key_format(self):
        """La clave de aceptacion es base64 valido."""
        key = base64.b64encode(os.urandom(16)).decode()
        accept = build_accept_key(key)
        decoded = base64.b64decode(accept)
        self.assertEqual(len(decoded), 20)


class TestWebSocketFraming(unittest.TestCase):
    """Tests del framing de mensajes WebSocket."""

    def test_encode_short_text(self):
        """Codifica un mensaje de texto corto (< 126 bytes)."""
        frame = encode_frame("hola", OPCODE_TEXT)
        self.assertEqual(frame[0], 0x81)
        self.assertEqual(frame[1], 4)
        self.assertEqual(frame[2:], b"hola")

    def test_encode_medium_text(self):
        """Codifica un mensaje de 200 bytes (usa campo de 2 bytes)."""
        msg = "x" * 200
        frame = encode_frame(msg, OPCODE_TEXT)
        self.assertEqual(frame[0], 0x81)
        self.assertEqual(frame[1], 126)
        length = struct.unpack("!H", frame[2:4])[0]
        self.assertEqual(length, 200)

    def test_decode_unmasked_frame(self):
        """Decodifica un frame sin mascara (servidor a cliente)."""
        frame = encode_frame("test", OPCODE_TEXT)
        opcode, payload = decode_frame(frame)
        self.assertEqual(opcode, OPCODE_TEXT)
        self.assertEqual(payload, b"test")

    def test_decode_masked_frame(self):
        """Decodifica un frame con mascara (cliente a servidor, obligatorio)."""
        payload = b"hola"
        mask_key = b"\x37\xfa\x21\x3d"
        masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        header = bytes([0x81, 0x80 | len(payload)])
        frame = header + mask_key + masked
        opcode, decoded = decode_frame(frame)
        self.assertEqual(opcode, OPCODE_TEXT)
        self.assertEqual(decoded, payload)

    def test_encode_close_frame(self):
        """Codifica un frame de cierre."""
        frame = encode_frame("", OPCODE_CLOSE)
        self.assertEqual(frame[0], 0x80 | OPCODE_CLOSE)

    def test_encode_ping_frame(self):
        """Codifica un frame de ping."""
        frame = encode_frame("ping", OPCODE_PING)
        self.assertEqual(frame[0], 0x80 | OPCODE_PING)

    def test_roundtrip_json(self):
        """Un mensaje JSON sobrevive la codificacion/decodificacion."""
        import json
        msg = json.dumps({"type": "event", "data": {"fase": "desarrollo"}})
        frame = encode_frame(msg, OPCODE_TEXT)
        opcode, payload = decode_frame(frame)
        recovered = json.loads(payload.decode("utf-8"))
        self.assertEqual(recovered["type"], "event")


if __name__ == "__main__":
    unittest.main()
