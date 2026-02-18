---
name: exploratory-testing
description: "Usar para testing exploratorio con sesiones documentadas"
---

# Testing exploratorio

## Resumen

Este skill ejecuta sesiones de testing exploratorio estructurado. A diferencia de los tests automatizados que verifican comportamientos conocidos, el testing exploratorio busca descubrir comportamientos inesperados que nadie penso en probar. Es el complemento humano imprescindible a la suite automatizada.

Cada sesion tiene un objetivo concreto, un tiempo limitado y produce documentacion de lo encontrado. No es "probar cosas al azar" sino una exploracion guiada por heuristicas.

## Proceso

1. **Definir el objetivo de la sesion.** Cada sesion se centra en un area o aspecto:

   - "Explorar el flujo de registro buscando estados inconsistentes."
   - "Probar la API de pagos con datos invalidos."
   - "Verificar el comportamiento bajo carga simulada."

   Un objetivo demasiado amplio ("probar todo") no es un objetivo.

2. **Establecer tiempo limitado.** Las sesiones duran 25 minutos (un pomodoro). El limite de tiempo obliga a centrarse y evita la fatiga que reduce la efectividad. Si se necesita mas tiempo, iniciar una nueva sesion con objetivo refinado.

3. **Aplicar heuristicas de exploracion.** Estas heuristicas guian la busqueda de problemas:

   - **Limites:** valores en los extremos de lo permitido (0, 1, maximo, maximo+1).
   - **Estados:** que pasa al cambiar de estado rapidamente (crear y eliminar inmediatamente, editar mientras otro usuario edita).
   - **Flujos alternativos:** seguir caminos que no son el happy path (cancelar a mitad, volver atras, refrescar la pagina).
   - **Datos invalidos:** inyectar datos que no se esperan (HTML, SQL, unicode exotico, strings vacios, valores negativos).
   - **Interrupciones:** que pasa si la conexion se corta a mitad de una operacion, si el navegador se cierra, si se agota el timeout.
   - **Concurrencia:** dos usuarios haciendo lo mismo a la vez, requests duplicadas, doble click.
   - **Rendimiento:** operaciones con volumen grande de datos, busquedas con resultados masivos.

4. **Documentar en tiempo real.** Durante la sesion, registrar:

   - Que se probo (accion concreta).
   - Que se esperaba que pasase.
   - Que paso realmente.
   - Si es un bug, un comportamiento confuso o un area sin cobertura.

5. **Clasificar los hallazgos:**

   - **Bug:** comportamiento incorrecto que debe corregirse.
   - **UX issue:** funciona pero confunde al usuario.
   - **Falta de cobertura:** area sin tests automatizados que deberia tenerlos.
   - **Duda:** comportamiento que no se sabe si es correcto sin consultar el requisito.

6. **Documentar lo que NO se probo.** Tan importante como lo probado es lo que quedo fuera. Esto alimenta futuras sesiones.

7. **Generar informe de sesion.** Resumen con: objetivo, duracion, hallazgos clasificados, areas no cubiertas, proximos pasos sugeridos.

## Criterios de exito

- La sesion tenia un objetivo concreto y un tiempo limitado.
- Se aplicaron al menos 3 heuristicas de exploracion distintas.
- Los hallazgos estan documentados con: accion, resultado esperado y resultado real.
- Los hallazgos estan clasificados (bug, UX, cobertura, duda).
- Se han documentado las areas que no se pudieron cubrir.
