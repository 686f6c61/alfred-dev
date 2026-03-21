---
description: "Muestra los comandos disponibles de Alfred Dev"
---

# Ayuda de Alfred Dev

Muestra al usuario la siguiente tabla de comandos disponibles con descripción y ejemplos:

| Comando | Argumentos | Descripción |
|---------|-----------|-------------|
| `/alfred-dev:feature` | [descripción] | Ciclo completo: producto, arquitectura, desarrollo, QA, documentación, entrega |
| `/alfred-dev:fix` | [descripción] | Corrección de bugs: diagnóstico, corrección TDD, validación |
| `/alfred-dev:spike` | [tema] | Investigación técnica sin compromiso de implementación |
| `/alfred-dev:ship` | -- | Preparar entrega: auditoría, docs, empaquetado, despliegue |
| `/alfred-dev:audit` | -- | Auditoría completa con 4 agentes en paralelo |
| `/alfred-dev:config` | -- | Configurar autonomía, stack, agentes opcionales y personalidad |
| `/alfred-dev:status` | -- | Estado de la sesión activa |
| `/alfred-dev:update` | -- | Comprobar y aplicar actualizaciones del plugin |
| `/alfred-dev:help` | -- | Esta ayuda |

Además, al escribir `/alfred-dev:alfred` sin subcomando, Alfred actúa como asistente contextual: evalúa el estado del proyecto y la sesión, y dirige al usuario al flujo más adecuado.

Explica brevemente que Alfred Dev es un equipo de **9 agentes de núcleo** (siempre activos) más **8 agentes opcionales** (activables según el proyecto) que cubren el ciclo completo de ingeniería de software, con quality gates y flujos automatizados.

### Agentes de núcleo

product-owner, architect, senior-dev, security-officer, qa-engineer, devops-engineer, tech-writer, project-manager (SonIA) y Alfred como orquestador.

### Agentes opcionales

Se activan con `/alfred-dev:config`. Alfred los sugiere automáticamente al analizar el proyecto:

| Agente | Cuándo es útil |
|--------|----------------|
| **data-engineer** | Proyectos con base de datos, ORM, migraciones |
| **ux-reviewer** | Proyectos con frontend |
| **performance-engineer** | Proyectos grandes o con requisitos de rendimiento |
| **github-manager** | Cualquier proyecto con repositorio GitHub |
| **seo-specialist** | Proyectos web con contenido público |
| **copywriter** | Proyectos con textos públicos |
| **librarian** | Proyectos con memoria persistente activa |
| **i18n-specialist** | Proyectos multiidioma o que necesitan traducción |
