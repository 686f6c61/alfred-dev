---
name: dependency-update
description: "Revisar dependencias desactualizadas, con CVEs o end-of-life, y proponer actualizaciones seguras. También: actualizar paquetes, actualizar dependencias, Dependabot, Renovate, versión desactualizada, breaking changes."
---

# Actualización segura de dependencias

## Resumen

Este skill revisa las dependencias del proyecto para detectar versiones desactualizadas, vulnerabilidades conocidas (CVEs) y paquetes en end-of-life. No se trata de actualizar todo ciegamente: cada actualización se evalúa por riesgo, impacto y necesidad antes de proponerla.

Las dependencias desactualizadas son una de las principales fuentes de vulnerabilidades. Pero una actualización precipitada puede romper el proyecto. El equilibrio es actualizar lo necesario, cuando es seguro hacerlo.

## Proceso

### Paso 1: inventariar dependencias

Según el runtime del proyecto:

**Node/npm:**
```bash
npm outdated
npm audit
```

**Python/pip:**
```bash
pip list --outdated
pip-audit
```

**Rust/Cargo:**
```bash
cargo outdated
cargo audit
```

### Paso 2: clasificar por urgencia

| Categoría | Descripción | Acción |
|-----------|-------------|--------|
| **Crítica** | CVE con severidad alta/crítica en producción | Actualizar inmediatamente |
| **Alta** | CVE con severidad media o dependencia en end-of-life | Planificar actualización esta semana |
| **Media** | Versión major desactualizada sin CVE conocido | Evaluar breaking changes y planificar |
| **Baja** | Versión minor/patch desactualizada sin CVE | Actualizar cuando sea conveniente |

### Paso 3: evaluar cada actualización

Para cada dependencia que necesite actualización:

- **Breaking changes**: leer el changelog entre la versión actual y la nueva. Hay breaking changes?
- **Compatibilidad**: es compatible con el resto del stack? (versión de Node, otras dependencias).
- **Tamaño del cambio**: minor/patch suelen ser seguros. Major requiere más cuidado.
- **Tests**: hay tests que cubran el uso de esta dependencia? Si no, escribirlos antes de actualizar.

### Paso 4: proponer el plan de actualización

Generar un informe con:

1. **Resumen**: número de dependencias desactualizadas por categoría.
2. **Actualizaciones críticas**: lista con CVE, severidad y versión objetivo.
3. **Actualizaciones recomendadas**: lista con razón y riesgo estimado.
4. **Actualizaciones pospuestas**: las que no merece la pena actualizar ahora y por qué.

### Paso 5: ejecutar las actualizaciones

Si el usuario aprueba:

- Actualizar una dependencia a la vez (no todas de golpe).
- Ejecutar los tests después de cada actualización.
- Si los tests fallan, investigar y corregir antes de continuar.
- Commitear cada actualización por separado para facilitar rollback.

## Qué NO hacer

- No actualizar todas las dependencias de golpe. Si algo se rompe, no sabrás qué lo causó.
- No ignorar las dependencias de desarrollo. Pueden inyectar código en el build.
- No forzar actualizaciones a major version sin evaluar breaking changes.
- No descartar CVEs por ser de severidad baja: el contexto del proyecto puede elevar su impacto.

## Clarificación

Este skill ejecuta actualizaciones concretas. Para auditar el estado de las dependencias primero, usar `dependency-audit`.
