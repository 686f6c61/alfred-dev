---
description: "Configura Alfred Dev: autonomía, proyecto, agentes opcionales, memoria y personalidad"
---

# Configuración de Alfred Dev

Lee el fichero `.claude/alfred-dev.local.md` si existe. Si no existe, créalo con la configuración canónica actual del plugin.

Escribe siempre la clave canónica `autonomia` en el frontmatter, aunque encuentres variantes legacy como `autonomía`. El runtime las entiende por retrocompatibilidad, pero la escritura nueva debe quedar normalizada.

Presenta al usuario la configuración actual organizada en secciones:

1. **Autonomía por fase** (`interactivo` / `semi-autonomo` / `autonomo`): producto, arquitectura, desarrollo, calidad, documentacion, entrega
2. **Proyecto** (detectado o manual): runtime, lenguaje, framework, ORM, test runner, bundler
3. **Agentes opcionales**: data-engineer, ux-reviewer, performance-engineer, github-manager, seo-specialist, copywriter, librarian, i18n-specialist, lucius
4. **Memoria persistente**: enabled, sync_to_native, sync_commits_limit, capture_decisions, capture_commits, retention_days
5. **Compliance**: estilo, lint, format_on_save
6. **Integraciones**: git, ci, deploy
7. **Personalidad**: nivel_sarcasmo (1-5), verbosidad, idioma, celebrar_victorias, insultar_malas_practicas

Usa AskUserQuestion para preguntar qué sección quiere modificar con un **menú
principal navegable**. No inventes ese menú a mano si puedes evitarlo: toma
como referencia las funciones canónicas de `core/config_loader.py`
(`build_config_section_summaries()` y `build_config_section_menu()`) para que
las descripciones de cada sección salgan de la configuración efectiva real y no
de texto reconstruido en el prompt. Después de cada cambio, actualiza el
fichero `.local.md`.

Antes de guardar, construye un **preview antes/después** de la sección tocada.
No improvises ese diff en prosa si puedes evitarlo: toma como referencia
`build_config_section_change_preview()` para confirmar qué cambia realmente y
detectar no-ops antes de reescribir el fichero.

Cuando el usuario confirme, evita recomponer el ciclo “cargar → aplicar →
guardar” a mano: usa como referencia `update_config_section()` o
`update_project_config_section()` para persistir solo la sección tocada sin
perder notas, orden estable ni claves canónicas.

No reescribas el frontmatter “a mano” si puedes evitarlo: toma como referencia
las funciones canónicas de `core/config_loader.py` (`render_config_markdown()`,
`save_config()`, `save_project_config()` y `apply_config_section_update()`) para
mantener orden estable, claves canónicas y round-trip limpio con
`load_config()`.

Si el proyecto no tiene configuración y hay ficheros en el directorio actual, ejecuta detección automática de stack y presenta los resultados al usuario para confirmar. Si es la primera sesión del proyecto, puedes encontrar que SessionStart ya haya sembrado `.claude/alfred-dev.local.md` con autonomía por fases en `autonomo` y memoria activada.

## Sección de agentes opcionales

Alfred Dev tiene 10 agentes de núcleo (siempre activos) y 9 agentes opcionales que el usuario puede activar según las necesidades de su proyecto. Los agentes opcionales son predefinidos: vienen con el plugin pero no se activan hasta que el usuario lo decide.

### Agentes opcionales disponibles

**Grupo A -- Técnicos:**

| Agente | Rol | Cuándo es útil |
|--------|-----|----------------|
| **data-engineer** | Ingeniero de datos | Esquema, migraciones, queries, índices o persistencia |
| **performance-engineer** | Ingeniero de rendimiento | Latencia, bundles, memoria o cuellos de botella medibles |
| **github-manager** | Gestor de GitHub | Proyectos con repositorio en GitHub |
| **librarian** | Bibliotecario | Proyectos con memoria persistente o historial de decisiones; especialista solo bajo demanda |

**Grupo B -- Contenido y UX:**

| Agente | Rol | Cuándo es útil |
|--------|-----|----------------|
| **ux-reviewer** | Revisor de UX | Proyectos con frontend (React, Vue, Svelte, etc.) |
| **seo-specialist** | Especialista SEO | Proyectos web con contenido público |
| **copywriter** | Copywriter | Proyectos con textos públicos: landing, emails, onboarding |
| **i18n-specialist** | Especialista i18n | Proyectos multiidioma o que necesitan prepararse para traducción |

**Grupo C -- Auditoría externa:**

| Agente | Rol | Cuándo es útil |
|--------|-----|----------------|
| **lucius** | Director técnico externo | Cuando el usuario quiere una segunda opinión técnica independiente para esta tarea o para una fase de cierre |

### Descubrimiento contextual

Si es la primera vez que el usuario configura el plugin en un proyecto (o si no tiene agentes opcionales activados), ejecuta el descubrimiento contextual:

