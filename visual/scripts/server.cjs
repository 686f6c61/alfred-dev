/**
 * server.cjs — Servidor HTTP + WebSocket para la visualizacion de Selina.
 *
 * Usa exclusivamente modulos nativos de Node.js (http, crypto, fs, path).
 * Sirve contenido HTML desde un directorio de sesion, inyecta helper.js,
 * envuelve fragmentos en frame-template.html y notifica al navegador
 * via WebSocket cuando el contenido cambia.
 *
 * Configuracion mediante variables de entorno:
 *   ALFRED_VISUAL_PORT     — Puerto (por defecto 0 = libre elegido por el SO)
 *   ALFRED_VISUAL_HOST     — Direccion de escucha (por defecto 127.0.0.1)
 *   ALFRED_VISUAL_URL_HOST — Host para URLs (por defecto localhost)
 *   ALFRED_VISUAL_DIR      — Directorio de sesion (por defecto /tmp/alfred-visual)
 *   ALFRED_VISUAL_OWNER_PID — PID del proceso padre (opcional)
 */

'use strict';

const http = require('node:http');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

// ---------------------------------------------------------------------------
// Constantes y configuracion
// ---------------------------------------------------------------------------

const HOST = process.env.ALFRED_VISUAL_HOST || '127.0.0.1';
const URL_HOST = process.env.ALFRED_VISUAL_URL_HOST || (HOST === '127.0.0.1' ? 'localhost' : HOST);
const SESSION_DIR = process.env.ALFRED_VISUAL_DIR || '/tmp/alfred-visual';
const OWNER_PID = process.env.ALFRED_VISUAL_OWNER_PID
  ? Number.parseInt(process.env.ALFRED_VISUAL_OWNER_PID, 10)
  : null;

/** Tiempo maximo de inactividad antes de apagar el servidor (30 min). */
const IDLE_TIMEOUT_MS = 30 * 60 * 1000;

/** Intervalo para comprobar si el proceso padre sigue vivo (60 s). */
const OWNER_CHECK_INTERVAL_MS = 60 * 1000;

/** Debounce para el vigilante de ficheros (100 ms). */
const WATCH_DEBOUNCE_MS = 100;

/** Tamaño máximo aceptado para eventos del navegador (64 KiB). */
const MAX_EVENT_BODY_BYTES = 64 * 1024;

/** Tamaño máximo de campos de evento persistidos. */
const MAX_EVENT_FIELD_CHARS = 512;

const CONTENT_DIR = path.join(SESSION_DIR, 'content');
const STATE_DIR = path.join(SESSION_DIR, 'state');
const DEBUG_WS = process.env.ALFRED_VISUAL_DEBUG_WS === '1';

function debugWs(message, details) {
  if (!DEBUG_WS) return;
  const payload = details === undefined ? '' : ` ${JSON.stringify(details)}`;
  process.stderr.write(`[visual-ws] ${message}${payload}\n`);
}

// ---------------------------------------------------------------------------
// WebSocket RFC 6455 — implementacion minima
// ---------------------------------------------------------------------------

/** Codigos de operacion definidos en RFC 6455, seccion 5.2. */
const OPCODES = {
  TEXT: 0x01,
  CLOSE: 0x08,
  PING: 0x09,
  PONG: 0x0a,
};

/**
 * Calcula la clave de aceptacion del handshake WebSocket.
 * @param {string} key — Valor de la cabecera Sec-WebSocket-Key.
 * @returns {string} Hash SHA-1 en base64 segun RFC 6455, seccion 4.2.2.
 */
function computeAcceptKey(key) {
  const MAGIC = '258EAFA5-E914-47DA-95CA-5AB5DC76B51E';
  return crypto
    .createHash('sha1')
    .update(key + MAGIC)
    .digest('base64');
}

/**
 * Normaliza cabeceras que deberian contener un unico valor.
 * Algunos clientes/proxies pueden entregarlas como array o
 * concatenadas por comas; para el handshake WebSocket usamos
 * solo el primer token significativo.
 * @param {string|string[]|undefined} value
 * @returns {string}
 */
