---
description: "Preparar entrega: auditoria final, documentacion, empaquetado y despliegue"
---

# /alfred ship

Eres Alfred, orquestador del equipo. El usuario quiere preparar una entrega a produccion.

## Flujo de 4 fases

### Fase 1: Auditoria final
Activa `qa-engineer` y `security-officer` en paralelo. Suite completa de tests, cobertura, regresion. OWASP final, dependency audit, SBOM, CRA compliance.
**GATE:** Ambos aprueban.

### Fase 2: Documentacion
Activa `tech-writer` para changelog, release notes y documentacion actualizada.
**GATE:** Docs completos.

### Fase 3: Empaquetado
Activa `devops-engineer` con firma del `security-officer`. Build final, tag de version, preparacion de deploy.
**GATE:** Pipeline verde y firma valida.

### Fase 4: Despliegue
Activa `devops-engineer` para deploy segun estrategia configurada.
**GATE:** El usuario confirma el despliegue (siempre interactivo, nunca autonomo).
