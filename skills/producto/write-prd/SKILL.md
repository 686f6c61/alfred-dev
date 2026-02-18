---
name: write-prd
description: "Usar para generar un PRD completo con problema, solucion, historias de usuario y criterios de aceptacion"
---

# Generar PRD (Product Requirements Document)

## Resumen

Este skill genera un documento de requisitos de producto estructurado y completo. El PRD sirve como fuente de verdad compartida entre producto, desarrollo y diseno, asegurando que todo el equipo entiende el problema que se resuelve, la solucion propuesta y los criterios con los que se medira el exito.

El proceso es iterativo: se genera un borrador que el usuario debe revisar y aprobar antes de considerarlo definitivo. Esto evita que se construya sobre suposiciones no validadas.

## Proceso

1. **Recopilar contexto inicial.** Preguntar al usuario por el problema que quiere resolver, el publico objetivo y cualquier restriccion conocida. Si el usuario ya ha proporcionado esta informacion, no repetir preguntas.

2. **Investigar el contexto del proyecto.** Revisar documentacion existente en `docs/`, issues abiertos, y cualquier PRD anterior para evitar duplicidades y mantener coherencia con decisiones previas.

3. **Redactar el PRD con la siguiente estructura:**

   - **Titulo y version:** nombre descriptivo del documento y fecha de creacion.
   - **Problema:** descripcion clara del dolor o necesidad del usuario. Incluir datos si estan disponibles.
   - **Contexto:** por que este problema importa ahora, que se ha intentado antes, que limitaciones existen.
   - **Solucion propuesta:** descripcion de alto nivel de lo que se va a construir. Sin entrar en detalles de implementacion, centrarse en el valor para el usuario.
   - **Historias de usuario:** formato "Como [rol], quiero [accion], para [beneficio]". Cada historia debe ser independiente y verificable.
   - **Criterios de aceptacion:** en formato Given/When/Then para cada historia. Deben ser lo bastante concretos como para convertirse en tests automatizados.
   - **Metricas de exito:** KPIs medibles que indiquen si la solucion funciona. Evitar metricas vanidosas.
   - **Riesgos y mitigaciones:** que puede salir mal y como se aborda cada riesgo.
   - **Fuera de alcance:** que NO se va a hacer en esta iteracion y por que.

4. **Utilizar la plantilla base.** Si existe `templates/prd.md`, usarla como punto de partida para mantener consistencia entre PRDs del proyecto.

5. **Presentar el borrador al usuario para revision.** HARD-GATE: el PRD no se da por finalizado hasta que el usuario lo aprueba explicitamente. Iterar sobre el feedback recibido.

6. **Guardar el PRD aprobado** en `docs/prd/` con un nombre descriptivo que incluya la fecha o un identificador del proyecto (por ejemplo, `docs/prd/2024-autenticacion-social.md`).

## Criterios de exito

- El PRD cubre todas las secciones obligatorias: problema, contexto, solucion, historias de usuario, criterios de aceptacion, metricas y riesgos.
- Las historias de usuario son independientes, verificables y priorizadas.
- Los criterios de aceptacion siguen el formato Given/When/Then y cubren escenarios positivos y negativos.
- El usuario ha revisado y aprobado el documento explicitamente.
- El fichero se ha guardado en `docs/prd/` siguiendo la convencion de nombres del proyecto.
