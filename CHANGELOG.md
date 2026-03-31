# Changelog

Todos los cambios relevantes del proyecto se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

---

## [0.6.0] - 2026-03-31

### Added

- **Lucius — El Director Técnico**: nuevo agente opcional que actúa como segunda opinión técnica externa. Invoca el Codex CLI de OpenAI (`codex review`) con GPT-5.4 para auditar el código del proyecto desde una perspectiva externa, sin modificar ningún fichero. Requiere Codex CLI instalado y suscripción activa de OpenAI (Plus o Pro).
- **Comando `/alfred-dev:lucius`**: punto de entrada para invocar la auditoría. Acepta directorio objetivo y scope opcionales (`all`, `security`, `tests`, `architecture`, `performance`).
- **Informe estructurado por ítem**: Lucius devuelve diagnóstico + prescripción + esfuerzo (S/M/L) + sugerencia de con quién implementar (Alfred o Codex) en cuatro secciones: Crítico, Relevante, Oportunidades y Lo que está bien.
- **Preflight de prerequisitos**: verifica que `codex` está en el PATH y autenticado. Si falta algún requisito, para con instrucciones claras de instalación.
- **HARD-GATE sin modificaciones**: el subcomando `codex review` activa `sandbox: read-only` y `approval: never` de forma nativa, garantizando que ningún fichero se toca.

### Changed

- **19 agentes totales**: el plugin pasa de 18 a 19 agentes (10 de núcleo + 9 opcionales) con la incorporación de Lucius.
- **26 comandos**: se añade `/alfred-dev:lucius` al manifiesto del plugin.
- **Versionado coherente a 0.6.0**: plugin, marketplace, instaladores, paquetes, README, changelog, docs y landing quedan alineados.
- **Landing actualizada**: tarjeta de Lucius antes de Selina con badge «Nuevo», agente opcional con use cases, counts actualizados a 19 agentes y 26 comandos.

---

## [0.5.0] - 2026-03-31

### Added

- **Selina — La Estilista**: nuevo agente de núcleo (10.º) que ocupa la fase 1b del flujo `feature`. Presenta tres direcciones de estilo visual en el navegador antes de que el architect diseñe componentes. Solo se activa si el proyecto tiene interfaz de usuario.
- **Servidor visual local**: servidor HTTP + WebSocket de dependencias cero (`visual/scripts/server.cjs`) para renderizar opciones de estilo en tres columnas. Gestiona sesiones por proyecto, hot-reload vía `fs.watch`, registro de clics en `state/events` y cierre limpio ante `SIGTERM`.
- **Skill de estilo visual** (`skills/estilo/style-direction/SKILL.md`): guía completa para que Selina arranque el servidor, escriba el HTML de opciones con `.style-grid`, lea la elección del usuario y genere `docs/style-direction.md`.
- **Fase condicional `estilo_visual`**: nueva condición `"tiene_frontend"` en el orquestador. La función `config_loader.has_frontend(stack)` evalúa el stack del proyecto y permite que `advance_phase()` salte la fase automáticamente en proyectos sin UI.
- **Helper `_advance_skipping_phases`**: función extraída del orquestador para gestionar el salto de fases con condición no cumplida, reduciendo la complejidad cognitiva de `advance_phase`.

### Changed

- **5 agentes actualizados** para leer `docs/style-direction.md` como referencia de estilo: `architect`, `senior-dev`, `ux-reviewer`, `copywriter`, `seo-specialist`.
- **`feature.md` actualizado**: documenta la fase 1b con instrucción explícita de activar Selina con la herramienta Task.
- **`plugin.json` actualizado**: incluye el agente Selina y el skill de estilo visual en el manifiesto. Descripción actualizada a 10 agentes de núcleo.
- **README actualizado**: recuento de agentes (9 → 10), fases (6 → 7), tabla de agentes con Selina, ejemplo de flujo con fase 1b.

### Fixed

- **Imports de módulos nativos**: `server.cjs` usa ahora el prefijo `node:` (`node:http`, `node:crypto`, `node:fs`, `node:path`) según la convención canónica de Node.js ≥18.
- **`Number.parseInt` en lugar de `parseInt`** en `server.cjs` para cumplir con las reglas de linting de SonarQube.
- **Complejidad cognitiva de `handleRequest` reducida**: el bloque `/files/*` se extrae a `serveStaticFile()`.
- **`catch` sin variable no usada**: el bloque `catch (e)` en `serveStaticFile` pasa a `catch {}` eliminando la variable no referenciada.
- **Complejidad cognitiva en `config_loader.py`**: `_count_source_files` (38 → ~6) y `suggest_optional_agents` (18 → ~3) resueltas extrayendo `_scan_dir_for_sources` (recursivo, reemplaza el triple bucle manual) y `_build_suggestion_checks` (lista de checks, elimina las 8 ramas if/elif).
- **Skill de SonarQube registrado en `plugin.json`**: el fichero `skills/calidad/sonarqube/SKILL.md` existía en disco pero no estaba en el array `skills` del manifiesto del plugin, por lo que Claude Code no lo cargaba.
- **Permisos de Docker en subagentes**: los comandos Docker añadidos a `~/.claude/settings.json` como entradas `Bash(docker ...)` permiten que el `security-officer` arranque SonarQube sin prompt de confirmación al usuario.

