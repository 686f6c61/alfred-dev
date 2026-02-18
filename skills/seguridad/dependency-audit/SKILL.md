---
name: dependency-audit
description: "Usar para auditar dependencias contra CVEs, versiones desactualizadas y licencias"
---

# Auditoria de dependencias

## Resumen

Este skill ejecuta una auditoria completa de las dependencias del proyecto, verificando vulnerabilidades conocidas (CVEs), versiones desactualizadas, licencias incompatibles y paquetes abandonados. Las dependencias son el vector de ataque mas comun en la cadena de suministro de software; este analisis es obligatorio antes de cualquier release y recomendable de forma periodica.

HARD-GATE: si se detecta una vulnerabilidad critica o alta sin parche disponible, el proceso se bloquea hasta que se resuelva o se documente una mitigacion explicitamente aceptada por el usuario.

## Proceso

1. **Detectar el ecosistema del proyecto.** Identificar el gestor de paquetes (npm, pip, cargo, go modules, composer, etc.) y ejecutar la herramienta de auditoria correspondiente:

   - **Node.js:** `npm audit` o `yarn audit` o `pnpm audit`.
   - **Python:** `pip-audit` o `safety check`.
   - **Rust:** `cargo audit`.
   - **Go:** `govulncheck`.
   - **PHP:** `composer audit`.

2. **Analizar vulnerabilidades por severidad:**

   | Severidad | Accion |
   |-----------|--------|
   | Critica | HARD-GATE: bloquear. Actualizar o eliminar la dependencia inmediatamente. |
   | Alta | HARD-GATE: bloquear. Actualizar o documentar mitigacion aceptada por el usuario. |
   | Media | Planificar actualizacion. Crear issue si no se puede resolver ahora. |
   | Baja | Documentar. Resolver cuando sea conveniente. |

3. **Verificar versiones.** Para cada dependencia, comprobar:

   - Version instalada vs ultima version estable.
   - Si hay breaking changes entre la version actual y la ultima (consultar changelog).
   - Si la dependencia sigue un esquema de versionado semantico.
   - Antiguedad de la version instalada (mas de 1 ano sin actualizar es una senal de alerta).

4. **Verificar licencias.** Listar las licencias de todas las dependencias (directas y transitivas) y verificar compatibilidad:

   - MIT, Apache 2.0, BSD: generalmente compatibles con cualquier proyecto.
   - GPL, AGPL: problematicas para proyectos propietarios.
   - Licencias no estandar o sin licencia: riesgo legal, evitar.

5. **Identificar paquetes abandonados.** Criterios de abandono:

   - Ultimo commit hace mas de 2 anos.
   - Issues criticas abiertas sin respuesta durante meses.
   - Mantenedor unico que ha dejado de responder.
   - Repositorio archivado.

6. **Generar informe.** Documentar los hallazgos en formato tabular con acciones recomendadas para cada problema encontrado.

## Criterios de exito

- Se ha ejecutado la herramienta de auditoria del ecosistema correspondiente.
- No hay vulnerabilidades criticas o altas sin resolver o sin mitigacion documentada.
- Las licencias son compatibles con el proyecto.
- Los paquetes abandonados estan identificados con alternativas propuestas.
- El informe incluye acciones concretas para cada hallazgo.