function normalizeSingleHeader(value) {
  if (Array.isArray(value)) {
    return String(value[0] || '').trim();
  }
  return String(value || '').split(',')[0].trim();
}

/**
 * Comprueba si una cabecera HTTP contiene un token concreto separado por comas.
 * @param {string|string[]|undefined} value
 * @param {string} token
 * @returns {boolean}
 */
function headerHasToken(value, token) {
  const rawValues = Array.isArray(value) ? value : [value];
  return rawValues.some((raw) => String(raw || '')
    .split(',')
    .map((part) => part.trim().toLowerCase())
    .includes(token.toLowerCase()));
}

/**
 * Valida que Sec-WebSocket-Key sea base64 de 16 bytes, como exige RFC 6455.
 * @param {string} key
 * @returns {boolean}
 */
function isValidWebSocketKey(key) {
  if (!key) return false;
  try {
    const decoded = Buffer.from(key, 'base64');
    return decoded.length === 16 && decoded.toString('base64') === key;
  } catch {
    return false;
  }
}

/**
 * Codifica un frame WebSocket para enviar al cliente.
 * @param {number} opcode — Codigo de operacion (TEXT, CLOSE, PING, PONG).
 * @param {Buffer|string} payload — Datos a enviar.
 * @returns {Buffer} Frame WebSocket listo para escribir en el socket.
 */
function encodeFrame(opcode, payload) {
  const data = Buffer.isBuffer(payload) ? payload : Buffer.from(payload, 'utf8');
  const len = data.length;
  let header;

  if (len < 126) {
    header = Buffer.alloc(2);
    header[0] = 0x80 | opcode;
    header[1] = len;
  } else if (len < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x80 | opcode;
    header[1] = 126;
    header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x80 | opcode;
    header[1] = 127;
    // Usamos writeBigUInt64BE para longitudes grandes
    header.writeBigUInt64BE(BigInt(len), 2);
  }

  return Buffer.concat([header, data]);
}

/**
 * Decodifica un frame WebSocket recibido del cliente.
 * Los clientes siempre envian datos enmascarados (seccion 5.3 del RFC).
 * @param {Buffer} buf — Datos crudos del socket.
 * @returns {{ opcode: number, payload: Buffer, totalLength: number } | null}
 *   null si el buffer esta incompleto.
 */
function decodeFrame(buf) {
  if (buf.length < 2) return null;

  const opcode = buf[0] & 0x0f;
  const masked = (buf[1] & 0x80) !== 0;
  let payloadLen = buf[1] & 0x7f;
  let offset = 2;

  if (payloadLen === 126) {
    if (buf.length < 4) return null;
    payloadLen = buf.readUInt16BE(2);
    offset = 4;
  } else if (payloadLen === 127) {
    if (buf.length < 10) return null;
    payloadLen = Number(buf.readBigUInt64BE(2));
    offset = 10;
  }

  const maskSize = masked ? 4 : 0;
  const totalLength = offset + maskSize + payloadLen;
  if (buf.length < totalLength) return null;

  let payload;
  if (masked) {
    const mask = buf.slice(offset, offset + maskSize);
    payload = Buffer.alloc(payloadLen);
    for (let i = 0; i < payloadLen; i++) {
      payload[i] = buf[offset + maskSize + i] ^ mask[i % 4];
    }
  } else {
    payload = buf.slice(offset, offset + payloadLen);
  }

  return { opcode, payload, totalLength };
}

// ---------------------------------------------------------------------------
// Utilidades de ficheros
// ---------------------------------------------------------------------------

/**
 * Obtiene el fichero .html mas reciente del directorio de contenido.
 * @returns {string|null} Ruta absoluta o null si no hay ficheros HTML.
 */
function getNewestHtml() {
  let files;
  try {
    files = fs.readdirSync(CONTENT_DIR);
  } catch {
    return null;
  }

  const htmlFiles = files
    .filter((f) => f.endsWith('.html'))
    .map((f) => {
      const full = path.join(CONTENT_DIR, f);
      try {
        return { name: f, mtime: fs.statSync(full).mtimeMs, path: full };
      } catch {
        return null;
      }
    })
    .filter(Boolean)
    .sort((a, b) => b.mtime - a.mtime);

  return htmlFiles.length > 0 ? htmlFiles[0].path : null;
}

