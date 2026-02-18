---
name: monitoring-setup
description: "Usar para configurar observabilidad del servicio"
---

# Configurar observabilidad

## Resumen

Este skill configura las tres patas de la observabilidad: logging estructurado, error tracking y metricas. Sin observabilidad, operar un servicio en produccion es como conducir de noche sin luces: todo va bien hasta que no. El objetivo es poder responder a tres preguntas fundamentales: que esta pasando ahora, que ha pasado antes y por que algo falla.

## Proceso

1. **Configurar logging estructurado.** Los logs en texto plano son dificiles de buscar y analizar. Usar JSON como formato estandar:

   ```json
   {
     "timestamp": "2024-03-15T10:30:00Z",
     "level": "error",
     "message": "Fallo al procesar pago",
     "service": "payment-service",
     "requestId": "abc-123",
     "userId": "usr-456",
     "error": {
       "type": "PaymentGatewayError",
       "message": "Timeout after 30s",
       "stack": "..."
     }
   }
   ```

   Principios del logging:

   - Cada entrada tiene timestamp, nivel, mensaje y contexto.
   - Los request IDs permiten trazar un flujo a traves de multiples servicios.
   - Los datos sensibles (contrasenas, tokens, datos personales) NUNCA aparecen en logs.
   - Niveles: `debug` (desarrollo), `info` (flujo normal), `warn` (situacion inusual), `error` (algo fallo).

2. **Configurar error tracking.** Herramientas como Sentry, Bugsnag o Rollbar proporcionan contexto rico para cada error:

   - Instalacion del SDK en la aplicacion.
   - Configuracion del DSN (endpoint de reporte).
   - Source maps para errores de frontend (si aplica).
   - Agrupacion de errores para evitar ruido.
   - Alertas para errores nuevos o con picos de frecuencia.
   - Integracion con el sistema de issues (GitHub, Jira) para seguimiento.

3. **Definir metricas de negocio y tecnicas.** Las metricas cuentan la historia del sistema en numeros:

   - **Tecnicas:** latencia de requests (p50, p95, p99), tasa de error, uso de CPU/memoria, conexiones a base de datos.
   - **Negocio:** registros por hora, transacciones completadas, tasa de conversion, usuarios activos.

   Las metricas de negocio son las que mas interesan al equipo de producto; las tecnicas son las que interesan a operaciones.

4. **Configurar alertas.** Las alertas deben ser accionables, no ruidosas:

   - **Critica:** el servicio esta caido o perdiendo datos. Requiere accion inmediata (pagina al ingeniero de guardia).
   - **Alta:** tasa de error elevada o degradacion significativa. Requiere atencion en la proxima hora.
   - **Media:** tendencia preocupante que no requiere accion inmediata. Revisar en el proximo dia laborable.

   Evitar alertas que nadie mira. Si una alerta se ignora sistematicamente, o se elimina o se ajusta su umbral.

5. **Implementar health endpoints.** La aplicacion debe exponer su estado de salud:

   - `GET /health`: responde 200 si la aplicacion esta corriendo (liveness).
   - `GET /ready`: responde 200 si la aplicacion puede procesar requests (readiness). Incluye verificacion de dependencias criticas (base de datos, cache).

6. **Documentar la configuracion.** Dejar claro donde se visualizan los logs, como se accede al error tracking y que dashboards estan disponibles.

## Criterios de exito

- Los logs son estructurados (JSON) con timestamp, nivel, mensaje y contexto.
- No hay datos sensibles en los logs.
- El error tracking esta integrado y agrupa errores correctamente.
- Las metricas cubren al menos latencia, tasa de error y una metrica de negocio.
- Las alertas son accionables y estan clasificadas por severidad.
- Los health endpoints estan implementados y responden correctamente.
