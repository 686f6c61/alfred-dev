# Alfred Dev

**Plugin de ingeniería de software automatizada para [Claude Code](https://docs.anthropic.com/en/docs/claude-code).**

17 agentes especializados con personalidad propia (9 de nucleo + 8 opcionales), 60 skills en 13 dominios, memoria persistente de decisiones por proyecto, 6 flujos de trabajo con quality gates infranqueables, verificacion de evidencia automatica, modo autopilot y compliance europeo (RGPD, NIS2, CRA) integrado desde el diseno.

[Documentación completa](https://686f6c61.github.io/alfred-dev/) -- [Instalar](#instalación) -- [Comandos](#comandos) -- [Arquitectura](#arquitectura)

---

## Qué es Alfred Dev

Alfred Dev es un plugin que orquesta el ciclo completo de desarrollo de software a través de agentes autónomos. Cada agente tiene un rol concreto, un ámbito de actuación delimitado y quality gates que impiden avanzar a la siguiente fase sin cumplir los criterios de calidad. El sistema está diseñado para que ningún artefacto llegue a producción sin haber pasado por producto, arquitectura, desarrollo con TDD, revisión de seguridad, QA y documentación.

El plugin detecta automáticamente el stack tecnológico del proyecto (Node.js, Python, Rust, Go, Ruby, Elixir, Java/Kotlin, PHP, C#/.NET, Swift) y adapta los artefactos generados al ecosistema real: frameworks, gestores de paquetes, convenciones de testing y estructura de directorios.

## Instalación

Una sola línea. El script clona el repositorio en la caché de plugins de Claude Code y lo registra automáticamente:

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.sh | bash
```

Reinicia Claude Code después de instalar y verifica con:

```bash
/alfred-dev:help
```

En Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/install.ps1 | iex
```

Requisitos:
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado y configurado.
- Python 3.10+ (para los hooks y el core; no necesario en Windows).
- git (para la descarga del plugin).

Para desinstalar:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.sh | bash
```

```powershell
# Windows
irm https://raw.githubusercontent.com/686f6c61/alfred-dev/main/uninstall.ps1 | iex
```

## Inicio rapido

Una vez instalado, estos tres pasos muestran Alfred Dev en accion:

```bash
# 1. Verificar que el plugin esta cargado
/alfred-dev:help

# 2. Configurar el proyecto (detecta el stack automaticamente)
/alfred-dev:config

# 3. Arrancar una funcionalidad de ejemplo
/alfred-dev:feature sistema de login con email y password
```

Alfred activara el flujo de 6 fases (producto, arquitectura, desarrollo, calidad, documentacion, entrega) y pedira confirmacion en cada quality gate antes de avanzar. Para una tarea mas rapida, prueba `/alfred-dev:quick` para cambios pequenos, `/alfred-dev:fix` para un bug o `/alfred-dev:spike` para investigar una tecnologia sin compromiso de implementacion.

## Novedades en v0.4.7

La v0.4.7 corrige un error intermitente en el hook `SessionStart` que provocaba el mensaje `SessionStart:startup hook error` al arrancar sesiones. La causa raíz era que el contexto se pasaba como argumento de línea de comandos a Python (`sys.argv[1]`), sujeto al límite `ARG_MAX` del kernel. Ahora la emisión JSON se hace por stdin con `json.dumps`, eliminando la clase de error por completo.

| Cambio | Descripcion |
|--------|-------------|
| **Hook SessionStart robusto** | La emisión JSON ya no se trunca con contenidos largos o caracteres especiales (tildes, backticks, comillas, barras invertidas). |
| **Emisión por stdin** | Nueva función `emit_hook_json()` que recibe el contexto por stdin y genera JSON válido directamente con `json.dumps`. |

### Novedades de v0.4.6

La v0.4.6 introduce una **Memory UI** local pensada para uso real: abre la SQLite del proyecto en el navegador, mezcla memoria persistente con señales operativas de SonIA y evita que la vista nazca vacía gracias a siembra helper-first e import de commits Git cuando hace falta.

| Novedad | Descripcion |
|---------|-------------|
| **Memory UI local** | Nuevo `/alfred-dev:memory-ui` para abrir timeline, decisiones, commits, búsqueda y salud de memoria en el navegador sobre la SQLite real del proyecto. |
| **Poblado natural de memoria** | `map-codebase`, `discuss` y `quick` ya dejan decisiones, progreso, trazabilidad y kanban útiles para que la UI tenga contexto desde el primer uso real. |
| **Commits visibles sin fricción** | La UI importa historial Git reciente cuando la memoria todavia no tenia commits enlazados, evitando paneles muertos en repos reales. |
| **Superficie pública actualizada** | Alfred pasa a reflejar `25` comandos visibles y la web/documentación explican la nueva capa visual de memoria. |
| **Hardening de release** | Se limpian docs internas de planificación del repo publicado y se alinea homepage/versionado/metadata para la release nueva. |

### Novedades de v0.4.5

La v0.4.5 extiende a SonIA con una capa PM mas operativa y colaborativa: ahora Alfred puede dar standup, listar bloqueos y trabajo en curso, validar la salud del tablero, buscar en artefactos + memoria y ejecutar **SonIA Sync** para reflejar el kanban local en GitHub sin perder la fuente de verdad en `docs/project/`.

| Novedad | Descripcion |
|---------|-------------|
| **Operaciones PM deterministas** | Llegan `/alfred-dev:standup`, `blocked`, `in-progress`, `validate` y `search` para explotar SonIA como backlog operativo real en CLI, sin abrir siempre un flujo multiagente. |
| **SonIA Sync para GitHub** | Nuevo `/alfred-dev:sync-github` para reflejar el tablero de SonIA en GitHub con `gh`, manteniendo la verdad local en `docs/project/` y `.claude/`. |
| **Búsqueda unificada de proyecto** | `/alfred-dev:search` cruza artefactos de SonIA y memoria SQLite en una sola consulta determinista. |
| **Validación operativa** | `/alfred-dev:validate` detecta tareas duplicadas, huecos de trazabilidad, evidencia ausente en `done`, UAT pendiente y desalineaciones del sync local. |
| **Standup y visibilidad fina** | `standup`, `blocked` e `in-progress` convierten el estado local de SonIA en vistas rápidas y accionables, al estilo PM operacional. |
| **End-to-end con GitHub real** | El bloque queda preparado para smoke tests con repo privado y `gh`, además de la suite automatizada. |

### Novedades de v0.4.4

La v0.4.4 convirtió Alfred en un sistema mucho mas usable en Claude Code CLI: ya orienta continuidad y brownfield por si solo, funciona mejor en `claude -p` con comandos helper-first y cierra la memoria persistente para uso real.

| Novedad | Descripcion |
|---------|-------------|
| **Continuidad operativa** | Llegan `/alfred-dev:map-codebase`, `discuss`, `next`, `pause`, `resume`, `progress`, `verify` y `quick` para orientar el trabajo sin abrir siempre un flujo completo. |
| **Helper-first real en CLI** | `map-codebase` y el caso brownfield de `/alfred-dev:alfred` ya se preparan y consumen de forma determinista, sin rehacer el trabajo a mano en `claude -p`. |
| **FTS de eventos corregido** | Los eventos con `content` ya aparecen en `memory_search` y `memory_health` no los trata como corrupcion. |
| **Purga completa** | `purge_old_events()` elimina tambien las filas del indice FTS, evitando huerfanos y falsos positivos tras la retencion. |
| **Config de memoria cableada** | `capture_decisions`, `capture_commits`, `retention_days` y `sync_commits_limit` pasan a aplicarse realmente en hooks, MCP y sync nativa. |
| **Tamano real en WAL** | La salud de la memoria ya contabiliza `.db`, `-wal` y `-shm`, reflejando el consumo real en disco. |
| **Import Git robusto** | Los mensajes de commit con `|` dejan de corromperse al importar historial o capturar `git commit`. |

### Novedades de v0.4.2

La v0.4.2 fue un parche de robustez tras una auditoria exhaustiva del evidence guard, autopilot, loop iterativo e informes de sesion:

| Novedad | Descripcion |
|---------|-------------|
| **Falso positivo "0 failures" corregido** | El patron de deteccion de fallos ya no considera "0 failures" como un fallo. |
| **Gate de arquitectura corregida** | La fase de arquitectura ahora evalua seguridad correctamente (gate `usuario+seguridad`). |
| **Patrones unificados** | `quality-gate.py` importa de `evidence_guard_lib.py` en lugar de mantener patrones propios que divergian. |
| **Informes de sesiones parciales** | El stop-hook genera informe cuando una sesion se interrumpe, no solo cuando se completa. |
| **Informes enriquecidos** | Los informes muestran modo (autopilot/interactivo), iteraciones por fase y version dinamica. |
| **Evidencia en gates documentada** | Los comandos instruyen a Claude para verificar `alfred-evidence.json` antes de aprobar gates automaticas. |
| **Loop iterativo documentado** | Los comandos `feature`, `fix` y `ship` incluyen instrucciones explicitas de reintento (max 5 por fase). |

### Novedades de v0.4.1

La v0.4.1 mejoro la experiencia de primer uso y corrigio la conexion entre el modo autopilot y los comandos:

| Novedad | Descripcion |
|---------|-------------|
| **Configuracion inicial automatica** | Al usar Alfred por primera vez en un proyecto, pregunta si se quiere modo interactivo o autopilot. Sin pasos manuales, sin reinicios. |
| **Autopilot conectado a los comandos** | Los comandos `feature`, `fix` y `ship` ahora comprueban el estado de autopilot y saltan las gates de usuario cuando esta activo. |

### Novedades de v0.4.0

La v0.4.0 incorporo cinco capacidades orientadas a fiabilidad, autonomia controlada y trazabilidad de resultados:

| Novedad | Descripcion |
|---------|-------------|
| **Verificacion de evidencia** | El hook `evidence-guard.py` intercepta cada ejecucion de tests y registra si hubo exitos o fallos reales. Cuando un agente afirma que «los tests pasan», el orquestador verifica la evidencia registrada antes de aprobar la gate. Sin salida real de tests, no hay aprobacion. |
| **Loop iterativo en fases** | Si una fase no supera su quality gate, el orquestador puede reintentar hasta 5 veces (`should_retry_phase`) antes de escalar al usuario. Cada reintento incluye el feedback del fallo anterior para que el agente corrija su enfoque. |
| **Modo autopilot** | `run_flow_autopilot()` permite ejecutar flujos completos con aprobacion automatica de las gates de usuario, manteniendo las gates de seguridad y calidad intactas. El nivel de autonomia se configura por fase en `/alfred-dev:config`. |
| **Informes de sesion** | Al finalizar cada sesion, `session_report.py` genera un informe Markdown en `docs/alfred-reports/` con las fases completadas, duraciones, equipo de agentes, evidencia recopilada y artefactos producidos. |

## Comandos

Toda la interfaz se controla desde la línea de comandos de Claude Code con el prefijo `/alfred-dev:`:

| Comando | Descripcion |
|---------|-------------|
| `/alfred-dev:alfred` | Entrada contextual: decide si toca mapear, discutir, continuar, verificar o abrir un flujo multiagente. |
| `/alfred-dev:map-codebase` | Analiza un repo existente y deja `codebase-map.md` y `current.md` antes de implementar. |
| `/alfred-dev:discuss <desc>` | Refina una idea o fase concreta y deja discovery persistente antes de abrir `feature`. |
| `/alfred-dev:next` | Dice que toca ahora segun el estado del proyecto y la sesion activa. |
| `/alfred-dev:pause` | Pausa el trabajo en curso y genera handoff persistente. |
| `/alfred-dev:resume` | Retoma una sesion pausada usando el handoff y el estado guardado. |
| `/alfred-dev:progress` | Resume kanban, bloqueos, trazabilidad, UAT y estado operativo del proyecto. |
| `/alfred-dev:memory-ui` | Abre una UI local en navegador para explorar la memoria SQLite con timeline, decisiones, grafo, commits y búsqueda. |
| `/alfred-dev:standup` | Standup breve y accionable desde SonIA: en curso, bloqueos, progreso y siguiente paso. |
| `/alfred-dev:blocked` | Lista solo las tareas bloqueadas con su dependencia o motivo visible. |
| `/alfred-dev:in-progress` | Lista solo las tareas que están en curso. |
| `/alfred-dev:verify` | Crea o cierra la validacion humana/UAT separada de los tests automaticos. |
| `/alfred-dev:validate` | Valida la integridad operativa de kanban, trazabilidad, UAT y sync local. |
| `/alfred-dev:search <texto>` | Busca en artefactos de SonIA y en la memoria SQLite del proyecto. |
| `/alfred-dev:sync-github [owner/repo]` | Ejecuta SonIA Sync: refleja el tablero local en GitHub Issues usando `gh`. |
| `/alfred-dev:quick <desc>` | Flujo ligero para cambios pequenos con menos ceremonia que `feature`. |
| `/alfred-dev:feature <desc>` | Ciclo completo de 6 fases o parcial. Alfred pregunta desde que fase arrancar. |
| `/alfred-dev:fix <desc>` | Correccion de bugs con flujo de 3 fases: diagnostico, correccion TDD, validacion. |
| `/alfred-dev:spike <tema>` | Investigacion tecnica sin compromiso: prototipos, benchmarks, documento de hallazgos. |
| `/alfred-dev:ship` | Release: auditoria final paralela, changelog, versionado semantico, despliegue. |
| `/alfred-dev:audit` | Auditoria completa con 4 agentes en paralelo: calidad, seguridad, arquitectura, documentacion. |
| `/alfred-dev:config` | Configurar autonomia, stack, compliance, personalidad, agentes opcionales y memoria persistente. |
| `/alfred-dev:status` | Fase actual, fases completadas con duracion, gate pendiente y agente activo. |
| `/alfred-dev:update` | Comprobar si hay version nueva y actualizar el plugin. |
| `/alfred-dev:help` | Referencia completa de comandos, agentes y flujos. |

### Ejemplo de uso

```
> /alfred-dev:feature sistema de autenticación con OAuth2

Alfred activa el flujo de 6 fases:
  1. Producto    -- PRD con historias de usuario y criterios de aceptación
  2. Arquitectura -- Diseño de componentes, ADRs, threat model en paralelo
  3. Desarrollo  -- Implementación TDD (rojo-verde-refactor)
  4. Calidad     -- Code review + OWASP scan + compliance check + SBOM
  5. Documentación -- API docs, guía de usuario, changelog
  6. Entrega     -- Pipeline CI/CD, Docker, deploy

Cada transición entre fases requiere superar la quality gate correspondiente.
```

## Arquitectura

### Agentes de nucleo (9)

El plugin implementa 9 agentes de nucleo, siempre activos, cada uno con un system prompt especializado, un conjunto de herramientas definido y un modelo asignado segun la complejidad de su tarea:

| Agente | Rol | Modelo | Responsabilidad |
|--------|-----|--------|-----------------|
| **Alfred** | Orquestador | opus | Coordina flujos, activa agentes, evalua gates entre fases |
| **SonIA** | Project Manager | sonnet | Descompone PRD en tareas, kanban con MD, trazabilidad criterio-tarea-test-doc, informes de progreso |
| **El buscador de problemas** | Product Owner | opus | PRDs, historias de usuario, criterios de aceptacion, analisis competitivo |
| **El dibujante de cajas** | Arquitecto | opus | Diseno de sistemas, ADRs, diagramas Mermaid, matrices de decision |
| **El artesano** | Senior Dev | opus | Implementacion TDD estricto, refactoring, commits atomicos |
| **El paranoico** | Security Officer | opus | OWASP Top 10, threat modeling STRIDE, SBOM, compliance RGPD/NIS2/CRA |
| **El rompe-cosas** | QA Engineer | sonnet | Test plans, code review, testing exploratorio, integracion, E2E, regresion |
| **El fontanero** | DevOps Engineer | sonnet | Docker multi-stage, CI/CD, deploy, monitoring, observabilidad |
| **El escriba** | Tech Writer | sonnet | Fase 3b: cabeceras, docstrings, comentarios inline. Fase 5: API docs, arquitectura, guias, changelogs |

Los agentes con modelo `opus` realizan tareas que requieren razonamiento complejo (diseno, seguridad, implementacion). Los agentes con modelo `sonnet` cubren tareas estructuradas con patrones mas predecibles (QA, infra, documentacion).

### Agentes opcionales (8)

Agentes predefinidos que el usuario activa segun las necesidades de su proyecto con `/alfred-dev:config`. Se sugieren automaticamente en funcion del stack detectado. Desde v0.3.6, Alfred tambien propone agentes opcionales de forma dinamica al arrancar cada flujo, analizando la descripcion de la tarea con keywords contextuales y combinandolas con las senales del proyecto. La seleccion dinamica es efimera (solo para esa sesion) y no modifica la configuracion persistente. Mas detalles en la [documentacion de configuracion](docs/configuration.md#composicion-dinamica-de-equipo).

| Agente | Rol | Cuando es util |
|--------|-----|----------------|
| **Data Engineer** | Ingeniero de datos | Proyectos con base de datos, ORM, migraciones |
| **UX Reviewer** | Revisor de UX | Proyectos con frontend (React, Vue, Svelte, etc.) |
| **Performance Engineer** | Ingeniero de rendimiento | Proyectos grandes o con requisitos de rendimiento |
| **GitHub Manager** | Gestor de GitHub | Cualquier proyecto con repositorio en GitHub |
| **SEO Specialist** | Especialista SEO | Proyectos web con contenido publico |
| **Copywriter** | Copywriter | Proyectos con textos publicos: landing, emails, onboarding |
| **El Bibliotecario** | Consultas historicas | Proyectos con memoria persistente activa |
| **La Interprete** | Especialista i18n | Proyectos multilingues: claves, formatos, cadenas hardcodeadas |

### Skills (60)

Cada skill es una habilidad concreta que un agente ejecuta. Estan organizados por dominio:

```
skills/
  producto/          -- write-prd, user-stories, acceptance-criteria, competitive-analysis
  arquitectura/      -- write-adr, choose-stack, design-system, evaluate-dependencies
  desarrollo/        -- tdd-cycle, explore-codebase, refactor, code-review-response
  seguridad/         -- threat-model, dependency-audit, security-review, compliance-check, sbom-generate
  calidad/           -- test-plan, code-review, exploratory-testing, regression-check
  devops/            -- dockerize, ci-cd-pipeline, deploy-config, monitoring-setup
  documentación/     -- api-docs, architecture-docs, user-guide, changelog
```

### Hooks (12)

Los hooks interceptan eventos del ciclo de vida de Claude Code para aplicar validaciones automaticas:

| Hook | Evento | Funcion |
|------|--------|---------|
| `session-bootstrap.sh` | `SessionStart` | Bootstrap síncrono del proyecto: config local, memoria, permisos y wrapper de continuidad |
| `session-start.sh` | `SessionStart` | Detecta stack tecnologico, inyecta contexto de sesion y memoria persistente |
| `stop-hook.py` | `Stop` | Genera resumen e informe de sesion con fases completadas y pendientes |
| `secret-guard.sh` | `PreToolUse` (Write/Edit) | Bloquea escritura de secretos (API keys, tokens, passwords) |
| `dangerous-command-guard.py` | `PreToolUse` (Bash) | Bloquea comandos destructivos (rm -rf /, force push, DROP DATABASE, etc.) |
| `sensitive-read-guard.py` | `PreToolUse` (Read) | Avisa al leer ficheros sensibles (claves privadas, .env, credenciales) |
| `quality-gate.py` | `PostToolUse` (Bash) | Verifica que los tests pasen despues de ejecuciones de Bash |
| `evidence-guard.py` | `PostToolUse` (Bash) | Registra evidencia de ejecucion de tests para verificacion de gates |
| `dependency-watch.py` | `PostToolUse` (Write/Edit) | Detecta dependencias nuevas y notifica al security officer |
| `spelling-guard.py` | `PostToolUse` (Write/Edit) | Detecta palabras castellanas sin tilde al escribir o editar ficheros |
| `activity-capture.py` | Multiples | Captura automatica de actividad, commits e iteraciones; en prompts helper-first prepara continuidad operativa antes del razonamiento |
| `memory-compact.py` | `PreCompact` | Protege decisiones criticas durante la compactacion de contexto |

### Templates (7)

Plantillas estandarizadas que los agentes usan para generar artefactos con estructura consistente:

- `prd.md` -- Product Requirements Document
- `adr.md` -- Architecture Decision Record
- `test-plan.md` -- Plan de testing por riesgo
- `threat-model.md` -- Modelado de amenazas STRIDE
- `sbom.md` -- Software Bill of Materials
- `changelog-entry.md` -- Entrada de changelog (Keep a Changelog)
- `release-notes.md` -- Notas de release con resumen ejecutivo

### Core (6 modulos)

El nucleo del plugin esta implementado en Python con tests unitarios:

| Modulo | Funcion |
|--------|---------|
| `orchestrator.py` | Maquina de estados de flujos, gestion de sesiones, evaluacion de gates, modo autopilot, loop iterativo |
| `personality.py` | Motor de personalidad: frases, tono, anuncios, formato de veredicto |
| `config_loader.py` | Carga de configuracion, deteccion de stack, preferencias de proyecto |
| `continuity.py` | Helper-first para continuidad CLI: map-codebase, discuss, next, pause, resume, progress, verify y quick |
| `memory.py` | Base de datos SQLite de memoria persistente: decisiones, commits, iteraciones, eventos |
| `session_report.py` | Generacion de informes de sesion en Markdown con fases, evidencia y artefactos |

```bash
# Ejecutar tests
python3 -m pytest tests/ -v
```

## Quality gates

Las quality gates son puntos de control infranqueables entre fases. Si una gate no se supera, el flujo se detiene. No hay excepciones, no hay modo de saltárselas:

| Gate | Condición |
|------|-----------|
| PRD aprobado | El usuario valida el PRD antes de pasar a arquitectura |
| Diseño aprobado | El usuario aprueba el diseño Y el security officer lo valida |
| Tests en verde | Todos los tests pasan antes de pasar a calidad |
| Evidencia verificada | Las afirmaciones de tests deben estar respaldadas por salida real registrada por `evidence-guard.py` |
| Loop iterativo | Si una gate falla, se reintenta hasta 5 veces con feedback antes de escalar al usuario |
| QA + seguridad | El QA engineer y el security officer aprueban en paralelo |
| Documentación completa | Todos los artefactos están documentados |
| Pipeline verde | CI/CD verde, sin usuario root en contenedor, sin secretos en imagen |

Cada gate produce un veredicto formal: **APROBADO**, **APROBADO CON CONDICIONES** o **RECHAZADO**, con hallazgos bloqueantes y próxima acción recomendada.

## Compliance

El plugin integra verificaciones de compliance europeo en el flujo de desarrollo:

- **RGPD** -- Protección de datos desde el diseño. Verificación de base legal, minimización de datos, derechos de los interesados.
- **NIS2** -- Directiva de ciberseguridad para operadores esenciales. Gestión de riesgos, notificación de incidentes, cadena de suministro.
- **CRA** -- Cyber Resilience Act. Requisitos de ciber-resiliencia para productos digitales con componentes conectados.
- **OWASP Top 10** -- Verificación sistemática de las 10 vulnerabilidades más explotadas en cada revisión de seguridad.
- **SBOM** -- Generación automática del Software Bill of Materials con inventario de dependencias, licencias y CVEs conocidos.

## Detección de stack

El hook `session-start.sh` analiza el directorio de trabajo al iniciar sesión y detecta automáticamente:

| Lenguaje | Señales | Ecosistema |
|----------|---------|------------|
| Node.js | `package.json` | npm, pnpm, bun, yarn -- Express, Next.js, Fastify, Hono |
| Python | `pyproject.toml`, `requirements.txt` | pip, poetry, uv -- Django, Flask, FastAPI |
| Rust | `Cargo.toml` | cargo -- Actix, Axum, Rocket |
| Go | `go.mod` | go mod -- Gin, Echo, Fiber |
| Ruby | `Gemfile` | bundler -- Rails, Sinatra |
| Elixir | `mix.exs` | mix -- Phoenix |
| Java / Kotlin | `pom.xml`, `build.gradle` | Maven, Gradle -- Spring Boot, Quarkus, Micronaut |
| PHP | `composer.json` | Composer -- Laravel, Symfony |
| C# / .NET | `*.csproj`, `*.sln` | dotnet, NuGet -- ASP.NET, Blazor |
| Swift | `Package.swift` | SPM -- Vapor |

## Memoria persistente

A partir de v0.2.0, Alfred Dev puede recordar decisiones, commits e iteraciones entre sesiones. La memoria se almacena en una base de datos SQLite local (`.claude/alfred-memory.db`) dentro de cada proyecto, sin dependencias externas ni servicios remotos. La v0.2.3 anade etiquetas, estado y relaciones entre decisiones, auto-captura de commits, filtros avanzados de busqueda y exportacion/importacion.

La activacion es opcional y se gestiona con `/alfred-dev:config`. Una vez activa, el hook `activity-capture.py` captura eventos automaticamente en multiples puntos del ciclo de vida: iteraciones, fases, commits (SHA, autor, ficheros afectados) y actividad general de la sesion. En `UserPromptSubmit`, si detecta comandos helper-first de continuidad (`/alfred-dev:map-codebase`, `discuss`, `quick` o el caso brownfield de `/alfred-dev:alfred`), deja preparados los artefactos operativos antes del razonamiento principal. Las decisiones arquitectonicas se registran a traves del agente **El Bibliotecario** o del servidor MCP integrado.

Funcionalidades principales:

- **Trazabilidad completa**: problema, decision, commit y validacion enlazados con IDs referenciables.
- **Busqueda avanzada**: texto completo con FTS5, filtros temporales (`since`/`until`), por etiquetas y por estado (`active`/`superseded`/`deprecated`).
- **Servidor MCP**: 15 herramientas accesibles desde cualquier agente (buscar, registrar, consultar, estadisticas, gestion de iteraciones, ciclo de vida de decisiones, validacion de integridad, export/import).
- **El Bibliotecario**: agente opcional que responde consultas historicas citando siempre las fuentes con formato `[D#id]`, `[C#sha]`, `[I#id]`. Gestiona el ciclo de vida de decisiones y valida la integridad de la memoria.
- **Contexto de sesion**: al iniciar, se inyectan las decisiones de la iteracion activa (o las 5 ultimas). Un hook PreCompact protege las decisiones criticas durante la compactacion.
- **Export/Import**: exportar decisiones a Markdown (formato ADR), importar desde historial Git o ficheros ADR existentes.
- **Seguridad**: sanitizacion de secretos con los mismos patrones que `secret-guard.sh`, permisos 0600 en el fichero de base de datos.
- **Migracion automatica**: el esquema se actualiza automaticamente con backup previo al abrir bases de datos de versiones anteriores.


## Estructura del proyecto

```
alfred-dev/
  .claude-plugin/
    plugin.json           # Manifiesto del plugin
    marketplace.json      # Metadatos para el marketplace
    mcp.json              # Servidor MCP de memoria persistente
  agents/                 # 9 agentes de nucleo
  agents/optional/        # 8 agentes opcionales
  commands/               # 25 comandos /alfred-dev
  skills/                 # 60 skills en 13 dominios
  hooks/                  # Hooks del ciclo de vida
    hooks.json            # Configuracion de eventos
  core/                   # Motor de orquestacion, memoria e informes (Python)
  mcp/                    # Servidor MCP stdio (memoria persistente)
  templates/              # 7 plantillas de artefactos
  tests/                  # Tests unitarios (pytest)
  site/                   # Landing page para GitHub Pages
```

## Configuracion

El plugin se configura por proyecto con el fichero `.claude/alfred-dev.local.md` en la raiz del proyecto. Se gestiona con `/alfred-dev:config`, que incluye descubrimiento contextual de agentes opcionales y activacion de memoria persistente:

```yaml
---
autonomia:
  producto: interactivo
  arquitectura: interactivo
  desarrollo: semi-autonomo
  seguridad: autonomo
  calidad: semi-autonomo
  documentacion: autonomo
  devops: semi-autonomo

agentes_opcionales:
  data-engineer: true
  ux-reviewer: false
  performance-engineer: false
  github-manager: true
  seo-specialist: false
  copywriter: false
  librarian: true
  i18n-specialist: false

memoria:
  enabled: true
  sync_to_native: true
  sync_commits_limit: 10
  capture_decisions: true
  capture_commits: true
  retention_days: 365

personalidad:
  nivel_sarcasmo: 3
  celebrar_victorias: true
  insultar_malas_practicas: true
---

Notas adicionales del proyecto que Alfred debe tener en cuenta.
```

## Descargo de responsabilidad

**Alfred Dev** es un proyecto independiente de codigo abierto. No esta afiliado, patrocinado ni respaldado por **Anthropic** ni por el equipo de **Claude Code**.

El software se proporciona «tal cual» (*as is*), sin garantias de ningun tipo, expresas o implicitas, incluyendo, entre otras, las garantias de comerciabilidad, adecuacion a un proposito particular y no infraccion. En ningun caso los autores o titulares de los derechos de autor seran responsables de reclamaciones, danos u otras responsabilidades derivadas del uso del software.

Alfred Dev ejecuta agentes que pueden crear, modificar y eliminar ficheros, ejecutar comandos en terminal e interactuar con servicios externos (GitHub, Docker, etc.). El usuario es responsable de revisar y aprobar las acciones que el plugin propone antes de su ejecucion.

Los agentes utilizan modelos de lenguaje de gran tamano (LLM) que pueden generar contenido incorrecto, incompleto o inadecuado. Las salidas del plugin deben tratarse como sugerencias que requieren revision humana, no como resultados definitivos.

## Licencia

MIT

---

[Documentación completa](https://686f6c61.github.io/alfred-dev/) | [Código fuente](https://github.com/686f6c61/alfred-dev)