/**
 * Determina si un contenido HTML es un documento completo o un fragmento.
 * Un documento completo empieza con <!DOCTYPE (ignorando espacios).
 * @param {string} html — Contenido HTML.
 * @returns {boolean}
 */
function isFullDocument(html) {
  return /^\s*<!DOCTYPE/i.test(html);
}

/** Carga helper.js desde el mismo directorio que este fichero. */
function loadHelperJs() {
  return fs.readFileSync(path.join(__dirname, 'helper.js'), 'utf8');
}

/** Carga frame-template.html desde el mismo directorio que este fichero. */
function loadFrameTemplate() {
  return fs.readFileSync(path.join(__dirname, 'frame-template.html'), 'utf8');
}

/**
 * Inyecta helper.js como script inline justo antes de </body>.
 * Si no hay </body>, lo anade al final.
 * @param {string} html — Documento HTML completo.
 * @returns {string}
 */
function injectHelper(html) {
  const script = `<script>\n${loadHelperJs()}\n</script>`;
  if (html.includes('</body>')) {
    return html.replace('</body>', script + '\n</body>');
  }
  return html + '\n' + script;
}

/**
 * Extrae bloques de estilos que conviene mover al <head> del frame.
 * Ahora mismo se usa para imports tipográficos generados por Selina.
 * @param {string} fragment
 * @returns {{ fragment: string, headHtml: string }}
 */
function extractHeadMarkup(fragment) {
  const matches = [];
  const cleaned = fragment.replace(/<style class="style-font-imports">[\s\S]*?<\/style>/g, (match) => {
    matches.push(match);
    return '';
  });
  return {
    fragment: cleaned.trim(),
    headHtml: matches.join('\n'),
  };
}

/**
 * Envuelve un fragmento HTML en el frame-template e inyecta helper.js.
 * @param {string} fragment — Fragmento HTML sin DOCTYPE.
 * @returns {string}
 */
function wrapInFrame(fragment) {
  const template = loadFrameTemplate();
  const { fragment: bodyFragment, headHtml } = extractHeadMarkup(fragment);
  let wrapped = template.replace('<!-- CONTENT -->', bodyFragment);
  if (headHtml && wrapped.includes('</head>')) {
    wrapped = wrapped.replace('</head>', `${headHtml}\n</head>`);
  }
  return injectHelper(wrapped);
}

/** Pagina de espera cuando aun no hay contenido HTML. */
function waitingPage() {
  const template = loadFrameTemplate();
  const msg = '<p class="waiting-message">Esperando a que Selina prepare las opciones de estilo...</p>';
  const wrapped = template.replace('<!-- CONTENT -->', msg);
  return injectHelper(wrapped);
}

// ---------------------------------------------------------------------------
// Tipos MIME basicos para servir ficheros estaticos
// ---------------------------------------------------------------------------

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

/** Cabeceras de seguridad aplicadas a todas las respuestas HTTP. */
const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Cache-Control': 'no-store',
};

// ---------------------------------------------------------------------------
// Estado global del servidor
// ---------------------------------------------------------------------------

/** Conexiones WebSocket activas. */
const wsClients = new Set();

/** Marca temporal de la ultima actividad (para idle timeout). */
let lastActivity = Date.now();

/** Ficheros conocidos en el directorio de contenido. */
let knownFiles = new Set();

/** Referencia global al servidor HTTP (necesaria para verificacion de origen WS). */
let _httpServer = null;

// ---------------------------------------------------------------------------
// Emision de mensajes JSON por stdout
// ---------------------------------------------------------------------------

/**
 * Emite un mensaje JSON por stdout.
 * Cada mensaje ocupa exactamente una linea.
 * @param {object} msg — Objeto a serializar.
 */
function emit(msg) {
  process.stdout.write(JSON.stringify(msg) + '\n');
}

/**
 * Limpia el registro de eventos de la pantalla visual actual.
 * Se usa cuando cambia la pantalla para evitar reutilizar clics
 * pertenecientes a una version anterior del HTML.
 */