---

## [0.4.7] - 2026-03-31

### Fixed

- **Hook SessionStart robusto**: la emisión JSON del contexto de sesión ya no se trunca cuando el contenido supera `ARG_MAX` del kernel o contiene caracteres especiales (tildes, backticks, comillas, barras invertidas). La causa raíz era que `escape_for_json()` pasaba el contexto como `sys.argv[1]`, sujeto al límite de tamaño de argumentos del sistema operativo.

### Changed

- **Emisión JSON por stdin**: la generación del JSON del hook pasa de interpolación en heredoc bash con `escape_for_json()` a emisión directa por stdin con `json.dumps()` en una nueva función `emit_hook_json()`, eliminando la clase de error por completo.
- **Versionado coherente a 0.4.7**: plugin, marketplace, instaladores, paquetes, metadata estructurada, README, changelog, docs y landing quedan alineados.

## [0.4.6] - 2026-03-23

### Added

- **Memory UI local**: nuevo `/alfred-dev:memory-ui` para abrir una vista viva en navegador sobre la SQLite del proyecto con overview, timeline, decisiones, grafo, commits, búsqueda, salud y señales operativas de SonIA.
- **Memory UI reforzada para produccion**: los flujos helper-first (`map-codebase`, `discuss`, `quick`) ya siembran progreso, trazabilidad y kanban de forma natural, la UI importa commits Git si faltan en memoria y muestra mejor los estados vacios.
- **Cobertura E2E de Memory UI**: nuevos tests para servidor local, contratos del comando y siembra helper-first que valida timeline, decisiones, commits y señales operativas sin rellenar SQLite a mano.

### Changed

- **Versionado coherente a 0.4.6**: plugin, marketplace, instaladores, paquetes, metadata estructurada, README, changelog, docs y landing quedan alineados.
- **Superficie pública actualizada**: Alfred refleja ahora `25` comandos y `13` hooks visibles, con `memory-ui` integrada en help, session-start, documentación y web.
- **Publicación más limpia**: se retiran del repositorio los documentos internos de planificación `docs/superpowers/` y se ignoran para no incluirlos en futuras releases.

## [0.4.5] - 2026-03-22

### Added

- **PM operativo determinista para SonIA**: nuevos comandos `/alfred-dev:standup`, `/alfred-dev:blocked`, `/alfred-dev:in-progress`, `/alfred-dev:validate` y `/alfred-dev:search` para explotar el kanban local, la trazabilidad y la memoria del proyecto desde CLI sin abrir siempre un flujo multiagente.
- **SonIA Sync para GitHub**: nuevo `/alfred-dev:sync-github [owner/repo]` para sincronizar backlog, trabajo en curso, bloqueos y tablero de SonIA usando `gh`, manteniendo `docs/project/` y `.claude/` como fuente de verdad local.
- **Busqueda unificada proyecto + memoria**: `search` cruza artefactos operativos (`docs/project/`) con la SQLite del proyecto y devuelve resultados accionables en una sola vista.
- **Validacion operativa del tablero**: `validate` detecta IDs de tarea duplicados, huecos de trazabilidad, falta de evidencia en `done`, bloqueos mal descritos, UAT pendiente y drift del sync local con GitHub.
- **Cobertura PM y GitHub ampliada**: nuevos tests para wrappers helper-first, parser del kanban de SonIA, renderizados operativos, sincronizacion a GitHub y smokes directos del helper CLI.

### Changed

- **SonIA pasa de agente interno a capa operativa visible**: `progress`, `standup`, `blocked`, `in-progress`, `validate` y `search` convierten el backlog local en una interfaz diaria real para Claude Code CLI.
- **Continuity.py se amplía a PM colaborativo**: la capa determinista ya no cubre solo continuidad y UAT, sino tambien vistas PM, validacion de artefactos y sync opcional con GitHub Issues.
- **Versionado coherente a 0.4.5**: plugin, marketplace, instaladores, paquetes, metadata estructurada, README, changelog, docs y landing quedan alineados.
- **Superficie pública actualizada**: Alfred refleja ahora `24` comandos y `13` hooks visibles, con la capa PM/GitHub integrada en help, session-start, documentación y web.

## [0.4.4] - 2026-03-22

### Fixed

