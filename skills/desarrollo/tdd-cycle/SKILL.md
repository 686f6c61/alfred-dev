---
name: tdd-cycle
description: "Usar siempre antes de implementar codigo. Ciclo rojo-verde-refactor estricto."
---

# Ciclo TDD (Test-Driven Development)

## Resumen

Este skill implementa el ciclo rojo-verde-refactor de TDD de forma estricta. La regla fundamental es que no se escribe ni una linea de codigo de produccion sin un test que falle primero. Esto no es una sugerencia, es un HARD-GATE: si no hay test fallando, no se escribe implementacion.

El TDD no es solo una tecnica de testing, es una tecnica de diseno. Escribir el test primero obliga a pensar en la interfaz publica antes que en la implementacion, lo que produce codigo mas limpio y con menor acoplamiento.

## Proceso

### Paso 1: Rojo - escribir un test que falle

- Escribir un unico test que describa el comportamiento esperado.
- El test debe ser especifico: probar UN aspecto del comportamiento, no varios.
- Nombrar el test de forma descriptiva: `deberia_devolver_error_cuando_email_es_invalido`, no `test1`.
- El test debe fallar por la razon correcta (el codigo no existe o no implementa el comportamiento), no por un error de sintaxis.

### Paso 2: Ejecutar y verificar que falla

- HARD-GATE: ejecutar el test y confirmar que falla.
- Verificar que el mensaje de error es el esperado. Si el test falla por una razon distinta a la esperada, corregir el test antes de continuar.
- Este paso no se puede saltar. Un test que pasa sin implementacion significa que el test no esta probando nada util.

### Paso 3: Verde - implementacion minima

- Escribir el minimo codigo necesario para que el test pase.
- "Minimo" significa literalmente lo minimo. Si el test espera que una funcion devuelva `true`, devolver `true` directamente es valido en este paso.
- No anticipar requisitos futuros. No anadir logica que ningun test pide.
- No preocuparse por la elegancia del codigo en este paso.

### Paso 4: Ejecutar y verificar que pasa

- Ejecutar todos los tests (no solo el nuevo) y verificar que pasan.
- Si algun test existente se rompe, corregir la implementacion sin cambiar los tests existentes (salvo que haya un test mal escrito).
- HARD-GATE: no avanzar hasta que todos los tests esten en verde.

### Paso 5: Refactorizar

- Ahora, con la red de seguridad de los tests, mejorar el codigo.
- Eliminar duplicacion, mejorar nombres, extraer funciones, simplificar condicionales.
- Ejecutar los tests despues de cada cambio de refactoring para asegurar que no se rompe nada.
- La refactorizacion no cambia comportamiento, solo estructura.

### Paso 6: Commit atomico

- Hacer commit del test y la implementacion juntos. El commit debe ser atomico: si se revierte, el proyecto sigue en un estado consistente.
- Formato del commit: `feat: [descripcion]` o `test: [descripcion]` segun corresponda.
- Volver al paso 1 con el siguiente comportamiento a implementar.

## Criterios de exito

- No existe codigo de produccion sin un test correspondiente que lo valide.
- Cada test se ha visto fallar antes de escribir la implementacion.
- Los tests son independientes entre si (no dependen de orden de ejecucion ni de estado compartido).
- El refactoring se ha realizado con todos los tests en verde.
- Los commits son atomicos y cada uno deja el proyecto en estado funcional.
