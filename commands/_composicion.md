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
   y que el usuario puede cambiarlo más tarde con `/alfred-dev:ajustes`.

**Si la sección `autonomia:` YA existe:** salta este paso y continúa directamente.

**Nota:** el usuario puede cambiar el modo en cualquier momento con `/alfred-dev:ajustes`.

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

El runtime solo admite **Lucius**. No ofrezcas ni actives data-engineer,
performance-engineer, github-manager, librarian, ux-reviewer, seo-specialist,
copywriter ni i18n-specialist.

| Agente | Especialidad | Cuándo es útil |
|--------|-------------|----------------|
| **lucius** | Segunda opinión técnica externa vía Codex CLI, solo lectura | Cierres de calidad, validación, `audit` o `ship` si el usuario quiere otra mirada |

### Criterios de decisión

Pregúntate solo: **¿esta tarea es un cierre que merece una segunda opinión
externa?** Si no, no actives a nadie más. El núcleo cubre producto, diseño,
código, seguridad, QA, docs y entrega.

## Paso 2b -- Comprobación de autopilot

Antes de presentar las preguntas al usuario, comprueba si el modo autopilot está activo:

1. Lee `.claude/alfred-dev.local.md` y comprueba si todas las fases de autonomía están en `autonomo`.
2. Lee `.claude/alfred-dev-state.json` y comprueba si tiene `"autopilot": true`
   o, por compatibilidad con sesiones antiguas, `"modo": "autopilot"`.

**Si el comando es `quick` o `fix`:** salta al paso 4. No preguntes por Lucius ni abras menús de opcionales. El núcleo basta. Si el usuario pidió a Lucius por su nombre, actívalo; si no, `opcionales_activos.lucius = false`.

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

> **Equipo de núcleo** (siempre activos): Alfred, Product Owner, Selina si hay
> frontend, Arquitecto, Senior Dev, Security Officer, QA Engineer, Tech Writer,
> DevOps. El kanban lo escribe el runtime, no un agente aparte.

Después, usa `AskUserQuestion` con **un menú** del grupo `Auditoria` si hace
falta decidir sobre Lucius. La fuente canónica es `core/optional_agents.py`
(`build_optional_agent_group_menu`). No inventes grupos Técnicos ni Contenido.

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
      question: "¿Quieres activar Lucius como segunda opinión externa?",
      header: "Auditoria",
      multiSelect: false,
      options: [
        { label: "Seguir sin activar más", description: "Pasar al siguiente grupo" },
        { label: "Lucius", description: "<razón contextual o descripción breve>" }
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
