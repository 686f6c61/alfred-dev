---
description: "Muestra los comandos disponibles de Alfred Dev"
---

# Ayuda de Alfred Dev

Muestra al usuario la siguiente tabla de comandos disponibles con descripción y ejemplos:

Si existe una sesión activa y solo vas a mostrar ayuda, arma antes un bypass
transitorio del stop hook para que Claude Code pueda cerrar este comando sin
reabrir el flujo:

```bash
python3 .claude/alfred-continuity.py allow-stop-once "$PWD" --command "/alfred-dev:help"
```

| Comando | Argumentos | Descripción |
|---------|-----------|-------------|
| `/alfred-dev:feature` | [descripción] | Ciclo completo: producto, arquitectura, desarrollo, QA, documentación, entrega |
| `/alfred-dev:discuss` | [idea] | Refina una idea o feature antes de abrir un flujo completo |
| `/alfred-dev:quick` | [descripción] | Cambio pequeño y acotado con menos ceremonia, pero con tests y seguridad |
| `/alfred-dev:fix` | [descripción] | Corrección de bugs: diagnóstico, corrección TDD, validación |
| `/alfred-dev:spike` | [tema] | Investigación técnica sin compromiso de implementación |
| `/alfred-dev:ship` | -- | Preparar entrega: auditoría, docs, empaquetado, despliegue |
| `/alfred-dev:audit` | -- | Auditoría completa con 4 agentes en paralelo |
| `/alfred-dev:map-codebase` | [área] | Mapa brownfield persistente del repositorio antes de abrir nuevos flujos |
| `/alfred-dev:next` | -- | Decide el siguiente paso operativo y actúa si es inequívoco |
| `/alfred-dev:pause` | -- | Crea un handoff explícito para pausar el trabajo actual |
| `/alfred-dev:progress` | -- | Resume progreso, kanban, bloqueos y trazabilidad del proyecto |
| `/alfred-dev:memory-ui` | -- | Abre una UI local en navegador con memoria SQLite, timeline, decisiones, grafo y búsqueda |
| `/alfred-dev:standup` | -- | Standup breve y accionable desde SonIA |
| `/alfred-dev:blocked` | -- | Lista las tareas bloqueadas del proyecto |
| `/alfred-dev:in-progress` | -- | Lista las tareas que están en curso |
| `/alfred-dev:resume` | -- | Retoma una sesión activa o un handoff pendiente |
| `/alfred-dev:verify` | [estado opcional] | Prepara o registra la validación manual/UAT del último entregable |
| `/alfred-dev:validate` | -- | Valida la salud operativa de kanban, trazabilidad, UAT y sync local |
| `/alfred-dev:search` | [texto] | Busca en artefactos de SonIA y memoria SQLite |
| `/alfred-dev:sync-github` | [owner/repo opcional] | Ejecuta SonIA Sync sobre GitHub Issues |
| `/alfred-dev:config` | -- | Configurar autonomía, stack, agentes opcionales y personalidad |
| `/alfred-dev:status` | -- | Estado de la sesión activa |
| `/alfred-dev:update` | -- | Comprobar y aplicar actualizaciones del plugin |
| `/alfred-dev:help` | -- | Esta ayuda |

Además, al escribir `/alfred-dev:alfred` sin subcomando, Alfred actúa como asistente contextual: evalúa el estado del proyecto y la sesión, y dirige al usuario al flujo más adecuado.

Explica brevemente que Alfred Dev es un equipo de **10 agentes de núcleo** (siempre activos) más **8 agentes opcionales** (activables según el proyecto) que cubren el ciclo completo de ingeniería de software, con quality gates y flujos automatizados.

### Agentes de núcleo

Alfred (orquestador), product-owner, architect, senior-dev, security-officer, qa-engineer, devops-engineer, tech-writer, project-manager (SonIA) y Selina (La Estilista, directora de estilo visual).

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
