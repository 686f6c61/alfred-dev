"""
test_visual_server.py — Tests de integracion para el servidor visual de Selina.

Comprueba el ciclo de vida del servidor (arranque, respuesta HTTP, escritura
de estado) usando subprocess para lanzar server.cjs y http.client para las
peticiones. Cada test crea un directorio temporal de sesion con las
subcarpetas content/ y state/.
"""

import http.client
import json
import os
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from base64 import b64encode

# Ruta al servidor — relativa a la raiz del proyecto
SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'visual', 'scripts', 'server.cjs',
)


class TestServerLifecycle(unittest.TestCase):
    """
    Tests de integracion para server.cjs.

    Cada test arranca una instancia del servidor en un puerto aleatorio,
    ejecuta las comprobaciones y limpia los recursos al terminar.
    """

    def setUp(self):
        """Crea el directorio de sesion temporal con content/ y state/."""
        self.session_dir = tempfile.mkdtemp(prefix='alfred-visual-test-')
        self.content_dir = os.path.join(self.session_dir, 'content')
        self.state_dir = os.path.join(self.session_dir, 'state')
        os.makedirs(self.content_dir)
        os.makedirs(self.state_dir)
        self.proc = None
        self.port = None

    def tearDown(self):
        """Detiene el servidor y elimina el directorio temporal."""
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        shutil.rmtree(self.session_dir, ignore_errors=True)

    def _start_server(self, extra_env=None):
        """
        Arranca el servidor y espera el mensaje de arranque por stdout.

        Devuelve el diccionario JSON del mensaje server-started.
        Lanza AssertionError si el servidor no arranca en 10 segundos.
        """
        env = os.environ.copy()
        env['ALFRED_VISUAL_DIR'] = self.session_dir
        env['ALFRED_VISUAL_HOST'] = '127.0.0.1'
        if extra_env:
            env.update(extra_env)

        self.proc = subprocess.Popen(
            ['node', SERVER_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        # Leer la primera linea de stdout (mensaje de arranque)
        # con timeout de 10 segundos
        import select
        start = time.time()
        line = b''
        while time.time() - start < 10:
            # Leer disponible
            ready, _, _ = select.select([self.proc.stdout], [], [], 1.0)
            if ready:
                chunk = self.proc.stdout.read1(4096) if hasattr(self.proc.stdout, 'read1') else self.proc.stdout.readline()
                line += chunk
                if b'\n' in line:
                    break

        self.assertIn(b'\n', line, 'El servidor no emitio mensaje de arranque en 10s')

        first_line = line.split(b'\n')[0]
        info = json.loads(first_line)
        self.assertEqual(info['type'], 'server-started')
        self.port = info['port']
        return info

    def _get(self, path='/'):
        """Realiza una peticion GET al servidor y devuelve (status, body)."""
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        conn.request('GET', path)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8')
        status = resp.status
        conn.close()
        return status, body

    def _open_websocket(self):
        """Abre una conexion WebSocket minima contra el servidor visual."""
        return self._open_websocket_with_origin(None)

    def _open_websocket_with_origin(self, origin):
        """Abre una conexion WebSocket minima contra el servidor visual."""
        sock = socket.create_connection(('127.0.0.1', self.port), timeout=5)
        key = b64encode(os.urandom(16)).decode('ascii')
        lines = [
            'GET / HTTP/1.1',
            f'Host: 127.0.0.1:{self.port}',
            'Upgrade: websocket',
            'Connection: Upgrade',
            f'Sec-WebSocket-Key: {key}',
            'Sec-WebSocket-Version: 13',
        ]
        if origin is not None:
            lines.append(f'Origin: {origin}')
        lines.extend(['', ''])
        request = '\r\n'.join(lines).encode('ascii')
        sock.sendall(request)

        response = b''
        while b'\r\n\r\n' not in response:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        self.assertIn(b'101 Switching Protocols', response)
        return sock

    def _recv_ws_text(self, sock):
        """Recibe un frame de texto no enmascarado enviado por el servidor."""
        first = sock.recv(2)
        self.assertEqual(len(first), 2)
        length = first[1] & 0x7F

        if length == 126:
            length = struct.unpack('!H', sock.recv(2))[0]
        elif length == 127:
            length = struct.unpack('!Q', sock.recv(8))[0]

        payload = b''
        while len(payload) < length:
            payload += sock.recv(length - len(payload))

        return payload.decode('utf-8')

    def _send_ws_text(self, sock, text):
        """Envia un frame WebSocket de texto enmascarado, como haria el navegador."""
        payload = text.encode('utf-8')
        header = bytearray([0x81])
        length = len(payload)

        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack('!H', length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack('!Q', length))

        mask = os.urandom(4)
        masked = bytes(payload[i] ^ mask[i % 4] for i in range(length))
        sock.sendall(bytes(header) + mask + masked)

    # -- Tests ---------------------------------------------------------------

    def test_server_starts_and_returns_info(self):
        """El servidor arranca y emite un JSON valido con tipo server-started."""
        info = self._start_server()
        self.assertEqual(info['type'], 'server-started')
        self.assertIn('port', info)
        self.assertIn('url', info)
        self.assertEqual(info['session_dir'], self.session_dir)
        self.assertEqual(info['server_pid'], self.proc.pid)
        self.assertIn('screen_dir', info)
        self.assertIn('state_dir', info)

    def test_server_accepts_port_zero_and_reports_real_port(self):
        """ALFRED_VISUAL_PORT=0 deja que el SO elija un puerto libre usable."""
        info = self._start_server({'ALFRED_VISUAL_PORT': '0'})
        self.assertGreater(info['port'], 0)
        self.assertIn(f":{info['port']}", info['url'])

    def test_server_serves_waiting_page(self):
        """Sin contenido HTML, GET / devuelve la pagina de espera."""
        self._start_server()
        status, body = self._get('/')
        self.assertEqual(status, 200)
        self.assertIn('Esperando', body)

    def test_server_serves_newest_html(self):
        """Tras escribir un fichero HTML, GET / lo incluye en la respuesta."""
        self._start_server()

        # Escribir un fichero de contenido
        html_content = '<div class="style-grid"><p>Hola mundo</p></div>'
        html_path = os.path.join(self.content_dir, 'estilo-001.html')
        with open(html_path, 'w') as f:
            f.write(html_content)

        # Dar tiempo al sistema de ficheros
        time.sleep(0.5)

        status, body = self._get('/')
        self.assertEqual(status, 200)
        self.assertIn('Hola mundo', body)

    def test_server_wraps_fragments_in_frame(self):
        """Un fragmento sin DOCTYPE se envuelve en el frame (contiene 'Selina')."""
        self._start_server()

        fragment = '<p>Fragmento de prueba</p>'
        with open(os.path.join(self.content_dir, 'frag.html'), 'w') as f:
            f.write(fragment)

        time.sleep(0.5)

        status, body = self._get('/')
        self.assertEqual(status, 200)
        self.assertIn('Selina', body)
        self.assertIn('Fragmento de prueba', body)

    def test_server_serves_full_documents_as_is(self):
        """Un documento completo con DOCTYPE se sirve sin envolver en el frame."""
        self._start_server()

        full_doc = '<!DOCTYPE html><html><head><title>Test</title></head><body><p>Documento completo</p></body></html>'
        with open(os.path.join(self.content_dir, 'full.html'), 'w') as f:
            f.write(full_doc)

        time.sleep(0.5)

        status, body = self._get('/')
        self.assertEqual(status, 200)
        self.assertIn('Documento completo', body)
        # Un documento completo NO debe contener la cabecera de Selina del frame
        # (a menos que el propio documento la incluya)
        # Verificamos que no tiene la clase alfred-header del frame
        self.assertNotIn('alfred-header', body)

    def test_server_rejects_malformed_static_path_without_crashing(self):
        """Una URL malformada en /files no debe tumbar el servidor."""
        self._start_server()
        status, body = self._get('/files/%E0%A4%A')
        self.assertEqual(status, 400)
        self.assertIn('Ruta invalida', body)

        status_after, _ = self._get('/')
        self.assertEqual(status_after, 200)

    def test_server_writes_server_info(self):
        """El fichero state/server-info existe tras el arranque."""
        self._start_server()

        info_path = os.path.join(self.state_dir, 'server-info')
        self.assertTrue(
            os.path.exists(info_path),
            f'No se encontro {info_path}',
        )

        with open(info_path) as f:
            info = json.loads(f.read())
        self.assertEqual(info['type'], 'server-started')
        self.assertEqual(info['port'], self.port)

    def test_server_records_click_events_with_canonical_shape(self):
        """Los clics WS se guardan con el contrato canónico esperado por Selina."""
        self._start_server()
        ws = self._open_websocket()
        try:
            self._send_ws_text(ws, json.dumps({'choice': 'A', 'label': 'Editorial cálido'}))
            time.sleep(0.2)
        finally:
            ws.close()

        events_path = os.path.join(self.state_dir, 'events')
        with open(events_path, 'r', encoding='utf-8') as fh:
            lines = [line.strip() for line in fh if line.strip()]

        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event['type'], 'click')
        self.assertEqual(event['choice'], 'A')
        self.assertEqual(event['label'], 'Editorial cálido')
        self.assertEqual(event['element'], '.style-option')
        self.assertEqual(event['source'], 'user-event')
        self.assertIn('ts', event)
        self.assertIn('timestamp', event)

    def test_server_accepts_loopback_origin_alias_for_websocket(self):
        """Abrir la URL como 127.0.0.1 no debe romper WS si el servidor anunció localhost."""
        self._start_server()
        ws = self._open_websocket_with_origin(f'http://127.0.0.1:{self.port}')
        try:
            self._send_ws_text(ws, json.dumps({'choice': 'A', 'label': 'Alias loopback'}))
            time.sleep(0.2)
        finally:
            ws.close()

        events_path = os.path.join(self.state_dir, 'events')
        with open(events_path, 'r', encoding='utf-8') as fh:
            lines = [line.strip() for line in fh if line.strip()]
        self.assertEqual(len(lines), 1)

    def test_server_broadcasts_reload_on_screen_update(self):
        """Actualizar la pantalla debe disparar reload por WebSocket."""
        self._start_server()
        html_path = os.path.join(self.content_dir, 'style-options.html')
        with open(html_path, 'w', encoding='utf-8') as fh:
            fh.write('<div class="style-grid"><div data-choice="A">Inicial</div></div>')
        time.sleep(0.3)

        ws = self._open_websocket()
        try:
            with open(html_path, 'w', encoding='utf-8') as fh:
                fh.write('<div class="style-grid"><div data-choice="B">Actualizada</div></div>')

            payload = json.loads(self._recv_ws_text(ws))
        finally:
            ws.close()

        self.assertEqual(payload, {'type': 'reload'})

    def test_server_clears_stale_events_when_rewriting_same_screen_file(self):
        """Reusar el mismo HTML para una pantalla nueva no debe dejar elecciones viejas."""
        self._start_server()
        html_path = os.path.join(self.content_dir, 'style-options.html')

        with open(html_path, 'w', encoding='utf-8') as fh:
            fh.write('<div class="style-grid"><div data-choice="A">Inicial</div></div>')

        time.sleep(0.3)

        ws = self._open_websocket()
        try:
            self._send_ws_text(ws, json.dumps({'choice': 'A', 'label': 'Inicial'}))
            time.sleep(0.2)
        finally:
            ws.close()

        events_path = os.path.join(self.state_dir, 'events')
        with open(events_path, 'r', encoding='utf-8') as fh:
            before = [line for line in fh if line.strip()]
        self.assertEqual(len(before), 1)

        with open(html_path, 'w', encoding='utf-8') as fh:
            fh.write('<div class="style-grid"><div data-choice="B">Nueva pantalla</div></div>')

        time.sleep(0.4)

        with open(events_path, 'r', encoding='utf-8') as fh:
            after = [line for line in fh if line.strip()]
        self.assertEqual(after, [])


if __name__ == '__main__':
    unittest.main()
