---
name: refactor
description: "Usar para refactorizar codigo con tests como red de seguridad"
---

# Refactorizar codigo

## Resumen

Este skill guia un proceso de refactorizacion seguro. La regla de oro es que la refactorizacion nunca cambia el comportamiento observable del sistema, solo mejora su estructura interna. Para garantizar esto, los tests existentes actuan como red de seguridad: deben pasar antes, durante y despues de la refactorizacion.

La refactorizacion y la adicion de funcionalidad son dos actividades distintas que nunca se mezclan en el mismo commit. Si se detecta un bug durante la refactorizacion, se anota y se corrige en un commit separado.

## Proceso

1. **Identificar el code smell.** Antes de refactorizar, tener claro que problema se esta resolviendo. Los code smells mas comunes son:

   - Funciones demasiado largas (mas de 30 lineas).
   - Parametros excesivos (mas de 3).
   - Duplicacion de logica.
   - Condicionales anidados profundamente.
   - Nombres poco descriptivos.
   - Clases con demasiadas responsabilidades.
   - Acoplamiento excesivo entre modulos.
   - Comentarios que compensan codigo confuso (mejor reescribir el codigo).

2. **Verificar que los tests pasan ANTES de empezar.** HARD-GATE: ejecutar la suite de tests completa (o al menos los tests del modulo afectado) y confirmar que todo esta en verde. No se refactoriza sobre una base rota.

3. **Si no hay tests suficientes, escribirlos primero.** Si el area a refactorizar no tiene cobertura de tests, escribir tests de caracterizacion que capturen el comportamiento actual antes de cambiar nada. Estos tests se commitean por separado.

4. **Aplicar la refactorizacion en pasos pequenos.** Cada paso debe ser:

   - Lo bastante pequeno como para ser reversible.
   - Verificable con los tests existentes.
   - Comprensible de forma aislada.

   Tecnicas comunes: extraer funcion, renombrar, mover a modulo, introducir parametro, reemplazar condicional con polimorfismo, simplificar expresion.

5. **Ejecutar tests despues de cada paso.** No acumular multiples cambios sin verificar. Si un test se rompe, deshacer el ultimo paso y analizar por que.

6. **Verificar que los tests SIGUEN pasando al final.** Ejecutar la suite completa una ultima vez. Comparar el comportamiento observable: mismos inputs deben producir mismos outputs.

7. **Hacer commit separado.** El commit de refactorizacion va aparte del commit de nueva funcionalidad. Mensaje descriptivo: `refactor: extraer logica de validacion a modulo independiente`.

## Criterios de exito

- Los tests pasan antes y despues de la refactorizacion.
- El comportamiento observable del sistema no ha cambiado.
- El code smell identificado se ha eliminado o reducido.
- El commit de refactorizacion no incluye nueva funcionalidad.
- El codigo resultante es mas legible, mantenible o simple que el anterior.
