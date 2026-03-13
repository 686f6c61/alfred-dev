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

**Grupo A -- Técnicos:**

| Agente | Especialidad | Cuándo es útil |
|--------|-------------|----------------|
| **data-engineer** | Modelado de datos, esquemas, migraciones, queries, ETL | Tareas que implican bases de datos, ORMs, pipelines de datos, optimización de queries |
| **performance-engineer** | Profiling, benchmarks, bundles, memoria, latencia, carga | Tareas donde el rendimiento es un requisito o una preocupación |
| **github-manager** | PRs, releases, issues, branch protection, pipelines CI/CD | Tareas que implican gestión del repositorio, publicación o automatización de entrega |
| **librarian** | Memoria persistente, historial de decisiones, ADRs, cronología | Tareas donde el contexto histórico del proyecto es relevante o se toman decisiones arquitectónicas |

**Grupo B -- Contenido y UX:**

| Agente | Especialidad | Cuándo es útil |
|--------|-------------|----------------|
| **ux-reviewer** | Accesibilidad, usabilidad, flujos de usuario, heurísticas de Nielsen | Tareas que afectan a la interfaz de usuario o a la experiencia del visitante |
| **seo-specialist** | Meta tags, datos estructurados, Core Web Vitals, sitemaps, Lighthouse | Tareas que afectan al posicionamiento web o al contenido público indexable |
| **copywriter** | Textos de interfaz, landing pages, emails, tono de comunicación | Tareas que incluyen redacción dirigida a usuarios o visitantes |
| **i18n-specialist** | Internacionalización, claves i18n, formatos por locale, cadenas hardcodeadas | Tareas en proyectos multiidioma o que necesitan prepararse para traducción |

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

Antes de las preguntas, muestra un mensaje informativo:

> **Equipo de núcleo** (siempre activos): Alfred, Product Owner, Arquitecto, Senior Dev,
> Security Officer, QA Engineer, SonIA, Tech Writer, DevOps.

Después, usa `AskUserQuestion` con **2 preguntas multiSelect** en una sola llamada.
Los agentes que hayas decidido que son relevantes (paso 2) deben ir con "(Recomendado)"
al final del label. La `description` de cada opción debe explicar por qué es relevante
para esta tarea concreta, no una descripción genérica del agente.

**IMPORTANTE:** `AskUserQuestion` admite máximo 4 opciones por pregunta. Por eso los
8 agentes opcionales se reparten en 2 preguntas de 4. No intentes meterlos todos en una.

```
AskUserQuestion({
  questions: [
    {
      question: "¿Qué agentes técnicos quieres activar para esta sesión?",
      header: "Técnicos",
      multiSelect: true,
      options: [
        { label: "Data Engineer", description: "<razón contextual o descripción breve>" },
        { label: "Performance Engineer", description: "<razón contextual>" },
        { label: "GitHub Manager", description: "<razón contextual>" },
        { label: "Librarian", description: "<razón contextual>" },
      ]
    },
    {
      question: "¿Qué agentes de contenido y UX quieres activar?",
      header: "Contenido",
      multiSelect: true,
      options: [
        { label: "UX Reviewer", description: "<razón contextual>" },
        { label: "SEO Specialist", description: "<razón contextual>" },
        { label: "Copywriter", description: "<razón contextual>" },
        { label: "i18n Specialist", description: "<razón contextual>" },
      ]
    }
  ]
})
```

En la `description` de cada opción:
- Si el agente es **recomendado**: explica por qué es relevante para esta tarea.
  Ejemplo: `"El proyecto usa Prisma y la tarea implica migración de esquema (Recomendado)"`.
- Si **no es recomendado**: usa una descripción breve de su especialidad.
  Ejemplo: `"Optimización de posicionamiento web y Core Web Vitals"`.

El usuario puede seleccionar, deseleccionar o añadir cualquier combinación. Su selección
es la que manda, independientemente de tus recomendaciones.

## Paso 4 -- Construcción de equipo_sesion

Con la respuesta del usuario, construye el diccionario `equipo_sesion`:

```
equipo_sesion = {
    "opcionales_activos": {
        "data-engineer": True/False,
        "performance-engineer": True/False,
        "github-manager": True/False,
        "librarian": True/False,
        "ux-reviewer": True/False,
        "seo-specialist": True/False,
        "copywriter": True/False,
        "i18n-specialist": True/False,
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
