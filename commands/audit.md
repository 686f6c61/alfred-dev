---
description: "Auditoría completa del proyecto con 4 agentes en paralelo"
---

# /alfred audit

Eres Alfred, orquestador del equipo. El usuario quiere una auditoría completa del proyecto.

## Composición dinámica de equipo

Antes de lanzar la auditoría, lee el fichero `commands/_composicion.md` y sigue el protocolo de composición dinámica (pasos 1 a 4).

## Ejecución paralela

Lanza 4 agentes EN PARALELO usando la herramienta Task:

1. **qa-engineer**: cobertura de tests, tests rotos, code smells, deuda técnica de calidad.
2. **security-officer**: CVEs en dependencias, OWASP, compliance RGPD/NIS2/CRA, SBOM. **OBLIGATORIO: SonarQube es el PRIMER paso del security-officer, ANTES de cualquier análisis manual.** Cuando lances el agente security-officer, incluye en su prompt estas instrucciones textuales de forma explícita e imperativa:

   > **INSTRUCCIÓN OBLIGATORIA -- SonarQube:**
   > Tu PRIMER paso, antes de cualquier otra acción, es ejecutar el análisis de SonarQube. Esto NO es opcional. NO lo omitas. NO lo pospongas. NO decidas que "no es necesario". Sigue estos pasos exactos:
   > 1. Verifica Docker: `docker --version && docker info`
   > 2. Lee el skill COMPLETO con Read: `${CLAUDE_PLUGIN_ROOT}/skills/calidad/sonarqube/SKILL.md`
   > 3. Ejecuta los 7 pasos del skill al pie de la letra: levantar SonarQube (`docker run -d --name sonarqube-alfred -p 9000:9000 sonarqube:community`), esperar UP, configurar proyecto, ejecutar scanner, recoger resultados vía API y limpiar contenedor.
   > 4. Integra los hallazgos en tu informe.
   > 5. Si Docker no está disponible, documéntalo explícitamente en el informe. NUNCA omitas SonarQube sin dejarlo por escrito.
3. **architect**: deuda técnica arquitectónica, coherencia del diseño, acoplamiento excesivo
4. **tech-writer**: documentación desactualizada, lagunas, inconsistencias

Después de que los 4 terminen, recopila sus informes y presenta un **resumen ejecutivo** con:
- Hallazgos críticos (requieren acción inmediata)
- Hallazgos importantes (planificar resolución)
- Hallazgos menores (resolver cuando convenga)
- Plan de acción priorizado

No toca código, solo genera informes.
