/**
 * helper.js — Cliente WebSocket para el visor de Selina.
 *
 * Se inyecta como script inline en cada pagina servida por server.cjs.
 * Gestiona la conexion WebSocket, la seleccion de opciones por parte
 * del usuario y la recarga automatica cuando el servidor notifica
 * cambios en el contenido.
 *
 * API publica expuesta en window:
 *   - window.toggleSelect(el) — Selecciona una opcion y deselecciona las demas.
 *   - window.selectedChoice   — Ultima eleccion seleccionada.
 *   - window.alfred           — { send(obj), choice(id, label) }
 */
(function alfredHelper() {
  'use strict';

  // -- Estado interno -------------------------------------------------------

  /** @type {WebSocket|null} */
  let ws = null;

  /** @type {string|null} Ultima eleccion del usuario. */
  let selectedChoice = null;

  /** Cola de mensajes emitidos antes de que el socket este listo. */
  const pendingMessages = [];

  /** Identificador del temporizador de reconexion. */
  let reconnectTimer = null;

  /** Intervalo de reintento en milisegundos. */
  const RECONNECT_MS = 1000;

  /**
   * Actualiza el indicador visual de conexion si existe en la pagina.
   * @param {string} color
   */
  function setConnectionDot(color) {
    var dot = document.getElementById('alfred-connection-dot');
    if (dot) dot.style.background = color;
  }

  /**
   * Programa un unico intento de reconexion.
   */
  function scheduleReconnect() {
    if (reconnectTimer !== null) return;
    reconnectTimer = setTimeout(function () {
      reconnectTimer = null;
      connect();
    }, RECONNECT_MS);
  }

  /**
   * Vuelca los mensajes pendientes cuando el socket ya esta abierto.
   */
  function flushPendingMessages() {
    while (pendingMessages.length > 0 && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(pendingMessages.shift()));
    }
  }

  // -- Conexion WebSocket ---------------------------------------------------

  /**
   * Establece la conexion WebSocket con reconexion automatica.
   * Cuando el servidor envia {type:'reload'}, recarga la pagina completa
   * para reflejar el contenido actualizado.
   */
  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const url = protocol + window.location.host;
    ws = new WebSocket(url);

    ws.onopen = function () {
      setConnectionDot('#27ae60');
      flushPendingMessages();
    };

    ws.onmessage = function (event) {
      try {
        var msg = JSON.parse(event.data);
        if (msg.type === 'reload') {
          window.location.reload();
        }
      } catch (_) {
        // Mensaje no JSON, ignorar
      }
    };

    ws.onclose = function () {
      ws = null;
      setConnectionDot('#e74c3c');
      scheduleReconnect();
    };

    ws.onerror = function () {
      // El evento close se dispara despues, ahi se reintenta
    };
  }

  // -- Envio de datos al servidor -------------------------------------------

  /**
   * Envia un objeto JSON al servidor a traves del WebSocket.
   * @param {object} obj — Datos a enviar.
   */
  function send(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(obj));
      return;
    }

    pendingMessages.push(obj);
  }

  /**
   * Registra una eleccion del usuario y la envia al servidor.
   * @param {string} id — Identificador de la opcion (p. ej. "A", "B", "C").
   * @param {string} label — Etiqueta legible de la opcion.
   */
  function choice(id, label) {
    selectedChoice = id;
    send({ choice: id, label: label });
  }

  // -- Seleccion visual de opciones ----------------------------------------

  /**
   * Selecciona un elemento de opcion y deselecciona sus hermanos.
   * Busca el atributo data-choice para identificar la eleccion y
   * el primer heading dentro del elemento para obtener la etiqueta legible.
   * @param {HTMLElement} el — Elemento con atributo data-choice.
   */
  function toggleSelect(el) {
    // Deseleccionar hermanos dentro del mismo contenedor
    var parent = el.parentElement;
    if (parent) {
      var siblings = parent.querySelectorAll('[data-choice]');
      for (var i = 0; i < siblings.length; i++) {
        siblings[i].classList.remove('selected');
      }
    }

    // Seleccionar el elemento clicado
    el.classList.add('selected');

    var id = el.getAttribute('data-choice');
    var heading = el.querySelector('h1, h2, h3, h4, h5, h6');
    // Se usa textContent, nunca innerHTML, para evitar XSS si el contenido
    // del encabezado contuviera HTML no confiable.
    var label = heading ? heading.textContent : id;

    choice(id, label);

    // Actualizar barra indicadora
    var indicator = document.getElementById('alfred-indicator');
    if (indicator) {
      indicator.textContent = 'Opcion ' + label + ' seleccionada — vuelve al terminal para continuar';
    }
  }

  // -- Captura de clics en opciones -----------------------------------------

  document.addEventListener('click', function (e) {
    var target = e.target.closest('[data-choice]');
    if (target) {
      e.preventDefault();
      toggleSelect(target);
    }
  });

  // -- API publica ----------------------------------------------------------

  Object.defineProperty(window, 'selectedChoice', {
    get: function () { return selectedChoice; },
    set: function (v) { selectedChoice = v; },
  });

  window.toggleSelect = toggleSelect;
  window.alfred = { send: send, choice: choice };

  // -- Arranque -------------------------------------------------------------

  connect();
})();
