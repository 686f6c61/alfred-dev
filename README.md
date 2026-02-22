# Alfred Dev

**Plugin de ingeniería de software automatizada para [Claude Code](https://docs.anthropic.com/en/docs/claude-code).**

15 agentes especializados con personalidad propia (8 de nucleo + 7 opcionales), 59 skills en 13 dominios, memoria persistente de decisiones por proyecto, dashboard web en tiempo real, 5 flujos de trabajo con quality gates infranqueables y compliance europeo (RGPD, NIS2, CRA) integrado desde el diseno.

[Documentación completa](https://686f6c61.github.io/alfred-dev/) -- [Instalar](#instalación) -- [Comandos](#comandos) -- [Dashboard](#dashboard-gui) -- [Arquitectura](#arquitectura)

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
/alfred help
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

## Comandos

Toda la interfaz se controla desde la línea de comandos de Claude Code con el prefijo `/alfred`:

| Comando | Descripcion |
|---------|-------------|
| `/alfred` | Asistente contextual: detecta el stack y la sesion activa, pregunta que necesitas. |
| `/alfred feature <desc>` | Ciclo completo de 6 fases o parcial. Alfred pregunta desde que fase arrancar. |
| `/alfred fix <desc>` | Correccion de bugs con flujo de 3 fases: diagnostico, correccion TDD, validacion. |
| `/alfred spike <tema>` | Investigacion tecnica sin compromiso: prototipos, benchmarks, documento de hallazgos. |
| `/alfred ship` | Release: auditoria final paralela, changelog, versionado semantico, despliegue. |
| `/alfred audit` | Auditoria completa con 4 agentes en paralelo: calidad, seguridad, arquitectura, documentacion. |
| `/alfred config` | Configurar autonomia, stack, compliance, personalidad, agentes opcionales y memoria persistente. |
| `/alfred gui` | Lanzar el dashboard web con estado del proyecto en tiempo real. |
| `/alfred status` | Fase actual, fases completadas con duracion, gate pendiente y agente activo. |
| `/alfred update` | Comprobar si hay version nueva y actualizar el plugin. |
| `/alfred help` | Referencia completa de comandos, agentes y flujos. |

### Ejemplo de uso

```
> /alfred feature sistema de autenticación con OAuth2

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

### Agentes de nucleo (8)

El plugin implementa 8 agentes de nucleo, siempre activos, cada uno con un system prompt especializado, un conjunto de herramientas definido y un modelo asignado segun la complejidad de su tarea:

| Agente | Rol | Modelo | Responsabilidad |
|--------|-----|--------|-----------------|
| **Alfred** | Orquestador | opus | Coordina flujos, activa agentes, evalua gates entre fases |
| **El buscador de problemas** | Product Owner | opus | PRDs, historias de usuario, criterios de aceptacion, analisis competitivo |
| **El dibujante de cajas** | Arquitecto | opus | Diseno de sistemas, ADRs, diagramas Mermaid, matrices de decision |
| **El artesano** | Senior Dev | opus | Implementacion TDD estricto, refactoring, commits atomicos |
| **El paranoico** | Security Officer | opus | OWASP Top 10, threat modeling STRIDE, SBOM, compliance RGPD/NIS2/CRA |
| **El rompe-cosas** | QA Engineer | sonnet | Test plans, code review, testing exploratorio, regresion |
| **El fontanero** | DevOps Engineer | sonnet | Docker multi-stage, CI/CD, deploy, monitoring, observabilidad |
| **El traductor** | Tech Writer | sonnet | Documentacion de API, arquitectura, guias de usuario, changelogs |

Los agentes con modelo `opus` realizan tareas que requieren razonamiento complejo (diseno, seguridad, implementacion). Los agentes con modelo `sonnet` cubren tareas estructuradas con patrones mas predecibles (QA, infra, documentacion).

### Agentes opcionales (7)

Agentes predefinidos que el usuario activa segun las necesidades de su proyecto con `/alfred config`. Se sugieren automaticamente en funcion del stack detectado:

| Agente | Rol | Cuando es util |
|--------|-----|----------------|
| **Data Engineer** | Ingeniero de datos | Proyectos con base de datos, ORM, migraciones |
| **UX Reviewer** | Revisor de UX | Proyectos con frontend (React, Vue, Svelte, etc.) |
| **Performance Engineer** | Ingeniero de rendimiento | Proyectos grandes o con requisitos de rendimiento |
| **GitHub Manager** | Gestor de GitHub | Cualquier proyecto con repositorio en GitHub |
| **SEO Specialist** | Especialista SEO | Proyectos web con contenido publico |
| **Copywriter** | Copywriter | Proyectos con textos publicos: landing, emails, onboarding |
| **El Bibliotecario** | Consultas historicas | Proyectos con memoria persistente activa |

### Skills (59)

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

### Hooks (11)

Los hooks interceptan eventos del ciclo de vida de Claude Code para aplicar validaciones automaticas:

| Hook | Evento | Funcion |
|------|--------|---------|
| `session-start.sh` | `SessionStart` | Detecta stack tecnologico, inyecta contexto de sesion y memoria persistente |
| `stop-hook.py` | `Stop` | Genera resumen de sesion con fases completadas y pendientes |
| `secret-guard.sh` | `PreToolUse` (Write/Edit) | Bloquea escritura de secretos (API keys, tokens, passwords) |
| `dangerous-command-guard.py` | `PreToolUse` (Bash) | Bloquea comandos destructivos (rm -rf /, force push, DROP DATABASE, etc.) |
| `sensitive-read-guard.py` | `PreToolUse` (Read) | Avisa al leer ficheros sensibles (claves privadas, .env, credenciales) |
| `quality-gate.py` | `PostToolUse` (Bash) | Verifica que los tests pasen despues de ejecuciones de Bash |
| `dependency-watch.py` | `PostToolUse` (Write/Edit) | Detecta dependencias nuevas y notifica al security officer |
| `spelling-guard.py` | `PostToolUse` (Write/Edit) | Detecta palabras castellanas sin tilde al escribir o editar ficheros |
| `memory-capture.py` | `PostToolUse` (Write/Edit) | Captura automatica de eventos en la memoria persistente del proyecto |
| `commit-capture.py` | `PostToolUse` (Bash) | Auto-captura de commits en la memoria persistente |
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

### Core (4 modulos)

El nucleo del plugin esta implementado en Python con tests unitarios:

| Modulo | Funcion |
|--------|---------|
| `orchestrator.py` | Maquina de estados de flujos, gestion de sesiones, evaluacion de gates |
| `personality.py` | Motor de personalidad: frases, tono, anuncios, formato de veredicto |
| `config_loader.py` | Carga de configuracion, deteccion de stack, preferencias de proyecto |
| `memory.py` | Base de datos SQLite de memoria persistente: decisiones, commits, iteraciones, eventos |

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

La activacion es opcional y se gestiona con `/alfred config`. Una vez activa, dos hooks complementarios capturan eventos automaticamente: `memory-capture.py` registra iteraciones y fases, y `commit-capture.py` detecta cada `git commit` y registra SHA, autor y ficheros afectados. Las decisiones arquitectonicas se registran a traves del agente **El Bibliotecario** o del servidor MCP integrado.

Funcionalidades principales:

- **Trazabilidad completa**: problema, decision, commit y validacion enlazados con IDs referenciables.
- **Busqueda avanzada**: texto completo con FTS5, filtros temporales (`since`/`until`), por etiquetas y por estado (`active`/`superseded`/`deprecated`).
- **Servidor MCP**: 15 herramientas accesibles desde cualquier agente (buscar, registrar, consultar, estadisticas, gestion de iteraciones, ciclo de vida de decisiones, validacion de integridad, export/import).
- **El Bibliotecario**: agente opcional que responde consultas historicas citando siempre las fuentes con formato `[D#id]`, `[C#sha]`, `[I#id]`. Gestiona el ciclo de vida de decisiones y valida la integridad de la memoria.
- **Contexto de sesion**: al iniciar, se inyectan las decisiones de la iteracion activa (o las 5 ultimas). Un hook PreCompact protege las decisiones criticas durante la compactacion.
- **Export/Import**: exportar decisiones a Markdown (formato ADR), importar desde historial Git o ficheros ADR existentes.
- **Seguridad**: sanitizacion de secretos con los mismos patrones que `secret-guard.sh`, permisos 0600 en el fichero de base de datos.
- **Migracion automatica**: el esquema se actualiza automaticamente con backup previo al abrir bases de datos de versiones anteriores.

## Dashboard GUI

> **Fase Alpha** -- Funcionalidad en desarrollo activo. La interfaz y el protocolo pueden cambiar entre versiones menores.

A partir de v0.3.0, Alfred Dev incluye un dashboard web que muestra el estado completo del proyecto en tiempo real sin intervenir en el terminal de Claude Code. La v0.3.1 refuerza la estabilidad del servidor (lectura robusta de frames WebSocket, cabeceras de seguridad HTTP, soporte movil) y anade inyeccion dinamica de version y puerto. Se lanza con `/alfred gui` y se abre automaticamente en el navegador.

El dashboard actua como fuente de verdad externa: persiste toda la informacion de la sesion independientemente de la compactacion de contexto de Claude Code. Si la conversacion se compacta y se pierde contexto, el dashboard sigue mostrando el historial completo.

![Vista de estado del dashboard de Alfred Dev](site/screenshots/dashboard-estado.png)

**7 vistas disponibles:**

| Vista | Contenido |
|-------|-----------|
| Estado | Resumen general: fase activa, progreso de gates, agente activo, contadores y marcados recientes |
| Timeline | Cronologia de todos los eventos del proyecto con filtros por tipo (fases, agentes, decisiones, commits, gates) |
| Decisiones | Tabla de decisiones tecnicas con busqueda, filtros por fase/estado y etiquetas |
| Agentes | Cuadricula de los 15 agentes (8 principales + 7 opcionales) con estado y toggle de activacion |
| Memoria | Explorador directo de la base de datos SQLite con pestanas por tabla |
| Commits | Historial de commits con SHA, autor y ficheros afectados |
| Marcados | Elementos importantes marcados por el usuario o el sistema, con prioridad y nota |

| | | |
|---|---|---|
| ![Timeline](site/screenshots/dashboard-timeline.png) | ![Decisiones](site/screenshots/dashboard-decisiones.png) | ![Agentes](site/screenshots/dashboard-agentes.png) |
| Timeline | Decisiones | Agentes |
| ![Memoria](site/screenshots/dashboard-memoria.png) | ![Commits](site/screenshots/dashboard-commits.png) | ![Marcados](site/screenshots/dashboard-marcados.png) |
| Memoria | Commits | Marcados |

Para la documentacion completa del protocolo WebSocket, las tablas SQLite del dashboard y la guia de desarrollo, consulta [docs/gui.md](docs/gui.md).

**Arquitectura tecnica:**

- **Servidor:** proceso Python asyncio con HTTP (puerto 7533) + WebSocket RFC 6455 manual (puerto 7534) + polling SQLite cada 500ms. Sin dependencias externas.
- **Frontend:** fichero HTML unico con CSS y JS vanilla embebidos. Estetica dark mode coherente con la landing page.
- **Comunicacion:** WebSocket bidireccional con reconexion automatica y backoff exponencial (1s, 2s, 4s, 8s, max 30s).
- **Principio fail-open:** si la GUI falla, Alfred funciona exactamente igual que sin ella. Los hooks siguen escribiendo en SQLite.

## Estructura del proyecto

```
alfred-dev/
  .claude-plugin/
    plugin.json           # Manifiesto del plugin
    marketplace.json      # Metadatos para el marketplace
    mcp.json              # Servidor MCP de memoria persistente
  agents/                 # 8 agentes de nucleo
  agents/optional/        # 7 agentes opcionales
  commands/               # 11 comandos /alfred (incluye gui)
  skills/                 # 59 skills en 13 dominios
  hooks/                  # 11 hooks del ciclo de vida
    hooks.json            # Configuracion de eventos
  core/                   # Motor de orquestacion y memoria (Python)
  gui/                    # Dashboard web (servidor + frontend)
    server.py             # Servidor HTTP + WebSocket + SQLite watcher
    websocket.py          # Protocolo WebSocket RFC 6455
    dashboard.html        # Frontend completo (HTML + CSS + JS)
  mcp/                    # Servidor MCP stdio (memoria persistente)
  templates/              # 7 plantillas de artefactos
  tests/                  # Tests unitarios (pytest)
  site/                   # Landing page para GitHub Pages
```

## Configuracion

El plugin se configura por proyecto con el fichero `.claude/alfred-dev.local.md` en la raiz del proyecto. Se gestiona con `/alfred config`, que incluye descubrimiento contextual de agentes opcionales y activacion de memoria persistente:

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

memoria:
  enabled: true
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

## Licencia

MIT

---

[Documentación completa](https://686f6c61.github.io/alfred-dev/) | [Código fuente](https://github.com/686f6c61/alfred-dev)
