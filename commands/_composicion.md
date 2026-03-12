# Protocolo de composición dinámica de equipo

Este fichero define el protocolo compartido para componer el equipo de cada sesión.
Lo usan todos los comandos de Alfred (feature, fix, spike, audit, ship). Cualquier
cambio aquí se refleja en todos los flujos.

## Paso 1 -- Contexto del proyecto

Llama a `suggest_optional_agents(project_dir)` para obtener señales basadas en I/O
del proyecto (stack detectado, presencia de ORM, frontend, HTML público, remote Git,
tamaño del proyecto, memoria activa). Estas señales son objetivas y complementan tu
razonamiento semántico.

## Paso 2 -- Razonamiento semántico

Lee la descripción de la tarea y las señales del proyecto. Decide qué agentes
opcionales son relevantes usando tu comprensión semántica, no keywords. Razona
sobre el dominio de la tarea, no sobre palabras sueltas.

### Catálogo de agentes opcionales

| Agente | Especialidad | Cuándo es útil |
|--------|-------------|----------------|
| **data-engineer** | Modelado de datos, esquemas, migraciones, queries, ETL | Tareas que implican bases de datos, ORMs, pipelines de datos, optimización de queries |
| **ux-reviewer** | Accesibilidad, usabilidad, flujos de usuario, heurísticas de Nielsen | Tareas que afectan a la interfaz de usuario o a la experiencia del visitante |
| **performance-engineer** | Profiling, benchmarks, bundles, memoria, latencia, carga | Tareas donde el rendimiento es un requisito o una preocupación |
| **github-manager** | PRs, releases, issues, branch protection, pipelines CI/CD | Tareas que implican gestión del repositorio, publicación o automatización de entrega |
| **seo-specialist** | Meta tags, datos estructurados, Core Web Vitals, sitemaps, Lighthouse | Tareas que afectan al posicionamiento web o al contenido público indexable |
| **copywriter** | Textos de interfaz, landing pages, emails, tono de comunicación | Tareas que incluyen redacción dirigida a usuarios o visitantes |
| **librarian** | Memoria persistente, historial de decisiones, ADRs, cronología | Tareas donde el contexto histórico del proyecto es relevante o se toman decisiones arquitectónicas |

### Criterios de decisión

Para cada agente, pregúntate: **¿participaría un profesional con esta especialidad
en esta tarea concreta?** No te guíes por palabras clave aisladas; entiende la
intención de la tarea.

Ejemplos de razonamiento:
- "Implementar pagos con Stripe" → senior-dev (negocio), quizá data-engineer si hay
  modelo de datos nuevo. NO es automático que "pagos" = data-engineer.
- "Dark mode en el dashboard" → ux-reviewer (afecta a la interfaz), aunque no
  contenga la palabra "formulario" ni "responsive".
- "¿Por qué se eligió SQLite?" → librarian, aunque no diga "historial".

Combina tu razonamiento con las señales del proyecto (paso 1): si el proyecto tiene
React y la tarea toca interfaz, ux-reviewer es casi seguro. Si no tiene frontend,
probablemente no.

## Paso 3 -- Presentación al usuario

Presenta un `AskUserQuestion` con `multiSelect` que contenga:

**Bloque informativo (no seleccionable):**
> Equipo de núcleo (siempre activos): Alfred, Product Owner, Arquitecto, Senior Dev,
> Security Officer, QA Engineer, Tech Writer, DevOps.

**TODOS los agentes opcionales como checkboxes:**
Muestra los 7 agentes opcionales. Los que has decidido que son relevantes van
**preseleccionados** con una razón breve. Los demás aparecen **disponibles pero
sin seleccionar**, para que el usuario pueda añadir cualquiera que se te haya
escapado.

Formato por agente:
- Preseleccionado: `[x] Data Engineer -- El proyecto usa Prisma y la tarea implica migración de esquema`
- Disponible: `[ ] SEO Specialist -- Optimización de posicionamiento web`

**Checkbox de infraestructura:**
- **Memoria persistente:** preseleccionada si hay una DB de memoria activa o si la
  tarea se beneficiaría de contexto histórico. Disponible siempre.

## Paso 4 -- Construcción de equipo_sesion

Con la respuesta del usuario, construye el diccionario `equipo_sesion`:

```
equipo_sesion = {
    "opcionales_activos": {
        "data-engineer": True/False,
        "ux-reviewer": True/False,
        "performance-engineer": True/False,
        "github-manager": True/False,
        "seo-specialist": True/False,
        "copywriter": True/False,
        "librarian": True/False,
    },
    "infra": {
        "memoria": True/False,
    },
    "fuente": "composicion_dinamica",
}
```

Pasa `equipo_sesion` internamente al flujo. Desde este momento, cada fase consulta
`equipo_sesion` en lugar de la configuración persistente para decidir qué agentes
opcionales participan.
