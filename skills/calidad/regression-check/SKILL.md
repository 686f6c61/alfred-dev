---
name: regression-check
description: "Usar para verificar que cambios nuevos no rompen funcionalidad existente"
---

# Verificacion de regresiones

## Resumen

Este skill verifica que los cambios recientes no han roto funcionalidad que antes funcionaba correctamente. Las regresiones son uno de los tipos de bug mas frustrantes: algo que el usuario daba por hecho deja de funcionar sin razon aparente. Este proceso las detecta antes de que lleguen a produccion.

El enfoque es sistematico: se analiza el impacto del cambio, se ejecutan los tests relevantes y se verifica la integracion con el resto del sistema.

## Proceso

1. **Analizar el alcance del cambio.** Entender que se ha modificado:

   - Ficheros cambiados (diff de Git).
   - Modulos afectados directamente.
   - Dependientes: que otros modulos importan o usan los modulos cambiados.
   - Interfaces publicas: se ha cambiado alguna firma de funcion, tipo de retorno o contrato?

2. **Mapear las areas de impacto potencial.** Un cambio en un modulo base puede afectar a todo lo que depende de el. Trazar el arbol de dependencias hacia arriba:

   ```
   Modulo cambiado --> Modulos que lo importan --> Modulos que importan a esos
   ```

   Cuanto mas profundo en el arbol, mayor es el area de impacto.

3. **Ejecutar los tests del area afectada.** En orden:

   - Tests unitarios de los modulos modificados.
   - Tests unitarios de los modulos dependientes.
   - Tests de integracion que cubran la interaccion entre modulos afectados.
   - Tests e2e de los flujos que pasan por los modulos afectados.

4. **Si hay tests que fallan, analizar la causa:**

   - El test falla porque el cambio rompe una funcionalidad existente? Es una regresion real. Corregir.
   - El test falla porque su expectativa era incorrecta y el cambio es correcto? Actualizar el test con justificacion.
   - El test es inestable (flaky) y falla intermitentemente? Documentar y marcar para arreglar.

5. **Identificar lagunas de testing.** Si hay areas afectadas por el cambio que no tienen tests:

   - Documentar la laguna como riesgo.
   - Si el riesgo es alto, escribir tests de caracterizacion antes de dar el cambio por bueno.
   - Crear issues para cubrir las lagunas detectadas.

6. **Verificar integracion.** Mas alla de los tests automatizados, verificar manualmente o con tests exploratorios que los flujos principales siguen funcionando. Prestar especial atencion a:

   - Flujos que cruzan multiples modulos.
   - Integraciones con servicios externos.
   - Comportamiento en condiciones de error.

7. **Documentar el resultado.** Registrar: que se verifico, que paso, que quedo sin verificar y por que.

## Criterios de exito

- Se ha analizado el impacto del cambio en todo el arbol de dependencias.
- Los tests del area afectada se han ejecutado y pasan.
- Los tests que fallan han sido analizados y clasificados (regresion real, test incorrecto, flaky).
- Las lagunas de testing estan documentadas con su nivel de riesgo.
- No hay regresiones reales sin corregir.
