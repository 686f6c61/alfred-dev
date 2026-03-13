---
name: code-review
description: "Usar para revisar código con foco en calidad, legibilidad y errores lógicos. También: revisar código, buscar errores, calidad del código, revisión de PR, pull request review."
---

# Revisión de código

## Resumen

Este skill ejecuta una revisión de código exhaustiva centrada en calidad, legibilidad, mantenibilidad y corrección lógica. La revisión no es un trámite burocrático sino una herramienta para mejorar el código y compartir conocimiento dentro del equipo.

Si las herramientas del toolkit `pr-review-toolkit` están disponibles, este skill las coordina para cubrir múltiples perspectivas: calidad general, fallos silenciosos y oportunidades de simplificación.

## Proceso

1. **Entender el contexto del cambio.** Antes de revisar línea por línea, entender el propósito del cambio. Leer la descripción del PR, el issue asociado o preguntar al usuario. Un cambio que parece incorrecto puede ser correcto si se entiende el contexto.

2. **Revisar la legibilidad.** El código se lee muchas más veces de las que se escribe:

   - Los nombres de variables, funciones y clases son descriptivos?
   - La estructura del código es clara sin necesidad de comentarios explicativos?
   - Las funciones son cortas y con responsabilidad única?
   - Los comentarios explican el "por qué", no el "qué"?

3. **Buscar errores lógicos.** Los bugs más peligrosos son los que no producen error:

   - Condiciones invertidas o incompletas.
   - Off-by-one errors en bucles e índices.
   - Variables no inicializadas o reutilizadas incorrectamente.
   - Race conditions en código asíncrono.
   - Falta de manejo de null/undefined/None.

4. **Verificar manejo de errores.** Los errores silenciosos son los peores:

   - Los catch/except vacíos se usan sin justificación?
   - Los errores se propagan correctamente o se tragan?
   - El usuario recibe información útil cuando algo falla?
   - Los errores se registran para depuración posterior?

5. **Evaluar la complejidad.** El código simple es más fácil de mantener y menos propenso a bugs:

   - Hay condicionales anidados profundamente que se podrían simplificar?
   - Hay duplicación que se podría abstraer?
   - Las abstracciones existentes son justificadas o son sobreingeniería?

6. **Verificar cobertura de edge cases.** Para cada función o flujo crítico:

   - Qué pasa con inputs vacíos?
   - Qué pasa con valores extremos (muy grandes, muy pequeños, negativos)?
   - Qué pasa con tipos inesperados?
   - Qué pasa bajo condiciones de error (red, disco, permisos)?

7. **Delegar en herramientas especializadas si están disponibles.** Si `pr-review-toolkit` está disponible:

   - `code-reviewer`: revisión general de calidad y adherencia a convenciones.
   - `silent-failure-hunter`: detección de fallos silenciosos y manejo inadecuado de errores.
   - `code-simplifier`: oportunidades de simplificación sin alterar funcionalidad.

   Umbral de confianza: solo reportar hallazgos con confianza >= 80%.

8. **Documentar hallazgos.** Cada hallazgo debe incluir: ubicación en el código, descripción del problema, impacto potencial y sugerencia de corrección.

## Criterios de éxito

- Se han revisado legibilidad, errores lógicos, manejo de errores, complejidad y edge cases.
- Los hallazgos incluyen ubicación, descripción, impacto y sugerencia de corrección.
- Solo se reportan hallazgos con confianza >= 80%.
- El tono de la revisión es constructivo y orientado a mejorar el código.
- Se distingue entre problemas que bloquean y sugerencias de mejora.

## Clarificación

Este skill guía la revisión de código. Para responder a los comentarios de una review recibida, usar `desarrollo/code-review-response`.

## Qué NO hacer

- No centrarse solo en el estilo (formateo, nombres, convenciones). Revisar la lógica primero; los problemas de estilo son los menos importantes.
- No aprobar sin haber entendido el contexto del cambio. Si no se entiende por qué se hizo un cambio, preguntar antes de opinar.
- No reportar hallazgos sin justificación. Cada comentario debe explicar el problema, el riesgo y la alternativa sugerida.
- No convertir la revisión en una lista de preferencias personales. Ceñirse a problemas objetivos de calidad, no a gustos.
