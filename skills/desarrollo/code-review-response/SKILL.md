---
name: code-review-response
description: "Usar al recibir feedback de code review para responder técnicamente. Activar cuando el usuario quiera responder a comentarios de PR, gestionar feedback de code review, resolver comentarios de un revisor, o cuando el revisor pide cambios en el código."
---

# Responder a code review

## Resumen

Este skill gestiona la respuesta técnica a comentarios de code review. El objetivo no es aceptar todo el feedback ciegamente ni rechazarlo por ego, sino evaluarlo técnicamente y responder con evidencia. Un buen proceso de code review mejora el código; un mal proceso genera fricción y resentimiento.

La clave es tratar cada comentario como una oportunidad de mejorar el código o de enriquecer la discusión técnica del equipo.

## Proceso

1. **Leer todos los comentarios antes de responder a ninguno.** Obtener una visión global del feedback. A veces un comentario individual cobra sentido diferente cuando se ve junto con los demás. Agrupar mentalmente por temática: estilo, lógica, arquitectura, rendimiento.

2. **Clasificar cada comentario:**

   - **Correcto y accionable:** el revisor ha detectado un problema real. Implementar el cambio.
   - **Correcto pero discutible:** el revisor tiene razón en el diagnóstico pero la solución propuesta no es la mejor. Contraargumentar con alternativa.
   - **Cuestión de estilo:** no hay bien o mal objetivo, es preferencia. Si el proyecto tiene guía de estilo, seguirla. Si no, aceptar a menos que haya buena razón para no hacerlo.
   - **Incorrecto:** el revisor ha malinterpretado el código o el contexto. Explicar con datos, no con autoridad.
   - **Fuera de alcance:** el comentario es válido pero no pertenece a este PR. Crear un issue para abordarlo después.

3. **Verificar si el comentario es correcto.** Para cada comentario técnico:

   - Leer el código señalado con ojos frescos.
   - Si el comentario reporta un bug, intentar reproducirlo.
   - Si sugiere un cambio de rendimiento, medir antes de aceptar.
   - Si propone un refactoring, verificar que los tests cubren el área afectada.

4. **Responder con evidencia, no con opiniones.** Si se acepta el cambio, implementarlo y responder con el commit que lo resuelve. Si se rechaza, explicar por qué con datos: métricas de rendimiento, referencia a una decisión de diseño documentada, test que demuestra que el comportamiento es correcto.

5. **Implementar los cambios aceptados.** Cada cambio derivado de code review se hace en un commit separado y descriptivo que referencie el comentario original cuando sea posible.

6. **No tomárselo como algo personal.** El code review es sobre el código, no sobre la persona. Si un comentario resulta brusco, responder al contenido técnico e ignorar el tono.

## Relación con otros skills

Este skill guía la respuesta técnica a comentarios de review. Para hacer la revisión de código en sí (como revisor), usar `calidad/code-review`.

## Qué NO hacer

- **No aceptar todas las sugerencias sin evaluar su mérito técnico.** Aceptar ciegamente genera código inconsistente y erosiona la confianza en el proceso de review. Cada cambio debe tener sentido técnico.
- **No responder de forma defensiva.** El code review es sobre el código, no sobre la persona. Una respuesta defensiva corta la discusión técnica y empeora el resultado.
- **No ignorar comentarios sin explicar por qué.** Si se decide no implementar un cambio sugerido, documentar la razón con evidencia técnica. Un comentario sin respuesta es peor que un rechazo argumentado.

## Criterios de éxito

- Todos los comentarios del code review tienen una respuesta (aceptación, rechazo argumentado o discusión).
- Los cambios aceptados están implementados y commiteados.
- Los rechazos están argumentados con evidencia técnica, no con opiniones.
- Los comentarios fuera de alcance se han registrado como issues para seguimiento.
- El tono de las respuestas es profesional y constructivo.