function clearEventLog() {
  try {
    fs.writeFileSync(path.join(STATE_DIR, 'events'), '');
  } catch {
    // No pasa nada si falla
  }
}

/**
 * Normaliza un clic del usuario al formato canónico del contrato visual.
 * Mantiene campos legacy por compatibilidad con integraciones existentes.
 * @param {object} event
 * @returns {object}
 */
function buildChoiceEvent(event) {
  const ts = new Date().toISOString();
  return {
    source: 'user-event',
    type: 'click',
    choice: event.choice,
    label: event.label,
    element: event.element || '.style-option',
    ts,
    timestamp: ts,
  };
}

/**
 * Normaliza la entrada recibida desde navegador antes de persistirla.
 * @param {unknown} event
 * @returns {{choice: string, label: string, element: string}|null}
 */
function normalizeChoiceEventInput(event) {
  if (!event || typeof event !== 'object' || Array.isArray(event)) {
    return null;
  }

  const choice = event.choice;
  if (typeof choice !== 'string' || choice.trim() === '' || choice.length > MAX_EVENT_FIELD_CHARS) {
    return null;
  }

  const label = typeof event.label === 'string' && event.label.length <= MAX_EVENT_FIELD_CHARS
    ? event.label
    : choice;
  const element = typeof event.element === 'string' && event.element.length <= MAX_EVENT_FIELD_CHARS
    ? event.element
    : '.style-option';

  return { choice, label, element };
}

/**
 * Registra una eleccion canónica en el log de eventos y la emite por stdout.
 * @param {object} event
 * @returns {object}
 */
function recordChoiceEvent(event) {
  const normalizedEvent = normalizeChoiceEventInput(event);
  if (!normalizedEvent) return null;
  const choiceEvent = buildChoiceEvent(normalizedEvent);
  const eventLine = JSON.stringify(choiceEvent);
  fs.appendFileSync(path.join(STATE_DIR, 'events'), eventLine + '\n');
  emit(choiceEvent);
  return choiceEvent;
}

/**
 * Devuelve el conjunto de origins permitidos para conexiones WebSocket locales.
 * Acepta aliases de loopback para evitar que localhost y 127.0.0.1 diverjan.
 * @returns {Set<string>}
 */
function getAllowedOrigins() {
  const port = _httpServer && _httpServer.address() && typeof _httpServer.address() === 'object'
    ? _httpServer.address().port
    : '';
  const hosts = new Set([URL_HOST, HOST]);

  if (hosts.has('127.0.0.1') || hosts.has('localhost')) {
    hosts.add('127.0.0.1');
    hosts.add('localhost');
  }

  if (hosts.has('::1')) {
    hosts.add('[::1]');
  }

  const origins = new Set();
  for (const host of hosts) {
    if (!host) continue;
    origins.add(`http://${host}:${port}`);
  }
  return origins;
}

// ---------------------------------------------------------------------------
// Manejador HTTP
// ---------------------------------------------------------------------------

/**
 * Sirve un fichero estatico del directorio de contenido.
 * Protege contra path traversal resolviendo la ruta real con realpathSync.
 * @param {http.IncomingMessage} req
 * @param {http.ServerResponse} res
 */
function serveStaticFile(req, res) {
  let relPath;
  try {
    relPath = decodeURIComponent(req.url.slice('/files/'.length));
  } catch {
    res.writeHead(400, SECURITY_HEADERS);
    res.end('Ruta invalida');
    return;
  }
  const filePath = path.join(CONTENT_DIR, relPath);

  // Proteccion contra path traversal: resolver ruta real para detectar symlinks
  const resolvedBase = fs.realpathSync(CONTENT_DIR);
  let resolvedPath;
  try {
    resolvedPath = fs.realpathSync(filePath);
  } catch {
    res.writeHead(404, SECURITY_HEADERS);
    res.end('No encontrado');
    return;
  }

  if (!resolvedPath.startsWith(resolvedBase + path.sep) && resolvedPath !== resolvedBase) {
    res.writeHead(403, SECURITY_HEADERS);
    res.end('Prohibido');
    return;
  }

  try {
    const data = fs.readFileSync(resolvedPath);
    const ext = path.extname(resolvedPath).toLowerCase();
    const mime = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': mime, ...SECURITY_HEADERS });
    res.end(data);
  } catch {
    res.writeHead(404, SECURITY_HEADERS);
    res.end('No encontrado');
  }
}

