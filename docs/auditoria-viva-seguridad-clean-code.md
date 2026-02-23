# Auditoria Viva de Seguridad y Clean Code (Alfred Dev)

Estado: `vivo`  
Fecha de revision: `2026-02-22`  
Tipo de revision: `estatica (sin ejecutar plugin)`

## Alcance

- Revisado: `hooks/`, `core/`, `gui/`, `mcp/`, scripts de instalacion/desinstalacion y documentacion operativa.
- No revisado a fondo: build del sitio `site/` (carpeta en progreso/no integrada en el paquete actual).

## Como mantener este documento vivo

1. No borres hallazgos cerrados: muévelos a "Historico" con fecha y PR.
2. Cada hallazgo debe tener: `ID`, `estado`, `owner`, `fecha objetivo`.
3. En cada release, revalida solo hallazgos `open` o `in_progress`.

---

## Resumen ejecutivo

Se ve una base tecnica bastante solida en persistencia, atomicidad y cobertura de tests del core. El riesgo principal no esta en SQL ni en shell injection clasica, sino en la **superficie local WebSocket del dashboard**: actualmente acepta conexiones sin autenticar ni validar `Origin`, y permite escribir acciones que luego se reinyectan en contexto. Ese vector habilita **context poisoning local** desde cualquier pagina web abierta en el navegador del usuario.

Tambien hay un problema funcional relevante: `commit-capture` usa `tool_result` mientras el resto del sistema/documentacion trabaja con `tool_output`, lo que puede dejar la captura de commits inoperativa de forma silenciosa.

---

## Hallazgos priorizados

| ID | Severidad | Estado | Hallazgo |
|---|---|---|---|
| SEC-01 | Critica | Open | WebSocket sin autenticacion ni validacion de `Origin` (expuesto a cross-site localhost abuse). |
| SEC-02 | Alta | Open | Acciones no confiables del dashboard se persisten y se reinyectan como contexto (riesgo de context poisoning). |
| SEC-03 | Media | Open | Logging en DEBUG por defecto en MCP imprime argumentos/mensajes potencialmente sensibles. |
| REL-01 | Alta | Open | `commit-capture` usa clave de payload inconsistente (`tool_result`) y puede no capturar commits. |
| REL-02 | Media | Open | Falta validacion estricta de limites/tipos en herramientas MCP; posible DoS/errores internos. |
| SEC-04 | Media | Open | Flujo de update/instalacion basado en `curl|bash`/`irm|iex` sin verificacion de integridad. |
| SEC-05 | Baja | Open | `secret-guard` ignora todo `.env*` (incluyendo `.env.example`), creando punto ciego. |
| CLN-01 | Baja | Open | Inconsistencia de orden de prioridad de "pinned" entre core y GUI. |
| CLN-02 | Baja | Open | Regex de "memoria enabled" duplicada en 4 sitios (riesgo de deriva). |

---

### SEC-01 (Critica)

**Evidencia**

- `gui/server.py:411` (handshake aceptado tras parseo minimo)
- `gui/server.py:449` (procesa mensajes `action` sin autenticacion)
- `gui/websocket.py:166` (solo verifica `Upgrade: websocket`)
- `gui/websocket.py:171` (extrae `Sec-WebSocket-Key`, sin validar `Origin`)

**Impacto**

Cualquier web abierta en el navegador puede intentar conectar a `ws://127.0.0.1:<puerto>` y enviar acciones al dashboard local.

**Recomendacion**

- Requerir token de sesion efimero (nonce) en handshake o primer mensaje.
- Validar `Origin` contra `http://127.0.0.1:<http_port>` y `http://localhost:<http_port>`.
- Rechazar conexiones sin `Origin` esperado + token.

---

### SEC-02 (Alta)

**Evidencia**

- `gui/server.py:451` (payload de accion pasa a `process_gui_action`)
- `core/memory.py:1710` (payload se persiste como JSON sin sanitizacion/limite)
- `hooks/memory-compact.py:64` (acciones pendientes se reinyectan en contexto)

**Impacto**

Un payload malicioso puede terminar en contexto de compactacion y condicionar comportamiento posterior del agente (context poisoning), ademas de inflar contexto (DoS por tamano).

**Recomendacion**

- Schema estricto por tipo de accion (allowlist de campos y longitudes).
- Limite de tamano por payload (p.ej., 2-4 KB).
- Sanitizar texto de payload antes de persistir/reinyectar.
- Marcar acciones procesadas para evitar reinyeccion indefinida.

---

### SEC-03 (Media)

**Evidencia**

- `mcp/memory_server.py:61` (`logging.DEBUG` por defecto)
- `mcp/memory_server.py:787` (log de argumentos completos)
- `mcp/memory_server.py:1496` (log parcial de mensaje JSON-RPC recibido)

**Impacto**

Campos sensibles enviados por herramientas MCP pueden quedar en stderr/logs.

**Recomendacion**

- Nivel por defecto `INFO`.
- Activar `DEBUG` solo por variable de entorno.
- Redactar campos sensibles antes de loggear (query, payload, argumentos libres).

---

### REL-01 (Alta)

**Evidencia**

- `hooks/commit-capture.py:51` (`tool_result = data.get("tool_result", {})`)
- `hooks/commit-capture.py:54` (usa `tool_result.exit_code`)
- `docs/hooks.md:45` y `docs/hooks.md:394` (PostToolUse documentado con `tool_output`)

