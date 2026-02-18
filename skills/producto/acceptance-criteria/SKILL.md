---
name: acceptance-criteria
description: "Usar para generar criterios de aceptacion en formato Given/When/Then"
---

# Generar criterios de aceptacion

## Resumen

Este skill genera criterios de aceptacion en formato Gherkin (Given/When/Then) a partir de una historia de usuario o requisito. Los criterios producidos deben ser lo bastante precisos como para convertirse directamente en tests automatizados, eliminando ambiguedad entre lo que producto espera y lo que desarrollo implementa.

El valor de unos buenos criterios de aceptacion es doble: sirven como especificacion ejecutable y como contrato entre producto y desarrollo. Si un criterio no se puede automatizar, probablemente es demasiado vago.

## Proceso

1. **Obtener la historia de usuario o requisito.** Si viene de un PRD o de una lista de historias existente, leerlo. Si no, pedir al usuario que describa la funcionalidad.

2. **Identificar los escenarios principales:**

   - **Escenario positivo (happy path):** el flujo normal cuando todo va bien. Es el caso de uso principal que justifica la existencia de la historia.
   - **Escenarios alternativos:** caminos validos pero menos frecuentes. Por ejemplo, un usuario que cancela a mitad de un flujo.
   - **Escenarios negativos:** que ocurre cuando la entrada es invalida, falta informacion o el sistema esta en un estado inesperado.
   - **Edge cases:** limites del sistema, valores extremos, condiciones de carrera, timeout, datos vacios.

3. **Redactar cada escenario en formato Gherkin:**

   ```gherkin
   Escenario: [Nombre descriptivo del escenario]
     Dado [contexto o estado previo del sistema]
     Cuando [accion que realiza el usuario o el sistema]
     Entonces [resultado esperado observable]
   ```

   Para escenarios con multiples condiciones, usar `Y` (And) para encadenar pasos:

   ```gherkin
   Escenario: Login con credenciales validas
     Dado que el usuario tiene una cuenta activa
     Y que esta en la pagina de login
     Cuando introduce su email y contrasena correctos
     Y pulsa el boton "Entrar"
     Entonces es redirigido al dashboard
     Y ve su nombre de usuario en la cabecera
   ```

4. **Verificar que cada criterio es automatizable.** Si un paso usa lenguaje ambiguo ("el sistema responde rapido", "la interfaz es intuitiva"), reescribirlo con metricas concretas ("el tiempo de respuesta es inferior a 200ms", "el formulario muestra etiquetas visibles en todos los campos").

5. **Cubrir el manejo de errores.** Para cada escenario positivo, pensar en al menos un escenario de error correspondiente. Documentar que mensaje ve el usuario, que estado queda el sistema y si se registra el error.

6. **Agrupar por historia de usuario.** Presentar los criterios organizados bajo la historia a la que pertenecen, facilitando la trazabilidad.

7. **Revisar con el usuario.** Los criterios de aceptacion son un acuerdo: producto dice que espera y desarrollo confirma que es viable. No se dan por finales sin validacion.

## Criterios de exito

- Cada historia tiene al menos un escenario positivo, uno negativo y un edge case.
- Todos los escenarios siguen el formato Given/When/Then sin ambiguedades.
- Los criterios son directamente convertibles en tests automatizados.
- Se ha cubierto el manejo de errores para los flujos criticos.
- El usuario ha validado que los criterios reflejan sus expectativas.
