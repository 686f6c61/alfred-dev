---
name: exploratory-testing
description: "Usar para testing exploratorio con sesiones documentadas. También: probar sin script, buscar bugs, testing manual, edge cases, sesión de testing."
---

# Testing exploratorio

## Resumen

Este skill ejecuta sesiones de testing exploratorio estructurado. A diferencia de los tests automatizados que verifican comportamientos conocidos, el testing exploratorio busca descubrir comportamientos inesperados que nadie pensó en probar. Es el complemento humano imprescindible a la suite automatizada.

Cada sesión tiene un objetivo concreto, un tiempo limitado y produce documentación de lo encontrado. No es "probar cosas al azar" sino una exploración guiada por heurísticas.

## Proceso

1. **Definir el objetivo de la sesión.** Cada sesión se centra en un área o aspecto:

   - "Explorar el flujo de registro buscando estados inconsistentes."
   - "Probar la API de pagos con datos inválidos."
   - "Verificar el comportamiento bajo carga simulada."

   Un objetivo demasiado amplio ("probar todo") no es un objetivo.

2. **Establecer tiempo limitado.** Las sesiones duran 25 minutos (un pomodoro). El límite de tiempo obliga a centrarse y evita la fatiga que reduce la efectividad. Si se necesita más tiempo, iniciar una nueva sesión con objetivo refinado.

3. **Aplicar heurísticas de exploración.** Estas heurísticas guían la búsqueda de problemas:

   - **Límites:** valores en los extremos de lo permitido (0, 1, máximo, máximo+1).
   - **Estados:** qué pasa al cambiar de estado rápidamente (crear y eliminar inmediatamente, editar mientras otro usuario edita).
   - **Flujos alternativos:** seguir caminos que no son el happy path (cancelar a mitad, volver atrás, refrescar la página).
   - **Datos inválidos:** inyectar datos que no se esperan (HTML, SQL, unicode exótico, strings vacíos, valores negativos).
   - **Interrupciones:** qué pasa si la conexión se corta a mitad de una operación, si el navegador se cierra, si se agota el timeout.
   - **Concurrencia:** dos usuarios haciendo lo mismo a la vez, requests duplicadas, doble click.
   - **Rendimiento:** operaciones con volumen grande de datos, búsquedas con resultados masivos.

4. **Documentar en tiempo real.** Durante la sesión, registrar:

   - Qué se probó (acción concreta).
   - Qué se esperaba que pasase.
   - Qué pasó realmente.
   - Si es un bug, un comportamiento confuso o un área sin cobertura.

5. **Clasificar los hallazgos:**

   - **Bug:** comportamiento incorrecto que debe corregirse.
   - **UX issue:** funciona pero confunde al usuario.
   - **Falta de cobertura:** área sin tests automatizados que debería tenerlos.
   - **Duda:** comportamiento que no se sabe si es correcto sin consultar el requisito.

6. **Documentar lo que NO se probó.** Tan importante como lo probado es lo que quedó fuera. Esto alimenta futuras sesiones.

7. **Generar informe de sesión.** Resumen con: objetivo, duración, hallazgos clasificados, áreas no cubiertas, próximos pasos sugeridos.

## Criterios de éxito

- La sesión tenía un objetivo concreto y un tiempo limitado.
- Se aplicaron al menos 3 heurísticas de exploración distintas.
- Los hallazgos están documentados con: acción, resultado esperado y resultado real.
- Los hallazgos están clasificados (bug, UX, cobertura, duda).
- Se han documentado las áreas que no se pudieron cubrir.
