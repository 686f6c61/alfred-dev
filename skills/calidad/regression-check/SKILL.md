---
name: regression-check
description: "Usar para verificar que cambios nuevos no rompen funcionalidad existente. También: algo se ha roto, cambio rompe funcionalidad, verificar que no hay regresión, tests de regresión."
---

# Verificación de regresiones

## Resumen

Este skill verifica que los cambios recientes no han roto funcionalidad que antes funcionaba correctamente. Las regresiones son uno de los tipos de bug más frustrantes: algo que el usuario daba por hecho deja de funcionar sin razón aparente. Este proceso las detecta antes de que lleguen a producción.

El enfoque es sistemático: se analiza el impacto del cambio, se ejecutan los tests relevantes y se verifica la integración con el resto del sistema.

## Proceso

1. **Analizar el alcance del cambio.** Entender qué se ha modificado:

   - Ficheros cambiados (diff de Git).
   - Módulos afectados directamente.
   - Dependientes: qué otros módulos importan o usan los módulos cambiados.
   - Interfaces públicas: se ha cambiado alguna firma de función, tipo de retorno o contrato?

2. **Mapear las áreas de impacto potencial.** Un cambio en un módulo base puede afectar a todo lo que depende de él. Trazar el árbol de dependencias hacia arriba:

   ```
   Módulo cambiado --> Módulos que lo importan --> Módulos que importan a esos
   ```

   Cuanto más profundo en el árbol, mayor es el área de impacto.

3. **Ejecutar los tests del área afectada.** En orden:

   - Tests unitarios de los módulos modificados.
   - Tests unitarios de los módulos dependientes.
   - Tests de integración que cubran la interacción entre módulos afectados.
   - Tests e2e de los flujos que pasan por los módulos afectados.

4. **Si hay tests que fallan, analizar la causa:**

   - El test falla porque el cambio rompe una funcionalidad existente? Es una regresión real. Corregir.
   - El test falla porque su expectativa era incorrecta y el cambio es correcto? Actualizar el test con justificación.
   - El test es inestable (flaky) y falla intermitentemente? Documentar y marcar para arreglar.

5. **Identificar lagunas de testing.** Si hay áreas afectadas por el cambio que no tienen tests:

   - Documentar la laguna como riesgo.
   - Si el riesgo es alto, escribir tests de caracterización antes de dar el cambio por bueno.
   - Crear issues para cubrir las lagunas detectadas.

6. **Verificar integración.** Más allá de los tests automatizados, verificar manualmente o con tests exploratorios que los flujos principales siguen funcionando. Prestar especial atención a:

   - Flujos que cruzan múltiples módulos.
   - Integraciones con servicios externos.
   - Comportamiento en condiciones de error.

7. **Documentar el resultado.** Registrar: qué se verificó, qué pasó, qué quedó sin verificar y por qué.

## Criterios de éxito

- Se ha analizado el impacto del cambio en todo el árbol de dependencias.
- Los tests del área afectada se han ejecutado y pasan.
- Los tests que fallan han sido analizados y clasificados (regresión real, test incorrecto, flaky).
- Las lagunas de testing están documentadas con su nivel de riesgo.
- No hay regresiones reales sin corregir.
