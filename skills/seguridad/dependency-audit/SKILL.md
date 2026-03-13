---
name: dependency-audit
description: "Usar para auditar dependencias contra CVEs, versiones desactualizadas y licencias. También: auditar paquetes, buscar CVEs, vulnerabilidades en dependencias, licencias incompatibles, paquetes abandonados, npm audit, pip audit."
---

# Auditoría de dependencias

## Resumen

Este skill ejecuta una auditoría completa de las dependencias del proyecto, verificando vulnerabilidades conocidas (CVEs), versiones desactualizadas, licencias incompatibles y paquetes abandonados. Las dependencias son el vector de ataque más común en la cadena de suministro de software; este análisis es obligatorio antes de cualquier release y recomendable de forma periódica.

HARD-GATE: si se detecta una vulnerabilidad crítica o alta sin parche disponible, el proceso se bloquea hasta que se resuelva o se documente una mitigación explícitamente aceptada por el usuario.

## Proceso

1. **Detectar el ecosistema del proyecto.** Identificar el gestor de paquetes (npm, pip, cargo, go modules, composer, etc.) y ejecutar la herramienta de auditoría correspondiente:

   - **Node.js:** `npm audit` o `yarn audit` o `pnpm audit`.
   - **Python:** `pip-audit` o `safety check`.
   - **Rust:** `cargo audit`.
   - **Go:** `govulncheck`.
   - **PHP:** `composer audit`.

2. **Analizar vulnerabilidades por severidad:**

   | Severidad | Acción |
   |-----------|--------|
   | Crítica | HARD-GATE: bloquear. Actualizar o eliminar la dependencia inmediatamente. |
   | Alta | HARD-GATE: bloquear. Actualizar o documentar mitigación aceptada por el usuario. |
   | Media | Planificar actualización. Crear issue si no se puede resolver ahora. |
   | Baja | Documentar. Resolver cuando sea conveniente. |

3. **Verificar versiones.** Para cada dependencia, comprobar:

   - Versión instalada vs última versión estable.
   - Si hay breaking changes entre la versión actual y la última (consultar changelog).
   - Si la dependencia sigue un esquema de versionado semántico.
   - Antigüedad de la versión instalada (más de 1 año sin actualizar es una señal de alerta).

4. **Verificar licencias.** Listar las licencias de todas las dependencias (directas y transitivas) y verificar compatibilidad:

   - MIT, Apache 2.0, BSD: generalmente compatibles con cualquier proyecto.
   - GPL, AGPL: problemáticas para proyectos propietarios.
   - Licencias no estándar o sin licencia: riesgo legal, evitar.

5. **Identificar paquetes abandonados.** Criterios de abandono:

   - Último commit hace más de 2 años.
   - Issues críticas abiertas sin respuesta durante meses.
   - Mantenedor único que ha dejado de responder.
   - Repositorio archivado.

6. **Generar informe.** Documentar los hallazgos en formato tabular con acciones recomendadas para cada problema encontrado.

## Criterios de éxito

- Se ha ejecutado la herramienta de auditoría del ecosistema correspondiente.
- No hay vulnerabilidades críticas o altas sin resolver o sin mitigación documentada.
- Las licencias son compatibles con el proyecto.
- Los paquetes abandonados están identificados con alternativas propuestas.
- El informe incluye acciones concretas para cada hallazgo.
- Los hallazgos críticos se han registrado en la memoria del proyecto.

## Paso de memoria

Registrar los hallazgos críticos en la memoria del proyecto con `memory_log_decision`. Esto permite hacer seguimiento de vulnerabilidades conocidas entre sesiones y verificar que se han resuelto.

## Referencia al stack

Consultar el stack detectado en la configuración de Alfred para seleccionar automáticamente la herramienta de auditoría adecuada (npm audit, pip-audit, cargo audit, etc.), evitando que el usuario tenga que especificarlo manualmente.

## Clarificación

Este skill se centra en la detección puntual de vulnerabilidades y licencias. Para una estrategia de gestión continua de dependencias, usar `dependency-strategy`. Para aplicar actualizaciones concretas, usar `dependency-update`.