- **FTS de eventos consistente**: los eventos con `content` ya son buscables en `memory_search` y `check_health()` deja de marcar la memoria como corrupta tras el primer evento indexado.
- **Purga limpia el indice FTS**: `purge_old_events()` elimina tambien las filas de `memory_fts`, evitando huerfanos y falsos errores despues de aplicar la retencion.
- **Tamano real de la DB en modo WAL**: `memory_health` suma ahora `.db`, `-wal` y `-shm`, de modo que el tamano reportado refleja el consumo real.
- **Importacion Git robusta**: `import_git_history()` y la captura de `git commit` ya no rompen mensajes o autores cuando el subject contiene el caracter `|`.
- **Sin techos silenciosos en sync/export**: la proyeccion a memoria nativa y la exportacion de decisiones dejan de truncarse en los primeros 1000 registros.

### Added

- **Capa operativa de continuidad**: nuevos comandos `/alfred-dev:map-codebase`, `/alfred-dev:discuss`, `/alfred-dev:next`, `/alfred-dev:pause`, `/alfred-dev:resume`, `/alfred-dev:progress`, `/alfred-dev:verify` y `/alfred-dev:quick` para orientar, pausar, retomar, mapear brownfield y cerrar UAT sin abrir siempre un flujo multiagente completo.
- **Helper determinista `core/continuity.py`**: nueva base común para continuidad CLI, artefactos `codebase-map.md`, `current.md`, `handoff.md`, `uat.md` y sesiones ligeras reproducibles.
- **Parser compartido de configuracion de memoria**: nuevo modulo `core/memory_config.py` para resolver defaults y leer `memoria.enabled`, `sync_to_native`, `sync_commits_limit`, `capture_decisions`, `capture_commits` y `retention_days` de forma uniforme.
- **Hardening helper-first en Claude CLI**: bootstrap de sesión, wrapper local `.claude/alfred-continuity.py`, autoallow de helpers seguros y barreras de prefetch para que `map-codebase` y el brownfield de `/alfred-dev:alfred` funcionen de forma natural en `claude -p`.
- **Cobertura de regresion ampliada**: tests nuevos para FTS de eventos, purga + salud, tamaño con WAL, importacion Git con `|`, config efectiva del servidor MCP, parser de memoria y sync mas alla de 1000 decisiones.

### Changed

- **Alfred decide mejor el siguiente paso**: el asistente contextual ya no solo clasifica `feature/fix/spike/audit`, sino también continuidad, brownfield, UAT y progreso operativo antes de abrir agentes.
- **La configuracion de memoria ya se aplica de verdad**: `capture_decisions`, `capture_commits`, `retention_days` y `sync_commits_limit` pasan a estar cableados en hooks, servidor MCP y sincronizacion nativa.
- **Versionado coherente a 0.4.4**: plugin, marketplace, instaladores, paquetes, servidor MCP, informes y metadata de la web quedan alineados.
- **Web, README y documentacion alineados**: la landing, el README y los docs reflejan ya el modelo actual de Alfred (`18` comandos, `6` flujos, `12` hooks, continuidad operativa y memoria persistente real).
- **Documentacion de memoria actualizada**: README, `docs/memory.md`, `docs/configuration.md` y `commands/config.md` reflejan el comportamiento real del sistema y el esquema actual.

---

## [0.4.3] - 2026-03-21

### Fixed

- **Preflight obligatorio de SonarQube en `/alfred audit`**: la auditoria ahora comprueba Docker antes de lanzar agentes y no deja que SonarQube se omita silenciosamente cuando falta el daemon o hacen falta permisos.
- **Pregunta interactiva incluso en autopilot**: si hay que instalar Docker, arrancarlo o abrir Docker Desktop, Alfred pide confirmacion explicita al usuario antes de tocar el sistema.
- **Skill de SonarQube endurecido**: el skill ya no asume permisos, contempla contenedor previo, puerto `9000` ocupado y limpieza final aunque el analisis falle.
- **Ayuda alineada con el equipo real**: `/alfred help` vuelve a listar los 9 agentes de nucleo incluyendo `project-manager (SonIA)`.

### Added

- **Tests de contrato para prompts operativos**: nueva cobertura de regresion para asegurar que `audit.md` y `skills/calidad/sonarqube/SKILL.md` siguen pidiendo permisos y documentando la omision de SonarQube cuando corresponde.

### Changed

- **Versionado coherente a 0.4.3**: plugin, marketplace, instaladores, paquetes y referencias visibles de la web quedan alineados en una sola version.

---

## [0.4.2] - 2026-03-14

### Fixed

- **Falso positivo en evidence guard**: el patron `\d+ failures` detectaba "0 failures" como fallo. Corregido para excluir el cero.
- **Gate de arquitectura mal tipada**: la fase de arquitectura del flujo feature tenia gate `usuario` en lugar de `usuario+seguridad`, haciendo inoperante la validacion de seguridad.
- **Patrones divergentes**: `quality-gate.py` tenia patrones de deteccion propios que divergian de `evidence_guard_lib.py`. Unificado para usar una sola fuente de verdad.
- **Clave de autopilot inconsistente**: los comandos markdown buscaban `"modo": "autopilot"` pero el codigo escribia `"autopilot": true`. Corregido.

### Added

