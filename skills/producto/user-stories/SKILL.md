---
name: user-stories
description: "Descomponer una feature en historias de usuario verificables. Activar cuando el usuario quiera crear historias de usuario, usar el formato como usuario quiero, descomponer una feature o definir requisitos funcionales."
---

# Descomponer en historias de usuario

## Resumen

Este skill toma una funcionalidad o requisito de alto nivel y lo descompone en historias de usuario granulares, cada una con criterios de aceptación, prioridad y estimación relativa. El objetivo es producir unidades de trabajo que un desarrollador pueda implementar de forma independiente en un máximo de 8 horas.

La descomposición sigue el principio INVEST: cada historia debe ser Independiente, Negociable, Valiosa, Estimable, Pequeña y Testeable. Historias que no cumplan estos criterios se dividen hasta que los cumplan.

## Proceso

1. **Entender la funcionalidad completa.** Revisar el PRD si existe, o pedir al usuario que describa la feature. Identificar los actores implicados, los flujos principales y los flujos alternativos.

2. **Identificar los roles de usuario.** Listar todos los perfiles que interactúan con la funcionalidad: usuario final, administrador, sistema externo, etc. Cada rol puede generar historias distintas.

3. **Redactar historias con el formato estándar:**

   ```
   Como [rol],
   quiero [acción concreta],
   para [beneficio medible].
   ```

   Evitar historias vagas como "Como usuario, quiero que funcione bien". La acción debe ser específica y el beneficio debe explicar el valor real.

4. **Añadir criterios de aceptación a cada historia.** Mínimo 2 criterios por historia: uno para el camino feliz y otro para un caso límite o error. Formato Given/When/Then preferible.

5. **Asignar prioridad con MoSCoW:**

   - **Must have:** sin esto la feature no tiene sentido.
   - **Should have:** importante pero no bloqueante para un primer lanzamiento.
   - **Could have:** mejora la experiencia pero se puede posponer.
   - **Won't have (this time):** descartado para esta iteración, documentado para referencia futura.

6. **Estimar de forma relativa.** Usar tallas de camiseta (S, M, L) o puntos de historia. La referencia es que una historia no debe superar 8 horas de trabajo. Si se estima mayor, dividirla.

7. **Verificar independencia.** Repasar que cada historia pueda implementarse y desplegarse sin depender del resto. Si hay dependencias, documentarlas explícitamente y ordenar en consecuencia.

8. **Presentar al usuario para validación.** Revisar la lista completa, ajustar prioridades y estimaciones según feedback.

## Criterios de éxito

- Cada historia sigue el formato "Como / quiero / para" con roles, acciones y beneficios concretos.
- Todas las historias tienen al menos 2 criterios de aceptación.
- Ninguna historia supera las 8 horas estimadas de trabajo.
- Las prioridades MoSCoW están asignadas y son coherentes con el objetivo de la feature.
- El usuario ha validado la descomposición y las prioridades.

## Que NO hacer

- No escribir historias demasiado grandes. Si una historia no se puede implementar y verificar en un máximo de 8 horas, necesita dividirse en historias más pequeñas.
- No mezclar múltiples acciones en una sola historia. Cada historia debe representar una unidad de valor independiente que se pueda desplegar por separado.
- No omitir los criterios de aceptación. Una historia sin criterios de aceptación no es verificable y genera ambigüedad entre producto y desarrollo.