/**
 * Gestiona las peticiones HTTP entrantes.
 * - GET / sirve el HTML mas reciente (o pagina de espera).
 * - GET /files/* sirve ficheros estaticos del directorio de contenido.
 */
function handleRequest(req, res) {
  lastActivity = Date.now();

  if (req.method === 'POST' && req.url === '/events') {
    const contentLength = Number.parseInt(normalizeSingleHeader(req.headers['content-length']) || '0', 10);
    if (Number.isFinite(contentLength) && contentLength > MAX_EVENT_BODY_BYTES) {
      res.writeHead(413, SECURITY_HEADERS);
      res.end('Evento demasiado grande');
      return;
    }

    const chunks = [];
    let receivedBytes = 0;
    let tooLarge = false;
    req.on('data', (chunk) => {
      receivedBytes += chunk.length;
      if (receivedBytes > MAX_EVENT_BODY_BYTES) {
        tooLarge = true;
        chunks.length = 0;
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      if (tooLarge) {
        res.writeHead(413, SECURITY_HEADERS);
        res.end('Evento demasiado grande');
        return;
      }

      try {
        const body = Buffer.concat(chunks).toString('utf8');
        const event = JSON.parse(body || '{}');
        if (!normalizeChoiceEventInput(event)) {
          res.writeHead(400, SECURITY_HEADERS);
          res.end('Evento invalido');
          return;
        }
        recordChoiceEvent(event);
        res.writeHead(202, SECURITY_HEADERS);
        res.end('accepted');
      } catch {
        res.writeHead(400, SECURITY_HEADERS);
        res.end('JSON invalido');
      }
    });
    return;
  }

  if (req.url === '/' || req.url === '/index.html') {
    const newest = getNewestHtml();
    let body;

    if (!newest) {
      body = waitingPage();
    } else {
      try {
        const raw = fs.readFileSync(newest, 'utf8');
        // textContent se usa en helper.js (no innerHTML) para evitar XSS
        body = isFullDocument(raw) ? injectHelper(raw) : wrapInFrame(raw);
      } catch {
        body = waitingPage();
      }
    }

    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', ...SECURITY_HEADERS });
    res.end(body);
    return;
  }

  if (req.url.startsWith('/files/')) {
    serveStaticFile(req, res);
    return;
  }

  res.writeHead(404, SECURITY_HEADERS);
  res.end('No encontrado');
}

// ---------------------------------------------------------------------------
// Gestion de WebSocket
// ---------------------------------------------------------------------------

/**
 * Difunde un mensaje a todas las conexiones WebSocket activas.
 * @param {string} message — Mensaje JSON serializado.
 */
function broadcast(message) {
  const frame = encodeFrame(OPCODES.TEXT, message);
  for (const socket of wsClients) {
    try {
      socket.write(frame);
    } catch {
      wsClients.delete(socket);
    }
  }
}

/**
 * Gestiona el upgrade HTTP a WebSocket segun RFC 6455.
 * @param {http.IncomingMessage} req
 * @param {net.Socket} socket
 */
function handleUpgrade(req, socket, head) {
  const rejectUpgrade = (reason) => {
    debugWs('upgrade-rejected', { reason });
    try {
      socket.write('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n');
    } catch {
      // La conexión puede estar ya cerrada.
    }
    socket.destroy();
  };

  if (!headerHasToken(req.headers.upgrade, 'websocket')) {
    rejectUpgrade('missing-upgrade-websocket');
    return;
  }
  if (!headerHasToken(req.headers.connection, 'upgrade')) {
    rejectUpgrade('missing-connection-upgrade');
    return;
  }
  if (normalizeSingleHeader(req.headers['sec-websocket-version']) !== '13') {
    rejectUpgrade('unsupported-websocket-version');
    return;
  }

  // Verificar origen del WebSocket para prevenir conexiones desde dominios ajenos
  const origin = normalizeSingleHeader(req.headers['origin']);
  debugWs('upgrade-request', {
    origin,
    key: normalizeSingleHeader(req.headers['sec-websocket-key']),
    headers: req.headers,
    headLength: head ? head.length : 0,
  });
  if (origin) {
    const allowedOrigins = getAllowedOrigins();
    if (!allowedOrigins.has(origin)) {
      debugWs('upgrade-rejected-origin', { origin, allowedOrigins: Array.from(allowedOrigins) });
      rejectUpgrade('origin-not-allowed');
      return;
    }
  }

  const key = normalizeSingleHeader(req.headers['sec-websocket-key']);
  if (!isValidWebSocketKey(key)) {
    debugWs('upgrade-rejected-missing-key');
    rejectUpgrade('invalid-websocket-key');
    return;
  }

  const accept = computeAcceptKey(key);
  debugWs('upgrade-accepted', { accept });
  const headers = [
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    `Sec-WebSocket-Accept: ${accept}`,
    '',
    '',
  ].join('\r\n');

  socket.write(headers);
  wsClients.add(socket);
  lastActivity = Date.now();

  let buffer = Buffer.alloc(0);
  socket.setNoDelay(true);

  function processChunk(chunk) {
    if (!chunk || chunk.length === 0) return;
    buffer = Buffer.concat([buffer, chunk]);

    // Procesar todos los frames completos del buffer
    let frame;
    while ((frame = decodeFrame(buffer)) !== null) {
      buffer = buffer.slice(frame.totalLength);

      switch (frame.opcode) {
        case OPCODES.TEXT: {
          const text = frame.payload.toString('utf8');
          try {
            const event = JSON.parse(text);
            // Si el evento contiene una eleccion, registrarla
            if (normalizeChoiceEventInput(event)) {
              recordChoiceEvent(event);
            }
          } catch {
            // Mensaje no JSON, ignorar
          }
          break;
        }
        case OPCODES.PING:
          socket.write(encodeFrame(OPCODES.PONG, frame.payload));
          break;
        case OPCODES.CLOSE:
          socket.write(encodeFrame(OPCODES.CLOSE, Buffer.alloc(0)));
          wsClients.delete(socket);
          socket.end();
          break;
      }
    }
  }

  if (head && head.length > 0) {
    processChunk(head);
  }

  socket.on('data', (chunk) => {
    lastActivity = Date.now();
    processChunk(chunk);
  });

  socket.on('close', () => wsClients.delete(socket));
  socket.on('error', () => wsClients.delete(socket));
}

// ---------------------------------------------------------------------------
// Vigilancia de ficheros (fs.watch con debounce)
// ---------------------------------------------------------------------------

/**
 * Inicia la vigilancia del directorio de contenido.
 * Cuando se detecta un fichero nuevo, limpia los eventos y difunde recarga.
 * Cuando se actualiza un fichero existente, solo difunde recarga.
 */
function startWatcher() {
  // Cargar ficheros conocidos iniciales
  try {
    const files = fs.readdirSync(CONTENT_DIR);
    knownFiles = new Set(files.filter((f) => f.endsWith('.html')));
  } catch {
    // El directorio puede no existir aun
  }

  let debounceTimer = null;

  try {
    fs.watch(CONTENT_DIR, (eventType, filename) => {
      if (!filename || !filename.endsWith('.html')) return;

      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const isNew = !knownFiles.has(filename);

        if (isNew) {
          // Fichero nuevo: limpiar eventos y notificar
          knownFiles.add(filename);
          clearEventLog();
          emit({ type: 'screen-added', file: filename });
        } else {
          clearEventLog();
          emit({ type: 'screen-updated', file: filename });
        }

        broadcast(JSON.stringify({ type: 'reload' }));
      }, WATCH_DEBOUNCE_MS);
    });
  } catch {
    // Si el directorio no existe, el watcher no arranca — no es critico
  }
}