1. Analiza el proyecto: stack, presencia de BD/ORM, frontend, contenido web público, remote GitHub, tamaño del proyecto, ficheros i18n.
2. Basándote en el análisis, sugiere qué agentes opcionales podrían ser útiles. Los recomendados llevan «(Recomendado)» en el label.
3. Presenta las sugerencias al usuario con **3 menús navegables**, uno por grupo (`Técnicos`, `Contenido y UX`, `Auditoría`). No lances las 3 preguntas a la vez ni como texto plano: cada grupo debe mostrarse como un menú seleccionable real.
4. Si el usuario quiere activar más de un agente dentro del mismo grupo, repite el menú del grupo y permite seleccionar **un agente por interacción** hasta que elija `Seguir sin activar más` o `Listo con este grupo`.
5. Cada menú debe incluir una opción explícita de salida (`Seguir sin activar más` o equivalente) para que el usuario no quede atrapado.

La estructura de estos menús ya no se inventa ad hoc: toma como referencia el
catálogo canónico de `core/optional_agents.py` (`build_optional_agent_group_menu`
y `build_optional_agent_group_menus`) para respetar el mismo orden, labels y
descripciones base en todos los comandos.

Ejemplo para un grupo:

```text
AskUserQuestion({
  question: "¿Qué agente técnico quieres activar ahora?",
  header: "Técnicos",
  options: [
    { label: "Seguir sin activar más", description: "Pasar al siguiente grupo" },
    { label: "Data Engineer", description: "<razón contextual>" },
    { label: "Performance Engineer", description: "<razón contextual>" },
    { label: "GitHub Manager", description: "<razón contextual>" }
  ]
})
```

Si el usuario selecciona `Data Engineer`, actualiza la selección acumulada y vuelve a mostrar el mismo grupo con las opciones restantes hasta que elija salir del grupo.

4. Guarda la selección en el fichero .local.md bajo la clave `agentes_opcionales`.

### Gestión manual

Si el usuario elige la sección de agentes opcionales desde el menú principal:

1. Muestra el estado actual (activo/inactivo) de cada agente opcional.
2. Usa los mismos **3 menús navegables por grupo** que en el descubrimiento contextual. No pongas todas las opciones de golpe en texto ni en una llamada única difícil de navegar.
3. Indica en la descripción cuáles están activos actualmente y repite cada menú tantas veces como haga falta para que el usuario active o desactive varios agentes, uno por interacción.
3. Actualiza el fichero .local.md con la nueva selección.

### Formato en el fichero .local.md

```yaml
agentes_opcionales:
  data-engineer: true
  performance-engineer: false
  github-manager: true
  librarian: false
  ux-reviewer: false
  seo-specialist: true
  copywriter: false
  i18n-specialist: false
  lucius: false
```

## Sección de memoria persistente

La memoria persistente permite que Alfred Dev recuerde decisiones, iteraciones y commits entre sesiones. Es la capa de datos del proyecto; el agente opcional **librarian** (El Bibliotecario) es el especialista para consultarla dentro de los flujos, pero su activación sigue siendo independiente.

### Paso 1: comprobar el estado actual

La memoria persistente es la capa de datos del proyecto. El agente opcional **librarian** es su especialista de consulta, pero sigue siendo una activación separada: `memoria.enabled: true` NO implica escribir `librarian: true` automáticamente.

Primero lee la configuración efectiva y comprueba `memoria.enabled`:

- **Si `memoria.enabled` es `true` y existe `.claude/alfred-memory.db`**: lee las estadísticas con la herramienta MCP `memory_stats` y presenta un resumen compacto: número de decisiones, commits registrados, iteraciones y fecha del registro más antiguo. Indica que la memoria está **activa**.
- **Si `memoria.enabled` es `true` pero la DB aún no existe**: indica que la memoria está **configurada como activa** y que la base de datos se inicializará en el siguiente arranque o en cuanto el runtime la necesite.
- **Si `memoria.enabled` es `false`**: indica que la memoria está **inactiva**, aunque puedan existir datos históricos en `.claude/alfred-memory.db`.

### Paso 2: preguntar al usuario

Usa AskUserQuestion para preguntar al usuario si quiere activar o desactivar la memoria persistente. Presenta las opciones de forma clara:

- **Activar**: Alfred registrará decisiones, commits e iteraciones automáticamente entre sesiones. Si el usuario quiere consultas históricas dentro de los flujos, podrá activar también `librarian`.
- **Desactivar**: no se registrará nada nuevo. Los datos existentes se conservan, pero Alfred no los capturará ni los consultará de forma operativa.

### Paso 3: aplicar la configuración

Si el usuario elige **activar** la memoria, escribe (o actualiza) la sección `memoria:` en el frontmatter de `.claude/alfred-dev.local.md` con estos valores:

```yaml
memoria:
  enabled: true
  sync_to_native: true
  sync_commits_limit: 10
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

- Si se activó: confirma que las decisiones y commits se registrarán a partir de ahora. Si `librarian` está desactivado, sugiere activarlo desde la sección de agentes opcionales, pero no lo cambies sin confirmación explícita.
- Si se desactivó: confirma que la memoria queda inactiva pero los datos existentes no se borran.
