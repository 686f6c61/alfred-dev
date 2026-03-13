---
name: usability-heuristics
description: "Evaluar interfaces con las 10 heurísticas de Nielsen. Activar ante: heuristicas de Nielsen, evaluacion de usabilidad, problemas de UX, interfaz confusa, consistencia de la interfaz"
---

# Evaluación heurística de usabilidad

## Resumen

Este skill aplica las 10 heurísticas de usabilidad de Jakob Nielsen para evaluar una interfaz de usuario de forma sistemática. La evaluación heurística es un método de inspección que no requiere usuarios reales, lo que la hace rápida y económica. No sustituye a las pruebas con usuarios, pero detecta la mayoría de problemas graves de usabilidad antes de que lleguen a producción.

Cada hallazgo se documenta con la heurística violada, la severidad, la ubicación en la interfaz y una propuesta de corrección concreta.

## Proceso

1. **Recorrer la interfaz aplicando cada heurística.** Evaluar el código y la interfaz contra las 10 heurísticas de Nielsen:

   - **H1 - Visibilidad del estado del sistema.** El sistema informa al usuario de lo que está pasando mediante feedback oportuno. Buscar: indicadores de carga, estados de progreso, confirmaciones de acciones, estados de formulario (enviando, enviado, error).

   - **H2 - Correspondencia con el mundo real.** El sistema usa el lenguaje y los conceptos del usuario, no jerga técnica. Buscar: mensajes de error con códigos internos, terminología del dominio del desarrollador en lugar del usuario, iconos no convencionales.

   - **H3 - Control y libertad del usuario.** El usuario puede deshacer y rehacer acciones fácilmente. Buscar: ausencia de botón "cancelar", acciones destructivas sin confirmación, imposibilidad de volver atrás en un flujo multipaso.

   - **H4 - Consistencia y estándares.** Los mismos conceptos se representan de la misma forma en toda la interfaz. Buscar: botones con estilos diferentes para la misma acción, terminología inconsistente, patrones de interacción que cambian entre pantallas.

   - **H5 - Prevención de errores.** El diseño evita que el usuario cometa errores en primer lugar. Buscar: campos sin validación en tiempo real, formularios que permiten enviar datos incompletos, acciones irreversibles sin paso de confirmación.

   - **H6 - Reconocer antes que recordar.** La información necesaria está visible o es fácilmente recuperable. Buscar: formularios sin placeholders ni ayudas contextuales, pasos que dependen de información de pantallas anteriores no visible, opciones ocultas en menús profundos.

   - **H7 - Flexibilidad y eficiencia de uso.** La interfaz se adapta tanto a usuarios novatos como expertos. Buscar: ausencia de atajos de teclado, imposibilidad de personalizar flujos frecuentes, falta de valores por defecto inteligentes.

   - **H8 - Diseño estético y minimalista.** Cada elemento en la pantalla compite por la atención. Buscar: información irrelevante que distrae de la tarea principal, exceso de opciones presentadas simultáneamente, texto innecesario.

   - **H9 - Ayuda para reconocer, diagnosticar y recuperarse de errores.** Los mensajes de error son claros y sugieren una solución. Buscar: mensajes genéricos ("Ha ocurrido un error"), errores sin indicar qué campo es incorrecto, ausencia de sugerencias de corrección.

   - **H10 - Ayuda y documentación.** Aunque el sistema debería ser usable sin documentación, la ayuda está disponible cuando se necesita. Buscar: funcionalidades complejas sin tooltips ni guías, ausencia de sección de ayuda, documentación desactualizada.

2. **Clasificar la severidad de cada hallazgo.** Usar la escala de Nielsen:

   | Nivel | Descripción |
   |-------|-------------|
   | 0 | No es un problema de usabilidad. |
   | 1 | Problema cosmético. Corregir solo si hay tiempo. |
   | 2 | Problema menor. Prioridad baja. |
   | 3 | Problema mayor. Importante corregir. Prioridad alta. |
   | 4 | Catástrofe. Imprescindible corregir antes de lanzar. |

3. **Documentar cada hallazgo.** Formato estandarizado:

   - **Heurística violada:** número y nombre.
   - **Severidad:** 0-4 con justificación.
   - **Ubicación:** pantalla, componente o flujo afectado.
   - **Descripción:** qué ocurre y por qué es un problema.
   - **Propuesta de corrección:** cambio concreto en la interfaz o el código.

4. **Priorizar y entregar.** Ordenar los hallazgos por severidad descendente. Agrupar correcciones que afecten al mismo componente para eficiencia. Distinguir entre correcciones que requieren cambios de UI, cambios de lógica y cambios de contenido.

## Que NO hacer

- No evaluar la estética subjetiva ("no me gusta el color"). Las heurísticas evalúan usabilidad, no preferencias visuales.
- No asumir que un hallazgo de severidad 1 no merece registro. Documentar todo; la priorización se hace después.
- No confundir esta evaluación con pruebas de usuario. La evaluación heurística detecta problemas desde la perspectiva experta, no valida si los usuarios reales tienen dificultades.
