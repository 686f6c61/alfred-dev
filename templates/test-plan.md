# Plan de testing: {{nombre_feature}}

**Fecha:** {{fecha}}
**Autor:** qa-engineer
**Versión:** {{version}}

## Alcance

{{alcance_del_testing}}

## Estrategia

| Tipo | Cobertura | Herramienta |
|------|-----------|-------------|
| Unitarios | {{cobertura_unit}} | {{herramienta_unit}} |
| Integración | {{cobertura_int}} | {{herramienta_int}} |
| E2E | {{cobertura_e2e}} | {{herramienta_e2e}} |

## Escenarios críticos (prioridad alta)

{{escenarios_criticos}}

## Escenarios principales (prioridad media)

{{escenarios_principales}}

## Edge cases (prioridad baja)

{{edge_cases}}

## Escenarios negativos

{{escenarios_negativos}}

## Datos de prueba

{{datos_de_prueba}}

## Criterios de paso

- [ ] Todos los tests críticos pasan
- [ ] Cobertura mínima: {{porcentaje_cobertura}}%
- [ ] Sin regresiones detectadas
- [ ] Security review aprobado

<!-- EJEMPLO COMPLETADO ─────────────────────────────────────────────────

# Plan de testing: memoria persistente

**Fecha:** 2026-02-21
**Autor:** qa-engineer
**Version:** 0.2.0

## Alcance

Cubrir el modulo core/memory.py (MemoryDB), los hooks de captura automatica
(memory-capture.py, commit-capture.py) y el servidor MCP (memory_server.py).

## Estrategia

| Tipo | Cobertura | Herramienta |
|------|-----------|-------------|
| Unitarios | 90% de MemoryDB | pytest + unittest |
| Integracion | Hooks + DB real | pytest con tempfile |
| E2E | MCP stdio completo | pytest + subprocess |

## Escenarios criticos (prioridad alta)

- Crear iteracion, registrar decision, buscar por texto: resultado correcto.
- sanitize_content() detecta y reemplaza todos los patrones de secretos.
- Permisos del fichero DB son 0600 tras creacion.
- Migracion de esquema v1 a v3 sin perdida de datos.
- FTS5 fallback a LIKE cuando no esta disponible.

## Escenarios principales (prioridad media)

- Busqueda con filtros temporales (since/until) devuelve solo resultados
  dentro del rango.
- Importar historial git crea commits con SHA, autor y ficheros.
- Exportar decisiones genera Markdown con formato ADR.
- check_health() detecta permisos incorrectos y FTS desincronizado.

## Edge cases (prioridad baja)

- DB con 10.000 decisiones: busqueda en < 1 segundo.
- Query con caracteres especiales FTS5 (comillas, asteriscos).
- Iteracion sin decisiones ni commits (vacia pero valida).
- Dos sesiones simultaneas escribiendo en la misma DB (WAL).

## Escenarios negativos

- JSON invalido en stdin del hook: exit 0 sin crash.
- DB corrupta: error descriptivo, no traceback.
- Memoria deshabilitada en config: hooks salen sin efecto.

## Datos de prueba

- Decisiones con titulos que contienen tildes y caracteres especiales.
- Commits con mensajes multilinea.
- Patrones de secretos reales (AKIA..., sk-..., ghp_...).

## Criterios de paso

- [x] Todos los tests criticos pasan
- [x] Cobertura minima: 80%
- [x] Sin regresiones detectadas
- [x] Security review aprobado

──────────────────────────────────────────────── FIN DEL EJEMPLO -->
