# Changelog

Todos los cambios relevantes del proyecto se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

---

## [0.3.0] - 2026-02-22

### Added

- **Dashboard GUI** (Fase Alpha): dashboard web en tiempo real que muestra el estado completo del proyecto sin intervenir en el terminal. 7 vistas: estado, timeline, decisiones, agentes, memoria, commits y marcados. Se lanza con `/alfred gui` y se abre automáticamente en el navegador.
- **Servidor monolítico Python**: HTTP estático (puerto 7533) + WebSocket RFC 6455 manual (puerto 7534) + SQLite watcher (polling 500 ms). Sin dependencias externas.
- **Protocolo WebSocket bidireccional**: mensajes `init` (estado completo al conectar), `update` (cambios incrementales), `action` (acciones del usuario) y `action_ack` (confirmación). Reconexión automática con backoff exponencial (1s a 30s).
- **Sistema de marcado** (pinning): elementos marcados manual o automáticamente sobreviven a la compactación del contexto. Se inyectan como `additionalContext` vía `memory-compact.py`.
- **Tablas SQLite nuevas**: `gui_actions` (cola de acciones del dashboard) y `pinned_items` (elementos marcados). Migración automática a esquema v3.
- **Comando `/alfred gui`**: abre el dashboard en el navegador por defecto. Si el servidor no está corriendo, lo arranca automáticamente.
- **Arranque automático**: `session-start.sh` levanta el servidor GUI en background al inicio de cada sesión si existe la base de datos de memoria. `stop-hook.py` lo para al cerrar.
- **Principio fail-open**: si la GUI falla, Alfred funciona exactamente igual que sin ella. Los hooks siguen escribiendo en SQLite.
- **Landing page**: sección Dashboard con galería de 7 capturas, etiqueta Fase Alpha, situada entre Agentes y Quality gates.
- **Documentación completa**: `docs/gui.md` con arquitectura, protocolo WebSocket, esquema de tablas, guía de desarrollo y solución de problemas.
- 29 tests nuevos para el módulo GUI. Total: 297 tests.

### Changed

- Versión bumpeada de 0.2.3 a 0.3.0 en plugin.json, marketplace.json, package.json, install.sh, install.ps1 y memory_server.py.
- README.md ampliado con capturas del dashboard y enlace a documentación técnica.
- `docs/README.md` actualizado con entrada para gui.md en la navegación.


## [0.2.3] - 2026-02-21

### Added

- **Memoria persistente v2**: migración de esquema con backup automático, etiquetas y estado en decisiones, relaciones entre decisiones (`supersedes`, `depends_on`, `contradicts`, `relates`), campo `files` en commits.
- **5 herramientas MCP nuevas** (total 15): `memory_update_decision`, `memory_link_decisions`, `memory_health`, `memory_export`, `memory_import`.
- **Filtros de búsqueda**: parámetros `since`, `until`, `tags` y `status` en `memory_search` y `memory_get_decisions`.
- **Validación de integridad**: `memory_health` comprueba versión de esquema, FTS5, permisos y tamaño de la DB.
- **Export/Import**: exportar decisiones a Markdown (formato ADR), importar desde historial Git e importar desde ficheros ADR existentes.
- **Hook commit-capture.py** (PostToolUse Bash): auto-captura de commits en la memoria persistente. Detecta `git commit` con regex y registra SHA, mensaje, autor y ficheros.
- **Hook memory-compact.py** (PreCompact): protege las decisiones críticas de la sesión durante la compactación de contexto.
- **Inyección de contexto mejorada**: si hay iteración activa, session-start.sh inyecta las decisiones de esa iteración (no las 5 últimas globales). Muestra etiquetas de las decisiones.
- ~49 tests nuevos. Total estimado: ~268 tests.

### Changed

- El Bibliotecario amplía sus capacidades: gestión del ciclo de vida de decisiones, validación de integridad, exportación e importación. 15 herramientas MCP documentadas.
- `memory_log_decision` acepta parámetro `tags`. `memory_log_commit` acepta parámetro `files`.


## [0.2.2] - 2026-02-21

### Added

