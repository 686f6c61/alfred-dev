---
name: refactor
description: "Usar para refactorizar código con tests como red de seguridad. Activar cuando el usuario quiera limpiar código, reducir complejidad, extraer función, mejorar nombres, eliminar duplicación, resolver un code smell o reorganizar la estructura interna sin cambiar comportamiento."
---

# Refactorizar código

## Resumen

Este skill guía un proceso de refactorización seguro. La regla de oro es que la refactorización nunca cambia el comportamiento observable del sistema, solo mejora su estructura interna. Para garantizar esto, los tests existentes actúan como red de seguridad: deben pasar antes, durante y después de la refactorización.

La refactorización y la adición de funcionalidad son dos actividades distintas que nunca se mezclan en el mismo commit. Si se detecta un bug durante la refactorización, se anota y se corrige en un commit separado.

## Proceso

1. **Identificar el code smell.** Antes de refactorizar, tener claro qué problema se está resolviendo. Los code smells más comunes son:

   - Funciones demasiado largas (más de 30 líneas).
   - Parámetros excesivos (más de 3).
   - Duplicación de lógica.
   - Condicionales anidados profundamente.
   - Nombres poco descriptivos.
   - Clases con demasiadas responsabilidades.
   - Acoplamiento excesivo entre módulos.
   - Comentarios que compensan código confuso (mejor reescribir el código).

2. **Verificar que los tests pasan ANTES de empezar.** HARD-GATE: ejecutar la suite de tests completa (o al menos los tests del módulo afectado) y confirmar que todo está en verde. No se refactoriza sobre una base rota.

3. **Si no hay tests suficientes, escribirlos primero.** Si el área a refactorizar no tiene cobertura de tests, escribir tests de caracterización que capturen el comportamiento actual antes de cambiar nada. Estos tests se commitean por separado.

4. **Aplicar la refactorización en pasos pequeños.** Cada paso debe ser:

   - Lo bastante pequeño como para ser reversible.
   - Verificable con los tests existentes.
   - Comprensible de forma aislada.

   Técnicas comunes: extraer función, renombrar, mover a módulo, introducir parámetro, reemplazar condicional con polimorfismo, simplificar expresión.

5. **Ejecutar tests después de cada paso.** No acumular múltiples cambios sin verificar. Si un test se rompe, deshacer el último paso y analizar por qué.

6. **Verificar que los tests SIGUEN pasando al final.** Ejecutar la suite completa una última vez. Comparar el comportamiento observable: mismos inputs deben producir mismos outputs.

7. **Hacer commit separado.** El commit de refactorización va aparte del commit de nueva funcionalidad. Mensaje descriptivo: `refactor: extraer lógica de validación a módulo independiente`.

## Criterios de éxito

- Los tests pasan antes y después de la refactorización.
- El comportamiento observable del sistema no ha cambiado.
- El code smell identificado se ha eliminado o reducido.
- El commit de refactorización no incluye nueva funcionalidad.
- El código resultante es más legible, mantenible o simple que el anterior.
