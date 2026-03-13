---
name: write-prd
description: "Generar un PRD completo con problema, solución, historias de usuario y criterios de aceptación. Activar cuando el usuario quiera definir requisitos de producto, decidir que construir, crear un documento de requisitos, redactar un PRD o elaborar una especificacion funcional."
---

# Generar PRD (Product Requirements Document)

## Resumen

Este skill genera un documento de requisitos de producto estructurado y completo. El PRD sirve como fuente de verdad compartida entre producto, desarrollo y diseño, asegurando que todo el equipo entiende el problema que se resuelve, la solución propuesta y los criterios con los que se medirá el éxito.

El proceso es iterativo: se genera un borrador que el usuario debe revisar y aprobar antes de considerarlo definitivo. Esto evita que se construya sobre suposiciones no validadas.

## Proceso

1. **Recopilar contexto inicial.** Formular preguntas **una a una** (una por turno, esperar respuesta antes de la siguiente) sobre el problema que quiere resolver, el público objetivo y restricciones conocidas. Usar `AskUserQuestion` con opciones cuando la pregunta tenga respuestas predefinidas; texto directo cuando sea abierta. Si el usuario ya ha proporcionado información suficiente, saltar las preguntas cuya respuesta ya se tiene.

2. **Investigar el contexto del proyecto.** Revisar documentación existente en `docs/`, issues abiertos, y cualquier PRD anterior para evitar duplicidades y mantener coherencia con decisiones previas.

3. **Redactar el PRD con la siguiente estructura:**

   - **Título y versión:** nombre descriptivo del documento y fecha de creación.
   - **Problema:** descripción clara del dolor o necesidad del usuario. Incluir datos si están disponibles.
   - **Contexto:** por qué este problema importa ahora, qué se ha intentado antes, qué limitaciones existen.
   - **Solución propuesta:** descripción de alto nivel de lo que se va a construir. Sin entrar en detalles de implementación, centrarse en el valor para el usuario.
   - **Historias de usuario:** formato "Como [rol], quiero [acción], para [beneficio]". Cada historia debe ser independiente y verificable.
   - **Criterios de aceptación:** en formato Given/When/Then para cada historia. Deben ser lo bastante concretos como para convertirse en tests automatizados.
   - **Métricas de éxito:** KPIs medibles que indiquen si la solución funciona. Evitar métricas vanidosas.
   - **Riesgos y mitigaciones:** qué puede salir mal y cómo se aborda cada riesgo.
   - **Fuera de alcance:** qué NO se va a hacer en esta iteración y por qué.

4. **Utilizar la plantilla base.** Si existe `templates/prd.md`, usarla como punto de partida para mantener consistencia entre PRDs del proyecto.

5. **Presentar el borrador al usuario para revisión.** HARD-GATE: el PRD no se da por finalizado hasta que el usuario lo aprueba explícitamente. Iterar sobre el feedback recibido.

6. **Guardar el PRD aprobado** en `docs/prd/` con un nombre descriptivo que incluya la fecha o un identificador del proyecto (por ejemplo, `docs/prd/2024-autenticacion-social.md`).

## Criterios de éxito

- El PRD cubre todas las secciones obligatorias: problema, contexto, solución, historias de usuario, criterios de aceptación, métricas y riesgos.
- Las historias de usuario son independientes, verificables y priorizadas.
- Los criterios de aceptación siguen el formato Given/When/Then y cubren escenarios positivos y negativos.
- El usuario ha revisado y aprobado el documento explícitamente.
- El fichero se ha guardado en `docs/prd/` siguiendo la convención de nombres del proyecto.

## Que NO hacer

- No confundir la solución propuesta con una especificación técnica detallada. El PRD describe el qué y el por qué, no el cómo a nivel de implementación.
- No escribir historias de usuario que describen implementación en vez de valor. "Como usuario, quiero que se use Redis para cachear" no es una historia de usuario; "Como usuario, quiero que la búsqueda responda en menos de 200ms" sí lo es.
- No dar el PRD por cerrado sin aprobación explícita del usuario. El PRD es un acuerdo entre partes; publicarlo sin validación anula su función como contrato.