- **Soporte para go test**: la salida de `go test` se detecta correctamente como exito en evidence guard.
- **Informe de sesiones parciales**: el stop-hook genera informe cuando una sesion se interrumpe, no solo cuando se completa.
- **Modo autopilot en informes**: los informes de sesion indican si se ejecutaron en modo autopilot o interactivo.
- **Iteraciones por fase en informes**: los informes muestran cuantos reintentos tuvo cada fase.
- **Verificacion de evidencia en markdown**: instruccion explicita para que Claude lea `alfred-evidence.json` antes de avanzar gates automaticas.
- **Loop iterativo documentado**: los comandos feature, fix y ship incluyen instrucciones de loop iterativo (max 5 reintentos por fase).
- **Persistencia de iteraciones**: instruccion para que Claude persista el estado despues de cada intento de gate.
- **Gate de deploy siempre interactiva**: refuerzo explicito de que el deploy nunca se auto-aprueba.

### Changed

- **stop-hook refactorizado**: extraidas funciones `should_block`, `build_block_message` y `handle_session_report` para testabilidad.
- **Mensaje de bloqueo adaptado a autopilot**: en modo autopilot, el stop-hook no pide confirmacion del usuario sino que indica investigar el error.
- **Evidencia sin ventana temporal para informes**: `get_evidence(max_age_seconds=None)` devuelve todos los registros sin filtrar por antiguedad.
- **Version dinamica en informes**: el template lee la version de `plugin.json` en lugar de tenerla hardcoded.
- **Limpieza de evidencia entre sesiones**: al completar una sesion, se limpia el fichero de evidencia para evitar contaminacion cruzada.

---

## [0.4.1] - 2026-03-13

### Added

- **Configuracion inicial automatica (onboarding)**: cuando Alfred se usa por primera vez en un proyecto (no hay configuracion de autonomia en `alfred-dev.local.md`), pregunta automaticamente si el usuario quiere modo interactivo o autopilot. La respuesta se guarda en el fichero de configuracion local y el flujo continua sin necesidad de reiniciar ni ejecutar comandos adicionales. Implementado en `_composicion.md` (Paso 0) para que aplique a todos los flujos (feature, fix, ship, spike, audit).

### Fixed

- **Modo autopilot desconectado de los comandos**: las instrucciones de los comandos (`feature.md`, `fix.md`, `ship.md`) no mencionaban el modo autopilot, por lo que Claude nunca lo activaba aunque el backend (`orchestrator.py`) lo soportase. Añadida seccion "Modo autopilot" a los tres comandos y "Paso 2b" a `_composicion.md` para que Claude compruebe el estado de autopilot y salte las gates de usuario cuando proceda.

---

## [0.4.0] - 2026-03-13

### Added

- **Verificacion de evidencia (evidence guard)**: nuevo hook PostToolUse que registra cada ejecucion de tests como evidencia verificable. Cuando un agente afirma que los tests pasan, el sistema puede comprobar que efectivamente se ejecutaron en los ultimos 10 minutos. Fichero de evidencia en `.claude/alfred-evidence.json` con rotacion a 50 registros.
- **Informe de sesion al cierre**: al finalizar una sesion de trabajo completada, se genera automaticamente un informe en `docs/alfred-reports/` con resumen de fases completadas, evidencia de tests, equipo de sesion y artefactos generados. Integrado en el stop-hook existente.
- **Loop iterativo dentro de fases**: los agentes pueden iterar dentro de una fase (hasta 5 intentos por defecto) hasta superar la gate correspondiente. Esto habilita ciclos TDD naturales, pasadas de QA repetidas y correccion iterativa sin intervencion manual. Al agotar las iteraciones, se escala al usuario.
- **Modo autopilot**: `run_flow_autopilot()` ejecuta un flujo completo sin interrupcion humana. Las gates de tipo «usuario» se aprueban automaticamente; las gates automaticas y de seguridad se evaluan normalmente. Solo se detiene si una gate automatica o de seguridad falla.
- **Tests nuevos**: cobertura de evidence guard (deteccion de runners, resultados, almacenamiento), informe de sesion (secciones, duracion, generacion), loop iterativo (retry, escalado, reset) y autopilot (gates automaticas, seguridad, usuario).

### Changed

- **Personalidades reescritas**: las 17 personalidades de agentes adoptan el tono Alfred Pennyworth: servicio impecable, ironia sutil, precision tecnica. Eliminadas expresiones coloquiales («bro», «señor», «que pasa»). Añadidos los agentes project-manager (SonIA) e i18n-specialist (La Interprete).
- **Orquestador ampliado**: `advance_phase()` reinicia automaticamente el contador de iteraciones internas al avanzar. Nuevas funciones publicas: `should_retry_phase()`, `reset_phase_iterations()`, `is_autopilot_gate_passable()`, `run_flow_autopilot()`.
- **Stop-hook con informe**: al cerrar una sesion completada, el stop-hook genera un informe de sesion automaticamente antes de permitir la salida.

---

## [0.3.9] - 2026-03-13

### Added

