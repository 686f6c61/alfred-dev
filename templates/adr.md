# ADR-{{numero}}: {{titulo}}

**Fecha:** {{fecha}}
**Estado:** {{estado}} (propuesto | aceptado | rechazado | obsoleto)
**Autor:** architect

## Contexto

{{contexto_del_problema}}

## Opciones evaluadas

### Opción 1: {{nombre_opcion_1}}

{{descripcion_opcion_1}}

**Ventajas:**
{{ventajas_1}}

**Desventajas:**
{{desventajas_1}}

### Opción 2: {{nombre_opcion_2}}

{{descripcion_opcion_2}}

**Ventajas:**
{{ventajas_2}}

**Desventajas:**
{{desventajas_2}}

### Opción 3: {{nombre_opcion_3}}

{{descripcion_opcion_3}}

**Ventajas:**
{{ventajas_3}}

**Desventajas:**
{{desventajas_3}}

## Decisión

{{decision_tomada}}

## Justificación

{{razonamiento}}

## Consecuencias

### Positivas
{{consecuencias_positivas}}

### Negativas
{{consecuencias_negativas}}

## Referencias

{{referencias}}

<!-- EJEMPLO COMPLETADO ─────────────────────────────────────────────────

# ADR-003: base de datos para memoria persistente

**Fecha:** 2026-02-20
**Estado:** aceptado
**Autor:** architect

## Contexto

Alfred Dev necesita almacenar decisiones, commits e iteraciones entre sesiones
de forma local, sin dependencias externas ni servicios remotos. Los datos son
estructurados (relaciones entre entidades) y el volumen es bajo (cientos de
registros por proyecto, no millones).

## Opciones evaluadas

### Opcion 1: SQLite

Base de datos relacional embebida. Fichero unico, sin servidor, con SQL
completo, soporte para FTS5 (busqueda de texto) y WAL (lecturas concurrentes).

**Ventajas:**
- Cero dependencias: sqlite3 viene en la stdlib de Python.
- Transacciones ACID con WAL.
- FTS5 para busqueda de texto completo.
- Un unico fichero facil de respaldar y migrar.

**Desventajas:**
- No escala a escrituras concurrentes masivas (irrelevante para este caso).
- Las migraciones de esquema requieren logica manual.

### Opcion 2: JSON plano

Un fichero JSON por proyecto con toda la informacion serializada.

**Ventajas:**
- Maxima simplicidad: leer, modificar, escribir.
- Sin schema: flexible ante cambios.

**Desventajas:**
- Sin transacciones: riesgo de corrupcion si el proceso se interrumpe.
- Sin busqueda eficiente: hay que cargar todo en memoria.
- Sin relaciones: desnormalizacion obligatoria.

### Opcion 3: TinyDB

Base de datos documental embebida en Python, almacenada en JSON.

**Ventajas:**
- API Pythonica sencilla.
- Sin dependencias nativas (puro Python).

**Desventajas:**
- Dependencia externa (viola la politica de cero deps).
- Sin FTS5 ni SQL.
- Rendimiento limitado con volumen medio.

## Decision

SQLite con FTS5 y WAL.

## Justificacion

El caso de uso es estructurado (decisiones, commits, iteraciones con
relaciones entre ellos), de volumen bajo y requiere busqueda textual.
SQLite cubre todos los requisitos sin anadir dependencias. La stdlib de
Python incluye sqlite3, y FTS5 esta disponible en la mayoria de builds.
El modo WAL permite lecturas concurrentes mientras los hooks escriben.

## Consecuencias

### Positivas
- Cero dependencias externas mantenidas.
- Busqueda textual rapida con FTS5.
- Backup trivial: copiar un fichero.
- Migraciones controladas con versionado de esquema.

### Negativas
- Las migraciones requieren SQL manual y logica de versionado.
- Si FTS5 no esta disponible en algun build de Python, se usa LIKE como
  fallback (mas lento pero funcional).

## Referencias

- https://www.sqlite.org/wal.html
- https://www.sqlite.org/fts5.html

──────────────────────────────────────────────── FIN DEL EJEMPLO -->
