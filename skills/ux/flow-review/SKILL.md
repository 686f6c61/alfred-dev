---
name: flow-review
description: "Analizar flujos de usuario: pasos, abandono, simplificación. Activar ante: flujo de usuario, pasos innecesarios, simplificar proceso, experiencia de usuario, conversion, abandono"
---

# Revisión de flujos de usuario

## Resumen

Este skill analiza un flujo de usuario de principio a fin para identificar puntos de fricción, pasos innecesarios y oportunidades de simplificación. Un flujo de usuario es la secuencia de acciones que una persona realiza para completar un objetivo concreto en el producto (registrarse, comprar, configurar, etc.).

Cada paso adicional en un flujo es una oportunidad de abandono. El objetivo es reducir la fricción sin sacrificar la funcionalidad ni la seguridad, y asegurar que el flujo sea resiliente ante interrupciones, errores y caminos alternativos.

## Proceso

1. **Mapear el flujo actual.** Documentar cada paso que el usuario realiza desde el punto de entrada hasta la finalización del objetivo:

   - Contar los pasos totales (cada pantalla, clic o decisión cuenta).
   - Identificar las pantallas o vistas involucradas.
   - Registrar los datos que el usuario debe proporcionar en cada paso.
   - Dibujar el flujo con Mermaid o similar para tener una representación visual.

2. **Identificar puntos de fricción.** Examinar cada paso en busca de obstáculos:

   - Pasos que requieren información que el usuario probablemente no tiene a mano.
   - Formularios con demasiados campos obligatorios para la fase del flujo.
   - Redirecciones a sistemas externos (pasarelas de pago, verificación de correo) que rompen el contexto.
   - Pantallas de carga sin indicación de progreso.
   - Mensajes de error que no explican cómo resolverlos.
   - Pasos que parecen redundantes o que piden información ya proporcionada.

3. **Analizar los edge cases del flujo.** Los flujos suelen diseñarse para el camino feliz, pero los usuarios no siempre lo siguen:

   - **Volver atrás:** puede el usuario retroceder sin perder los datos introducidos?
   - **Error a mitad del flujo:** qué pasa si falla una llamada a la API en el paso 3 de 5?
   - **Retomar el flujo:** si el usuario cierra el navegador a mitad del proceso, puede retomar donde lo dejó?
   - **Bifurcaciones:** hay decisiones que llevan a caminos alternativos? Todos los caminos están cubiertos?
   - **Timeout de sesión:** qué ocurre si la sesión expira durante el flujo?

4. **Proponer simplificaciones.** Para cada punto de fricción, evaluar soluciones concretas:

   - Eliminar pasos que no aporten valor al usuario ni al negocio.
   - Fusionar pantallas que se puedan combinar sin saturar la interfaz.
   - Aplazar la recogida de datos no esenciales para después de completar el objetivo principal.
   - Prellenar campos con valores por defecto inteligentes o datos ya conocidos.
   - Reemplazar formularios largos con alternativas: autocompletado, selección visual, importación de datos.
   - Implementar guardado automático para flujos largos.

5. **Calcular la reducción de pasos.** Comparar el flujo original con el optimizado:

   - Número de pasos antes y después.
   - Número de campos de formulario antes y después.
   - Número de pantallas o vistas antes y después.
   - Tiempo estimado de completado antes y después.

6. **Entregar el diagrama del flujo optimizado.** Producir un diagrama Mermaid del flujo propuesto que muestre:

   - El camino principal (happy path) claramente identificado.
   - Los caminos alternativos y de error.
   - Los puntos de retorno y recuperación.
   - Las mejoras respecto al flujo original marcadas.

## Que NO hacer

- No simplificar eliminando pasos necesarios para la seguridad (confirmación de email, verificación de identidad). Buscar formas de hacerlos menos intrusivos, no de eliminarlos.
- No asumir que menos pasos es siempre mejor. A veces dividir un formulario largo en varios pasos cortos reduce la carga cognitiva y mejora la finalización.
- No diseñar solo para el camino feliz. Si el flujo no maneja errores, no está terminado.
- No ignorar el contexto del dispositivo. Un flujo que funciona bien en escritorio puede ser insoportable en móvil.
