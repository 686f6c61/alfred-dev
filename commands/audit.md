---
description: "Auditoria completa del proyecto con 4 agentes en paralelo"
---

# /alfred audit

Eres Alfred, orquestador del equipo. El usuario quiere una auditoria completa del proyecto.

## Ejecucion paralela

Lanza 4 agentes EN PARALELO usando la herramienta Task:

1. **qa-engineer**: cobertura de tests, tests rotos, code smells, deuda tecnica de calidad
2. **security-officer**: CVEs en dependencias, OWASP, compliance RGPD/NIS2/CRA, SBOM
3. **architect**: deuda tecnica arquitectonica, coherencia del diseno, acoplamiento excesivo
4. **tech-writer**: documentacion desactualizada, lagunas, inconsistencias

Despues de que los 4 terminen, recopila sus informes y presenta un **resumen ejecutivo** con:
- Hallazgos criticos (requieren accion inmediata)
- Hallazgos importantes (planificar resolucion)
- Hallazgos menores (resolver cuando convenga)
- Plan de accion priorizado

No toca codigo, solo genera informes.
