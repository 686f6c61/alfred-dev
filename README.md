# Alfred Dev

**Plugin de ingeniería de software automatizada para [Claude Code](https://docs.anthropic.com/en/docs/claude-code).**

8 agentes especializados con personalidad propia, 56 skills organizados en 13 dominios, 5 flujos de trabajo con quality gates infranqueables y compliance europeo (RGPD, NIS2, CRA) integrado desde el diseño.

[Documentación completa](https://686f6c61.github.io/Claude-JARVIS-dev/) -- [Instalar](#instalación) -- [Comandos](#comandos) -- [Arquitectura](#arquitectura)

---

## Qué es Alfred Dev

Alfred Dev es un plugin que orquesta el ciclo completo de desarrollo de software a través de agentes autónomos. Cada agente tiene un rol concreto, un ámbito de actuación delimitado y quality gates que impiden avanzar a la siguiente fase sin cumplir los criterios de calidad. El sistema está diseñado para que ningún artefacto llegue a producción sin haber pasado por producto, arquitectura, desarrollo con TDD, revisión de seguridad, QA y documentación.

El plugin detecta automáticamente el stack tecnológico del proyecto (Node.js, Python, Rust, Go, Ruby, Elixir, Java/Kotlin, PHP, C#/.NET, Swift) y adapta los artefactos generados al ecosistema real: frameworks, gestores de paquetes, convenciones de testing y estructura de directorios.

## Instalación

Una sola línea. El script clona el repositorio en la caché de plugins de Claude Code y lo registra automáticamente:

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/install.sh | bash
```

Reinicia Claude Code después de instalar y verifica con:

```bash
/alfred help
```

Requisitos:
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado y configurado.
- Python 3.10+ (para los hooks y el core).
- git (para la descarga del plugin).

Para desinstalar:

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/uninstall.sh | bash
```

## Comandos

Toda la interfaz se controla desde la línea de comandos de Claude Code con el prefijo `/alfred`:

| Comando | Descripción |
|---------|-------------|
| `/alfred feature <desc>` | Ciclo completo de 6 fases o parcial. Alfred pregunta desde qué fase arrancar. |
| `/alfred fix <desc>` | Corrección de bugs con flujo de 3 fases: diagnóstico, corrección TDD, validación. |
| `/alfred spike <tema>` | Investigación técnica sin compromiso: prototipos, benchmarks, documento de hallazgos. |
| `/alfred ship` | Release: auditoría final paralela, changelog, versionado semántico, despliegue. |
| `/alfred audit` | Auditoría completa con 4 agentes en paralelo: calidad, seguridad, arquitectura, documentación. |
| `/alfred config` | Configurar autonomía, stack, compliance y personalidad del equipo. |
| `/alfred status` | Fase actual, fases completadas con duración, gate pendiente y agente activo. |
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

### Agentes

El plugin implementa 8 agentes, cada uno con un system prompt especializado, un conjunto de herramientas definido y un modelo asignado según la complejidad de su tarea:

| Agente | Rol | Modelo | Responsabilidad |
|--------|-----|--------|-----------------|
| **Alfred** | Orquestador | opus | Coordina flujos, activa agentes, evalúa gates entre fases |
| **El buscador de problemas** | Product Owner | opus | PRDs, historias de usuario, criterios de aceptación, análisis competitivo |
| **El dibujante de cajas** | Arquitecto | opus | Diseño de sistemas, ADRs, diagramas Mermaid, matrices de decisión |
| **El artesano** | Senior Dev | opus | Implementación TDD estricto, refactoring, commits atómicos |
| **El paranoico** | Security Officer | opus | OWASP Top 10, threat modeling STRIDE, SBOM, compliance RGPD/NIS2/CRA |
| **El rompe-cosas** | QA Engineer | sonnet | Test plans, code review, testing exploratorio, regresión |
| **El fontanero** | DevOps Engineer | sonnet | Docker multi-stage, CI/CD, deploy, monitoring, observabilidad |
| **El traductor** | Tech Writer | sonnet | Documentación de API, arquitectura, guías de usuario, changelogs |

Los agentes con modelo `opus` realizan tareas que requieren razonamiento complejo (diseño, seguridad, implementación). Los agentes con modelo `sonnet` cubren tareas estructuradas con patrones más predecibles (QA, infra, documentación).

### Skills (29)

Cada skill es una habilidad concreta que un agente ejecuta. Están organizados por dominio:

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

### Hooks (5)

Los hooks interceptan eventos del ciclo de vida de Claude Code para aplicar validaciones automáticas:

| Hook | Evento | Función |
|------|--------|---------|
| `session-start.sh` | `SessionStart` | Detecta stack tecnológico e inicializa el contexto de sesión |
| `stop-hook.py` | `Stop` | Genera resumen de sesión con fases completadas y pendientes |
| `secret-guard.sh` | `PreToolUse` (Write/Edit) | Bloquea escritura de secretos (API keys, tokens, passwords) |
| `quality-gate.py` | `PostToolUse` (Bash) | Verifica que los tests pasen después de ejecuciones de Bash |
| `dependency-watch.py` | `PostToolUse` (Write/Edit) | Detecta dependencias nuevas y notifica al security officer |

### Templates (7)

Plantillas estandarizadas que los agentes usan para generar artefactos con estructura consistente:

- `prd.md` -- Product Requirements Document
- `adr.md` -- Architecture Decision Record
- `test-plan.md` -- Plan de testing por riesgo
- `threat-model.md` -- Modelado de amenazas STRIDE
- `sbom.md` -- Software Bill of Materials
- `changelog-entry.md` -- Entrada de changelog (Keep a Changelog)
- `release-notes.md` -- Notas de release con resumen ejecutivo

### Core (3 módulos, ~1.400 líneas)

El núcleo del plugin está implementado en Python con tests unitarios:

| Módulo | Líneas | Función |
|--------|--------|---------|
| `orchestrator.py` | ~600 | Máquina de estados de flujos, gestión de sesiones, evaluación de gates |
| `personality.py` | ~400 | Motor de personalidad: frases, tono, anuncios, formato de veredicto |
| `config_loader.py` | ~400 | Carga de configuración, detección de stack, preferencias de proyecto |

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

## Estructura del proyecto

```
alfred-dev/
  .claude-plugin/
    plugin.json           # Manifiesto del plugin
    marketplace.json      # Metadatos para el marketplace
  agents/                 # 8 agentes con system prompts completos
  commands/               # 8 comandos /alfred
  skills/                 # 56 skills en 13 dominios
  hooks/                  # 6 hooks del ciclo de vida
    hooks.json            # Configuración de eventos
  core/                   # Motor de orquestación (Python)
  templates/              # 7 plantillas de artefactos
  tests/                  # Tests unitarios (pytest)
  site/                   # Landing page para GitHub Pages
```

## Configuración

El plugin se puede configurar por proyecto creando el fichero `.claude/alfred-dev.local.md` en la raíz del proyecto:

```yaml
---
autonomy: medium          # low | medium | high
compliance:
  - rgpd
  - nis2
  - cra
stack: auto               # auto | node | python | rust | go | ...
personality: formal       # formal | casual | minimal
---

Notas adicionales del proyecto que Alfred debe tener en cuenta.
```

## Licencia

MIT

---

[Documentación completa](https://686f6c61.github.io/Claude-JARVIS-dev/) | [Código fuente](https://github.com/686f6c61/Claude-JARVIS-dev)
