# Modelo de amenazas: {{nombre_componente}}

**Fecha:** {{fecha}}
**Autor:** security-officer
**Metodología:** STRIDE

## Superficie de ataque

{{superficie_de_ataque}}

## Activos a proteger

| Activo | Clasificación | Impacto de compromiso |
|--------|--------------|----------------------|
| {{activo_1}} | {{clasificacion_1}} | {{impacto_1}} |

## Análisis STRIDE

### Spoofing (suplantación de identidad)
{{analisis_spoofing}}

### Tampering (manipulación)
{{analisis_tampering}}

### Repudiation (repudio)
{{analisis_repudiation}}

### Information Disclosure (fuga de información)
{{analisis_disclosure}}

### Denial of Service (denegación de servicio)
{{analisis_dos}}

### Elevation of Privilege (elevación de privilegios)
{{analisis_elevation}}

## Matriz de riesgo

| Amenaza | Probabilidad | Impacto | Riesgo | Mitigación |
|---------|-------------|---------|--------|------------|
| {{amenaza_1}} | {{prob_1}} | {{imp_1}} | {{riesgo_1}} | {{mit_1}} |

## Recomendaciones

{{recomendaciones}}

<!-- EJEMPLO COMPLETADO ─────────────────────────────────────────────────

# Modelo de amenazas: memoria persistente (alfred-memory.db)

**Fecha:** 2026-02-21
**Autor:** security-officer
**Metodologia:** STRIDE

## Superficie de ataque

- Fichero SQLite local en `.claude/alfred-memory.db`.
- Hooks que escriben datos de la sesion en la DB.
- Servidor MCP stdio que expone 15 herramientas de lectura/escritura.
- Funcion import que lee ficheros externos (git log, ADRs en disco).

## Activos a proteger

| Activo | Clasificacion | Impacto de compromiso |
|--------|--------------|----------------------|
| Contenido de la DB | Confidencial | Fuga de decisiones de diseno, posibles secretos residuales |
| Integridad de la DB | Critico | Datos corruptos invalidan la trazabilidad |
| Fichero DB en disco | Sensible | Acceso no autorizado a todo el historial |

## Analisis STRIDE

### Spoofing (suplantacion de identidad)
Riesgo bajo. La DB es local y no tiene autenticacion porque corre dentro del
proceso de Claude Code, que ya esta autenticado.

### Tampering (manipulacion)
Riesgo medio. Un proceso local malicioso podria modificar la DB. Mitigacion:
permisos 0600 y WAL mode que protege contra escrituras parciales.

### Repudiation (repudio)
Riesgo bajo. Los eventos incluyen timestamps y source_type que permiten
rastrear el origen. Los commits tienen SHA verificable.

### Information Disclosure (fuga de informacion)
Riesgo alto. La DB podria contener secretos si sanitize_content() falla.
Mitigacion: 14 patrones regex aplicados a todo texto antes de persistir.

### Denial of Service (denegacion de servicio)
Riesgo bajo. Una DB muy grande podria ralentizar las busquedas. Mitigacion:
purga automatica con retention_days y limites en queries.

### Elevation of Privilege (elevacion de privilegios)
Riesgo bajo. El servidor MCP no ejecuta codigo arbitrario; solo lee y
escribe en SQLite mediante queries parametrizadas.

## Matriz de riesgo

| Amenaza | Probabilidad | Impacto | Riesgo | Mitigacion |
|---------|-------------|---------|--------|------------|
| Secretos en DB | Media | Alto | Alto | sanitize_content() con 14 patrones |
| DB accesible por otros usuarios | Baja | Alto | Medio | chmod 0600 + check_health() |
| SQL injection via MCP | Baja | Alto | Medio | Queries parametrizadas en todo el codigo |
| Corrupcion por crash | Baja | Medio | Bajo | WAL mode + backup antes de migraciones |

## Recomendaciones

1. Mantener sanitize_content() actualizado con nuevos patrones de secretos.
2. Ejecutar check_health() periodicamente para verificar permisos y FTS.
3. No exponer la DB via red (solo acceso local).
4. Considerar cifrado at-rest en futuras versiones.

──────────────────────────────────────────────── FIN DEL EJEMPLO -->
