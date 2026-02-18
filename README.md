# Alfred Dev

**Plugin de ingenieria de software automatizada para [Claude Code](https://docs.anthropic.com/en/docs/claude-code).**

8 agentes especializados con personalidad propia, 29 skills organizados en 7 dominios, 5 flujos de trabajo con quality gates infranqueables y compliance europeo (RGPD, NIS2, CRA) integrado desde el diseno.

[Documentacion completa](https://686f6c61.github.io/Claude-JARVIS-dev/) -- [Instalar](#instalacion) -- [Comandos](#comandos) -- [Arquitectura](#arquitectura)

---

## Que es Alfred Dev

Alfred Dev es un plugin que orquesta el ciclo completo de desarrollo de software a traves de agentes autonomos. Cada agente tiene un rol concreto, un ambito de actuacion delimitado y quality gates que impiden avanzar a la siguiente fase sin cumplir los criterios de calidad. El sistema esta disenado para que ningun artefacto llegue a produccion sin haber pasado por producto, arquitectura, desarrollo con TDD, revision de seguridad, QA y documentacion.

El plugin detecta automaticamente el stack tecnologico del proyecto (Node.js, Python, Rust, Go, Ruby, Elixir, Java/Kotlin, PHP, C#/.NET, Swift) y adapta los artefactos generados al ecosistema real: frameworks, gestores de paquetes, convenciones de testing y estructura de directorios.

## Instalacion

Una sola linea. El script clona el repositorio en la cache de plugins de Claude Code y lo registra automaticamente:

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/install.sh | bash
```

Reinicia Claude Code despues de instalar y verifica con:

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

Toda la interfaz se controla desde la linea de comandos de Claude Code con el prefijo `/alfred`:

| Comando | Descripcion |
|---------|-------------|
| `/alfred feature <desc>` | Ciclo completo de 6 fases o parcial. Alfred pregunta desde que fase arrancar. |
| `/alfred fix <desc>` | Correccion de bugs con flujo de 3 fases: diagnostico, correccion TDD, validacion. |
| `/alfred spike <tema>` | Investigacion tecnica sin compromiso: prototipos, benchmarks, documento de hallazgos. |
| `/alfred ship` | Release: auditoria final paralela, changelog, versionado semantico, despliegue. |
| `/alfred audit` | Auditoria completa con 4 agentes en paralelo: calidad, seguridad, arquitectura, documentacion. |
| `/alfred config` | Configurar autonomia, stack, compliance y personalidad del equipo. |
| `/alfred status` | Fase actual, fases completadas con duracion, gate pendiente y agente activo. |
| `/alfred help` | Referencia completa de comandos, agentes y flujos. |

### Ejemplo de uso

```
> /alfred feature sistema de autenticacion con OAuth2

Alfred activa el flujo de 6 fases:
  1. Producto    -- PRD con historias de usuario y criterios de aceptacion
  2. Arquitectura -- Diseno de componentes, ADRs, threat model en paralelo
  3. Desarrollo  -- Implementacion TDD (rojo-verde-refactor)
  4. Calidad     -- Code review + OWASP scan + compliance check + SBOM
  5. Documentacion -- API docs, guia de usuario, changelog
  6. Entrega     -- Pipeline CI/CD, Docker, deploy

Cada transicion entre fases requiere superar la quality gate correspondiente.
```

## Arquitectura

### Agentes

El plugin implementa 8 agentes, cada uno con un system prompt especializado, un conjunto de herramientas definido y un modelo asignado segun la complejidad de su tarea:

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

### Skills (29)

Cada skill es una habilidad concreta que un agente ejecuta. Estan organizados por dominio:

```
skills/
  producto/          -- write-prd, user-stories, acceptance-criteria, competitive-analysis
  arquitectura/      -- write-adr, choose-stack, design-system, evaluate-dependencies
  desarrollo/        -- tdd-cycle, explore-codebase, refactor, code-review-response
  seguridad/         -- threat-model, dependency-audit, security-review, compliance-check, sbom-generate
  calidad/           -- test-plan, code-review, exploratory-testing, regression-check
  devops/            -- dockerize, ci-cd-pipeline, deploy-config, monitoring-setup
  documentacion/     -- api-docs, architecture-docs, user-guide, changelog
```

### Hooks (5)

Los hooks interceptan eventos del ciclo de vida de Claude Code para aplicar validaciones automaticas:

| Hook | Evento | Funcion |
|------|--------|---------|
| `session-start.sh` | `SessionStart` | Detecta stack tecnologico e inicializa el contexto de sesion |
| `stop-hook.py` | `Stop` | Genera resumen de sesion con fases completadas y pendientes |
| `secret-guard.sh` | `PreToolUse` (Write/Edit) | Bloquea escritura de secretos (API keys, tokens, passwords) |
| `quality-gate.py` | `PostToolUse` (Bash) | Verifica que los tests pasen despues de ejecuciones de Bash |
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

### Core (3 modulos, ~1.400 lineas)

El nucleo del plugin esta implementado en Python con tests unitarios:

| Modulo | Lineas | Funcion |
|--------|--------|---------|
| `orchestrator.py` | ~600 | Maquina de estados de flujos, gestion de sesiones, evaluacion de gates |
| `personality.py` | ~400 | Motor de personalidad: frases, tono, anuncios, formato de veredicto |
| `config_loader.py` | ~400 | Carga de configuracion, deteccion de stack, preferencias de proyecto |

```bash
# Ejecutar tests
python3 -m pytest tests/ -v
```

## Quality gates

Las quality gates son puntos de control infranqueables entre fases. Si una gate no se supera, el flujo se detiene. No hay excepciones, no hay modo de saltarselas:

| Gate | Condicion |
|------|-----------|
| PRD aprobado | El usuario valida el PRD antes de pasar a arquitectura |
| Diseno aprobado | El usuario aprueba el diseno Y el security officer lo valida |
| Tests en verde | Todos los tests pasan antes de pasar a calidad |
| QA + seguridad | El QA engineer y el security officer aprueban en paralelo |
| Documentacion completa | Todos los artefactos estan documentados |
| Pipeline verde | CI/CD verde, sin usuario root en contenedor, sin secretos en imagen |

Cada gate produce un veredicto formal: **APROBADO**, **APROBADO CON CONDICIONES** o **RECHAZADO**, con hallazgos bloqueantes y proxima accion recomendada.

## Compliance

El plugin integra verificaciones de compliance europeo en el flujo de desarrollo:

- **RGPD** -- Proteccion de datos desde el diseno. Verificacion de base legal, minimizacion de datos, derechos de los interesados.
- **NIS2** -- Directiva de ciberseguridad para operadores esenciales. Gestion de riesgos, notificacion de incidentes, cadena de suministro.
- **CRA** -- Cyber Resilience Act. Requisitos de ciber-resiliencia para productos digitales con componentes conectados.
- **OWASP Top 10** -- Verificacion sistematica de las 10 vulnerabilidades mas explotadas en cada revision de seguridad.
- **SBOM** -- Generacion automatica del Software Bill of Materials con inventario de dependencias, licencias y CVEs conocidos.

## Deteccion de stack

El hook `session-start.sh` analiza el directorio de trabajo al iniciar sesion y detecta automaticamente:

| Lenguaje | Senales | Ecosistema |
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
  skills/                 # 29 skills en 7 dominios
  hooks/                  # 5 hooks del ciclo de vida
    hooks.json            # Configuracion de eventos
  core/                   # Motor de orquestacion (Python)
  templates/              # 7 plantillas de artefactos
  tests/                  # Tests unitarios (pytest)
  site/                   # Landing page para GitHub Pages
```

## Configuracion

El plugin se puede configurar por proyecto creando el fichero `.claude/alfred-dev.local.md` en la raiz del proyecto:

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

[Documentacion completa](https://686f6c61.github.io/Claude-JARVIS-dev/) | [Codigo fuente](https://github.com/686f6c61/Claude-JARVIS-dev)
