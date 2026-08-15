---
description: "Configura Alfred Dev: autonomía, proyecto, Lucius, memoria y personalidad. Antes /alfred-dev:config"
---

# /alfred-dev:ajustes

Lee el fichero `.claude/alfred-dev.local.md` si existe. Si no existe, créalo con la configuración canónica actual del plugin.

Escribe siempre la clave canónica `autonomia` en el frontmatter, aunque encuentres variantes legacy como `autonomía`. El runtime las entiende por retrocompatibilidad, pero la escritura nueva debe quedar normalizada.

## Paso 0: helper determinista

Antes de razonar o preguntar, ejecuta este Bash inmediatamente para cargar o
crear la configuración, detectar stack, construir las 7 secciones y generar el
menú canónico:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/core/config_cli.py" "$PWD" --headless
```

Conserva ese stdout como `CONFIG_SUMMARY`. Si el comando falla porque
`CLAUDE_PLUGIN_ROOT` no existe en desarrollo local, reintenta una sola vez con
`python3 core/config_cli.py "$PWD" --headless` solo si estás en el repo del
plugin. En modo headless, `CONFIG_SUMMARY` debe contener el marcador literal
`CONFIG_HEADLESS_MENU`.

## Modo no interactivo / `claude -p`

Si esta invocación se está ejecutando en modo no interactivo/headless
(`claude -p`, SDK sin callback `canUseTool`, auditoría automatizada o cualquier
contexto donde no puedas recibir una selección del usuario en esta misma
llamada), **no llames `AskUserQuestion`**. En ese modo:

1. devuelve `CONFIG_SUMMARY` tal cual, sin reescribirlo con otra tabla;
2. no abras submenús;
3. no termines con una pregunta abierta.

No esperes indefinidamente una respuesta humana en modo headless y no abras los
submenús de agentes opcionales ni memoria sin una selección real del usuario.
Si llamas a `AskUserQuestion` y la herramienta vuelve cancelada, sin selección,
sin respuesta utilizable o con cualquier señal de que el usuario no pudo elegir,
trátalo igual que modo headless: devuelve `CONFIG_SUMMARY` tal cual. No
conviertas esa cancelación en una pregunta abierta tipo "¿sobre qué sección
actúo?".

Presenta al usuario la configuración actual organizada en secciones:

1. **Autonomía por fase** (`interactivo` / `semi-autonomo` / `autonomo`): producto, arquitectura, desarrollo, calidad, documentacion, entrega
2. **Proyecto** (detectado o manual): runtime, lenguaje, framework, ORM, test runner, bundler
3. **Agentes opcionales**: solo Lucius
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

El runtime solo admite **Lucius**. No ofrezcas data-engineer, github-manager,
copywriter, librarian ni el resto del catálogo 0.6.

| Agente | Rol | Cuándo es útil |
|--------|-----|----------------|
| **lucius** | Director técnico externo | Segunda opinión vía Codex CLI en un cierre de calidad, `audit` o `ship` |

Usa el menú canónico de `core/optional_agents.py`
(`build_optional_agent_group_menu`) con un único grupo `Auditoria`.

```text
AskUserQuestion({
  questions: [
    {
      question: "¿Quieres activar Lucius como segunda opinión externa?",
      header: "Auditoria",
      multiSelect: false,
      options: [
        { label: "Seguir sin activar más", description: "Pasar al siguiente grupo" },
        { label: "Lucius", description: "<razón contextual>" }
      ]
    }
  ]
})
```

Guarda solo esta clave:

```yaml
agentes_opcionales:
  lucius: false
```

## Sección de memoria persistente

La memoria persistente guarda decisiones, gates, handoffs, UAT y commits hechos
en una sesión de Alfred. No importa el historial antiguo de Git ni rellena la
UI con consejos operativos. Para consultarla usa las tools MCP `alfred-memory`
o `/alfred-dev:memory-ui`.

### Paso 1: comprobar el estado actual

Primero lee la configuración efectiva y comprueba `memoria.enabled`:

- **Si `memoria.enabled` es `true` y existe `.claude/alfred-memory.db`**: lee las estadísticas con la herramienta MCP `memory_stats` y presenta un resumen compacto: número de decisiones, commits registrados, iteraciones y fecha del registro más antiguo. Indica que la memoria está **activa**.
- **Si `memoria.enabled` es `true` pero la DB aún no existe**: indica que la memoria está **configurada como activa** y que la base de datos se inicializará en el siguiente arranque o en cuanto el runtime la necesite.
- **Si `memoria.enabled` es `false`**: indica que la memoria está **inactiva**, aunque puedan existir datos históricos en `.claude/alfred-memory.db`.

### Paso 2: preguntar al usuario

Usa AskUserQuestion para preguntar al usuario si quiere activar o desactivar la memoria persistente. Presenta las opciones de forma clara:

- **Activar**: Alfred registrará decisiones de diseño, gates, handoffs, UAT y commits de la sesión.
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

- Si se activó: confirma que solo se registrará lo útil (decisiones, gates, handoffs, UAT, commits de la sesión).
- Si se desactivó: confirma que la memoria queda inactiva pero los datos existentes no se borran.
