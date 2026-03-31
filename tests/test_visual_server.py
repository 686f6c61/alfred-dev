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
import subprocess
import sys
import tempfile
import time
import unittest

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

    def _start_server(self):
        """
        Arranca el servidor y espera el mensaje de arranque por stdout.

        Devuelve el diccionario JSON del mensaje server-started.
        Lanza AssertionError si el servidor no arranca en 10 segundos.
        """
        env = os.environ.copy()
        env['ALFRED_VISUAL_DIR'] = self.session_dir
        env['ALFRED_VISUAL_HOST'] = '127.0.0.1'
        # Puerto 0 no es valido para HTTP, usamos un rango alto aleatorio
        # dejando que el servidor elija

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

    # -- Tests ---------------------------------------------------------------

    def test_server_starts_and_returns_info(self):
        """El servidor arranca y emite un JSON valido con tipo server-started."""
        info = self._start_server()
        self.assertEqual(info['type'], 'server-started')
        self.assertIn('port', info)
        self.assertIn('url', info)
        self.assertIn('screen_dir', info)
        self.assertIn('state_dir', info)

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


if __name__ == '__main__':
    unittest.main()
