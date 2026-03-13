---
name: schema-design
description: "Diseñar esquemas de base de datos normalizados con índices y documentación. Activar cuando el usuario quiera diseñar base de datos, crear tablas, definir relaciones, aplicar normalizacion, configurar indices, crear un modelo de datos o generar un ERD."
---

# Diseño de esquemas de base de datos

## Resumen

Este skill guía el proceso de diseñar un esquema de base de datos relacional a partir de requisitos funcionales. El diseño no es solo crear tablas que almacenen datos, sino modelar el dominio del negocio de forma que garantice integridad, rendimiento y evolución sostenible.

El esquema resultante debe estar normalizado hasta la tercera forma normal (3NF) como mínimo, con índices justificados, constraints que protejan la integridad y documentación que permita a cualquier miembro del equipo entender cada tabla y columna sin necesidad de leer el código de la aplicación.

## Proceso

1. **Analizar los requisitos y extraer entidades.** A partir de los requisitos funcionales, identificar las entidades del dominio. Cada sustantivo relevante es un candidato a entidad: usuario, pedido, producto, factura. Documentar qué atributos tiene cada entidad y cuáles son obligatorios.

2. **Definir las relaciones entre entidades.** Para cada par de entidades relacionadas, determinar la cardinalidad:

   - Uno a uno (1:1): poco frecuente, evaluar si realmente son dos entidades o una sola.
   - Uno a muchos (1:N): la más habitual. La clave foránea va en el lado "muchos".
   - Muchos a muchos (N:M): requiere tabla intermedia con claves foráneas compuestas.

   Documentar la dirección de la relación y si es obligatoria u opcional en cada extremo.

3. **Normalizar hasta 3NF.** Aplicar las formas normales secuencialmente:

   - **1NF:** cada columna contiene valores atómicos, sin listas ni objetos anidados.
   - **2NF:** todos los atributos no clave dependen de la clave primaria completa, no de una parte.
   - **3NF:** ningún atributo no clave depende de otro atributo no clave (eliminar dependencias transitivas).

   Si hay motivos de rendimiento para desnormalizar, documentar la justificación explícitamente.

4. **Aplicar convenciones de naming.** Mantener coherencia en todo el esquema:

   - Tablas en plural y snake_case: `users`, `order_items`, `payment_methods`.
   - Columnas en singular y snake_case: `email`, `created_at`, `total_amount`.
   - Claves primarias: `id` o `<tabla_singular>_id`.
   - Claves foráneas: `<tabla_referenciada_singular>_id`.
   - Índices: `idx_<tabla>_<columnas>`.
   - Timestamps de auditoría: `created_at` y `updated_at` en todas las tablas.

5. **Definir constraints e integridad referencial.** Para cada tabla:

   - PRIMARY KEY en todas las tablas, sin excepción.
   - FOREIGN KEY con la acción ON DELETE adecuada (CASCADE, SET NULL, RESTRICT).
   - NOT NULL en columnas obligatorias.
   - UNIQUE donde corresponda (email, slug, códigos).
   - CHECK para validaciones a nivel de base de datos (rangos, enumerados, formatos).

6. **Diseñar los índices.** Los índices se crean para consultas concretas, no de forma preventiva:

   - Índice en todas las claves foráneas (muchos motores no lo hacen automáticamente).
   - Índice en columnas usadas frecuentemente en WHERE, ORDER BY y JOIN.
   - Índices compuestos cuando las consultas filtran por varias columnas (respetar el orden).
   - Evaluar índices parciales o funcionales si el motor lo permite.

7. **Adaptar al ORM del proyecto.** Traducir el diseño a la sintaxis del ORM utilizado (Prisma, Drizzle, SQLAlchemy, Django ORM, TypeORM). Asegurarse de que las relaciones, índices y constraints se expresan correctamente en el modelo del ORM, ya que no todos soportan las mismas funcionalidades.

8. **Registrar las decisiones de modelado.** Registrar las decisiones de modelado en la memoria del proyecto con `memory_log_decision`. Esto incluye el motivo de cada desnormalización, la elección de tipos de datos especiales y las concesiones de rendimiento vs. integridad.

9. **Documentar el esquema.** Cada tabla debe tener un comentario que explique su propósito. Las columnas no obvias deben documentar qué representan, sus valores posibles y sus restricciones. Si el motor lo permite, usar comentarios nativos (COMMENT ON); si no, documentar en un fichero adjunto o en el propio código del ORM.

## Que NO hacer

- No crear campos JSON "para todo". Los campos JSON son útiles para datos semiestructurados, pero no sustituyen a columnas y relaciones bien diseñadas.
- No usar soft delete (columna `deleted_at`) sin evaluar las consecuencias en queries, índices y unicidad.
- No omitir las migraciones. Todo cambio en el esquema debe pasar por el sistema de migraciones del proyecto.
- No crear índices en todas las columnas "por si acaso". Cada índice ocupa espacio y ralentiza las escrituras.
- No ignorar los tipos de datos. Usar el tipo más específico posible: `TIMESTAMP` para fechas, `DECIMAL` para dinero, `UUID` para identificadores distribuidos.
- No normalizar en exceso para escenarios de alta lectura. A veces una desnormalización controlada y documentada es la decisión correcta cuando el patrón de acceso lo justifica.
- No diseñar sin conocer los patrones de consulta. El esquema debe servir a las queries que la aplicación ejecutará, no al revés.
- No olvidar los índices para las queries más frecuentes. Diseñar los índices junto con el esquema, no como una corrección posterior.