- **Hook dangerous-command-guard.py** (PreToolUse Bash): bloquea comandos destructivos antes de que se ejecuten. Cubre `rm -rf /`, force push a main/master, `DROP DATABASE/TABLE`, `docker system prune -af`, fork bombs, `mkfs`/`dd` sobre dispositivos y `git reset --hard origin/main`. Política fail-open.
- **Hook sensitive-read-guard.py** (PreToolUse Read): aviso informativo al leer ficheros sensibles (claves privadas, `.env`, credenciales AWS/SSH/GPG, keystores Java). No bloquea, solo alerta.
- **4 herramientas MCP nuevas**: `memory_get_stats`, `memory_get_iteration`, `memory_get_latest_iteration`, `memory_abandon_iteration`. Total: 10 herramientas.
- **3 skills nuevos**: incident-response, release-planning, dependency-strategy.
- Capacidades ampliadas en arquitecto, security officer y senior dev.
- `/alfred feature` permite seleccionar la fase de inicio del flujo.
- Test de consistencia de versión que verifica que los 5 ficheros con versión declaran el mismo valor.
- 5 ficheros de tests nuevos (219 tests en total).

### Fixed

- **quality-gate.py**: corregido ancla de posición para runners de una palabra. `cat pytest.ini` ya no activa el hook. Aplicado `re.IGNORECASE` a la detección de fallos para cubrir variantes de case mixto.
- **Respuestas MCP**: las respuestas de error ahora se marcan con `isError: true` en el protocolo MCP en vez de devolverse como respuestas exitosas.
- **Encapsulación en MemoryDB**: `get_latest_iteration()` expuesto como método público. El servidor MCP ya no accede al atributo privado `_conn`.
- Logging en bloques `except` silenciosos en `config_loader.py`, `session-start.sh` y `orchestrator.py`.
- Instrucciones de recuperación en el mensaje de error de estado de sesión corrupto.
- `User-Agent: alfred-dev-plugin` en las peticiones a la API de GitHub desde session-start.sh.

## [0.2.1] - 2026-02-21

### Fixed

- **Ruta de caché en scripts de Windows** (install.ps1, uninstall.ps1): alineada con la convención de Claude Code (`cache/<marketplace>/<plugin>/<version>`). Los usuarios de Windows tenían instalaciones rotas.
- **memory-capture.py**: los 4 bloques `except` que tragaban errores silenciosamente ahora emiten diagnóstico por stderr.
- **session-start.sh**: el `except Exception` genérico del bloque de memoria reemplazado por catches específicos (`ImportError`, `OperationalError`, `DatabaseError`) con mensajes descriptivos.

### Changed