- **Agente opcional i18n-specialist**: nuevo agente para proyectos multiidioma con deteccion automatica de señales i18n (directorios `i18n/`, `locales/`, `translations/`, ficheros de configuracion i18n). Se integra en las fases de desarrollo y calidad en paralelo con los agentes de nucleo.
- **Deteccion automatica de i18n**: nueva funcion `_has_i18n_signals()` en `config_loader.py` que analiza el proyecto y sugiere `i18n-specialist` cuando detecta estructura de internacionalizacion.

### Changed

- **Seleccion de agentes opcionales rediseñada**: los 8 agentes opcionales se presentan en 2 preguntas `multiSelect` agrupadas por tema (técnicos + contenido/UX) usando `AskUserQuestion`, compatible con el limite de 4 opciones por pregunta. Actualizado en `_composicion.md`, `config.md` y documentacion.
- **Product Owner con preguntas secuenciales**: la fase de producto formula las preguntas **una a una** (una por turno, esperar respuesta) en vez de lanzar el bloque completo, siguiendo el patron de refinamiento progresivo.
- **8 agentes opcionales**: añadido `i18n-specialist` al catalogo, `DEFAULT_CONFIG`, `_KNOWN_OPTIONAL_AGENTS`, `OPTIONAL_INTEGRATIONS`, tablas de `feature.md`, `help.md`, `config.md` y `docs/configuration.md`. Tests actualizados.

---

## [0.3.8] - 2026-03-13

### Added

- **Capa de sincronizacion SQLite a memoria nativa**: nuevo modulo `core/memory_sync.py` que proyecta las decisiones, iteraciones, commits y resumen del proyecto desde `alfred-memory.db` a ficheros `.md` en `~/.claude/projects/<hash>/memory/` con el formato nativo de Claude Code (frontmatter YAML con `name`, `description`, `type` y `source: alfred-memory`). SQLite es la fuente de verdad; los `.md` son proyecciones de lectura que Claude carga automaticamente en cada conversacion.
- **Sincronizacion hibrida (full + incremental)**: `session-start.sh` ejecuta `sync_all` al arrancar la sesion (regeneracion completa); `activity-capture.py` dispara sincronizaciones incrementales tras cada escritura en SQLite (decisiones, iteraciones, commits).
- **Gestion segura de MEMORY.md**: seccion delimitada con marcadores `<!-- ALFRED-SYNC:START/END -->` que se actualiza sin tocar el contenido manual del usuario. Validacion de posicion de marcadores para evitar corrupcion por marcadores huerfanos o invertidos.
- **Limpieza de ficheros huerfanos**: `cleanup_stale()` elimina ficheros de decisiones archivadas o iteraciones cerradas, identificando ficheros autogenerados por el campo `source: alfred-memory` en el frontmatter.
- **Creacion automatica del directorio de memoria**: `resolve_memory_dir()` crea `~/.claude/projects/<hash>/memory/` si no existe al cargar Alfred por primera vez, eliminando la friccion de activacion manual.
- **Fichero de decisiones archivadas**: las decisiones con estado `superseded` o `rejected` se consolidan en `alfred-decisions-archived.md` en formato compacto (una linea por decision) en lugar de ficheros individuales.
- **22 tests para memory_sync**: cobertura de resolucion de directorios, proyeccion de decisiones, sincronizacion completa, gestion de MEMORY.md, limpieza de huerfanos, commits, casos de borde (DB vacia, marcadores corruptos, campos None) y flujo end-to-end.
- **Skill de testing E2E**: nuevo skill `calidad/e2e-testing` para configurar y escribir tests end-to-end con Playwright o Cypress, incluyendo integracion en CI.

### Changed

- **60 skills revisadas y mejoradas** (antes 56 + 3 protocolos sueltos): revision completa de las 56 skills existentes mas reorganizacion de los 3 protocolos sueltos (`incident-response`, `dependency-strategy`, `release-planning`) en sus categorias logicas (`calidad/`, `seguridad/`, `devops/`).
- **Descriptions enriquecidas para triggering**: todas las skills incluyen sinonimos y escenarios de activacion en el campo `description` del frontmatter, mejorando la precision con la que los agentes seleccionan la skill adecuada.
- **Integracion con memoria persistente**: 10 skills que producen decisiones o hallazgos ahora registran automaticamente en `memory_log_decision` para trazabilidad entre sesiones (write-adr, choose-stack, design-system, compliance-check, dependency-audit, threat-model, schema-design, test-plan, competitive-analysis, competitive-analysis).
- **Seccion "Que NO hacer" en 51 skills**: antipatrones y errores comunes documentados para prevenir malas practicas. Las 9 skills restantes ya cubrian estas restricciones en su estructura interna.
- **Referencia al stack de Alfred en 9 skills**: las skills que dependen del runtime o lenguaje del proyecto (dockerize, ci-cd-pipeline, deploy-config, profiling, benchmark, dependency-audit, sonarqube, test-plan, monitoring-setup) consultan `detect_stack` en vez de repetir la deteccion.
- **Clarificacion de solapamientos**: skills que cubren areas adyacentes (dependency-audit vs dependency-strategy vs dependency-update, code-review vs code-review-response, changelog vs release-planning, write-adr vs choose-stack vs design-system) documentan explicitamente su alcance y cuando usar cada una.
- **Versiones normativas documentadas**: compliance-check (RGPD 2016/679, NIS2 2022/2555, CRA 2024/2847), security-review (OWASP Top 10 edicion 2021), accessibility-audit (WCAG 2.1 AA, nota sobre WCAG 2.2).