// ---------------------------------------------------------------------------
// Gestion del ciclo de vida
// ---------------------------------------------------------------------------

/**
 * Escribe la informacion del servidor en el directorio de estado.
 * @param {object} info — Datos del servidor (puerto, host, URL, etc.).
 */
function writeServerInfo(info) {
  try {
    fs.writeFileSync(path.join(STATE_DIR, 'server-info'), JSON.stringify(info, null, 2));
  } catch {
    // No es critico si falla
  }
}

/**
 * Detiene el servidor de forma limpia, notifica por stdout y escribe
 * el fichero server-stopped.
 * @param {string} reason — Motivo del cierre.
 */
function shutdown(reason) {
  emit({ type: 'server-stopped', reason });
  try {
    fs.writeFileSync(path.join(STATE_DIR, 'server-stopped'), JSON.stringify({ reason, timestamp: new Date().toISOString() }));
  } catch {
    // Ignorar errores en el cierre
  }

  // Cerrar todas las conexiones WebSocket
  for (const socket of wsClients) {
    try {
      socket.write(encodeFrame(OPCODES.CLOSE, Buffer.alloc(0)));
      socket.end();
    } catch {
      // Ignorar
    }
  }

  process.exit(0);
}

/**
 * Comprueba si el proceso padre sigue vivo.
 * Si se definio OWNER_PID y el proceso ya no existe, apaga el servidor.
 */
