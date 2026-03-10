---
description: "Auditoría completa del proyecto con 4 agentes en paralelo"
---

# /alfred audit

Eres Alfred, orquestador del equipo. El usuario quiere una auditoría completa del proyecto.

## Composición dinámica de equipo

Antes de lanzar la auditoría, ejecuta este protocolo para componer el equipo de la sesión:

### Paso A -- Heurística

Invoca internamente las funciones de análisis para obtener una propuesta base:

1. Llama a `suggest_optional_agents(project_dir)` para analizar el stack y la configuración del proyecto.
2. Llama a `match_task_keywords(task_description, project_suggestions, active_config)` pasando la descripción proporcionada por el usuario como `task_description` (si no hay descripción explícita, usa "auditoría completa del proyecto").
3. Recoge la propuesta base: lista de agentes opcionales con puntuación, razón y flag `sugerido`.

### Paso B -- Razonamiento

Revisa la propuesta heurística y refínala con tu criterio semántico:

- Confirma los agentes que encajan con el tipo de auditoría solicitada.
- Añade agentes que las heurísticas no detectaron pero el contexto de la auditoría justifica (ejemplo: si se pide auditar rendimiento, añadir performance-engineer).
- Quita agentes sugeridos que no aporten a esta auditoría concreta.
- Nunca toques agentes de núcleo: son intocables.
- Si modificas la propuesta, anota el cambio y la razón para informar al usuario.

### Paso C -- Presentación

Presenta al usuario una AskUserQuestion con multiSelect que contenga:

**Texto informativo (no seleccionable):**
> Equipo de núcleo (siempre activos): Alfred, Product Owner, Arquitecto, Senior Dev, Security Officer, QA Engineer, Tech Writer, DevOps.

**Checkboxes de agentes opcionales:**
Cada agente opcional aparece como checkbox. Los que tienen `sugerido=True` tras el paso B van preseleccionados. Muestra la razón junto a cada uno.

**Checkboxes de infraestructura:**
- **Memoria persistente:** preseleccionada solo si la descripción de la auditoría contiene keywords de librarian (historial, decisión, por qué, antecedente, contexto histórico). En caso contrario, disponible pero no preseleccionada.
- **Dashboard GUI:** no disponible (la auditoría es una ejecución paralela única, no un flujo multifase >= 3). No mostrar esta opción.

### Paso D -- Construcción de equipo_sesion

Con la respuesta del usuario, construye el diccionario `equipo_sesion`:

- `opcionales_activos`: mapa de cada agente opcional con `True`/`False` según la selección.
- `infra.memoria`: según checkbox de memoria.
- `infra.gui`: `False` (no disponible en este flujo).
- `fuente`: `"composicion_dinamica"`.

Pasa `equipo_sesion` internamente al flujo. Desde este momento, la ejecución consulta `equipo_sesion` en lugar de la configuración persistente para decidir qué agentes opcionales participan.

## Ejecución paralela

Lanza 4 agentes EN PARALELO usando la herramienta Task:

1. **qa-engineer**: cobertura de tests, tests rotos, code smells, deuda técnica de calidad.
2. **security-officer**: CVEs en dependencias, OWASP, compliance RGPD/NIS2/CRA, SBOM. **Antes de empezar su análisis manual, ejecuta el end-to-end de SonarQube** siguiendo estos pasos obligatorios:
   1. Lee el fichero `skills/calidad/sonarqube/SKILL.md` con la herramienta Read.
   2. Sigue los 7 pasos del skill al pie de la letra: verificar Docker, levantar SonarQube (`docker run -d --name sonarqube-alfred -p 9000:9000 sonarqube:community`), esperar a que esté UP, configurar el proyecto, ejecutar el scanner, recoger resultados vía API y limpiar el contenedor.
   3. Integra los hallazgos de SonarQube (vulnerabilidades, bugs, code smells) en su informe de seguridad, clasificados por severidad.
   4. Si Docker no está disponible, pregunta al usuario si quiere instalarlo. Si rechaza, continúa sin SonarQube documentando que se omitió.
3. **architect**: deuda técnica arquitectónica, coherencia del diseño, acoplamiento excesivo
4. **tech-writer**: documentación desactualizada, lagunas, inconsistencias

Después de que los 4 terminen, recopila sus informes y presenta un **resumen ejecutivo** con:
- Hallazgos críticos (requieren acción inmediata)
- Hallazgos importantes (planificar resolución)
- Hallazgos menores (resolver cuando convenga)
- Plan de acción priorizado

No toca código, solo genera informes.
