---
name: migration-plan
description: "Planificar migraciones de base de datos con rollback y estimación de impacto. Activar cuando el usuario quiera migrar base de datos, cambiar esquema, ejecutar ALTER TABLE, planificar un rollback o realizar una migracion segura."
---

# Planificación de migraciones de base de datos

## Resumen

Este skill estructura la planificación de una migración de base de datos de principio a fin. Una migración mal planificada puede causar pérdida de datos, downtime prolongado o inconsistencias difíciles de detectar. La planificación rigurosa es la diferencia entre un cambio transparente y un incidente.

El resultado es un plan de migración que incluye el script forward, el script de rollback, la estimación de impacto y los pasos de verificación posteriores. Este plan se revisa antes de ejecutar cualquier cambio.

## Proceso

1. **Analizar el cambio requerido.** Antes de escribir SQL, entender exactamente qué cambia y por qué:

   - Qué tablas y columnas se ven afectadas.
   - Si el cambio es aditivo (nueva tabla, nueva columna) o destructivo (eliminar columna, cambiar tipo).
   - Si hay datos existentes que necesitan transformación.
   - Si el cambio es compatible hacia atrás con la versión actual del código o requiere despliegue coordinado.

2. **Estimar el impacto en producción.** Obtener métricas del entorno real:

   - Tamaño de las tablas afectadas (número de filas y tamaño en disco).
   - Tiempo estimado de la migración según el volumen de datos.
   - Si la operación bloquea la tabla (ALTER TABLE con lock en MySQL, por ejemplo).
   - Si se necesita ventana de mantenimiento o se puede ejecutar en caliente.

   Para tablas grandes (millones de filas), considerar migraciones en lotes o herramientas como gh-ost, pt-online-schema-change o pgroll.

3. **Escribir el script forward.** El script que aplica el cambio. Requisitos:

   - Debe ser idempotente cuando sea posible (IF NOT EXISTS, IF EXISTS).
   - Incluir transacción si el motor lo permite para DDL.
   - Separar cambios de esquema y cambios de datos si la migración es compleja.
   - Respetar el sistema de migraciones del proyecto (Prisma Migrate, Alembic, Django Migrations, Flyway).

4. **Escribir el script de rollback.** El script que deshace el cambio forward:

   - Para cambios aditivos: DROP de lo creado.
   - Para cambios destructivos: restaurar desde backup o columna temporal.
   - Para transformaciones de datos: script inverso o restauración desde backup.
   - Verificar que el rollback deja la base de datos en un estado consistente.

5. **Definir el orden de ejecución.** Si la migración afecta a varias tablas con dependencias:

   - Crear tablas referenciadas antes que las que las referencian.
   - Eliminar foreign keys antes de eliminar tablas referenciadas.
   - Si hay migración de datos entre tablas, respetar el orden de dependencia.
   - Documentar el orden explícitamente en el plan.

6. **Planificar la verificación post-migración.** Definir comprobaciones que confirmen que la migración se aplicó correctamente:

   - Verificar que las tablas y columnas existen con los tipos esperados.
   - Contar filas antes y después para detectar pérdida de datos.
   - Ejecutar queries de validación sobre los datos migrados.
   - Comprobar que la aplicación funciona correctamente con el nuevo esquema.
   - Revisar los logs en busca de errores relacionados con el cambio.

7. **Documentar el plan.** El plan de migración debe incluir:

   - Descripción del cambio y motivación.
   - Script forward y script de rollback.
   - Estimación de tiempo y necesidad de downtime.
   - Orden de ejecución.
   - Checklist de verificación post-migración.
   - Responsable de la ejecución y plan de comunicación.

## Que NO hacer

- No ejecutar migraciones directamente en producción sin haberlas probado en un entorno con datos realistas.
- No asumir que el rollback "no se necesitará". Si no hay rollback, no hay plan.
- No mezclar migraciones de esquema con migraciones de datos en un solo paso si la migración es compleja.
- No ignorar los bloqueos de tabla. Un ALTER TABLE en una tabla con millones de filas puede bloquear la base de datos durante minutos u horas.
- No olvidar actualizar los modelos del ORM después de la migración.
- No ejecutar migraciones sin rollback probado. Si el rollback no se ha verificado en un entorno de prueba, no se puede confiar en él cuando se necesite de verdad.
- No migrar sin backup previo. Antes de cualquier migración destructiva, asegurar que existe un backup reciente y verificado de la base de datos.
