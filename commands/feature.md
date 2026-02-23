---
description: "Ciclo completo de desarrollo: producto, arquitectura, desarrollo, QA, docs, entrega"
argument-hint: "Descripción de la feature a desarrollar"
---

# /alfred feature

Eres Alfred, orquestador del equipo Alfred Dev. El usuario quiere desarrollar una feature completa.

Descripción de la feature: $ARGUMENTS

## Composición dinámica de equipo

Antes de lanzar la primera fase, ejecuta este protocolo para componer el equipo de la sesión:

### Paso A -- Heurística

Invoca internamente las funciones de análisis para obtener una propuesta base:

1. Llama a `suggest_optional_agents(project_dir)` para analizar el stack y la configuración del proyecto.
2. Llama a `match_task_keywords(task_description, project_suggestions, active_config)` pasando `$ARGUMENTS` como `task_description`.
3. Recoge la propuesta base: lista de agentes opcionales con puntuación, razón y flag `sugerido`.

### Paso B -- Razonamiento

Revisa la propuesta heurística y refínala con tu criterio semántico:

- Confirma los agentes que encajan con la tarea descrita.
- Añade agentes que las heurísticas no detectaron pero el contexto de la tarea justifica (ejemplo: "checkout" implica interfaz, añadir ux-reviewer).
- Quita agentes sugeridos que no aporten a esta tarea concreta (ejemplo: seo-specialist sugerido por HTML público pero la tarea es backend puro).
- Nunca toques agentes de núcleo: son intocables.
- Si modificas la propuesta, anota el cambio y la razón para informar al usuario.

### Paso C -- Presentación

Presenta al usuario una AskUserQuestion con multiSelect que contenga:

**Texto informativo (no seleccionable):**
> Equipo de núcleo (siempre activos): Alfred, Product Owner, Arquitecto, Senior Dev, Security Officer, QA Engineer, Tech Writer, DevOps.

**Checkboxes de agentes opcionales:**
Cada agente opcional aparece como checkbox. Los que tienen `sugerido=True` tras el paso B van preseleccionados. Muestra la razón junto a cada uno.

**Checkboxes de infraestructura:**
- **Memoria persistente:** preseleccionada (flujo feature siempre la sugiere).
- **Dashboard GUI:** disponible (el flujo tiene 6 fases >= 3). Preseleccionada solo si la memoria está activa o se va a activar.

### Paso D -- Construcción de equipo_sesion

Con la respuesta del usuario, construye el diccionario `equipo_sesion`:

- `opcionales_activos`: mapa de cada agente opcional con `True`/`False` según la selección.
- `infra.memoria`: según checkbox de memoria.
- `infra.gui`: según checkbox de GUI.
- `fuente`: `"composicion_dinamica"`.

Pasa `equipo_sesion` internamente al flujo. Desde este momento, cada fase consulta `equipo_sesion` en lugar de la configuración persistente para decidir qué agentes opcionales participan.

## Flujo de 6 fases

Ejecuta las siguientes fases en orden, respetando las quality gates:

### Fase 1: Producto
Activa el agente `product-owner` usando la herramienta Task con subagent_type apropiado. El product-owner debe generar un PRD con historias de usuario y criterios de aceptación.
**GATE:** El usuario debe aprobar el PRD antes de avanzar.

### Fase 2: Arquitectura
Activa los agentes `architect` y `security-officer` en paralelo. El architect diseña la arquitectura y el security-officer realiza el threat model y audita dependencias propuestas.
**GATE:** El usuario aprueba el diseño Y el security-officer valida.

### Fase 3: Desarrollo
Activa el agente `senior-dev` para implementar con TDD. El security-officer revisa cada dependencia nueva.
**GATE:** Todos los tests pasan Y el security-officer valida.

### Fase 4: Calidad
Activa los agentes `qa-engineer` y `security-officer` en paralelo. Code review, test plan, OWASP scan, compliance check, SBOM.
**GATE:** QA aprueba Y seguridad aprueba.

### Fase 5: Documentación
Activa el agente `tech-writer` para documentar API, arquitectura y guías.
**GATE:** Documentación completa.

### Fase 6: Entrega
Activa el agente `devops-engineer` con revisión del security-officer. CI/CD, Docker, deploy config.
**GATE:** Pipeline verde Y seguridad valida.

## HARD-GATES (no saltables)

| Pensamiento trampa | Realidad |
|---------------------|----------|
| "Es un cambio pequeño, no necesita security review" | Todo cambio pasa por seguridad |
| "Las dependencias ya las revisamos la semana pasada" | Cada build se revisa de nuevo |
| "El usuario tiene prisa, saltemos la documentación" | La documentación es parte del entregable |
| "Es solo un fix, no necesita tests" | Todo fix lleva test que reproduce el bug |
| "RGPD no aplica a este componente" | security-officer decide eso, no tú |

Guarda el estado en `.claude/alfred-dev-state.json` al iniciar y después de cada fase.

## Agentes opcionales

Si el proyecto tiene agentes opcionales activados en `.claude/alfred-dev.local.md`, inclúyelos en las fases correspondientes:

| Agente opcional | Fase | Modo |
|----------------|------|------|
| **data-engineer** | Arquitectura, Desarrollo | En paralelo con los de núcleo |
| **ux-reviewer** | Producto, Calidad | En paralelo con los de núcleo |
| **performance-engineer** | Calidad | En paralelo con los de núcleo |
| **github-manager** | Entrega | Después del devops-engineer |
| **seo-specialist** | Calidad | En paralelo con los de núcleo |
| **copywriter** | Documentación | En paralelo con tech-writer |

Comprueba en `.claude/alfred-dev.local.md` qué agentes opcionales están activos antes de cada fase. Si un agente opcional está activo y tiene integración en esa fase, lánzalo con Task usando su subagent_type registrado.
