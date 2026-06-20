---
description: "Protocolo interno compartido para la composición dinámica del equipo de Alfred según tarea, stack y señales runtime."
---

# Protocolo de composición dinámica de equipo

Este fichero define el protocolo compartido para componer el equipo de cada sesión.
Lo usan todos los comandos de Alfred (feature, quick, fix, spike, audit, ship). Cualquier
cambio aquí se refleja en todos los flujos.

## Paso 0 -- Configuración inicial del proyecto

Antes de cualquier otra cosa, comprueba si el proyecto ya tiene configurado el modo
de autonomía. Lee `.claude/alfred-dev.local.md` y busca la sección `autonomia:` en
el frontmatter YAML.

**Si la sección `autonomia:` NO existe** (primera vez que se usa Alfred en este proyecto):

1. Escribe directamente una configuración por defecto compatible con Claude Code
   CLI en `.claude/alfred-dev.local.md`:

   ```yaml
   autonomia:
     producto: autonomo
     arquitectura: autonomo
     desarrollo: autonomo
     calidad: autonomo
     documentacion: autonomo
     entrega: autonomo
   ```

2. NO uses `AskUserQuestion` en este bootstrap inicial. El objetivo es que
   Alfred pueda actuar automáticamente desde la primera sesión si el usuario
   invoca `/alfred`, `/alfred-dev:feature`, `/alfred-dev:quick`, `/alfred-dev:fix`,
   `/alfred-dev:spike`, `/alfred-dev:audit` o `/alfred-dev:ship`.

3. Muestra un mensaje breve indicando que Alfred ha activado el modo
   autopilot por defecto para evitar bloquear el flujo en la primera sesión
   y que el usuario puede cambiarlo más tarde con `/alfred-dev:config`.

**Si la sección `autonomia:` YA existe:** salta este paso y continúa directamente.

**Nota:** el usuario puede cambiar el modo en cualquier momento con `/alfred-dev:config`.

## Paso 1 -- Contexto del proyecto

