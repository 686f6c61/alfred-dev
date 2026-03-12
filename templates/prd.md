# PRD: {{nombre_feature}}

**Fecha:** {{fecha}}
**Autor:** product-owner
**Estado:** {{estado}}

## Problema

{{descripcion_problema}}

## Contexto

{{contexto_negocio}}

## Solución propuesta

{{descripcion_solucion}}

## Historias de usuario

{{historias_de_usuario}}

## Criterios de aceptación

{{criterios_aceptacion}}

## Métricas de éxito

| Métrica | Valor objetivo | Cómo se mide |
|---------|---------------|--------------|
| {{metrica_1}} | {{valor_1}} | {{medicion_1}} |

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| {{riesgo_1}} | {{prob_1}} | {{impacto_1}} | {{mitigacion_1}} |

## Fuera de alcance

{{fuera_de_alcance}}

## Dependencias

{{dependencias}}

<!-- EJEMPLO COMPLETADO ─────────────────────────────────────────────────

# PRD: sistema de memoria persistente

**Fecha:** 2026-02-18
**Autor:** product-owner
**Estado:** aprobado

## Problema

Alfred Dev pierde todo el contexto de decisiones y commits al cerrar una sesion
de Claude Code. Cuando el desarrollador retoma el trabajo, ni Alfred ni los
agentes recuerdan que se decidio, por que se decidio ni que se ha implementado.
Esto obliga al usuario a repetir contexto constantemente.

## Contexto

Los plugins de Claude Code no tienen persistencia nativa entre sesiones. La
unica forma de conservar informacion es escribir en disco. El proyecto ya usa
SQLite para la memoria persistente, lo que establece un precedente tecnologico.

## Solucion propuesta

Base de datos SQLite local por proyecto (`.claude/alfred-memory.db`) que
almacena decisiones, commits, iteraciones y eventos. Captura automatica
mediante hooks y consulta via agente El Bibliotecario o servidor MCP.

## Historias de usuario

- Como desarrollador, quiero que Alfred recuerde las decisiones de diseno
  de sesiones anteriores para no tener que repetirlas.
- Como arquitecto, quiero poder buscar por que se eligio una tecnologia
  concreta hace semanas, citando la decision original.
- Como nuevo miembro del equipo, quiero consultar el historial de decisiones
  del proyecto para entender el razonamiento detras de la arquitectura actual.

## Criterios de aceptacion

- Given una sesion nueva, when se inicia Alfred, then las decisiones de la
  iteracion activa (o las 5 ultimas) se inyectan en el contexto.
- Given una decision registrada, when se busca por texto, then aparece en
  los resultados con su justificacion completa.
- Given un commit capturado, when se consulta, then muestra SHA, autor,
  mensaje y ficheros afectados.

## Metricas de exito

| Metrica | Valor objetivo | Como se mide |
|---------|---------------|--------------|
| Repeticion de contexto | < 1 vez por sesion | Feedback del usuario |
| Tiempo de busqueda | < 500 ms | Benchmark con 500 decisiones |
| Adopcion | > 50% de usuarios activos | Config con memoria.enabled: true |

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Fuga de secretos en la DB | Media | Alto | sanitize_content() con patrones regex |
| DB corrupta por crash | Baja | Alto | WAL mode + backup antes de migraciones |
| Rendimiento con DB grande | Baja | Medio | FTS5 + limites de retencion |

## Fuera de alcance

- Sincronizacion entre maquinas o repositorios.
- Interfaz grafica para editar decisiones.
- Versionado de la DB (se usan migraciones de esquema).

## Dependencias

- SQLite 3.x con FTS5 (incluido en Python 3.10+ stdlib).
- Hooks PostToolUse para captura automatica.

──────────────────────────────────────────────── FIN DEL EJEMPLO -->