**Impacto**

Si el runtime solo expone `tool_output`, la captura automatica de commits puede no dispararse nunca (degradacion silenciosa de trazabilidad).

**Recomendacion**

- Leer `exit_code` desde `tool_output` y mantener fallback a `tool_result` por compatibilidad.
- Añadir test de integracion del `main()` con payload real de PostToolUse.

---

### REL-02 (Media)

**Evidencia**

- `mcp/memory_server.py:861` (`limit` sin cotas en `memory_search`)
- `mcp/memory_server.py:1223` (`limit` sin cotas en `memory_get_decisions`)
- `mcp/memory_server.py:1436` (`limit` sin cotas en `memory_import`)
- `mcp/memory_server.py:1258` (comparacion de `retention_days` sin validar tipo)
- `core/memory.py:1534` (`git log` en import sin timeout)

**Impacto**

Entradas anmalas pueden provocar consumo elevado, errores internos o operaciones largas.

**Recomendacion**

- Validar tipo/rango en cada handler MCP (`1..N`).
- Definir limites maximos razonables (`limit <= 500`, etc.).
- Añadir timeout a `import_git_history`.

---

### SEC-04 (Media)

**Evidencia**

- `commands/update.md:86` (`curl ... | bash`)
- `commands/update.md:93` (`irm ... | iex`)
- `README.md:22` y `README.md:34` (mismo patron para instalacion)

**Impacto**

Riesgo de supply-chain si origen remoto es comprometido.

**Recomendacion**

- Soportar instalacion por release firmado/checksum.
- Publicar hash SHA256 por version.
- Ofrecer alternativa "download + verify + execute".

---

### SEC-05 (Baja)

**Evidencia**

- `hooks/secret-guard.sh:79` (excluye `.env*` por patron amplio)

**Impacto**

Secretos reales en `.env.example`/`.env.sample` o variantes pueden colarse sin aviso del guard.

**Recomendacion**

- Mantener exclusion para `.env` real, pero revisar `.env.example/.sample` con modo warning (no bloqueante).

---

### CLN-01 (Baja)

**Evidencia**

- `core/memory.py:1822` (orden de pinned: `priority DESC`)
- `gui/server.py:210` (orden de pinned: `priority ASC`)

**Impacto**

Comportamiento incoherente entre capa core y GUI.

**Recomendacion**

Unificar criterio de prioridad en un solo lugar y reutilizarlo en ambos lados.

---

### CLN-02 (Baja)

**Evidencia**

- `hooks/commit-capture.py:121`
- `hooks/memory-compact.py:83`
- `hooks/memory-capture.py:136`
- `core/config_loader.py:797`

**Impacto**

Misma regex copiada en 4 archivos: cualquier ajuste puede quedar inconsistente.

**Recomendacion**

Extraer helper comun (`core/config_flags.py`) y reutilizar en hooks/core.

---

## Puntos fuertes detectados

1. `core/memory.py` usa SQL parametrizado de forma consistente (buena base contra SQL injection).
2. Persistencia de estado con escritura atomica en `core/orchestrator.py:545` y `core/orchestrator.py:548`.
3. Permisos restrictivos `0600` para DB en `core/memory.py:334`.
4. Defensa de secretos en dos capas: bloqueo preventivo (`hooks/secret-guard.sh`) + sanitizacion al persistir (`core/memory.py:154`).
5. Cobertura de tests del core claramente por encima de lo habitual para un plugin de este tipo (`tests/test_memory.py`, `tests/test_orchestrator.py`, etc.).
6. Servicios de GUI/MCP acotados a localhost (`gui/server.py:612`, `gui/server.py:648`).

---

## Puntos a mejorar (clean code y mantenibilidad)

1. Reducir archivos monoliticos (`hooks/session-start.sh`, `core/memory.py`, `mcp/memory_server.py`) con capas/servicios mas pequenos.
2. Homogeneizar contrato de eventos de hooks (`tool_output` vs `tool_result`) y centralizar parsing.
3. Definir schemas compartidos para acciones GUI y argumentos MCP para evitar validaciones dispersas.
4. Mejorar observabilidad segura (logs estructurados + redaccion + niveles por entorno).
5. Completar tests de hooks faltantes (especialmente `secret-guard.sh`, `sensitive-read-guard.py`, `session-start.sh`) y tests E2E de payload real.

---

## Plan de remediacion recomendado

### Fase 0 (24-48h)

- Corregir `REL-01` (payload de `commit-capture`).
- Bajar logging MCP a `INFO` + flag para `DEBUG` (`SEC-03`).
- Poner limites de `limit` y tipos basicos en handlers MCP (`REL-02`).

### Fase 1 (1 semana)

- Cerrar `SEC-01`: auth + origin check en WebSocket.
- Cerrar `SEC-02`: schema/limites/sanitizacion de acciones GUI.
- Unificar orden de prioridad y helper comun de memoria (`CLN-01`, `CLN-02`).

### Fase 2 (2-4 semanas)

- Endurecer instalacion/update con verificacion de integridad (`SEC-04`).
- Añadir warning controlado en `.env.example` (`SEC-05`).
- Mejorar arquitectura modular de hooks/core.

---

## Historico de cambios del documento

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-02-22 | Creacion inicial de auditoria viva | Codex |
