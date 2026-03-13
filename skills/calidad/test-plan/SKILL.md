---
name: test-plan
description: "Usar para generar un plan de testing priorizado por riesgo. También: plan de testing, qué probar, priorizar tests por riesgo, estrategia de testing, cobertura de tests."
---

# Generar plan de testing

## Resumen

Este skill produce un plan de testing estructurado y priorizado por riesgo. No se trata de probar todo con la misma intensidad, sino de concentrar el esfuerzo donde más impacto tiene: las áreas críticas del sistema que, si fallan, causan mayor daño al usuario o al negocio.

El plan cubre desde tests unitarios hasta tests end-to-end, pasando por integración, edge cases y escenarios negativos. El resultado es un documento accionable que guía el esfuerzo de testing.

## Proceso

1. **Identificar el alcance.** Definir qué se va a probar: una feature nueva, un módulo refactorizado, el sistema completo, o un área específica. El alcance determina la profundidad del plan.

2. **Analizar el riesgo de cada área.** Para cada componente o funcionalidad, evaluar:

   - **Impacto del fallo:** qué pasa si esta parte falla (pérdida de datos, caída del servicio, mala experiencia de usuario, etc.).
   - **Probabilidad de fallo:** complejidad del código, frecuencia de cambios, historial de bugs.
   - **Visibilidad:** si el fallo es visible para el usuario o silencioso.

   Clasificar cada área como crítica, alta, media o baja prioridad de testing.

3. **Definir las categorías de tests:**

   - **Unitarios:** funciones individuales aisladas de sus dependencias. Rápidos, abundantes, cubren lógica de negocio y casos límite.
   - **Integración:** interacción entre módulos o con servicios externos (base de datos, APIs). Verifican que las piezas encajan.
   - **End-to-end (e2e):** flujos completos desde la perspectiva del usuario. Pocos pero críticos. Cubren los happy paths más importantes.
   - **Edge cases:** valores límite, inputs vacíos, unicode, números negativos, listas gigantes.
   - **Escenarios negativos:** qué pasa cuando las cosas van mal (red caída, base de datos llena, permisos insuficientes, timeout).

4. **Asignar prioridad a cada test:**

   | Prioridad | Criterio | Ejemplo |
   |-----------|----------|---------|
   | Crítica | Fallo = pérdida de datos o dinero | Test de transacciones, test de backup |
   | Alta | Fallo = servicio no disponible | Test de autenticación, test de endpoints principales |
   | Media | Fallo = mala experiencia de usuario | Test de validación de formularios, test de paginación |
   | Baja | Fallo = molestia menor | Test de formato de fecha, test de ordenación |

5. **Estimar el esfuerzo.** Para cada grupo de tests, estimar el tiempo necesario para escribirlos. Esto ayuda a planificar sprints y a negociar alcance si hay restricciones de tiempo.

6. **Documentar el plan.** Utilizar `templates/test-plan.md` si existe. El documento debe ser una referencia viva que se actualiza conforme el proyecto evoluciona.

## Criterios de éxito

- Cada área del sistema tiene un nivel de riesgo asignado.
- Los tests están categorizados (unitario, integración, e2e, edge case, negativo).
- Las prioridades reflejan el impacto real del fallo, no la facilidad de escribir el test.
- El esfuerzo está estimado para permitir planificación.
- El plan cubre escenarios positivos, negativos y edge cases para las áreas críticas.
- Las decisiones de estrategia de testing se han registrado en la memoria del proyecto.

## Paso de memoria

Registrar las decisiones de estrategia de testing en la memoria del proyecto con `memory_log_decision`. Esto incluye qué áreas se han priorizado, qué se ha descartado y por qué, para que el plan se mantenga coherente entre sesiones.

## Referencia al stack

Consultar el stack detectado en la configuración de Alfred para seleccionar automáticamente el framework de testing adecuado (Jest, Vitest, pytest, etc.) y adaptar las recomendaciones al ecosistema del proyecto.

## Qué NO hacer

- No priorizar tests por facilidad de escritura. Priorizar por riesgo e impacto del fallo, que es el criterio que realmente protege al usuario.
- No planificar tests E2E para todo. Los tests E2E son lentos y frágiles; reservarlos para flujos críticos y cubrir el resto con tests unitarios y de integración.
- No generar un plan de testing sin conocer el código. El plan debe basarse en la arquitectura real, no en una plantilla genérica.
- No ignorar los tests negativos y de edge cases. Los happy paths se prueban solos; los bugs viven en los caminos inesperados.
