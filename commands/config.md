---
description: "Configura Alfred Dev: autonomía, stack, agentes opcionales y personalidad"
---

# Configuración de Alfred Dev

Lee el fichero `.claude/alfred-dev.local.md` si existe. Si no existe, créalo con la configuración por defecto.

Presenta al usuario la configuración actual organizada en secciones:

1. **Autonomía por fase** (interactivo/semi-autónomo/autónomo): producto, arquitectura, desarrollo, seguridad, calidad, documentación, devops
2. **Proyecto** (detectado o manual): nombre, lenguaje, framework, runtime, gestor de paquetes, base de datos, ORM
3. **Agentes opcionales**: data-engineer, ux-reviewer, performance-engineer, github-manager, seo-specialist, copywriter
4. **Compliance**: RGPD, NIS2, CRA, sector, jurisdicción
5. **Integraciones**: CI, contenedores, registro, hosting, monitoring
6. **Personalidad**: nivel de sarcasmo (1-5), celebrar victorias, insultar malas prácticas

Usa AskUserQuestion para preguntar qué sección quiere modificar. Después de cada cambio, actualiza el fichero .local.md.

Si el proyecto no tiene configuración y hay ficheros en el directorio actual, ejecuta detección automática de stack y presenta los resultados al usuario para confirmar.

## Sección de agentes opcionales

Alfred Dev tiene 8 agentes de núcleo (siempre activos) y 6 agentes opcionales que el usuario puede activar según las necesidades de su proyecto. Los agentes opcionales son predefinidos: vienen con el plugin pero no se activan hasta que el usuario lo decide.

### Agentes opcionales disponibles

| Agente | Rol | Cuándo es útil |
|--------|-----|----------------|
| **data-engineer** | Ingeniero de datos | Proyectos con base de datos, ORM, migraciones |
| **ux-reviewer** | Revisor de UX | Proyectos con frontend (React, Vue, Svelte, etc.) |
| **performance-engineer** | Ingeniero de rendimiento | Proyectos grandes o con requisitos de rendimiento |
| **github-manager** | Gestor de GitHub | Cualquier proyecto con repositorio en GitHub |
| **seo-specialist** | Especialista SEO | Proyectos web con contenido público |
| **copywriter** | Copywriter | Proyectos con textos públicos: landing, emails, onboarding |

### Descubrimiento contextual

Si es la primera vez que el usuario configura el plugin en un proyecto (o si no tiene agentes opcionales activados), ejecuta el descubrimiento contextual:

1. Analiza el proyecto: stack, presencia de BD/ORM, frontend, contenido web público, remote Git, tamaño del proyecto.
2. Basándote en el análisis, sugiere qué agentes opcionales podrían ser útiles. Explica brevemente por qué cada uno es relevante para este proyecto concreto.
3. Presenta las sugerencias al usuario con AskUserQuestion (multiSelect: true) para que elija cuáles activar.
4. Guarda la selección en el fichero .local.md bajo la clave `agentes_opcionales`.

### Gestión manual

Si el usuario elige la sección de agentes opcionales desde el menú principal:

1. Muestra el estado actual (activo/inactivo) de cada agente opcional.
2. Usa AskUserQuestion (multiSelect: true) con los 6 agentes como opciones, preseleccionando los que ya están activos.
3. Actualiza el fichero .local.md con la nueva selección.

### Formato en el fichero .local.md

```yaml
agentes_opcionales:
  data-engineer: true
  ux-reviewer: false
  performance-engineer: false
  github-manager: true
  seo-specialist: true
  copywriter: false
```

## Sección de memoria persistente

La memoria persistente permite que Alfred Dev recuerde decisiones, iteraciones y commits entre sesiones. Está gestionada por el agente **librarian** (El Bibliotecario), que se activa automáticamente cuando la memoria está habilitada.

### Paso 1: comprobar el estado actual

Comprueba si la base de datos de memoria existe buscando el fichero `.claude/alfred-memory.db` en el proyecto:

- **Si existe**: lee las estadísticas con la herramienta MCP `memory_stats` y presenta al usuario un resumen compacto: número de decisiones, commits registrados, iteraciones y fecha del registro más antiguo. Indica que la memoria está **activa**.
- **Si no existe**: indica al usuario que la memoria persistente **no está activada** y que puede activarla desde aquí.

### Paso 2: preguntar al usuario

Usa AskUserQuestion para preguntar al usuario si quiere activar o desactivar la memoria persistente. Presenta las opciones de forma clara:

- **Activar**: Alfred registrará decisiones, commits e iteraciones automáticamente entre sesiones. El Bibliotecario estará disponible para consultas históricas.
- **Desactivar**: no se registrará nada y el Bibliotecario no participará en los flujos. Los datos existentes se conservan pero no se consultan.

### Paso 3: aplicar la configuración

Si el usuario elige **activar** la memoria, escribe (o actualiza) la sección `memoria:` en el frontmatter de `.claude/alfred-dev.local.md` con estos valores:

```yaml
memoria:
  enabled: true
  capture_decisions: true
  capture_commits: true
  retention_days: 365
```

Si el usuario elige **desactivar** la memoria, actualiza la sección a:

```yaml
memoria:
  enabled: false
```

### Paso 4: confirmar

Informa al usuario del resultado:

- Si se activó: confirma que el Bibliotecario se activará automáticamente en los flujos y que las decisiones y commits se registrarán a partir de ahora.
- Si se desactivó: confirma que la memoria queda inactiva pero los datos existentes no se borran.
