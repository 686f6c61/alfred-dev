---
name: code-review-response
description: "Usar al recibir feedback de code review para responder tecnicamente"
---

# Responder a code review

## Resumen

Este skill gestiona la respuesta tecnica a comentarios de code review. El objetivo no es aceptar todo el feedback ciegamente ni rechazarlo por ego, sino evaluarlo tecnicamente y responder con evidencia. Un buen proceso de code review mejora el codigo; un mal proceso genera friccion y resentimiento.

La clave es tratar cada comentario como una oportunidad de mejorar el codigo o de enriquecer la discusion tecnica del equipo.

## Proceso

1. **Leer todos los comentarios antes de responder a ninguno.** Obtener una vision global del feedback. A veces un comentario individual cobra sentido diferente cuando se ve junto con los demas. Agrupar mentalmente por tematica: estilo, logica, arquitectura, rendimiento.

2. **Clasificar cada comentario:**

   - **Correcto y accionable:** el revisor ha detectado un problema real. Implementar el cambio.
   - **Correcto pero discutible:** el revisor tiene razon en el diagnostico pero la solucion propuesta no es la mejor. Contraargumentar con alternativa.
   - **Cuestion de estilo:** no hay bien o mal objetivo, es preferencia. Si el proyecto tiene guia de estilo, seguirla. Si no, aceptar a menos que haya buena razon para no hacerlo.
   - **Incorrecto:** el revisor ha malinterpretado el codigo o el contexto. Explicar con datos, no con autoridad.
   - **Fuera de alcance:** el comentario es valido pero no pertenece a este PR. Crear un issue para abordarlo despues.

3. **Verificar si el comentario es correcto.** Para cada comentario tecnico:

   - Leer el codigo senalado con ojos frescos.
   - Si el comentario reporta un bug, intentar reproducirlo.
   - Si sugiere un cambio de rendimiento, medir antes de aceptar.
   - Si propone un refactoring, verificar que los tests cubren el area afectada.

4. **Responder con evidencia, no con opiniones.** Si se acepta el cambio, implementarlo y responder con el commit que lo resuelve. Si se rechaza, explicar por que con datos: metricas de rendimiento, referencia a una decision de diseno documentada, test que demuestra que el comportamiento es correcto.

5. **Implementar los cambios aceptados.** Cada cambio derivado de code review se hace en un commit separado y descriptivo que referencie el comentario original cuando sea posible.

6. **No tomarselo como algo personal.** El code review es sobre el codigo, no sobre la persona. Si un comentario resulta brusco, responder al contenido tecnico e ignorar el tono.

## Criterios de exito

- Todos los comentarios del code review tienen una respuesta (aceptacion, rechazo argumentado o discusion).
- Los cambios aceptados estan implementados y commiteados.
- Los rechazos estan argumentados con evidencia tecnica, no con opiniones.
- Los comentarios fuera de alcance se han registrado como issues para seguimiento.
- El tono de las respuestas es profesional y constructivo.