- **Configuracion local ampliada**: `alfred-dev.local.md` incluye las opciones `sync_to_native: true` y `sync_commits_limit: 10` para controlar la sincronizacion.
- **Politica fail-open en sincronizacion**: todas las operaciones de sync capturan excepciones y continuan sin bloquear el flujo de trabajo. Los errores se registran en stderr con el prefijo `[alfred-dev]`.

## [0.3.7] - 2026-03-12

### Added

- **SonIA -- Project Manager**: nuevo agente de nucleo transversal. Descompone el PRD en tareas, gestiona un kanban en `docs/project/kanban/` con 4 ficheros MD (backlog, in-progress, done, blocked), mantiene la matriz de trazabilidad (criterio -- tarea -- test -- doc) y genera informes de progreso por fase. HARD-GATE: completitud de trazabilidad (criterio -- tarea -- test -- doc enlazados).
- **La Interprete -- i18n Specialist**: nuevo agente opcional para internacionalizacion. Auditoria de claves i18n, deteccion de cadenas hardcodeadas, validacion de formatos por locale, generacion de esqueletos para nuevos idiomas. HARD-GATE: completitud de claves (N en base = N en todos los idiomas).
- **QA Engineer ampliado**: nueva seccion de testing de integracion y E2E con estrategias para Playwright/Cypress, tabla de decision entre tipos de test (unitario, integracion, E2E, regresion) y criterios de seleccion.

### Changed

- **El Escriba (antes El Traductor)**: tech-writer reescrito como agente de nucleo con doble activacion: fase 3b (documentacion inline: cabeceras, docstrings, comentarios de contexto) y fase 5 (documentacion de proyecto: API, arquitectura con diagramas Mermaid, guias, changelogs). Guia de estilo estricta: castellano sin latinismos, anglicismos permitidos, sin emojis.
- **HARD-GATEs en 5 agentes opcionales**: data-engineer (integridad de migraciones), ux-reviewer (WCAG 2.1 nivel A), performance-engineer (umbrales de rendimiento), seo-specialist (requisitos minimos de indexacion), github-manager (operaciones destructivas requieren confirmacion).
- **Equipo ampliado a 17 agentes**: 9 de nucleo (antes 8) + 8 opcionales (antes 7). Todos los conteos actualizados en web, README y manifiesto.
- **Colores de agentes unificados**: QA Engineer de red a amber (conflicto con security-officer), performance-engineer y copywriter alineados entre frontmatter y cuerpo del agente.
- Variable CSS `--magenta` anadida al sistema de diseno para el color de SonIA.
- Landing page actualizada: nueva entrada de changelog, FAQs actualizados, conteos corregidos en hero, meta, footer y secciones de agentes.
- **Memoria persistente mejorada**: optimizaciones en el modulo SQLite, consultas mas eficientes y mejor gestion de la base de datos entre sesiones.
- **Todos los agentes revisados**: inconsistencias corregidas en frontmatter (colores, herramientas), descripciones alineadas con las capacidades reales, personalidades refinadas y cadenas de integracion actualizadas.

### Removed

- **Dashboard GUI eliminado**: la interfaz web del dashboard (introducida en v0.3.0) se retira por no cumplir las expectativas de usabilidad. El servidor HTTP/WebSocket, los ficheros de dashboard, las tablas SQLite de GUI (`gui_actions`, `pinned_items`) y los hooks de arranque/parada automatica dejan de estar activos. La funcionalidad de estado del proyecto se cubre con `/alfred-dev:status`.

## [0.3.6] - 2026-03-10

### Fixed

- **Agentes de nucleo registrados en plugin.json**: los 7 agentes de nucleo (product-owner, architect, senior-dev, security-officer, qa-engineer, devops-engineer, tech-writer) no estaban registrados en el manifiesto del plugin, por lo que Claude Code no podia cargar sus system prompts como subagentes. Ahora los 14 agentes (7 nucleo + 7 opcionales) estan registrados.
- **Herramientas MCP fantasma en librarian**: el agente librarian referenciaba 5 herramientas MCP con nombres incorrectos (`memory_record_decision`, `memory_record_iteration`, `memory_record_event`, `memory_record_commit`, `memory_link_commit`). Corregidos a los nombres reales del servidor MCP.
- **Dashboard vacio en primera sesion**: el pipeline de datos del dashboard fallaba en cascada por 3 causas: (1) la configuracion local no se creaba con memoria activada, (2) sin iteracion activa los commits no se asociaban, (3) `get_full_state()` devolvia arrays vacios sin iteracion. Corregido con auto-creacion de config, iteracion de sesion automatica y fallback a datos globales.
- **Conflicto de puertos del dashboard**: si otro proyecto ya usaba los puertos 7533/7534, el dashboard no arrancaba. Ahora detecta puertos ocupados y busca alternativas automaticamente.
- **Comentarios de cabecera del servidor MCP**: los nombres de herramientas en el docstring del modulo no coincidian con los registrados. Alineados.

