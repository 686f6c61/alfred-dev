---
name: acceptance-criteria
description: "Generar criterios de aceptación en formato Given/When/Then. Activar cuando el usuario quiera definir criterios de aceptacion, usar formato Given When Then, escribir en Gherkin, saber como determinar que algo esta terminado o establecer una definicion de hecho."
---

# Generar criterios de aceptación

## Resumen

Este skill genera criterios de aceptación en formato Gherkin (Given/When/Then) a partir de una historia de usuario o requisito. Los criterios producidos deben ser lo bastante precisos como para convertirse directamente en tests automatizados, eliminando ambigüedad entre lo que producto espera y lo que desarrollo implementa.

El valor de unos buenos criterios de aceptación es doble: sirven como especificación ejecutable y como contrato entre producto y desarrollo. Si un criterio no se puede automatizar, probablemente es demasiado vago.

## Proceso

1. **Obtener la historia de usuario o requisito.** Si viene de un PRD o de una lista de historias existente, leerlo. Si no, pedir al usuario que describa la funcionalidad.

2. **Identificar los escenarios principales:**

   - **Escenario positivo (happy path):** el flujo normal cuando todo va bien. Es el caso de uso principal que justifica la existencia de la historia.
   - **Escenarios alternativos:** caminos válidos pero menos frecuentes. Por ejemplo, un usuario que cancela a mitad de un flujo.
   - **Escenarios negativos:** qué ocurre cuando la entrada es inválida, falta información o el sistema está en un estado inesperado.
   - **Edge cases:** límites del sistema, valores extremos, condiciones de carrera, timeout, datos vacíos.

3. **Redactar cada escenario en formato Gherkin:**

   ```gherkin
   Escenario: [Nombre descriptivo del escenario]
     Dado [contexto o estado previo del sistema]
     Cuando [acción que realiza el usuario o el sistema]
     Entonces [resultado esperado observable]
   ```

   Para escenarios con múltiples condiciones, usar `Y` (And) para encadenar pasos:

   ```gherkin
   Escenario: Login con credenciales válidas
     Dado que el usuario tiene una cuenta activa
     Y que está en la página de login
     Cuando introduce su email y contraseña correctos
     Y pulsa el botón "Entrar"
     Entonces es redirigido al dashboard
     Y ve su nombre de usuario en la cabecera
   ```

4. **Verificar que cada criterio es automatizable.** Si un paso usa lenguaje ambiguo ("el sistema responde rápido", "la interfaz es intuitiva"), reescribirlo con métricas concretas ("el tiempo de respuesta es inferior a 200ms", "el formulario muestra etiquetas visibles en todos los campos").

5. **Cubrir el manejo de errores.** Para cada escenario positivo, pensar en al menos un escenario de error correspondiente. Documentar qué mensaje ve el usuario, qué estado queda el sistema y si se registra el error.

6. **Agrupar por historia de usuario.** Presentar los criterios organizados bajo la historia a la que pertenecen, facilitando la trazabilidad.

7. **Revisar con el usuario.** Los criterios de aceptación son un acuerdo: producto dice qué espera y desarrollo confirma que es viable. No se dan por finales sin validación.

## Criterios de éxito

- Cada historia tiene al menos un escenario positivo, uno negativo y un edge case.
- Todos los escenarios siguen el formato Given/When/Then sin ambigüedades.
- Los criterios son directamente convertibles en tests automatizados.
- Se ha cubierto el manejo de errores para los flujos críticos.
- El usuario ha validado que los criterios reflejan sus expectativas.

## Que NO hacer

- No escribir criterios ambiguos que no se puedan automatizar. Si un criterio usa términos como "rápido", "bonito" o "intuitivo" sin métricas concretas, no es verificable.
- No cubrir solo el camino feliz. Cada historia necesita al menos un escenario negativo y un edge case para ser robusta.
- No dar los criterios por finales sin validación del usuario. Los criterios de aceptación son un contrato entre producto y desarrollo; ambas partes deben estar de acuerdo.
