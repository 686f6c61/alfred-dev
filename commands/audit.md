---
description: "Auditoría completa del proyecto con 4 agentes en paralelo"
---

# /alfred-dev:audit

Eres Alfred, orquestador del equipo. El usuario quiere una auditoría completa del proyecto.

## Composición dinámica de equipo

Antes de lanzar la auditoría, localiza el fichero compartido de composición dentro del plugin Alfred Dev, NO dentro del proyecto auditado. Si no conoces la ruta exacta, búscala primero en la instalación del plugin (por ejemplo, bajo `~/.claude/plugins/cache/alfred-dev/**/commands/_composicion.md`) y léela desde ahí.

Después, sigue el protocolo de composición dinámica (pasos 1 a 4). Si por cualquier motivo no consigues localizar ese fichero, NO bloquees `/alfred-dev:audit` solo por esa búsqueda: continúa con el equipo de núcleo por defecto (qa-engineer, security-officer, architect, tech-writer) y deja constancia breve de la degradación.

## Preflight de SonarQube

Antes de lanzar ningún agente, verifica si SonarQube puede ejecutarse de verdad en esta sesión:

1. Ejecuta `docker --version` y `docker info`.
2. Interpreta el resultado ANTES de seguir:
   - **Docker instalado y daemon operativo**: SonarQube puede ejecutarse. Continúa con la auditoría y lanza al `security-officer` con la instrucción obligatoria de SonarQube.
   - **Docker no instalado**: NO intentes instalarlo por tu cuenta. Explica al usuario que SonarQube requiere instalar Docker y probablemente permisos de administrador. Usa `AskUserQuestion` antes de lanzar la auditoría con dos opciones:
     - `Instalar/preparar Docker (Recomendado)` -- Alfred podrá intentar instalar Docker y ejecutar SonarQube al principio de la auditoría.
     - `Seguir sin SonarQube` -- la auditoría continuará sin SonarQube y el informe lo documentará explícitamente.
   - **Docker instalado pero daemon apagado o inaccesible**: NO intentes arrancarlo por tu cuenta. Explica al usuario que SonarQube requiere iniciar Docker Desktop o el servicio del daemon. Usa `AskUserQuestion` antes de lanzar la auditoría con dos opciones:
     - `Arrancar Docker y ejecutar SonarQube (Recomendado)` -- Alfred podrá iniciar Docker y ejecutar SonarQube.
     - `Seguir sin SonarQube` -- la auditoría continuará sin SonarQube y el informe lo documentará explícitamente.
3. Conserva el resultado de este preflight como una decisión binaria en tu contexto:
   - `sonarqube_autorizado = true` si Docker ya funciona o el usuario ha autorizado instalarlo/arrancarlo.
   - `sonarqube_autorizado = false` si el usuario ha rechazado preparar Docker o si no se puede obtener el permiso necesario.
4. **IMPORTANTE:** esta pregunta es obligatoria incluso si el proyecto está en modo autopilot. Instalar Docker, arrancar el daemon o abrir Docker Desktop tiene impacto sobre el sistema y requiere confirmación explícita del usuario.

## Ejecución paralela

Lanza 4 agentes EN PARALELO usando la herramienta Task:

1. **qa-engineer**: cobertura de tests, tests rotos, code smells, deuda técnica de calidad.
2. **security-officer**: CVEs en dependencias, OWASP, compliance RGPD/NIS2/CRA, SBOM.
   - **Si `sonarqube_autorizado = true`**: SonarQube es el PRIMER paso del `security-officer`, ANTES de cualquier análisis manual. Cuando lances el agente, incluye en su prompt estas instrucciones textuales de forma explícita e imperativa:

     > **INSTRUCCIÓN OBLIGATORIA -- SonarQube:**
     > Tu PRIMER paso, antes de cualquier otra acción, es ejecutar el análisis de SonarQube. Esto NO es opcional. NO lo omitas. NO lo pospongas. NO decidas que "no es necesario". Sigue estos pasos exactos:
     > 1. Lee el skill COMPLETO con Read usando la ruta instalada del plugin Alfred Dev. Si `${CLAUDE_PLUGIN_ROOT}` no está resuelta en tu contexto, localiza primero `skills/calidad/sonarqube/SKILL.md` dentro de la instalación del plugin y léelo desde ahí.
     > 2. Ejecuta el preflight del skill al pie de la letra. Si requiere instalar Docker, arrancarlo o abrir Docker Desktop, usa exclusivamente la autorización ya obtenida en el preflight de `/alfred-dev:audit`.
     > 3. Ejecuta el análisis completo de SonarQube, integra los hallazgos en tu informe y limpia el contenedor temporal al terminar.
     > 4. Si SonarQube no puede ejecutarse tras el intento autorizado (por ejemplo, permisos insuficientes, daemon caído, puerto ocupado), documéntalo explícitamente en el informe. NUNCA lo omitas sin dejarlo por escrito.
   - **Si `sonarqube_autorizado = false`**: cuando lances el agente, indícale explícitamente que NO intente instalar Docker, NO intente arrancar el daemon y NO intente abrir Docker Desktop. Debe continuar con la auditoría manual y dejar por escrito en el informe que SonarQube se omitió por decisión explícita del usuario o por falta de permisos.
3. **architect**: deuda técnica arquitectónica, coherencia del diseño, acoplamiento excesivo
4. **tech-writer**: documentación desactualizada, lagunas, inconsistencias

Después de que los 4 terminen, recopila sus informes y presenta un **resumen ejecutivo** con:
- Hallazgos críticos (requieren acción inmediata)
- Hallazgos importantes (planificar resolución)
- Hallazgos menores (resolver cuando convenga)
- Plan de acción priorizado

No toca código, solo genera informes.
