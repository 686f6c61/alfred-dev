---
name: user-stories
description: "Usar para descomponer una feature en historias de usuario verificables"
---

# Descomponer en historias de usuario

## Resumen

Este skill toma una funcionalidad o requisito de alto nivel y lo descompone en historias de usuario granulares, cada una con criterios de aceptacion, prioridad y estimacion relativa. El objetivo es producir unidades de trabajo que un desarrollador pueda implementar de forma independiente en un maximo de 8 horas.

La descomposicion sigue el principio INVEST: cada historia debe ser Independiente, Negociable, Valiosa, Estimable, Pequena y Testeable. Historias que no cumplan estos criterios se dividen hasta que los cumplan.

## Proceso

1. **Entender la funcionalidad completa.** Revisar el PRD si existe, o pedir al usuario que describa la feature. Identificar los actores implicados, los flujos principales y los flujos alternativos.

2. **Identificar los roles de usuario.** Listar todos los perfiles que interactuan con la funcionalidad: usuario final, administrador, sistema externo, etc. Cada rol puede generar historias distintas.

3. **Redactar historias con el formato estandar:**

   ```
   Como [rol],
   quiero [accion concreta],
   para [beneficio medible].
   ```

   Evitar historias vagas como "Como usuario, quiero que funcione bien". La accion debe ser especifica y el beneficio debe explicar el valor real.

4. **Anadir criterios de aceptacion a cada historia.** Minimo 2 criterios por historia: uno para el camino feliz y otro para un caso limite o error. Formato Given/When/Then preferible.

5. **Asignar prioridad con MoSCoW:**

   - **Must have:** sin esto la feature no tiene sentido.
   - **Should have:** importante pero no bloqueante para un primer lanzamiento.
   - **Could have:** mejora la experiencia pero se puede posponer.
   - **Won't have (this time):** descartado para esta iteracion, documentado para referencia futura.

6. **Estimar de forma relativa.** Usar tallas de camiseta (S, M, L) o puntos de historia. La referencia es que una historia no debe superar 8 horas de trabajo. Si se estima mayor, dividirla.

7. **Verificar independencia.** Repasar que cada historia pueda implementarse y desplegarse sin depender del resto. Si hay dependencias, documentarlas explicitamente y ordenar en consecuencia.

8. **Presentar al usuario para validacion.** Revisar la lista completa, ajustar prioridades y estimaciones segun feedback.

## Criterios de exito

- Cada historia sigue el formato "Como / quiero / para" con roles, acciones y beneficios concretos.
- Todas las historias tienen al menos 2 criterios de aceptacion.
- Ninguna historia supera las 8 horas estimadas de trabajo.
- Las prioridades MoSCoW estan asignadas y son coherentes con el objetivo de la feature.
- El usuario ha validado la descomposicion y las prioridades.
