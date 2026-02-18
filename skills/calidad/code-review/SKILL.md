---
name: code-review
description: "Usar para revisar codigo con foco en calidad, legibilidad y errores logicos"
---

# Revision de codigo

## Resumen

Este skill ejecuta una revision de codigo exhaustiva centrada en calidad, legibilidad, mantenibilidad y correccion logica. La revision no es un tramite burocratico sino una herramienta para mejorar el codigo y compartir conocimiento dentro del equipo.

Si las herramientas del toolkit `pr-review-toolkit` estan disponibles, este skill las coordina para cubrir multiples perspectivas: calidad general, fallos silenciosos y oportunidades de simplificacion.

## Proceso

1. **Entender el contexto del cambio.** Antes de revisar linea por linea, entender el proposito del cambio. Leer la descripcion del PR, el issue asociado o preguntar al usuario. Un cambio que parece incorrecto puede ser correcto si se entiende el contexto.

2. **Revisar la legibilidad.** El codigo se lee muchas mas veces de las que se escribe:

   - Los nombres de variables, funciones y clases son descriptivos?
   - La estructura del codigo es clara sin necesidad de comentarios explicativos?
   - Las funciones son cortas y con responsabilidad unica?
   - Los comentarios explican el "por que", no el "que"?

3. **Buscar errores logicos.** Los bugs mas peligrosos son los que no producen error:

   - Condiciones invertidas o incompletas.
   - Off-by-one errors en bucles e indices.
   - Variables no inicializadas o reutilizadas incorrectamente.
   - Race conditions en codigo asincrono.
   - Falta de manejo de null/undefined/None.

4. **Verificar manejo de errores.** Los errores silenciosos son los peores:

   - Los catch/except vacios se usan sin justificacion?
   - Los errores se propagan correctamente o se tragan?
   - El usuario recibe informacion util cuando algo falla?
   - Los errores se registran para depuracion posterior?

5. **Evaluar la complejidad.** El codigo simple es mas facil de mantener y menos propenso a bugs:

   - Hay condicionales anidados profundamente que se podrian simplificar?
   - Hay duplicacion que se podria abstraer?
   - Las abstracciones existentes son justificadas o son sobreingenieria?

6. **Verificar cobertura de edge cases.** Para cada funcion o flujo critico:

   - Que pasa con inputs vacios?
   - Que pasa con valores extremos (muy grandes, muy pequenos, negativos)?
   - Que pasa con tipos inesperados?
   - Que pasa bajo condiciones de error (red, disco, permisos)?

7. **Delegar en herramientas especializadas si estan disponibles.** Si `pr-review-toolkit` esta disponible:

   - `code-reviewer`: revision general de calidad y adherencia a convenciones.
   - `silent-failure-hunter`: deteccion de fallos silenciosos y manejo inadecuado de errores.
   - `code-simplifier`: oportunidades de simplificacion sin alterar funcionalidad.

   Umbral de confianza: solo reportar hallazgos con confianza >= 80%.

8. **Documentar hallazgos.** Cada hallazgo debe incluir: ubicacion en el codigo, descripcion del problema, impacto potencial y sugerencia de correccion.

## Criterios de exito

- Se han revisado legibilidad, errores logicos, manejo de errores, complejidad y edge cases.
- Los hallazgos incluyen ubicacion, descripcion, impacto y sugerencia de correccion.
- Solo se reportan hallazgos con confianza >= 80%.
- El tono de la revision es constructivo y orientado a mejorar el codigo.
- Se distingue entre problemas que bloquean y sugerencias de mejora.