function checkOwnerAlive() {
  if (OWNER_PID === null) return;
  try {
    process.kill(OWNER_PID, 0);
  } catch {
    shutdown('owner-exited');
  }
}

// ---------------------------------------------------------------------------
// Arranque del servidor
// ---------------------------------------------------------------------------

/**
 * Punto de entrada principal.
 * Crea los directorios necesarios, arranca el servidor HTTP y configura
 * los temporizadores de inactividad y vigilancia del proceso padre.
 */
function main() {
  // Asegurar que los directorios de sesion existen
  fs.mkdirSync(CONTENT_DIR, { recursive: true });
  fs.mkdirSync(STATE_DIR, { recursive: true });

  // Elegir puerto: variable de entorno valida o un puerto libre asignado por el SO.
  const rawPort = process.env.ALFRED_VISUAL_PORT;
  const requestedPort = rawPort === undefined || rawPort === ''
    ? 0
    : Number.parseInt(rawPort, 10);
  if (!Number.isInteger(requestedPort) || requestedPort < 0 || requestedPort > 65535) {
    process.stderr.write(`Puerto invalido para ALFRED_VISUAL_PORT: ${rawPort}\n`);
    process.exit(1);
  }

  const server = http.createServer(handleRequest);
  _httpServer = server;
  server.on('upgrade', handleUpgrade);
  server.on('error', (error) => {
    process.stderr.write(`Error al arrancar el servidor visual: ${error.message}\n`);
    process.exit(1);
  });

  server.listen(requestedPort, HOST, () => {
    const address = server.address();
    const actualPort = address && typeof address === 'object' ? address.port : requestedPort;
    const url = `http://${URL_HOST}:${actualPort}`;
    const info = {
      type: 'server-started',
      port: actualPort,
      host: HOST,
      url_host: URL_HOST,
      url,
      session_dir: SESSION_DIR,
      server_pid: process.pid,
      screen_dir: CONTENT_DIR,
      state_dir: STATE_DIR,
    };

    writeServerInfo(info);
    emit(info);

    // Iniciar vigilancia de ficheros
    startWatcher();

    // Temporizador de inactividad (30 min)
    setInterval(() => {
      if (Date.now() - lastActivity > IDLE_TIMEOUT_MS) {
        shutdown('idle-timeout');
      }
    }, 60 * 1000);

    // Comprobacion periodica del proceso padre
    if (OWNER_PID !== null) {
      setInterval(checkOwnerAlive, OWNER_CHECK_INTERVAL_MS);
    }
  });

  // Cierre limpio ante senales del sistema
  process.on('SIGTERM', () => shutdown('sigterm'));
  process.on('SIGINT', () => shutdown('sigint'));
}

// Solo ejecutar si es el modulo principal (no cuando se importa para tests)
if (require.main === module) {
  main();
}

// ---------------------------------------------------------------------------
// Exportaciones para tests
// ---------------------------------------------------------------------------

module.exports = { computeAcceptKey, encodeFrame, decodeFrame, OPCODES };
