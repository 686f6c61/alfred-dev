---
name: test-plan
description: "Usar para generar un plan de testing priorizado por riesgo"
---

# Generar plan de testing

## Resumen

Este skill produce un plan de testing estructurado y priorizado por riesgo. No se trata de probar todo con la misma intensidad, sino de concentrar el esfuerzo donde mas impacto tiene: las areas criticas del sistema que, si fallan, causan mayor dano al usuario o al negocio.

El plan cubre desde tests unitarios hasta tests end-to-end, pasando por integracion, edge cases y escenarios negativos. El resultado es un documento accionable que guia el esfuerzo de testing.

## Proceso

1. **Identificar el alcance.** Definir que se va a probar: una feature nueva, un modulo refactorizado, el sistema completo, o un area especifica. El alcance determina la profundidad del plan.

2. **Analizar el riesgo de cada area.** Para cada componente o funcionalidad, evaluar:

   - **Impacto del fallo:** que pasa si esta parte falla (perdida de datos, caida del servicio, mala experiencia de usuario, etc.).
   - **Probabilidad de fallo:** complejidad del codigo, frecuencia de cambios, historial de bugs.
   - **Visibilidad:** si el fallo es visible para el usuario o silencioso.

   Clasificar cada area como critica, alta, media o baja prioridad de testing.

3. **Definir las categorias de tests:**

   - **Unitarios:** funciones individuales aisladas de sus dependencias. Rapidos, abundantes, cubren logica de negocio y casos limite.
   - **Integracion:** interaccion entre modulos o con servicios externos (base de datos, APIs). Verifican que las piezas encajan.
   - **End-to-end (e2e):** flujos completos desde la perspectiva del usuario. Pocos pero criticos. Cubren los happy paths mas importantes.
   - **Edge cases:** valores limite, inputs vacios, unicode, numeros negativos, listas gigantes.
   - **Escenarios negativos:** que pasa cuando las cosas van mal (red caida, base de datos llena, permisos insuficientes, timeout).

4. **Asignar prioridad a cada test:**

   | Prioridad | Criterio | Ejemplo |
   |-----------|----------|---------|
   | Critica | Fallo = perdida de datos o dinero | Test de transacciones, test de backup |
   | Alta | Fallo = servicio no disponible | Test de autenticacion, test de endpoints principales |
   | Media | Fallo = mala experiencia de usuario | Test de validacion de formularios, test de paginacion |
   | Baja | Fallo = molestia menor | Test de formato de fecha, test de ordenacion |

5. **Estimar el esfuerzo.** Para cada grupo de tests, estimar el tiempo necesario para escribirlos. Esto ayuda a planificar sprints y a negociar alcance si hay restricciones de tiempo.

6. **Documentar el plan.** Utilizar `templates/test-plan.md` si existe. El documento debe ser una referencia viva que se actualiza conforme el proyecto evoluciona.

## Criterios de exito

- Cada area del sistema tiene un nivel de riesgo asignado.
- Los tests estan categorizados (unitario, integracion, e2e, edge case, negativo).
- Las prioridades reflejan el impacto real del fallo, no la facilidad de escribir el test.
- El esfuerzo esta estimado para permitir planificacion.
- El plan cubre escenarios positivos, negativos y edge cases para las areas criticas.