- Landing page disponible en dominio personalizado [alfred-dev.com](https://alfred-dev.com).

## [0.2.0] - 2026-02-20

### Added

- **Memoria persistente por proyecto**: base de datos SQLite local (`.claude/alfred-memory.db`) que registra decisiones, commits, iteraciones y eventos entre sesiones. Activación opcional con `/alfred config`.
- **Servidor MCP integrado**: servidor MCP stdio sin dependencias externas con 6 herramientas: `memory_search`, `memory_log_decision`, `memory_log_commit`, `memory_get_iteration`, `memory_get_timeline`, `memory_stats`.
- **Agente El Bibliotecario**: agente opcional para consultas históricas sobre el proyecto. Cita fuentes con formato `[D#id]`, `[C#sha]`, `[I#id]`.
- **Hook memory-capture.py**: captura automática de eventos del flujo de trabajo (inicio/fin de iteraciones, cambios de fase) en la memoria persistente.
- Inyección de contexto de memoria al inicio de sesión (últimas 5 decisiones, iteración activa).
- Sección de configuración de memoria en `/alfred config`.
- Sanitización de secretos en la memoria con los mismos patrones que `secret-guard.sh`.
- Permisos 0600 en el fichero de base de datos.
- Búsqueda de texto completo con FTS5 (cuando disponible) o fallback a LIKE.
- 58 tests nuevos para el módulo de memoria. Total: 114 tests.

### Changed

- Agentes opcionales pasan de 6 a 7 (nuevo: librarian / El Bibliotecario).

## [0.1.5] - 2026-02-20

### Fixed

- **Secret-guard con política fail-closed**: cuando el hook detecta contenido a escribir pero no puede determinar la ruta del fichero destino, ahora bloquea la operación (exit 2) en lugar de permitirla.
- **Instalador idempotente en entorno limpio**: `mkdir -p` para crear `~/.claude/plugins/` si no existe. En instalaciones donde Claude Code no había creado ese directorio, el script abortaba.
- **Detección de versión en `/alfred update`**: el comando anterior concatenaba todos los `plugin.json` de la caché con un glob, rompiendo `json.load`. Ahora selecciona explícitamente el fichero más reciente por fecha de modificación.

### Changed

- README actualizado con cifras reales: 56 skills en 13 dominios y 6 hooks.

## [0.1.4] - 2026-02-19

### Added

- **Sistema de agentes opcionales**: 6 nuevos agentes activables con `/alfred config`: data-engineer, ux-reviewer, performance-engineer, github-manager, seo-specialist, copywriter.
- **Descubrimiento contextual**: Alfred analiza el proyecto y sugiere qué agentes opcionales activar.
- **27 skills nuevos en 6 dominios**: datos (3), UX (3), rendimiento (3), GitHub (4), SEO (3), marketing (3). Ampliaciones en seguridad (+1), calidad (+2), documentación (+5). Total: 56 skills en 13 dominios.
- **Soporte Windows**: `install.ps1` y `uninstall.ps1` nativos en PowerShell con `irm | iex`.
- **Hook spelling-guard.py**: detección de tildes omitidas en castellano al escribir o editar ficheros. Diccionario de 60+ palabras.
- **Quality gates ampliados**: de 8 a 18 (10 de núcleo + 8 opcionales).
- Autoinstalación de herramientas: los agentes que dependen de herramientas externas (Docker, gh CLI, Lighthouse) preguntan al usuario antes de instalar.
- Detección de plataforma en `/alfred update` (bash en macOS/Linux, PowerShell en Windows).

### Changed

- Landing page actualizada con secciones de agentes opcionales, nuevos dominios de skills, tabs de instalación multiplataforma.
- Tests: 56 (antes 23).

## [0.1.2] - 2026-02-18

### Fixed

- **Prefijo correcto en comandos**: `/alfred-dev:feature`, `/alfred-dev:update`, etc.
- **Comando update robusto**: detecta la versión instalada dinámicamente.
- **Registro explícito de comandos**: los 10 comandos declarados en `plugin.json` para garantizar su descubrimiento.

### Changed

- **Nueva personalidad de Alfred**: compañero cercano y con humor, en lugar de mayordomo solemne. Los 8 agentes tienen voz propia.
- Corrección ortográfica completa en los 68 ficheros del plugin (tildes, eñes, diacríticos según RAE).

## [0.1.1] - 2026-02-18

### Fixed

- **[Alta] session-start.sh**: corregido error de sintaxis en línea 125 (paréntesis huérfano + redirección `2>&2`) que impedía la ejecución del hook SessionStart.
- **[Media] secret-guard.sh**: arreglada política fail-closed. Con `set -e`, un fallo de parseo salía con código 1 en vez de 2. Ahora bloquea correctamente ante errores de análisis.
- **[Media] stop-hook.py + orchestrator.py**: validación de tipos para claves del estado de sesión. Un JSON corrupto con tipos incorrectos ya no provoca TypeError.

### Changed

- **install.sh + uninstall.sh**: eliminada interpolación directa de variables bash dentro de `python3 -c`. Ahora usa `sys.argv` con heredocs (`<<'PYEOF'`), inmune a rutas con caracteres especiales.
- Eliminada constante `HARD_GATES` no usada en orchestrator.py (código muerto).

## [0.1.0] - 2026-02-18

### Added

- Primera release pública.
- 8 agentes especializados con personalidad propia (producto, arquitectura, desarrollo, seguridad, QA, DevOps, documentación, orquestación).
- 5 flujos de trabajo: feature (6 fases), fix (3 fases), spike (2 fases), ship (4 fases), audit (paralelo).
- 29 skills organizados en 7 dominios.
- Quality gates infranqueables en cada fase.
- Compliance RGPD/NIS2/CRA integrado.
- 5 hooks de protección automática (secretos, calidad, dependencias, parada, arranque).
- Detección automática de stack tecnológico (Node.js, Python, Rust, Go, Ruby, Elixir, Java, PHP, C#, Swift).
- Sistema de actualizaciones basado en releases de GitHub.
- Asistente contextual al invocar `/alfred` sin subcomando.

---

[0.2.3]: https://github.com/686f6c61/alfred-dev/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/686f6c61/alfred-dev/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/686f6c61/alfred-dev/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/686f6c61/alfred-dev/compare/v0.1.5...v0.2.0
[0.1.5]: https://github.com/686f6c61/alfred-dev/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/686f6c61/alfred-dev/compare/v0.1.2...v0.1.4
[0.1.2]: https://github.com/686f6c61/alfred-dev/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/686f6c61/alfred-dev/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/686f6c61/alfred-dev/releases/tag/v0.1.0