## [0.3.5] - 2026-03-10

### Changed

- **SonarQube movido al security-officer**: el análisis de SonarQube lo ejecuta ahora el security-officer en lugar del qa-engineer durante `/alfred-dev:audit`. El security-officer levanta Docker, ejecuta el scanner end-to-end e integra los hallazgos en su informe de seguridad. Si Docker no está disponible, informa al usuario y continúa sin SonarQube.
- **Instrucciones imperativas para SonarQube**: el subagente recibe pasos explícitos y secuenciales (leer el skill con Read, ejecutar los 7 pasos, integrar resultados) en lugar de una referencia textual que podía ignorarse.

## [0.3.4] - 2026-03-03

### Fixed

- **Nomenclatura de comandos en la web**: todos los comandos actualizados de `/alfred X` a `/alfred-dev:X` para reflejar la convencion real de Claude Code.
- **Stats de la web corregidos**: skills 56 a 59, comandos 10 a 11, hooks 7 a 11.
- **Comando /alfred-dev:gui visible**: anadido a la lista publica de comandos en la web (ES + EN).
- **SonarQube integrado en audit**: el security-officer ejecuta el skill de SonarQube como paso por defecto en `/alfred-dev:audit`.
- **Fichero de puertos del dashboard**: `session-start.sh` crea `.claude/alfred-gui-port` y verifica conexion real al servidor.
- **Colores de agentes opcionales**: los 5 agentes sin color en el frontmatter ahora tienen colores asignados.

## [0.3.3] - 2026-02-24

### Fixed

- **Inicializacion de SQLite al arrancar**: la BD de memoria (`alfred-memory.db`) se crea automaticamente en `session-start.sh` si no existe. Antes, la BD solo se creaba cuando los hooks de captura se disparaban, lo que impedia que el servidor GUI arrancara en la primera sesion.
- **Servidor GUI siempre operativo**: el dashboard arranca desde el minuto 1 en cada sesion. Se elimino la dependencia circular que requeria una BD preexistente para levantar el servidor.
- **Agentes servidos por WebSocket**: el catalogo de 15 agentes (8 principales + 7 opcionales) se envia desde el servidor en el mensaje `init`, eliminando la lista hardcodeada en `dashboard.html`. El dashboard no muestra datos que no provengan del WebSocket.
- **Hooks resilientes a actualizaciones**: todos los comandos en `hooks.json` usan guardas `test -f ... || true` para degradacion graceful cuando `CLAUDE_PLUGIN_ROOT` apunta a un directorio eliminado tras una actualizacion de version.

## [0.3.2] - 2026-02-23

### Added

- **Composición dinámica de equipo**: sistema de 4 capas (heurística, razonamiento, presentación, ejecución) que sugiere agentes opcionales según la descripción de la tarea. `match_task_keywords()` puntúa 7 agentes con keywords contextuales y combina señales de proyecto, tarea y configuración activa. La selección es efímera (solo para esa sesión) y no modifica la configuración persistente.
- **Función `run_flow()`**: punto de entrada para flujos con equipo de sesión efímero. Valida la estructura, inyecta el equipo y registra diagnósticos de error en `equipo_sesion_error` para que los consumidores downstream informen al usuario.
- **Tabla `TASK_KEYWORDS`**: mapa de 7 agentes opcionales con listas de keywords y pesos base para la composición dinámica.

### Fixed

- **Matching por palabra completa**: `match_task_keywords()` usa `\b` word boundary en vez de subcadena, eliminando falsos positivos para keywords cortas ("ui", "ci", "pr", "form", "orm", "bd", "cd", "copy").
- **Retroalimentación de validación**: `run_flow()` registra el motivo del descarte en `equipo_sesion_error` cuando el equipo no pasa la validación.
- **Aviso al truncar**: descripciones de tarea mayores de 10 000 caracteres emiten aviso a stderr en vez de truncarse silenciosamente.
- **Tipos no-str**: `match_task_keywords()` avisa cuando recibe tipos inesperados en vez de convertirlos silenciosamente a cadena vacía.

### Changed

- `_KNOWN_OPTIONAL_AGENTS` derivado de `TASK_KEYWORDS` (fuente única de verdad) en vez de duplicar la lista de agentes.
- Los 6 skills de comandos (alfred, feature, fix, spike, ship, audit) incluyen instrucciones de composición dinámica con checkboxes para el usuario.
- Documentación actualizada: `docs/configuration.md` con sección completa de composición dinámica, `docs/architecture.md` y `README.md` con referencias.
- 326 tests (29 nuevos para composición dinámica y validación de equipo).


