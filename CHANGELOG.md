# Changelog

Todos los cambios relevantes del proyecto se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [versionado semantico](https://semver.org/lang/es/).

---

## [0.2.2] - 2026-02-21

### Added

- **Hook dangerous-command-guard.py** (PreToolUse Bash): bloquea comandos destructivos antes de que se ejecuten. Cubre `rm -rf /`, force push a main/master, `DROP DATABASE/TABLE`, `docker system prune -af`, fork bombs, `mkfs`/`dd` sobre dispositivos y `git reset --hard origin/main`. Politica fail-open.
- **Hook sensitive-read-guard.py** (PreToolUse Read): aviso informativo al leer ficheros sensibles (claves privadas, `.env`, credenciales AWS/SSH/GPG, keystores Java). No bloquea, solo alerta.
- **4 herramientas MCP nuevas**: `memory_get_stats`, `memory_get_iteration`, `memory_get_latest_iteration`, `memory_abandon_iteration`. Total: 10 herramientas.
- **3 skills nuevos**: incident-response, release-planning, dependency-strategy.
- Capacidades ampliadas en arquitecto, security officer y senior dev.
- `/alfred feature` permite seleccionar la fase de inicio del flujo.
- Test de consistencia de version que verifica que los 5 ficheros con version declaran el mismo valor.
- 5 ficheros de tests nuevos (219 tests en total).

### Fixed

- **quality-gate.py**: corregido ancla de posicion para runners de una palabra. `cat pytest.ini` ya no activa el hook. Aplicado `re.IGNORECASE` a la deteccion de fallos para cubrir variantes de case mixto.
- **Respuestas MCP**: las respuestas de error ahora se marcan con `isError: true` en el protocolo MCP en vez de devolverse como respuestas exitosas.
- **Encapsulacion en MemoryDB**: `get_latest_iteration()` expuesto como metodo publico. El servidor MCP ya no accede al atributo privado `_conn`.
- Logging en bloques `except` silenciosos en `config_loader.py`, `session-start.sh` y `orchestrator.py`.
- Instrucciones de recuperacion en el mensaje de error de estado de sesion corrupto.
- `User-Agent: alfred-dev-plugin` en las peticiones a la API de GitHub desde session-start.sh.

## [0.2.1] - 2026-02-21

### Fixed

- **Ruta de cache en scripts de Windows** (install.ps1, uninstall.ps1): alineada con la convencion de Claude Code (`cache/<marketplace>/<plugin>/<version>`). Los usuarios de Windows tenian instalaciones rotas.
- **memory-capture.py**: los 4 bloques `except` que tragaban errores silenciosamente ahora emiten diagnostico por stderr.
- **session-start.sh**: el `except Exception` generico del bloque de memoria reemplazado por catches especificos (`ImportError`, `OperationalError`, `DatabaseError`) con mensajes descriptivos.

### Changed

- Landing page disponible en dominio personalizado [alfred-dev.com](https://alfred-dev.com).

## [0.2.0] - 2026-02-20

### Added

- **Memoria persistente por proyecto**: base de datos SQLite local (`.claude/alfred-memory.db`) que registra decisiones, commits, iteraciones y eventos entre sesiones. Activacion opcional con `/alfred config`.
- **Servidor MCP integrado**: servidor MCP stdio sin dependencias externas con 6 herramientas: `memory_search`, `memory_log_decision`, `memory_log_commit`, `memory_get_iteration`, `memory_get_timeline`, `memory_stats`.
- **Agente El Bibliotecario**: agente opcional para consultas historicas sobre el proyecto. Cita fuentes con formato `[D#id]`, `[C#sha]`, `[I#id]`.
- **Hook memory-capture.py**: captura automatica de eventos del flujo de trabajo (inicio/fin de iteraciones, cambios de fase) en la memoria persistente.
- Inyeccion de contexto de memoria al inicio de sesion (ultimas 5 decisiones, iteracion activa).
- Seccion de configuracion de memoria en `/alfred config`.
- Sanitizacion de secretos en la memoria con los mismos patrones que `secret-guard.sh`.
- Permisos 0600 en el fichero de base de datos.
- Busqueda de texto completo con FTS5 (cuando disponible) o fallback a LIKE.
- 58 tests nuevos para el modulo de memoria. Total: 114 tests.

### Changed

- Agentes opcionales pasan de 6 a 7 (nuevo: librarian / El Bibliotecario).

## [0.1.5] - 2026-02-20

### Fixed

- **Secret-guard con politica fail-closed**: cuando el hook detecta contenido a escribir pero no puede determinar la ruta del fichero destino, ahora bloquea la operacion (exit 2) en lugar de permitirla.
- **Instalador idempotente en entorno limpio**: `mkdir -p` para crear `~/.claude/plugins/` si no existe. En instalaciones donde Claude Code no habia creado ese directorio, el script abortaba.
- **Deteccion de version en `/alfred update`**: el comando anterior concatenaba todos los `plugin.json` de la cache con un glob, rompiendo `json.load`. Ahora selecciona explicitamente el fichero mas reciente por fecha de modificacion.

### Changed

- README actualizado con cifras reales: 56 skills en 13 dominios y 6 hooks.

## [0.1.4] - 2026-02-19

### Added

- **Sistema de agentes opcionales**: 6 nuevos agentes activables con `/alfred config`: data-engineer, ux-reviewer, performance-engineer, github-manager, seo-specialist, copywriter.
- **Descubrimiento contextual**: Alfred analiza el proyecto y sugiere que agentes opcionales activar.
- **27 skills nuevos en 6 dominios**: datos (3), UX (3), rendimiento (3), GitHub (4), SEO (3), marketing (3). Ampliaciones en seguridad (+1), calidad (+2), documentacion (+5). Total: 56 skills en 13 dominios.
- **Soporte Windows**: `install.ps1` y `uninstall.ps1` nativos en PowerShell con `irm | iex`.
- **Hook spelling-guard.py**: deteccion de tildes omitidas en castellano al escribir o editar ficheros. Diccionario de 60+ palabras.
- **Quality gates ampliados**: de 8 a 18 (10 de nucleo + 8 opcionales).
- Autoinstalacion de herramientas: los agentes que dependen de herramientas externas (Docker, gh CLI, Lighthouse) preguntan al usuario antes de instalar.
- Deteccion de plataforma en `/alfred update` (bash en macOS/Linux, PowerShell en Windows).

### Changed

- Landing page actualizada con secciones de agentes opcionales, nuevos dominios de skills, tabs de instalacion multiplataforma.
- Tests: 56 (antes 23).

## [0.1.2] - 2026-02-18

### Fixed

- **Prefijo correcto en comandos**: `/alfred-dev:feature`, `/alfred-dev:update`, etc.
- **Comando update robusto**: detecta la version instalada dinamicamente.
- **Registro explicito de comandos**: los 10 comandos declarados en `plugin.json` para garantizar su descubrimiento.

### Changed

- **Nueva personalidad de Alfred**: companero cercano y con humor, en lugar de mayordomo solemne. Los 8 agentes tienen voz propia.
- Correccion ortografica completa en los 68 ficheros del plugin (tildes, enes, diacriticos segun RAE).

## [0.1.1] - 2026-02-18

### Fixed

- **[Alta] session-start.sh**: corregido error de sintaxis en linea 125 (parentesis huerfano + redireccion `2>&2`) que impedia la ejecucion del hook SessionStart.
- **[Media] secret-guard.sh**: arreglada politica fail-closed. Con `set -e`, un fallo de parseo salia con codigo 1 en vez de 2. Ahora bloquea correctamente ante errores de analisis.
- **[Media] stop-hook.py + orchestrator.py**: validacion de tipos para claves del estado de sesion. Un JSON corrupto con tipos incorrectos ya no provoca TypeError.

### Changed

- **install.sh + uninstall.sh**: eliminada interpolacion directa de variables bash dentro de `python3 -c`. Ahora usa `sys.argv` con heredocs (`<<'PYEOF'`), inmune a rutas con caracteres especiales.
- Eliminada constante `HARD_GATES` no usada en orchestrator.py (codigo muerto).

## [0.1.0] - 2026-02-18

### Added

- Primera release publica.
- 8 agentes especializados con personalidad propia (producto, arquitectura, desarrollo, seguridad, QA, DevOps, documentacion, orquestacion).
- 5 flujos de trabajo: feature (6 fases), fix (3 fases), spike (2 fases), ship (4 fases), audit (paralelo).
- 29 skills organizados en 7 dominios.
- Quality gates infranqueables en cada fase.
- Compliance RGPD/NIS2/CRA integrado.
- 5 hooks de proteccion automatica (secretos, calidad, dependencias, parada, arranque).
- Deteccion automatica de stack tecnologico (Node.js, Python, Rust, Go, Ruby, Elixir, Java, PHP, C#, Swift).
- Sistema de actualizaciones basado en releases de GitHub.
- Asistente contextual al invocar `/alfred` sin subcomando.

---

[0.2.2]: https://github.com/686f6c61/alfred-dev/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/686f6c61/alfred-dev/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/686f6c61/alfred-dev/compare/v0.1.5...v0.2.0
[0.1.5]: https://github.com/686f6c61/alfred-dev/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/686f6c61/alfred-dev/compare/v0.1.2...v0.1.4
[0.1.2]: https://github.com/686f6c61/alfred-dev/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/686f6c61/alfred-dev/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/686f6c61/alfred-dev/releases/tag/v0.1.0
