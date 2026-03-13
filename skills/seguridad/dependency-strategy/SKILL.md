---
name: dependency-strategy
description: "Estrategia integral de gestion de dependencias: inventario, evaluacion de riesgo, politica de actualizaciones y documentacion. Usar para auditar el estado global de las dependencias del proyecto."
---

# Estrategia de dependencias

El usuario quiere evaluar, auditar o planificar la gestion de dependencias del proyecto. Este skill proporciona un marco estructurado para tomar decisiones informadas sobre que dependencias incorporar, cuales actualizar y cuales retirar.

> **Nota:** Este skill define la estrategia global de dependencias. Para auditar vulnerabilidades puntuales, usar `dependency-audit`. Para aplicar actualizaciones concretas, usar `dependency-update`.

## Resumen

Las dependencias son una de las mayores fuentes de riesgo en un proyecto de software: vulnerabilidades de seguridad, licencias incompatibles, abandonware y bloat innecesario. En entornos corporativos, cada dependencia es un contrato implicito de mantenimiento. Este skill ayuda a gestionar ese riesgo de forma sistematica.

## Proceso

### Fase 1: Inventario (security-officer)

1. Listar todas las dependencias directas y transitivas del proyecto.
2. Para cada dependencia, recopilar:
   - Version actual vs ultima version disponible.
   - Licencia (MIT, Apache-2.0, GPL, etc.).
   - Ultimo commit/release (actividad del mantenedor).
   - Vulnerabilidades conocidas (CVEs abiertos).
   - Tamano del paquete (impacto en bundle/build).

**Herramientas:** `npm audit`, `pip audit`, `cargo audit`, `gh api advisories` segun el ecosistema.

**Artefacto:** tabla de inventario de dependencias.

### Fase 2: Evaluacion de riesgo

Clasificar cada dependencia en una matriz de riesgo:

| Criterio | Bajo | Medio | Alto |
|----------|------|-------|------|
| CVEs abiertos | 0 | 1-2 (no criticos) | Cualquier critico |
| Licencia | MIT, Apache-2.0, ISC | BSD, MPL | GPL, AGPL, sin licencia |
| Actividad | Release en ultimos 6 meses | Release en ultimo ano | Sin releases en >1 ano |
| Alternativas | Sin alternativa viable | Alternativas parciales | Multiples alternativas mejores |

### Fase 3: Plan de accion

Para cada dependencia de riesgo medio o alto, definir una accion:

| Accion | Cuando aplicar |
|--------|----------------|
| **Actualizar** | Version desactualizada con parches disponibles |
| **Reemplazar** | Dependencia abandonada con alternativas mejores |
| **Eliminar** | Dependencia innecesaria (funcionalidad duplicada o infrautilizada) |
| **Aceptar riesgo** | Sin alternativa, impacto controlado, mitigacion aplicada |
| **Fijar version** | Dependencia estable que no conviene actualizar automaticamente |

### Fase 4: Politica de actualizaciones

Establecer una politica de actualizaciones para el proyecto:

1. **Patch versions:** actualizar automaticamente (Dependabot, Renovate).
2. **Minor versions:** revisar changelog, actualizar en sprint de mantenimiento.
3. **Major versions:** evaluar breaking changes, planificar migracion.
4. **Dependencias de seguridad:** actualizar inmediatamente, sin esperar a sprint.

### Fase 5: Documentacion

Registrar las decisiones de dependencias en la memoria del proyecto usando `memory_log_decision`:

- Dependencias rechazadas y motivo.
- Dependencias aceptadas con riesgo y mitigacion.
- Politica de actualizaciones acordada.

**Artefacto:** documento de estrategia de dependencias + decisiones registradas en memoria.

## Criterios de exito

- Existe un inventario completo de dependencias directas y transitivas con su estado actual.
- Cada dependencia tiene una clasificacion de riesgo basada en criterios objetivos.
- Las dependencias de riesgo medio y alto tienen una accion definida (actualizar, reemplazar, eliminar o aceptar riesgo con justificacion).
- La politica de actualizaciones esta documentada y diferenciada por tipo de version (patch, minor, major).
- Las decisiones de dependencias quedan registradas en la memoria del proyecto.

## Que NO hacer

- **No definir una politica de actualizaciones sin evaluar el riesgo de cada dependencia.** Una politica generica de "actualizar todo" puede introducir breaking changes inesperados, mientras que "no actualizar nada" acumula deuda tecnica y vulnerabilidades. La politica debe estar informada por la evaluacion de riesgo individual.
- **No tratar todas las dependencias con la misma prioridad.** Una dependencia de seguridad con CVEs criticos no puede esperar al proximo sprint de mantenimiento, del mismo modo que una dependencia estable sin cambios no necesita atencion urgente. La priorizacion debe reflejar el riesgo real de cada caso.