## [0.3.1] - 2026-02-23

### Fixed

- **Lectura robusta de frames WebSocket**: el servidor usaba `reader.read()` que puede devolver frames parciales por fragmentacion TCP. Reescrito con `readexactly()` para leer bytes exactos segun la cabecera del frame RFC 6455. Esto elimina desconexiones aleatorias y corrupcion de mensajes bajo carga.
- **Conexion SQLite cross-thread**: la conexion de polling se creaba en un hilo y se usaba en el bucle asyncio de otro. Anadido `check_same_thread=False` para evitar `ProgrammingError` en Python 3.12+.
- **Consistencia en `get_full_state()`**: el metodo mezclaba dos conexiones SQLite (la del modulo `MemoryDB` y la de polling). Reescrito para usar exclusivamente la conexion de polling, eliminando posibles inconsistencias entre vistas.
- **Polling de elementos marcados**: el watcher solo monitorizaba eventos, decisiones y commits. Anadido `poll_new_pinned()` y checkpoint de marcados para que las acciones de pin/unpin se propaguen en tiempo real.
- **Formato de timestamps**: `formatTime()` no distinguia entre epoch en segundos y milisegundos, y no gestionaba cadenas ISO sin zona horaria. Corregido con umbral automatico y append de `Z` para UTC.
- **Validacion de tipos en acciones GUI**: los campos `item_id` y `pin_id` se pasaban sin validar. Anadidos casts a `int()` y `str()` para prevenir inyeccion de tipos inesperados.
- **Buffer de handshake WebSocket**: ampliado de 4096 a 8192 bytes para soportar navegadores que envian cabeceras extensas (extensiones, cookies).
- **Limpieza de writers WebSocket**: al cerrar el servidor, los writers de clientes conectados no se cerraban. Anadida limpieza explicita en `close()` para liberar sockets.

### Added

- **Soporte movil**: menu hamburguesa con sidebar deslizante y overlay para pantallas estrechas. La navegacion es completamente funcional en movil.
- **Cabeceras de seguridad HTTP**: `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` y `Content-Security-Policy` restrictiva para prevenir ataques de inyeccion.
- **Inyeccion dinamica de version**: el servidor lee la version de `package.json` y la inyecta como variable JavaScript en el dashboard. La cabecera y el pie muestran la version real sin hardcodear.
- **Inyeccion dinamica de puerto WebSocket**: el servidor inyecta el puerto WS real en el HTML, eliminando el puerto 7534 hardcodeado que fallaba cuando el puerto por defecto estaba ocupado.
- **Icono SVG de marcado**: sustituido el texto `[*]` por un icono SVG de pin en timeline y decisiones para una interfaz mas limpia.

### Changed

- Version bumpeada de 0.3.0 a 0.3.1 en plugin.json, marketplace.json, package.json, install.sh, install.ps1, memory_server.py, dashboard.html y site/index.html.
- `docs/gui.md` actualizado con las mejoras de estabilidad y las nuevas funcionalidades.
- README.md actualizado con referencia a las mejoras de v0.3.1.
- Landing page actualizada con entrada de changelog v0.3.1 y auditoria SEO completa (canonical, og:image, FAQPage schema, hreflang, CLS).


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

[0.4.7]: https://github.com/686f6c61/alfred-dev/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/686f6c61/alfred-dev/compare/v0.4.5...v0.4.6
[0.4.5]: https://github.com/686f6c61/alfred-dev/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/686f6c61/alfred-dev/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/686f6c61/alfred-dev/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/686f6c61/alfred-dev/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/686f6c61/alfred-dev/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/686f6c61/alfred-dev/compare/v0.3.9...v0.4.0
[0.3.9]: https://github.com/686f6c61/alfred-dev/compare/v0.3.8...v0.3.9
[0.3.8]: https://github.com/686f6c61/alfred-dev/compare/v0.3.7...v0.3.8
[0.3.7]: https://github.com/686f6c61/alfred-dev/compare/v0.3.6...v0.3.7
[0.3.6]: https://github.com/686f6c61/alfred-dev/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/686f6c61/alfred-dev/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/686f6c61/alfred-dev/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/686f6c61/alfred-dev/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/686f6c61/alfred-dev/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/686f6c61/alfred-dev/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/686f6c61/alfred-dev/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/686f6c61/alfred-dev/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/686f6c61/alfred-dev/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/686f6c61/alfred-dev/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/686f6c61/alfred-dev/compare/v0.1.5...v0.2.0
[0.1.5]: https://github.com/686f6c61/alfred-dev/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/686f6c61/alfred-dev/compare/v0.1.2...v0.1.4
[0.1.2]: https://github.com/686f6c61/alfred-dev/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/686f6c61/alfred-dev/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/686f6c61/alfred-dev/releases/tag/v0.1.0