Llama a `suggest_optional_agents(project_dir)` para obtener señales basadas en I/O
del proyecto (stack detectado, presencia de ORM, frontend, HTML público, remote GitHub,
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
| **github-manager** | PRs, releases, issues, branch protection, pipelines CI/CD | Tareas que implican gestión de un repositorio GitHub, publicación o automatización de entrega |
| **librarian** | Memoria persistente, historial de decisiones, ADRs, cronología | Tareas donde el contexto histórico del proyecto es relevante; especialista solo bajo demanda |

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

### Reglas anti-solape para contenido y UX

Usa estas fronteras para no activar varios especialistas por la misma razón:

- `ux-reviewer`: accesibilidad, fricción del flujo, affordance, estados y comprensión de la interacción. No es el dueño del tono. No es el dueño del SEO técnico. No es el dueño de la cobertura de locales.
- `copywriter`: CTA, microcopy, tono y claridad del texto visible para usuario. No es el dueño de WCAG. No es el dueño de la indexación ni del structured data. No es el dueño de la integridad de claves i18n.
- `seo-specialist`: indexación, meta tags, schema.org, sitemap, rastreabilidad y Core Web Vitals con impacto SEO. No es el dueño del tono del texto. No es el dueño de la traducción. No es el dueño del flujo UX general.
- `i18n-specialist`: claves, locales, formatos regionales, cobertura entre idiomas y cadenas hardcodeadas. No es el dueño del tono comercial. No es el dueño del SEO. No es el dueño de la usabilidad del flujo.

Si una tarea toca varias fronteras de verdad, puedes combinar agentes. Si solo toca una, evita activar al resto "por si acaso".

### Reglas anti-solape para datos y rendimiento

Usa estas fronteras para no activar dos técnicos por la misma intuición:

- `data-engineer`: esquema, migraciones, índices, integridad de datos, ORM y diseño de queries. Es el dueño de corregir persistencia cuando ya sabemos que el cuello o el bug está en la capa de datos.
- `performance-engineer`: baseline, profiling, benchmarks, bundles, memoria, latencia y validación de mejora. Es el dueño de medir y aislar el cuello de botella antes de optimizar.
- Si el síntoma es "va lento" pero aún no sabemos por qué, empieza por `performance-engineer`.
- Si el diagnóstico ya apunta a una query lenta, un índice ausente, una migración o un problema de persistencia, activa también `data-engineer`.
- No actives `data-engineer` solo porque haya base de datos en el proyecto. No actives `performance-engineer` solo porque exista ORM o porque "optimizar" suene bien.

## Paso 2b -- Comprobación de autopilot

Antes de presentar las preguntas al usuario, comprueba si el modo autopilot está activo:

1. Lee `.claude/alfred-dev.local.md` y comprueba si todas las fases de autonomía están en `autonomo`.
2. Lee `.claude/alfred-dev-state.json` y comprueba si tiene `"autopilot": true`
   o, por compatibilidad con sesiones antiguas, `"modo": "autopilot"`.

**Si autopilot está activo:** salta directamente al paso 4. Usa los agentes opcionales configurados en `.claude/alfred-dev.local.md` (si existen) o los que tu razonamiento semántico (paso 2) haya marcado como relevantes. No uses `AskUserQuestion`. Muestra un mensaje breve indicando qué agentes se activan y por qué.

**Si autopilot NO está activo:** continúa con el paso 3 (presentación interactiva al usuario).

## Paso 2c -- Verificación de evidencia antes de gates automáticas

Antes de avanzar una fase con gate automática o automática+seguridad, lee
`.claude/alfred-evidence.json` y comprueba que el último registro tiene
`result: "pass"` y un timestamp de los últimos 10 minutos. Si no hay
evidencia o el último resultado no es `pass`, NO avances. Ejecuta los
tests primero.

## Paso 2d -- Persistencia de estado tras gates

Después de cada intento de superar una gate (exitoso o no), guarda el estado
actualizado en `.claude/alfred-dev-state.json`. Esto incluye el contador de
iteraciones de la fase actual.

## Paso 2e -- Honestidad operativa y antifingimiento

Antes de declarar una gate como superada, un test como ejecutado, una auditoría
como completada o una integración externa como verificada, comprueba que tienes
evidencia directa en salida de herramienta, artefacto persistido o respuesta
explícita del usuario.

- No digas "he ejecutado", "ha pasado" o "está validado" si solo lo has inferido.
- Si un helper, comando, agente o servicio externo falla, dilo con el error
  relevante y deja el siguiente paso verificable; no lo conviertas en éxito.
- Si faltan credenciales, permisos, Docker, red o contexto, declara el límite y
  conserva el flujo en estado pendiente o bloqueado.
- Distingue siempre entre "recomiendo ejecutar X" y "he ejecutado X con este
  resultado".

## Paso 3 -- Presentación al usuario

Antes de las preguntas, muestra un mensaje informativo:

> **Equipo de núcleo** (siempre activos): Alfred, Product Owner, Selina, Arquitecto,
> Senior Dev, Security Officer, QA Engineer, SonIA, Tech Writer, DevOps.

Después, usa `AskUserQuestion` con **3 menús navegables por grupo**, no con
las 3 preguntas de golpe. Los **9 agentes opcionales** siguen repartidos entre
`Técnicos`, `Contenido` y `Auditoría`, pero cada grupo se presenta y se recorre
por separado. La fuente canónica de esa estructura es `core/optional_agents.py`:
reutiliza sus grupos, orden, labels y opciones de salida (`build_optional_agent_group_menu`
/ `build_optional_agent_group_menus`) en vez de reinventar el menú en cada comando.

Los agentes que hayas decidido que son relevantes (paso 2) deben ir con
"(Recomendado)" al final del label. La `description` de cada opción debe
explicar por qué es relevante para esta tarea concreta, no una descripción
genérica del agente.

**IMPORTANTE:** no pongas una lista estática de tres bloques sin selección
real. Cada grupo debe ser un menú seleccionable. Si el usuario quiere más de
un agente del mismo grupo, repite el menú y permite elegir **uno por
interacción** hasta que seleccione `Seguir sin activar más`.

Ejemplo de un grupo:

```text
AskUserQuestion({
  questions: [
    {
      question: "¿Qué agente técnico quieres activar para esta sesión?",
      header: "Técnicos",
      multiSelect: false,
      options: [
        { label: "Seguir sin activar más", description: "Pasar al siguiente grupo" },
        { label: "Data Engineer", description: "<razón contextual o descripción breve>" },
        { label: "Performance Engineer", description: "<razón contextual>" },
        { label: "GitHub Manager", description: "<razón contextual>" }
      ]
    }
  ]
})
```

Si el usuario elige un agente, añádelo a la selección acumulada y vuelve a
mostrar ese mismo grupo con las opciones restantes. Cuando elija salir del
grupo, pasa al siguiente.

Para el grupo de auditoría, el menú mínimo debe dejar visible la opción:

```text
{ label: "Lucius", description: "<razón contextual>" }
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
        "lucius": True/False,
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
